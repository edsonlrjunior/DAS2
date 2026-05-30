import logging
import azure.functions as func

app = func.FunctionApp()

from triggers.extract_csat import app as extract_csat
from triggers.extract_sla import app as extract_sla
from triggers.extract_categoria import app as extract_categoria
from triggers.extract_cliente_organizacao import app as cliente_organizacao
from triggers.extract_solicitante import app as extract_solicitante
from triggers.extract_fila import app as extract_fila
from triggers.extract_analista import app as extract_analista

app.register_functions(extract_csat)
app.register_functions(extract_sla)
app.register_functions(extract_categoria)
app.register_functions(cliente_organizacao)
app.register_functions(extract_solicitante)
app.register_functions(extract_fila)
app.register_functions(extract_analista)