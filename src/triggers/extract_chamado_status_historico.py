import pyodbc
import os
import logging
import azure.functions as func

app = func.Blueprint()


def get_source_connection() -> pyodbc.Connection:
    conn_str = (
        "DRIVER={ODBC Driver 18 for SQL Server};"
        f"SERVER={os.getenv('SQL_SERVER_SOURCE')};"
        f"DATABASE={os.getenv('SQL_DATABASE_SOURCE')};"
        f"UID={os.getenv('SQL_USER_SOURCE')};"
        f"PWD={os.getenv('SQL_PASSWORD_SOURCE')};"
        "Encrypt=yes;"
        "TrustServerCertificate=no;"
        "Connection Timeout=30;"
    )
    return pyodbc.connect(conn_str)


def get_target_connection() -> pyodbc.Connection:
    conn_str = (
        "DRIVER={ODBC Driver 18 for SQL Server};"
        f"SERVER={os.getenv('SQL_SERVER_TARGET')};"
        f"DATABASE={os.getenv('SQL_DATABASE_TARGET')};"
        f"UID={os.getenv('SQL_USER_TARGET')};"
        f"PWD={os.getenv('SQL_PASSWORD_TARGET')};"
        "Encrypt=yes;"
        "TrustServerCertificate=no;"
        "Connection Timeout=30;"
    )
    return pyodbc.connect(conn_str)


@app.timer_trigger(schedule="0 20 12 * * *", arg_name="myTimer", run_on_startup=False,
                   use_monitor=False)
def extract_chamado_status_historico(myTimer: func.TimerRequest) -> None:
    """
    Lê todo o histórico de status dos chamados e faz upsert em
    corptech.chamado_status_historico.

    FKs resolvidas por chave natural:
      - id_chamado              <- nr_chamado
      - id_analista_responsavel <- cd_analista
      - id_fila                 <- cd_fila

    Chave do MERGE: cd_registro_origem (identificador único vindo do sistema de origem).

    ATENÇÃO: ds_status_chamado tem CHECK constraint no destino.
    Valores aceitos: OPEN, IN_PROGRESS, PENDING, RESOLVED, CLOSED, CANCELLED.
    """
    logging.info("extract_chamado_status_historico: iniciando.")

    SELECT_SQL = """
        SELECT
            c.nr_chamado,
            csh.ds_status_chamado,
            csh.dt_inicio_status,
            csh.dt_fim_status,
            csh.qt_tempo_status_minutos,
            a.cd_analista   AS cd_analista_responsavel,
            f.cd_fila,
            csh.dt_inclusao,
            csh.dt_atualizacao,
            csh.nm_sistema_origem,
            csh.cd_registro_origem
        FROM itsm.chamado_status_historico AS csh
        INNER JOIN itsm.chamado  AS c ON c.id_chamado  = csh.id_chamado
        LEFT JOIN  itsm.analista AS a ON a.id_analista = csh.id_analista_responsavel
        LEFT JOIN  itsm.fila     AS f ON f.id_fila     = csh.id_fila
    """

    UPSERT_SQL = """
        MERGE corptech.chamado_status_historico AS tgt
        USING (
            SELECT
                ch_dst.id_chamado,
                src.ds_status_chamado,
                src.dt_inicio_status,
                src.dt_fim_status,
                src.qt_tempo_status_minutos,
                a_dst.id_analista AS id_analista_responsavel,
                f_dst.id_fila,
                src.dt_inclusao,
                src.dt_atualizacao,
                src.nm_sistema_origem,
                src.cd_registro_origem
            FROM (VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)) AS src (
                nr_chamado, ds_status_chamado, dt_inicio_status, dt_fim_status,
                qt_tempo_status_minutos, cd_analista_responsavel, cd_fila,
                dt_inclusao, dt_atualizacao, nm_sistema_origem, cd_registro_origem
            )
            INNER JOIN corptech.chamado  AS ch_dst ON ch_dst.nr_chamado = src.nr_chamado
            LEFT JOIN  corptech.analista AS a_dst  ON a_dst.cd_analista = src.cd_analista_responsavel
            LEFT JOIN  corptech.fila     AS f_dst  ON f_dst.cd_fila     = src.cd_fila
        ) AS resolved
        ON tgt.cd_registro_origem = resolved.cd_registro_origem
        WHEN MATCHED THEN
            UPDATE SET
                id_chamado              = resolved.id_chamado,
                ds_status_chamado       = resolved.ds_status_chamado,
                dt_inicio_status        = resolved.dt_inicio_status,
                dt_fim_status           = resolved.dt_fim_status,
                qt_tempo_status_minutos = resolved.qt_tempo_status_minutos,
                id_analista_responsavel = resolved.id_analista_responsavel,
                id_fila                 = resolved.id_fila,
                dt_atualizacao          = SYSUTCDATETIME(),
                nm_sistema_origem       = resolved.nm_sistema_origem
        WHEN NOT MATCHED THEN
            INSERT (
                id_chamado, ds_status_chamado, dt_inicio_status, dt_fim_status,
                qt_tempo_status_minutos, id_analista_responsavel, id_fila,
                dt_inclusao, dt_atualizacao, nm_sistema_origem, cd_registro_origem
            )
            VALUES (
                resolved.id_chamado, resolved.ds_status_chamado, resolved.dt_inicio_status,
                resolved.dt_fim_status, resolved.qt_tempo_status_minutos,
                resolved.id_analista_responsavel, resolved.id_fila,
                resolved.dt_inclusao, resolved.dt_atualizacao,
                resolved.nm_sistema_origem, resolved.cd_registro_origem
            );
    """

    try:
        with get_source_connection() as src_conn:
            rows = src_conn.cursor().execute(SELECT_SQL).fetchall()

        logging.info(f"extract_chamado_status_historico: {len(rows)} linha(s) lida(s) da origem.")

        with get_target_connection() as dst_conn:
            cursor = dst_conn.cursor()
            cursor.fast_executemany = True
            cursor.executemany(UPSERT_SQL, rows)
            dst_conn.commit()

        logging.info("extract_chamado_status_historico: upsert concluído.")

    except Exception as e:
        logging.error(f"extract_chamado_status_historico: erro – {e}")
        raise