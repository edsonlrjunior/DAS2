# ADR 003: Uso de Azure Functions com Timer Trigger para processamento do TAPR

**Status:** Aceito

## Contexto

Os dados do sistema ITSM precisam ser copiados e atualizados periodicamente no repositório analítico. A execução manual das cargas aumentaria o risco de esquecimento, dados desatualizados e dependência de uma estação de trabalho.

O arquivo `src/function_app.py` registra diferentes rotinas de extração, entre elas chamados, analistas, filas, categorias, SLA, CSAT, solicitantes e histórico de status. As rotinas estão implementadas como Blueprints do Azure Functions e utilizam `timer_trigger`.

## Decisão

Utilizar **Azure Functions em Python** com **Timer Trigger** para executar as rotinas de ETL do TAPR.

Cada domínio é mantido em um arquivo separado dentro de `src/triggers`, enquanto `src/function_app.py` registra as funções na Function App principal.

O fluxo básico adotado é:

1. O Timer Trigger inicia a função no horário configurado.
2. A função conecta ao banco de origem.
3. Os registros são consultados no schema `itsm`.
4. Os relacionamentos necessários são resolvidos.
5. A função conecta ao banco de destino.
6. Os dados são inseridos ou atualizados no schema `corptech` por meio de `MERGE`.

## Consequências

### Benefícios

- Processamento automático e periódico.
- Não exige servidor dedicado executando continuamente.
- Separação das rotinas por domínio facilita a localização e manutenção do código.
- As funções podem ser evoluídas individualmente.
- Integração natural com a infraestrutura Azure já adotada pelo projeto.

### Pontos negativos e trade-offs

- Algumas cargas possuem dependência entre entidades, portanto a ordem e os horários de execução precisam ser controlados.
- Falhas de conexão ou indisponibilidade do banco interrompem a função e exigem acompanhamento dos logs.
- O código atual repete lógica de conexão em diferentes triggers.
- O uso de `use_monitor=False` nos timers reduz o controle persistente de ocorrências do agendamento e deve ser reavaliado caso a confiabilidade da execução se torne mais crítica.
- Não existe no código atual uma camada própria de filas ou retentativas para desacoplar as cargas.
