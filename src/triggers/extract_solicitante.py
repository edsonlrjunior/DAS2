import logging
import azure.functions as func
import os
import pyodbc

app = func.Blueprint()

@app.timer_trigger(schedule="0 0 12 * * *", arg_name="myTimer", run_on_startup=False,
                   use_monitor=False)
def extract_solicitante(myTimer: func.TimerRequest) -> None:
    logging.info("extract_solicitante: iniciando.")

    SELECT_SQL = """
        SELECT
            s.cd_solicitante,
            co.cd_cliente_organizacao,   -- natural key for FK resolution
            s.nm_solicitante,
            s.ds_email,
            s.ds_telefone,
            s.fl_ativo,
            s.dt_inclusao,
            s.dt_atualizacao,
            s.nm_sistema_origem,
            s.cd_registro_origem
        FROM itsm.solicitante AS s
        INNER JOIN itsm.cliente_organizacao AS co
               ON co.id_cliente_organizacao = s.id_cliente_organizacao
    """

    UPSERT_SQL = """
        MERGE corptech.solicitante AS tgt
        USING (
            SELECT
                src.cd_solicitante,
                co_dst.id_cliente_organizacao,
                src.nm_solicitante,
                src.ds_email,
                src.ds_telefone,
                src.fl_ativo,
                src.dt_inclusao,
                src.dt_atualizacao,
                src.nm_sistema_origem,
                src.cd_registro_origem
            FROM (VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)) AS src (
                cd_solicitante, cd_cliente_organizacao, nm_solicitante,
                ds_email, ds_telefone, fl_ativo,
                dt_inclusao, dt_atualizacao, nm_sistema_origem, cd_registro_origem
            )
            INNER JOIN corptech.cliente_organizacao AS co_dst
                    ON co_dst.cd_cliente_organizacao = src.cd_cliente_organizacao
        ) AS resolved
        ON tgt.cd_solicitante = resolved.cd_solicitante
        WHEN MATCHED THEN
            UPDATE SET
                id_cliente_organizacao = resolved.id_cliente_organizacao,
                nm_solicitante         = resolved.nm_solicitante,
                ds_email               = resolved.ds_email,
                ds_telefone            = resolved.ds_telefone,
                fl_ativo               = resolved.fl_ativo,
                dt_atualizacao         = SYSUTCDATETIME(),
                nm_sistema_origem      = resolved.nm_sistema_origem,
                cd_registro_origem     = resolved.cd_registro_origem
        WHEN NOT MATCHED THEN
            INSERT (cd_solicitante, id_cliente_organizacao, nm_solicitante,
                    ds_email, ds_telefone, fl_ativo, dt_inclusao,
                    dt_atualizacao, nm_sistema_origem, cd_registro_origem)
            VALUES (resolved.cd_solicitante, resolved.id_cliente_organizacao, resolved.nm_solicitante,
                    resolved.ds_email, resolved.ds_telefone, resolved.fl_ativo, resolved.dt_inclusao,
                    resolved.dt_atualizacao, resolved.nm_sistema_origem, resolved.cd_registro_origem);
    """

    try:
        with get_source_connection() as src_conn:
            rows = src_conn.cursor().execute(SELECT_SQL).fetchall()

        logging.info(f"extract_solicitante: {len(rows)} linha(s) lida(s) da origem.")

        with get_target_connection() as dst_conn:
            cursor = dst_conn.cursor()
            cursor.fast_executemany = True
            cursor.executemany(UPSERT_SQL, rows)
            dst_conn.commit()

        logging.info("extract_solicitante: upsert concluído.")

    except Exception as e:
        logging.error(f"extract_solicitante: erro – {e}")
        
    
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