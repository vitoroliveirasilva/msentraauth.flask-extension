# Changelog

## Adicionado

- Modelo público `Identity`, congelado e profundamente imutável;
- Construção de identidade a partir de claims validadas e tenant esperado;
- Proxy Flask `current_identity` com falha explícita fora de contexto ou sem autenticação;
- Hierarquia pública de erros de autenticação, identidade, consentimento, token e indisponibilidade;
- Serviço MSAL por aplicação, criado sem chamadas de rede durante `init_app()`;
- Fábrica injetável de cliente MSAL para testes e integrações controladas;
- Uso exclusivo de `SerializableTokenCache` para serialização do cache;
- Persistência de cache por conta com chave derivada por SHA-256;
- Aquisição silenciosa server-side por `MicrosoftEntraAuth.acquire_token()`;
- Configuração `MS_ENTRA_TOKEN_CACHE_TTL` com padrão de oito horas;
- ADRs sobre identidade/contexto e núcleo MSAL/cache;
- Testes de identidade, contexto, cliente, cache e aquisição silenciosa.

## Alterado

- Versão elevada para `0.4.0`;
- Estado da aplicação passa a incluir serviço MSAL isolado;
- `init_app()` continua sem rede, mas prepara configuração, storage e orquestração MSAL;
- Documentação, critérios de aceite, exemplos, segurança e status atualizados para as ETAPAS 03 e 04;
- Smoke test do pacote passa a validar identidade e serviço MSAL lazy.

## Segurança

- Identidades rejeitam credenciais e valores de claims não compatíveis com JSON;
- Claims são copiadas e congeladas recursivamente;
- Access tokens nunca são anexados à identidade;
- Cache é persistido apenas como serialização do MSAL e refresh tokens não são acessados diretamente;
- Chaves de cache não incluem `home_account_id` em texto claro;
- PII logging do MSAL permanece desativado;
- Erros do provedor são sanitizados e não copiam descrições brutas.

## Limites

- Login, callback, Authorization Code Flow, state, nonce, replay protection, rotas, logout, decorators e hooks continuam não implementados;
- A identidade ainda não é restaurada automaticamente entre requisições;
- `MemoryStorage` continua inadequado para produção.
