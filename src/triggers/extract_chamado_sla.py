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
def extract_chamado_sla(myTimer: func.TimerRequest) -> None:
    """
    Lê todos os registros de SLA por chamado e faz upsert em corptech.chamado_sla.

    FKs resolvidas por chave natural:
      - id_chamado <- nr_chamado
      - id_sla     <- cd_sla

    Chave do MERGE: cd_registro_origem (identificador único vindo do sistema de origem).
    """
    logging.info("extract_chamado_sla: iniciando.")

    SELECT_SQL = """
        SELECT
            c.nr_chamado,
            s.cd_sla,
            cs.fl_breach,
            cs.qt_tempo_restante_minutos,
            cs.qt_tempo_decorrido_minutos,
            cs.qt_meta_minutos,
            cs.dt_referencia,
            cs.dt_inclusao,
            cs.dt_atualizacao,
            cs.nm_sistema_origem,
            cs.cd_registro_origem
        FROM itsm.chamado_sla AS cs
        INNER JOIN itsm.chamado AS c ON c.id_chamado = cs.id_chamado
        INNER JOIN itsm.sla     AS s ON s.id_sla     = cs.id_sla
    """

    UPSERT_SQL = """
        MERGE corptech.chamado_sla AS tgt
        USING (
            SELECT
                ch_dst.id_chamado,
                s_dst.id_sla,
                src.fl_breach,
                src.qt_tempo_restante_minutos,
                src.qt_tempo_decorrido_minutos,
                src.qt_meta_minutos,
                src.dt_referencia,
                src.dt_inclusao,
                src.dt_atualizacao,
                src.nm_sistema_origem,
                src.cd_registro_origem
            FROM (VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)) AS src (
                nr_chamado, cd_sla, fl_breach,
                qt_tempo_restante_minutos, qt_tempo_decorrido_minutos, qt_meta_minutos,
                dt_referencia, dt_inclusao, dt_atualizacao,
                nm_sistema_origem, cd_registro_origem
            )
            INNER JOIN corptech.chamado AS ch_dst ON ch_dst.nr_chamado = src.nr_chamado
            INNER JOIN corptech.sla     AS s_dst  ON s_dst.cd_sla      = src.cd_sla
        ) AS resolved
        ON tgt.cd_registro_origem = resolved.cd_registro_origem
        WHEN MATCHED THEN
            UPDATE SET
                id_chamado                 = resolved.id_chamado,
                id_sla                     = resolved.id_sla,
                fl_breach                  = resolved.fl_breach,
                qt_tempo_restante_minutos  = resolved.qt_tempo_restante_minutos,
                qt_tempo_decorrido_minutos = resolved.qt_tempo_decorrido_minutos,
                qt_meta_minutos            = resolved.qt_meta_minutos,
                dt_referencia              = resolved.dt_referencia,
                dt_atualizacao             = SYSUTCDATETIME(),
                nm_sistema_origem          = resolved.nm_sistema_origem
        WHEN NOT MATCHED THEN
            INSERT (
                id_chamado, id_sla, fl_breach,
                qt_tempo_restante_minutos, qt_tempo_decorrido_minutos, qt_meta_minutos,
                dt_referencia, dt_inclusao, dt_atualizacao,
                nm_sistema_origem, cd_registro_origem
            )
            VALUES (
                resolved.id_chamado, resolved.id_sla, resolved.fl_breach,
                resolved.qt_tempo_restante_minutos, resolved.qt_tempo_decorrido_minutos,
                resolved.qt_meta_minutos, resolved.dt_referencia, resolved.dt_inclusao,
                resolved.dt_atualizacao, resolved.nm_sistema_origem, resolved.cd_registro_origem
            );
    """

    try:
        with get_source_connection() as src_conn:
            rows = src_conn.cursor().execute(SELECT_SQL).fetchall()

        logging.info(f"extract_chamado_sla: {len(rows)} linha(s) lida(s) da origem.")

        with get_target_connection() as dst_conn:
            cursor = dst_conn.cursor()
            cursor.fast_executemany = True
            cursor.executemany(UPSERT_SQL, rows)
            dst_conn.commit()

        logging.info("extract_chamado_sla: upsert concluído.")

    except Exception as e:
        logging.error(f"extract_chamado_sla: erro – {e}")
        raise