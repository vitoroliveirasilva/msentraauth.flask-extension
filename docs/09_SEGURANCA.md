# Modelo de segurança

## Ativos

Client secret, configuração, redirect URIs, sessão, fluxo, token cache, tokens, claims e logs.

## Controles implementados na ETAPA 01

| Ameaça                                 | Controle atual                                             |
| -------------------------------------- | ---------------------------------------------------------- |
| Configuração ausente ou placeholder    | Validação fail-fast                                        |
| Client secret em erro ou representação | Mensagens sem valor e campo fora do `repr`                 |
| Redirect externo sem TLS               | HTTP permitido somente em loopback                         |
| Authority insegura                     | URL HTTPS absoluta, sem credenciais, query ou fragmento    |
| Tenant divergente na authority         | Correspondência obrigatória com tenant configurado         |
| Configuração alterada após startup     | Objeto congelado preservado na inicialização idempotente   |
| Vazamento entre aplicações             | Configuração e estado separados em `app.extensions`        |
| Configuração multi-tenant acidental    | Aliases `common`, `organizations` e `consumers` rejeitados |

## Ameaças e controles planejados

| Ameaça                | Controle futuro                        |
| --------------------- | -------------------------------------- |
| Login CSRF            | Fluxo MSAL persistido e state validado |
| Callback injetado     | Correspondência com sessão             |
| Session fixation      | Integração para regeneração da sessão  |
| Open redirect         | Validação do destino pós-login         |
| Token em cookie       | Storage server-side                    |
| Token em log          | Redação e proibição                    |
| Token expirado        | Aquisição silenciosa                   |
| Replay                | Consumo do fluxo                       |
| Host header poisoning | Redirect URI explícita                 |
| Forced logout         | POST e CSRF pela aplicação             |
| Supply chain          | Auditoria e atualização controlada     |

## Responsabilidade compartilhada

A aplicação continua responsável por HTTPS, `SECRET_KEY`, cookies, CSRF, storage, proxy, headers, rate limit, autorização, carregamento dos secrets e proteção das credenciais.

## Validação atual

- Configuração obrigatória;
- Placeholders;
- Tenant e authority;
- Redirect URI;
- Scopes;
- Isolamento entre apps;
- Ausência de segredo em erro e representação;
- Análise estática;
- Auditoria de dependências.

## Validação futura

State divergente, callback sem fluxo, replay, next URL, cache ausente ou corrompido, logs sem tokens e revisão manual do callback pertencem às etapas seguintes.

A extensão não garante conformidade regulatória nem substitui revisão de segurança.
