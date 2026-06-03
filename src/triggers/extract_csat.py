import logging
import azure.functions as func

from database_connects import get_source_connection, get_target_connection

app = func.Blueprint()

@app.timer_trigger(schedule="0 0 12 * * *", arg_name="myTimer", run_on_startup=False,
                   use_monitor=False)
def extract_csat(myTimer: func.TimerRequest) -> None:
    logging.info("extract_csat: iniciando.")

    SELECT_SQL = "SELECT Id, Column1, Column2 FROM itsm.csat"

    UPSERT_SQL = """
        MERGE corptech.csat AS tgt
        USING (VALUES (?, ?, ?)) AS src (Id, Column1, Column2)
        ON tgt.Id = src.Id
        WHEN MATCHED THEN
            UPDATE SET Column1 = src.Column1, Column2 = src.Column2
        WHEN NOT MATCHED THEN
            INSERT (Id, Column1, Column2) VALUES (src.Id, src.Column1, src.Column2);
    """

    try:
        with get_source_connection().cursor() as src_conn:
            rows = src_conn.execute(SELECT_SQL).fetchall()

        logging.info(f"extract_csat: {len(rows)} linha(s) lida(s) da origem.")

        with get_target_connection().cursor() as dst_conn:
            dst_conn.fast_executemany = True
            dst_conn.executemany(UPSERT_SQL, rows)
            dst_conn.commit()

        logging.info("extract_csat: upsert concluído.")

    except Exception as e:
        logging.error(f"extract_csat: erro – {e}")
        raise
