# Modelo de segurança

## Ativos

Client secret, fluxo, sessão, identidade, claims, token cache, access token, refresh token gerenciado pelo MSAL, redirect URI e logs.

## Controles implementados

| Ameaça                              | Controle atual                                |
| ----------------------------------- | --------------------------------------------- |
| Configuração insegura               | Validação fail-fast e objetos congelados      |
| Tenant inesperado                   | Comparação de claim `tid` com tenant esperado |
| Token dentro da identidade          | Claims de credencial rejeitadas               |
| Mutação de claims                   | Congelamento recursivo                        |
| PII em representação                | `Identity.__repr__` sanitizado                |
| Cache em chave identificável        | SHA-256 do `home_account_id`                  |
| Manipulação manual de refresh token | Uso exclusivo de `SerializableTokenCache`     |
| Cache inválido                      | `StorageError` seguro                         |
| PII logging do MSAL                 | `enable_pii_log=False`                        |
| Erro bruto do provedor              | Sanitização de código/correlation ID          |
| Token no cliente                    | Aquisição retorna somente ao código servidor  |
| Estado global de usuário            | Contexto Flask request-local                  |

## Responsabilidade compartilhada

A aplicação continua responsável por HTTPS, `SECRET_KEY`, cookies, CSRF, storage de produção, proxy, headers, rate limit, autorização, proteção de secrets e por não devolver access tokens ao navegador.

## Ainda não implementado

State, nonce, callback, replay protection, open redirect, regeneração de sessão e logout serão tratados nas etapas de fluxo e hardening.

## Auditoria

A validação inclui testes de ausência de credenciais, imutabilidade, tenant, isolamento, cache, sanitização, Bandit, pip-audit e revisão de artefatos. Isso não substitui revisão de segurança do fluxo completo.
