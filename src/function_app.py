import logging
import azure.functions as func

app = func.FunctionApp()

@app.timer_trigger(schedule="0 */3 * * * *", arg_name="myTimer", run_on_startup=False,
              use_monitor=False) 
def timer_trigger_1(myTimer: func.TimerRequest) -> None:
    if myTimer.past_due:
        logging.info('The timer is past due!')

    logging.info('TIMER_TRIGGER_1 running')

@app.timer_trigger(schedule="0 */2 * * * *", arg_name="myTimer", run_on_startup=False,
              use_monitor=False) 
def timer_trigger_2(myTimer: func.TimerRequest) -> None:
    
    if myTimer.past_due:
        logging.info('The timer is past due!')

    logging.info('TIMER_TRIGGER_2 running') 

@app.timer_trigger(schedule="0 */6 * * * *", arg_name="myTimer", run_on_startup=False,
              use_monitor=False) 
def timer_trigger_gian(myTimer: func.TimerRequest) -> None:
    
    if myTimer.past_due:
        logging.info('The timer is past due!')

    logging.info('Python timer trigger function executed GIAN.')