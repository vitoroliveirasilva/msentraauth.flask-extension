# Segurança

## Controles implementados

| Ameaça                           | Controle                                   |
| -------------------------------- | ------------------------------------------ |
| CSRF e replay no callback        | State imprevisível e consumo único         |
| Corrida entre workers            | `AtomicAuthStorage.take()` opcional        |
| Backend sem garantia distribuída | Auditoria e modo `require_atomic`          |
| Open redirect                    | Destino validado e allowlist exata         |
| Auth code ou token no cookie     | Referências aleatórias server-side         |
| Vínculo local inválido           | Hook antes da sessão e rejeição explícita  |
| Vazamento em observabilidade     | Evento fechado e mensagem de log constante |
| Cookie inseguro                  | Auditoria de HttpOnly, SameSite e Secure   |
| Secret ausente ou fraco          | Achado de auditoria e modo estrito         |
| Storage local em produção        | Aviso de auditoria                         |
| Refresh token manipulado         | `SerializableTokenCache` exclusivo         |
| Logout amplo acidental           | Limpeza limitada à sessão atual            |

## Auditoria

`audit_security()` é somente leitura. `SecurityFinding` não contém valores de configuração. O relatório pode ser executado após inicialização e é armazenado no estado da aplicação.

## Concorrência

Fluxo e identidade usam consumo atômico quando disponível. O fallback local não é garantia distribuída. Token cache permanece last-write-wins e não detecta conflitos.

## Responsabilidade compartilhada

A aplicação continua responsável por HTTPS, CSRF geral, proxy, rate limit, headers, secret provider, storage de produção, disponibilidade, backup e autorização.

Consulte [`17_THREAT_MODEL.md`](17_THREAT_MODEL.md).
