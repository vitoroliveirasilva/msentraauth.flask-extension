# Modelo de segurança

## Ativos

Client secret, sessão, fluxo, token cache, tokens, claims, redirect URIs e logs.

## Ameaças e controles

| Ameaça | Controle |
|---|---|
| Login CSRF | Fluxo MSAL persistido e state validado |
| Callback injetado | Correspondência com sessão |
| Session fixation | Integração para regeneração da sessão |
| Open redirect | Validação do destino |
| Token em cookie | Storage server-side |
| Token em log | Redação e proibição |
| Token expirado | Aquisição silenciosa |
| Tenant inesperado | Validação de tenant |
| Replay | Consumo do fluxo |
| Host header poisoning | Redirect URI explícita |
| Forced logout | POST e CSRF pela aplicação |
| Supply chain | Auditoria e atualização controlada |

## Responsabilidade compartilhada

A aplicação continua responsável por HTTPS, SECRET_KEY, cookies, CSRF, storage, proxy, headers, rate limit, autorização e proteção dos secrets.

## Validação

- State divergente;
- Callback sem fluxo;
- Replay;
- Open redirect;
- Cache ausente e corrompido;
- Logs sem tokens;
- Análise estática;
- Auditoria de dependências;
- Revisão manual do callback.

A extensão não garante conformidade regulatória nem substitui revisão de segurança.