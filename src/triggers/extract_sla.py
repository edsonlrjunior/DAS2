import logging
import azure.functions as func
import os
import pyodbc

app = func.Blueprint()

@app.timer_trigger(schedule="0 0 12 * * *", arg_name="myTimer", run_on_startup=False,
                   use_monitor=False)
def extract_sla(myTimer: func.TimerRequest) -> None:
    logging.info("extract_sla: iniciando.")

    SELECT_SQL = """
        SELECT
            cd_sla,
            nm_sla,
            qt_meta_minutos,
            ds_descricao,
            fl_ativo,
            dt_inclusao,
            dt_atualizacao,
            nm_sistema_origem,
            cd_registro_origem
        FROM itsm.sla
    """

    UPSERT_SQL = """
        MERGE corptech.sla AS tgt
        USING (VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)) AS src (
            cd_sla, nm_sla, qt_meta_minutos, ds_descricao, fl_ativo,
            dt_inclusao, dt_atualizacao, nm_sistema_origem, cd_registro_origem
        )
        ON tgt.cd_sla = src.cd_sla
        WHEN MATCHED THEN
            UPDATE SET
                nm_sla             = src.nm_sla,
                qt_meta_minutos    = src.qt_meta_minutos,
                ds_descricao       = src.ds_descricao,
                fl_ativo           = src.fl_ativo,
                dt_atualizacao     = SYSUTCDATETIME(),
                nm_sistema_origem  = src.nm_sistema_origem,
                cd_registro_origem = src.cd_registro_origem
        WHEN NOT MATCHED THEN
            INSERT (cd_sla, nm_sla, qt_meta_minutos, ds_descricao, fl_ativo,
                    dt_inclusao, dt_atualizacao, nm_sistema_origem, cd_registro_origem)
            VALUES (src.cd_sla, src.nm_sla, src.qt_meta_minutos, src.ds_descricao, src.fl_ativo,
                    src.dt_inclusao, src.dt_atualizacao, src.nm_sistema_origem, src.cd_registro_origem);
    """

    try:
        with get_source_connection() as src_conn:
            rows = src_conn.cursor().execute(SELECT_SQL).fetchall()

        logging.info(f"extract_sla: {len(rows)} linha(s) lida(s) da origem.")

        with get_target_connection() as dst_conn:
            cursor = dst_conn.cursor()
            cursor.fast_executemany = True
            cursor.executemany(UPSERT_SQL, rows)
            dst_conn.commit()

        logging.info("extract_sla: upsert concluído.")

    except Exception as e:
        logging.error(f"extract_sla: erro – {e}")
        raise

def get_source_connection() -> pyodbc.Connection:
    """Abre a conexão com SOURCE banco."""
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
    """Abre a conexão com TARGET banco (corptech schema)."""
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