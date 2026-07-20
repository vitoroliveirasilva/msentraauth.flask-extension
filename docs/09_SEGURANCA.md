# Modelo de segurança

## Controles implementados

| Ameaça                         | Controle                                              |
| ------------------------------ | ----------------------------------------------------- |
| CSRF/replay no callback        | State imprevisível, comparação segura e consumo único |
| Reutilização concorrente       | Fluxo removido antes da redenção                      |
| Open redirect                  | Destino local validado ou allowlist exata             |
| Callback ambíguo               | Campos duplicados e estruturas excessivas rejeitados  |
| Auth code ou token no cookie   | Cookie contém somente referências aleatórias          |
| Sequestro lógico de identidade | Tenant, object ID e conta MSAL validados              |
| Fixação da referência interna  | Referência rotacionada após login                     |
| Vazamento de claims            | Identidade server-side e `repr` sanitizado            |
| Manipulação de refresh token   | `SerializableTokenCache` exclusivo                    |
| Logout amplo acidental         | Limpeza limitada à sessão atual                       |
| Erro bruto do provedor         | Exceções e respostas sanitizadas                      |

## Responsabilidade compartilhada

A aplicação continua responsável por HTTPS, `SECRET_KEY` forte e rotacionada, flags de cookie, CSRF geral, proxy confiável, headers, rate limit, storage de produção, proteção de secrets e autorização.

A rota padrão de logout usa `POST`; aplicações devem integrar sua política CSRF quando necessário.

## Limites

Concorrência distribuída, CAS, threat model formal, telemetria estruturada e testes contra provedor real pertencem ao hardening futuro.

## Auditoria

A validação inclui casos de state, replay, cancelamento, open redirect, sessão mínima, logout isolado, erros sanitizados, Bandit, pip-audit, build e inspeção dos artefatos.
