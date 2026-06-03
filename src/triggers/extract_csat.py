import logging
import azure.functions as func
import os
import pyodbc

app = func.Blueprint()

@app.timer_trigger(schedule="0 0 12 * * *", arg_name="myTimer", run_on_startup=False,
                   use_monitor=False)
def extract_csat(myTimer: func.TimerRequest) -> None:
    try:
        logging.info("extract_csat: iniciando.")

        SELECT_SQL = "SELECT * FROM itsm.csat"

        UPSERT_SQL = """
        INSERT INTO corptech.csat (Id, Column1, Column2)
            VALUES (?, ?, ?)
        """
        
        conn_source_str = (
            "DRIVER={ODBC Driver 18 for SQL Server};"
            f"SERVER={os.getenv('SQL_SERVER_SOURCE')};"
            f"DATABASE={os.getenv('SQL_DATABASE_SOURCE')};"
            f"UID={os.getenv('SQL_USER_SOURCE')};"
            f"PWD={os.getenv('SQL_PASSWORD_SOURCE')};"
            "Encrypt=yes;"
            "TrustServerCertificate=no;"
            "Connection Timeout=30;"
        )
        
        conn_target_str = (
            "DRIVER={ODBC Driver 18 for SQL Server};"
            f"SERVER={os.getenv('SQL_SERVER_TARGET')};"
            f"DATABASE={os.getenv('SQL_DATABASE_TARGET')};"
            f"UID={os.getenv('SQL_USER_TARGET')};"
            f"PWD={os.getenv('SQL_PASSWORD_TARGET')};"
            "Encrypt=yes;"
            "TrustServerCertificate=no;"
            "Connection Timeout=30;"
        )
        
        conn_source = pyodbc.connect(conn_source_str)
        conn_target = pyodbc.connect(conn_target_str)

    
        with conn_source.cursor() as src_cursor:
            rows = src_cursor.execute(SELECT_SQL).fetchall()

        logging.info(f"extract_csat: {len(rows)} linha(s) lida(s) da origem.")

        with conn_target.cursor() as dst_cursor:
            dst_cursor.fast_executemany = True
            dst_cursor.executemany(UPSERT_SQL, rows)
            conn_target.commit()

        logging.info("extract_csat: upsert concluído.")

    except Exception as e:
        logging.error(f"extract_csat: erro – {e}")
        raise
