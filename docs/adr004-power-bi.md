# ADR 004: Uso do Microsoft Power BI para visualização dos dados

**Status:** Aceito

## Contexto

Após a consolidação dos dados de ITSM no schema `corptech`, os usuários precisam acompanhar informações como chamados abertos, encerrados, situação geral e outros indicadores operacionais sem consultar diretamente o banco de dados.

O repositório já contém o arquivo `docs/db-corptech.pbix` e imagens dos dashboards geral, abertos e encerrados.

## Decisão

Utilizar o **Microsoft Power BI** como camada de visualização e análise do TAPR.

O Power BI consulta os dados consolidados no banco de destino e apresenta as informações em dashboards voltados ao acompanhamento do ambiente de IT Service Management.

A aplicação TAPR fica responsável pela preparação e atualização dos dados, enquanto o Power BI permanece responsável pela apresentação dos indicadores.

## Consequências

### Benefícios

- Criação de dashboards sem necessidade de desenvolver uma aplicação web específica para relatórios.
- Boa integração com bancos SQL e com o ecossistema Microsoft utilizado pelo projeto.
- Facilidade para criar filtros, métricas e diferentes visões dos mesmos dados.
- Separação clara entre processamento de dados e visualização.
- Usuários podem consumir indicadores sem executar consultas SQL manualmente.

### Pontos negativos e trade-offs

- O arquivo `.pbix` é binário e possui limitações para comparação de alterações e versionamento no Git.
- Mudanças no schema `corptech` podem quebrar consultas, medidas ou visuais do Power BI.
- Atualizações automáticas podem depender de configuração de credenciais, gateway ou serviço Power BI, conforme o ambiente de publicação.
- Algumas funcionalidades de compartilhamento e atualização podem depender de licenciamento do Power BI.
