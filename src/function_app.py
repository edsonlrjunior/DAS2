import azure.functions as func

app = func.FunctionApp()

from triggers.extract_csat import app as extract_csat
from triggers.extract_sla import app as extract_sla
from triggers.extract_categoria import app as extract_categoria
from triggers.extract_cliente_organizacao import app as cliente_organizacao
from triggers.extract_solicitante import app as extract_solicitante
from triggers.extract_fila import app as extract_fila
from triggers.extract_analista import app as extract_analista
from triggers.extract_chamado import app as extract_chamado
from triggers.extract_chamado_status_historico import app as extract_chamado_status_historico
from triggers.extract_csat_avaliacao import app as extract_csat_avaliacao
from triggers.extract_chamado_sla import app as extract_chamado_sla

app.register_functions(extract_csat)
app.register_functions(extract_sla)
app.register_functions(extract_categoria)
app.register_functions(cliente_organizacao)
app.register_functions(extract_solicitante)
app.register_functions(extract_fila)
app.register_functions(extract_analista)
app.register_functions(extract_chamado)
app.register_functions(extract_chamado_status_historico)
app.register_functions(extract_csat_avaliacao)
app.register_functions(extract_chamado_sla)        