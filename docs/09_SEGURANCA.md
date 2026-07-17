# Modelo de segurança

## Ativos

Client secret, configuração, redirect URIs, namespace, chaves internas, sessão, fluxo, token cache, tokens, claims e logs.

## Controles implementados até a ETAPA 02

| Ameaça                                          | Controle atual                                |
| ----------------------------------------------- | --------------------------------------------- |
| Configuração ausente ou placeholder             | Validação fail-fast                           |
| Client secret em erro ou representação          | Mensagens sem valor e campo fora do `repr`    |
| Redirect externo sem TLS                        | HTTP permitido somente em loopback            |
| Authority insegura ou tenant divergente         | HTTPS e correspondência obrigatória           |
| Vazamento entre aplicações                      | Estado, configuração e namespace separados    |
| Colisão de chaves em backend compartilhado      | Prefixo `msentra:<namespace>:`                |
| Valor não binário ou TTL inválido               | Validação antes da operação                   |
| Expiração baseada em relógio civil              | Relógio monotônico no backend em memória      |
| Condição de corrida local                       | Operações protegidas por `RLock`              |
| Erro externo expondo conteúdo                   | `StorageError` sanitizado com causa encadeada |
| Uso acidental do backend em memória em produção | Limitação explícita na API e documentação     |

## Ameaças e controles planejados

| Ameaça            | Controle futuro                        |
| ----------------- | -------------------------------------- |
| Login CSRF        | Fluxo MSAL persistido e state validado |
| Callback injetado | Correspondência com sessão             |
| Session fixation  | Integração para regeneração da sessão  |
| Open redirect     | Validação do destino pós-login         |
| Token em cookie   | Storage server-side                    |
| Token em log      | Redação e proibição                    |
| Token expirado    | Aquisição silenciosa                   |
| Replay            | Consumo do fluxo                       |
| Forced logout     | POST e CSRF pela aplicação             |

## Responsabilidade compartilhada

A aplicação e o operador continuam responsáveis por HTTPS, `SECRET_KEY`, cookies, CSRF, backend de produção, TLS, timeouts, credenciais de storage, proxy, headers, rate limit, autorização e carregamento seguro dos secrets.

## Validação atual

- Configuração, tenant, authority, redirect e scopes;
- Namespace, chave, bytes e TTL;
- Isolamento entre aplicações;
- Expiração e concorrência local;
- Ausência de segredo, chave e valor em erros;
- Análise estática e auditoria de dependências.

## Validação futura

State divergente, callback sem fluxo, replay, next URL, cache MSAL ausente ou corrompido e logs sem tokens pertencem às etapas seguintes.

A extensão não garante conformidade regulatória nem substitui revisão de segurança.
