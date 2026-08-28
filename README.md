# DAS2 - Análise Arquitetural do Sistema TAPR

Atividade individual da disciplina **Design e Arquitetura de Software II**, realizada a partir do sistema legado **TAPR-2026-1-ITSM**.

## Entrega individual

**Aluno:** Edson Luis Rosa Junior  
**Sistema analisado:** TAPR-2026-1-ITSM  
**Tema:** IT Service Management

## Projeto original

O TAPR é uma plataforma analítica de IT Service Management. O projeto original foi desenvolvido por:

- Gian Carlo Fiamoncini
- Edson Luis Rosa Junior
- Gustavo Pereira
- Carlos Alberto Junior

A solução utiliza rotinas em Python executadas por Azure Functions para consultar dados do ambiente ITSM, consolidá-los em uma base analítica e disponibilizá-los ao Power BI.

## Arquitetura identificada no código

Durante a análise do repositório foram identificados os seguintes elementos:

- Azure Functions em Python como mecanismo de execução das rotinas de integração.
- Funções agendadas com `Timer Trigger`.
- Banco SQL Server de origem utilizando o schema `itsm`.
- Banco SQL Server de destino utilizando o schema `corptech`.
- Acesso aos bancos com `pyodbc` e ODBC Driver 18 for SQL Server.
- Sincronização de dados com comandos `MERGE`.
- Variáveis de ambiente para configurações e credenciais de origem e destino.
- Deploy da Function App pela pipeline do GitHub Actions.
- Microsoft Power BI como ferramenta de visualização dos dados consolidados.

## Documentação de Arquitetura

### Diagrama C4 - Nível de Contexto

![Diagrama C4 de Contexto do TAPR](docs/c4-contexto.png)

- [C4 Contexto - PNG](docs/c4-contexto.png)
- [C4 Contexto - Draw.io](docs/c4-contexto.drawio)

O diagrama apresenta o TAPR como sistema central e registra suas relações com o sistema ITSM/JSM, os bancos SQL e o Microsoft Power BI.

### Architectural Decision Records

- [ADR 001 - Microsoft Azure](docs/adr001-cloud.md)
- [ADR 002 - Banco de Dados](docs/adr002-database.md)
- [ADR 003 - Azure Functions](docs/adr003-azure-function.md)
- [ADR 004 - Power BI](docs/adr004-power-bi.md)

## Divergências e pontos formalizados

A documentação existente no projeto apresentava o desenho geral da solução, uma justificativa de uso da Azure e imagens do Power BI, porém algumas decisões arquiteturais estavam apenas implícitas no código.

Nesta análise foram formalizados:

- o uso de duas conexões SQL distintas, origem e destino;
- a separação dos schemas `itsm` e `corptech`;
- o padrão de sincronização por `MERGE`;
- o uso de Azure Functions com Timer Trigger;
- a automação de deploy pela branch `main`;
- a responsabilidade do Power BI como camada de visualização;
- as fronteiras do sistema por meio de um Diagrama C4 de Contexto.

## Materiais anteriores do projeto

- [Desenho original da arquitetura](docs/desenho.png)
- [Arquivo Excalidraw original](docs/desenho.excalidraw)
- [Justificativa ITSM / Azure](docs/Justificativa_ITSM_Azure.docx)
- [Dashboard Power BI](docs/db-corptech.pbix)
- [Dashboard - Geral](docs/dashboard-geral.png)
- [Dashboard - Chamados Abertos](docs/dashboard-aberto.png)
- [Dashboard - Chamados Encerrados](docs/dashboard-encerrados.png)
