# ADR-010: configuração validada e imutável por aplicação

## Contexto

A extensão deve falhar cedo diante de credenciais ou URIs inválidas, suportar application factory e permitir que uma mesma instância inicialize aplicações distintas sem compartilhar configuração resolvida.

## Decisão

- Resolver valores na ordem: argumentos da instância, `app.config` e padrões seguros;
- Manter argumentos da instância em estrutura interna imutável;
- Validar toda a configuração durante `init_app()` antes de registrar estado;
- Armazenar a configuração resolvida em objeto congelado por aplicação;
- Derivar authority a partir do tenant quando ausente;
- Aceitar HTTP para redirect URI somente em hosts de loopback;
- Rejeitar aliases multi-tenant na fase single-tenant;
- Normalizar scopes para uma tupla sem duplicatas exatas;
- Expor `ConfigurationError` sem incluir valores sensíveis.

## Consequências

- Erros de configuração surgem no startup, antes de qualquer chamada de rede;
- Alterações posteriores em `app.config` não afetam uma aplicação já inicializada;
- A mesma extensão continua reutilizável em múltiplas aplicações;
- Customizações multi-tenant, B2C/External ID ou authorities com múltiplos segmentos exigirão decisão futura explícita;
- Nenhum cliente MSAL é criado nesta etapa.
