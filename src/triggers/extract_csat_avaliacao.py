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
def extract_csat_avaliacao(myTimer: func.TimerRequest) -> None:
    """
    Lê todas as avaliações CSAT da origem e faz upsert em corptech.csat_avaliacao.

    FKs resolvidas por chave natural:
      - id_chamado  <- nr_chamado
      - id_analista <- cd_analista

    Chave do MERGE: cd_registro_origem (identificador único vindo do sistema de origem).
    """
    logging.info("extract_csat_avaliacao: iniciando.")

    SELECT_SQL = """
        SELECT
            c.nr_chamado,
            a.cd_analista,
            ca.nr_score,
            ca.ds_comentario,
            ca.dt_avaliacao,
            ca.dt_inclusao,
            ca.dt_atualizacao,
            ca.nm_sistema_origem,
            ca.cd_registro_origem
        FROM itsm.csat_avaliacao AS ca
        INNER JOIN itsm.chamado  AS c ON c.id_chamado  = ca.id_chamado
        LEFT JOIN  itsm.analista AS a ON a.id_analista = ca.id_analista
    """

    UPSERT_SQL = """
        MERGE corptech.csat_avaliacao AS tgt
        USING (
            SELECT
                ch_dst.id_chamado,
                a_dst.id_analista,
                src.nr_score,
                src.ds_comentario,
                src.dt_avaliacao,
                src.dt_inclusao,
                src.dt_atualizacao,
                src.nm_sistema_origem,
                src.cd_registro_origem
            FROM (VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)) AS src (
                nr_chamado, cd_analista, nr_score, ds_comentario,
                dt_avaliacao, dt_inclusao, dt_atualizacao,
                nm_sistema_origem, cd_registro_origem
            )
            INNER JOIN corptech.chamado  AS ch_dst ON ch_dst.nr_chamado = src.nr_chamado
            LEFT JOIN  corptech.analista AS a_dst  ON a_dst.cd_analista = src.cd_analista
        ) AS resolved
        ON tgt.cd_registro_origem = resolved.cd_registro_origem
        WHEN MATCHED THEN
            UPDATE SET
                id_chamado        = resolved.id_chamado,
                id_analista       = resolved.id_analista,
                nr_score          = resolved.nr_score,
                ds_comentario     = resolved.ds_comentario,
                dt_avaliacao      = resolved.dt_avaliacao,
                dt_atualizacao    = SYSUTCDATETIME(),
                nm_sistema_origem = resolved.nm_sistema_origem
        WHEN NOT MATCHED THEN
            INSERT (
                id_chamado, id_analista, nr_score, ds_comentario,
                dt_avaliacao, dt_inclusao, dt_atualizacao,
                nm_sistema_origem, cd_registro_origem
            )
            VALUES (
                resolved.id_chamado, resolved.id_analista, resolved.nr_score,
                resolved.ds_comentario, resolved.dt_avaliacao, resolved.dt_inclusao,
                resolved.dt_atualizacao, resolved.nm_sistema_origem, resolved.cd_registro_origem
            );
    """

    try:
        with get_source_connection() as src_conn:
            rows = src_conn.cursor().execute(SELECT_SQL).fetchall()

        logging.info(f"extract_csat_avaliacao: {len(rows)} linha(s) lida(s) da origem.")

        with get_target_connection() as dst_conn:
            cursor = dst_conn.cursor()
            cursor.fast_executemany = True
            cursor.executemany(UPSERT_SQL, rows)
            dst_conn.commit()

        logging.info("extract_csat_avaliacao: upsert concluído.")

    except Exception as e:
        logging.error(f"extract_csat_avaliacao: erro – {e}")
        raise