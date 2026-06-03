import logging
import azure.functions as func
import os
import pyodbc
import database_connects

app = func.Blueprint()

@app.timer_trigger(schedule="0 0 12 * * *", arg_name="myTimer", run_on_startup=False,
                   use_monitor=False)
def extract_analista(myTimer: func.TimerRequest) -> None:
    logging.info("extract_analista: iniciando.")

    # Pull analista joined to fila so we can carry the fila code across
    SELECT_SQL = """
        SELECT
            a.cd_analista,
            a.nm_analista,
            a.ds_email,
            a.ds_nivel,
            f.cd_fila   AS cd_fila_atual,
            a.fl_ativo,
            a.dt_inclusao,
            a.dt_atualizacao,
            a.nm_sistema_origem,
            a.cd_registro_origem
        FROM itsm.analista AS a
        LEFT JOIN itsm.fila AS f ON f.id_fila = a.id_fila_atual
    """

    # MERGE using cd_analista; resolve id_fila_atual from the destination fila table
    UPSERT_SQL = """
        MERGE corptech.analista AS tgt
        USING (
            SELECT
                src.cd_analista,
                src.nm_analista,
                src.ds_email,
                src.ds_nivel,
                f_dst.id_fila  AS id_fila_atual,
                src.fl_ativo,
                src.dt_inclusao,
                src.dt_atualizacao,
                src.nm_sistema_origem,
                src.cd_registro_origem
            FROM (VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)) AS src (
                cd_analista, nm_analista, ds_email, ds_nivel, cd_fila_atual,
                fl_ativo, dt_inclusao, dt_atualizacao, nm_sistema_origem, cd_registro_origem
            )
            LEFT JOIN corptech.fila AS f_dst ON f_dst.cd_fila = src.cd_fila_atual
        ) AS resolved
        ON tgt.cd_analista = resolved.cd_analista
        WHEN MATCHED THEN
            UPDATE SET
                nm_analista        = resolved.nm_analista,
                ds_email           = resolved.ds_email,
                ds_nivel           = resolved.ds_nivel,
                id_fila_atual      = resolved.id_fila_atual,
                fl_ativo           = resolved.fl_ativo,
                dt_atualizacao     = SYSUTCDATETIME(),
                nm_sistema_origem  = resolved.nm_sistema_origem,
                cd_registro_origem = resolved.cd_registro_origem
        WHEN NOT MATCHED THEN
            INSERT (cd_analista, nm_analista, ds_email, ds_nivel, id_fila_atual,
                    fl_ativo, dt_inclusao, dt_atualizacao, nm_sistema_origem, cd_registro_origem)
            VALUES (resolved.cd_analista, resolved.nm_analista, resolved.ds_email, resolved.ds_nivel,
                    resolved.id_fila_atual, resolved.fl_ativo, resolved.dt_inclusao,
                    resolved.dt_atualizacao, resolved.nm_sistema_origem, resolved.cd_registro_origem);
    """

    try:
        with database_connects.get_source_connection() as src_conn:
            rows = src_conn.cursor().execute(SELECT_SQL).fetchall()

        logging.info(f"extract_analista: {len(rows)} linha(s) lida(s) da origem.")

        with database_connects.get_target_connection() as dst_conn:
            cursor = dst_conn.cursor()
            cursor.fast_executemany = True
            cursor.executemany(UPSERT_SQL, rows)
            dst_conn.commit()

        logging.info("extract_analista: upsert concluído.")

    except Exception as e:
        logging.error(f"extract_analista: erro – {e}")
        raise
