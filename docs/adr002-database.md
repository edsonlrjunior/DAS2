# ADR 002: Uso de SQL Server para origem e repositório analítico

**Status:** Aceito

## Contexto

O TAPR precisa ler dados operacionais de ITSM e disponibilizá-los em uma estrutura organizada para consumo analítico. O código atual trabalha com duas conexões: uma de origem e outra de destino.

As funções acessam o banco por meio da biblioteca `pyodbc` e do **ODBC Driver 18 for SQL Server**. Na origem são consultadas tabelas do schema `itsm`; no destino os registros são gravados no schema `corptech`.

As credenciais e endereços dos bancos são obtidos por variáveis de ambiente, como `SQL_SERVER_SOURCE`, `SQL_DATABASE_SOURCE`, `SQL_SERVER_TARGET` e `SQL_DATABASE_TARGET`.

## Decisão

Manter o **SQL Server** como tecnologia de banco de dados para a integração do TAPR.

A arquitetura utiliza:

- **Origem:** schema `itsm`, contendo os dados operacionais.
- **Destino:** schema `corptech`, utilizado como repositório consolidado para análise.
- Conexão via `pyodbc`, com criptografia habilitada (`Encrypt=yes`).
- Sincronização por comandos `MERGE`, atualizando registros existentes e inserindo novos registros.
- Resolução de relacionamentos por chaves naturais antes da gravação das chaves estrangeiras no destino.

## Consequências

### Benefícios

- Modelo relacional adequado aos dados estruturados de chamados, SLA, filas, analistas e demais entidades.
- Compatibilidade direta com os comandos SQL utilizados no código.
- Boa integração com o Power BI.
- O uso de `MERGE` permite executar cargas de forma idempotente, evitando inserções duplicadas quando a mesma informação é processada novamente.
- Separação entre a base operacional e a base destinada à análise.

### Pontos negativos e trade-offs

- Forte dependência de SQL Server, ODBC e da estrutura atual dos schemas.
- Alterações em nomes de tabelas, colunas ou relacionamentos exigem alteração das funções de extração.
- Há repetição de código de conexão em diferentes arquivos, aumentando o esforço de manutenção.
- Grandes volumes de dados podem exigir otimizações futuras no processo de carga e nas consultas SQL.
