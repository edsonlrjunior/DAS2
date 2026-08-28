# ADR 001: Adoção da Microsoft Azure como plataforma de nuvem

**Status:** Aceito

## Contexto

O TAPR precisa executar rotinas de integração e processamento de dados de IT Service Management de forma automática, sem depender da execução manual em uma máquina local. O código também precisa acessar bancos SQL, manter configurações por variáveis de ambiente e permitir publicação controlada do serviço.

O repositório possui uma Function App em Python e um workflow de GitHub Actions que publica o conteúdo da pasta `src` na aplicação Azure Functions `azfunitsm-694`.

## Decisão

Adotar a **Microsoft Azure** como plataforma de nuvem para execução do TAPR, utilizando **Azure Functions** como serviço de processamento.

O deploy da aplicação será realizado pelo **GitHub Actions**, usando autenticação com credenciais configuradas como secrets do repositório. As configurações de conexão com os bancos permanecem fora do código-fonte, por meio de variáveis de ambiente da aplicação.

## Consequências

### Benefícios

- Infraestrutura gerenciada, sem necessidade de manter servidor próprio para executar as rotinas.
- Integração direta com Azure Functions e serviços de banco de dados compatíveis com SQL Server.
- Possibilidade de automatizar o deploy a partir da branch `main`.
- Separação entre código-fonte e configurações sensíveis do ambiente.
- Facilidade para evoluir o processamento sem alterar a infraestrutura local dos usuários.

### Pontos negativos e trade-offs

- Dependência do ecossistema Microsoft Azure.
- Necessidade de configurar corretamente permissões, secrets e variáveis de ambiente.
- Possibilidade de custos de nuvem conforme uso e recursos contratados.
- Problemas na plataforma Azure ou na configuração da Function App podem interromper as cargas de dados.
