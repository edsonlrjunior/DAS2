import logging
import azure.functions as func

app = func.FunctionApp()

from triggers.extract_chamado import app as chamado
from triggers.extract_csat import app as extract_csat
from triggers.extract_sla import app as extract_sla

app.register_functions(chamado)
app.register_functions(extract_csat)
app.register_functions(extract_sla)