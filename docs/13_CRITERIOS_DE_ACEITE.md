# Critérios de aceite

## Etapas anteriores

Fundação, configuração, storage, identidade e núcleo MSAL permanecem cobertos e compatíveis.

## Fluxo web: ETAPA 05

| Critério                                       |
| ---------------------------------------------- |
| Login inicia Authorization Code Flow pelo MSAL |
| Fluxo e destino ficam server-side com TTL      |
| State imprevisível e validado                  |
| Callback consome fluxo uma única vez           |
| Replay e callback expirado falham              |
| Cancelamento é previsível                      |
| Erros do provedor são sanitizados              |
| Claims, tenant e conta são validados           |
| Identidade é persistida e restaurada           |
| Cookie contém somente referência aleatória     |
| Next URL evita open redirect                   |
| Auth code não entra em cookie ou log           |

## Rotas e decorator: ETAPA 06

| Critério                                  |
| ----------------------------------------- |
| Blueprint padrão opcional                 |
| Prefixo configurável                      |
| Registro automático configurável          |
| Login e callback por `GET`                |
| Logout local por `POST`                   |
| `login_required` bare e parametrizado     |
| Redirect somente em métodos seguros       |
| Modo explícito `raise`                    |
| Tratamento de erros configurável          |
| Logout preserva dados alheios da sessão   |
| Logout remove cache apenas da conta atual |

## Qualidade

Lint, formatação, tipagem, testes, cobertura, auditoria, build, metadata, artefatos e instalação limpa devem permanecer aprovados.

## Fora do escopo

Hooks, integração automática com cadastro local, hardening distribuído, template, Graph e publicação.
