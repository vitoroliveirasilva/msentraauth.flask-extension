# Critérios de aceite

## Etapas anteriores

Os critérios das ETAPAS 00, 01 e 02 permanecem atendidos: instalação, application factory, configuração, storage, isolamento, qualidade, auditoria e build.

## Identidade: ETAPA 03

| Critério                                            |
| --------------------------------------------------- |
| `Identity` pública e tipada                         |
| Dataclass congelada e com slots                     |
| Claims profundamente imutáveis                      |
| `oid`, `tid` e `home_account_id` obrigatórios       |
| Tenant esperado validado                            |
| `stable_id` usa tenant + object ID                  |
| Username/email não usados como chave                |
| Credenciais rejeitadas                              |
| Token ausente de identidade e `repr`                |
| `current_identity` request-local                    |
| Falha explícita fora de contexto e sem autenticação |
| Isolamento entre requisições e apps                 |

## MSAL: ETAPA 04

| Critério                                    |
| ------------------------------------------- |
| Cliente confidencial construído sob demanda |
| Nenhum cliente ou rede em `init_app()`      |
| Fábrica injetável para testes sem rede      |
| PII logging desligado                       |
| `SerializableTokenCache` exclusivo          |
| Cache separado por conta e namespace        |
| Chave sem `home_account_id` em texto claro  |
| Cache salvo somente quando alterado         |
| TTL configurável e positivo                 |
| Conta selecionada por `home_account_id`     |
| Aquisição silenciosa server-side            |
| Interação necessária gera `ConsentRequired` |
| Erros do provedor sanitizados               |
| Refresh token não manipulado diretamente    |
| Token não armazenado em identidade/cookie   |

## Fluxo web

Não iniciado. Login, callback, state, nonce, replay e restauração de identidade pertencem à ETAPA 05.

## Release

Build, twine check, tipagem, lint, testes, cobertura, Bandit, pip-audit, documentação e changelog permanecem configurados. Publicação não foi realizada.
