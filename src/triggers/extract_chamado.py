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


@app.timer_trigger(schedule="0 10 12 * * *", arg_name="myTimer", run_on_startup=False,
                   use_monitor=False)
def extract_chamado(myTimer: func.TimerRequest) -> None:
    """
    Lê todos os chamados da origem e faz upsert em corptech.chamado.

    FKs resolvidas por chave natural:
      - id_analista_atual      <- cd_analista
      - id_reporter            <- cd_solicitante
      - id_categoria           <- cd_categoria
      - id_cliente_organizacao <- cd_cliente_organizacao
      - id_fila_atual          <- cd_fila
    """
    logging.info("extract_chamado: iniciando.")

    SELECT_SQL = """
        SELECT
            c.nr_chamado,
            c.ds_tipo_chamado,
            c.ds_status_chamado,
            c.ds_prioridade,
            c.dt_criacao,
            c.dt_resolucao,
            c.dt_ultima_atualizacao,
            a.cd_analista               AS cd_analista_atual,
            s.cd_solicitante,
            cat.cd_categoria,
            co.cd_cliente_organizacao,
            f.cd_fila                   AS cd_fila_atual,
            c.ds_titulo,
            c.ds_descricao,
            c.dt_inclusao,
            c.dt_atualizacao,
            c.nm_sistema_origem,
            c.cd_registro_origem
        FROM itsm.chamado AS c
        LEFT JOIN  itsm.analista             AS a   ON a.id_analista             = c.id_analista_atual
        INNER JOIN itsm.solicitante          AS s   ON s.id_solicitante          = c.id_reporter
        LEFT JOIN  itsm.categoria            AS cat ON cat.id_categoria          = c.id_categoria
        INNER JOIN itsm.cliente_organizacao  AS co  ON co.id_cliente_organizacao = c.id_cliente_organizacao
        LEFT JOIN  itsm.fila                 AS f   ON f.id_fila                 = c.id_fila_atual
    """

    UPSERT_SQL = """
        MERGE corptech.chamado AS tgt
        USING (
            SELECT
                src.nr_chamado,
                src.ds_tipo_chamado,
                src.ds_status_chamado,
                src.ds_prioridade,
                src.dt_criacao,
                src.dt_resolucao,
                src.dt_ultima_atualizacao,
                a_dst.id_analista               AS id_analista_atual,
                sol_dst.id_solicitante          AS id_reporter,
                cat_dst.id_categoria,
                co_dst.id_cliente_organizacao,
                f_dst.id_fila                   AS id_fila_atual,
                src.ds_titulo,
                src.ds_descricao,
                src.dt_inclusao,
                src.dt_atualizacao,
                src.nm_sistema_origem,
                src.cd_registro_origem
            FROM (VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)) AS src (
                nr_chamado, ds_tipo_chamado, ds_status_chamado, ds_prioridade,
                dt_criacao, dt_resolucao, dt_ultima_atualizacao,
                cd_analista_atual, cd_solicitante, cd_categoria,
                cd_cliente_organizacao, cd_fila_atual,
                ds_titulo, ds_descricao, dt_inclusao, dt_atualizacao,
                nm_sistema_origem, cd_registro_origem
            )
            LEFT JOIN  corptech.analista            AS a_dst   ON a_dst.cd_analista             = src.cd_analista_atual
            INNER JOIN corptech.solicitante          AS sol_dst ON sol_dst.cd_solicitante        = src.cd_solicitante
            LEFT JOIN  corptech.categoria            AS cat_dst ON cat_dst.cd_categoria          = src.cd_categoria
            INNER JOIN corptech.cliente_organizacao  AS co_dst  ON co_dst.cd_cliente_organizacao = src.cd_cliente_organizacao
            LEFT JOIN  corptech.fila                 AS f_dst   ON f_dst.cd_fila                 = src.cd_fila_atual
        ) AS resolved
        ON tgt.nr_chamado = resolved.nr_chamado
        WHEN MATCHED THEN
            UPDATE SET
                ds_tipo_chamado        = resolved.ds_tipo_chamado,
                ds_status_chamado      = resolved.ds_status_chamado,
                ds_prioridade          = resolved.ds_prioridade,
                dt_criacao             = resolved.dt_criacao,
                dt_resolucao           = resolved.dt_resolucao,
                dt_ultima_atualizacao  = resolved.dt_ultima_atualizacao,
                id_analista_atual      = resolved.id_analista_atual,
                id_reporter            = resolved.id_reporter,
                id_categoria           = resolved.id_categoria,
                id_cliente_organizacao = resolved.id_cliente_organizacao,
                id_fila_atual          = resolved.id_fila_atual,
                ds_titulo              = resolved.ds_titulo,
                ds_descricao           = resolved.ds_descricao,
                dt_atualizacao         = SYSUTCDATETIME(),
                nm_sistema_origem      = resolved.nm_sistema_origem,
                cd_registro_origem     = resolved.cd_registro_origem
        WHEN NOT MATCHED THEN
            INSERT (
                nr_chamado, ds_tipo_chamado, ds_status_chamado, ds_prioridade,
                dt_criacao, dt_resolucao, dt_ultima_atualizacao,
                id_analista_atual, id_reporter, id_categoria,
                id_cliente_organizacao, id_fila_atual,
                ds_titulo, ds_descricao, dt_inclusao, dt_atualizacao,
                nm_sistema_origem, cd_registro_origem
            )
            VALUES (
                resolved.nr_chamado, resolved.ds_tipo_chamado, resolved.ds_status_chamado,
                resolved.ds_prioridade, resolved.dt_criacao, resolved.dt_resolucao,
                resolved.dt_ultima_atualizacao, resolved.id_analista_atual,
                resolved.id_reporter, resolved.id_categoria,
                resolved.id_cliente_organizacao, resolved.id_fila_atual,
                resolved.ds_titulo, resolved.ds_descricao, resolved.dt_inclusao,
                resolved.dt_atualizacao, resolved.nm_sistema_origem, resolved.cd_registro_origem
            );
    """

    try:
        with get_source_connection() as src_conn:
            rows = src_conn.cursor().execute(SELECT_SQL).fetchall()

        logging.info(f"extract_chamado: {len(rows)} linha(s) lida(s) da origem.")

        with get_target_connection() as dst_conn:
            cursor = dst_conn.cursor()
            cursor.fast_executemany = True
            cursor.executemany(UPSERT_SQL, rows)
            dst_conn.commit()

        logging.info("extract_chamado: upsert concluído.")

    except Exception as e:
        logging.error(f"extract_chamado: erro – {e}")
        raise