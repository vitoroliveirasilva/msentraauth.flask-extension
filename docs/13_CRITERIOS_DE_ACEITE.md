# Critérios de aceite

## Fundação e configuração

Os critérios das ETAPAS 00 e 01 permanecem atendidos: instalação, application factory, múltiplas apps, ausência de `self.app`, configuração validada e imutável, pacote tipado, build, CI, qualidade e auditoria.

## Storage: ETAPA 02

| Critério                                                |
| ------------------------------------------------------- |
| `AuthStorage` público e tipado                          |
| `MemoryStorage` funcional para desenvolvimento          |
| `load`, `save` e `delete` cobertos por suíte contratual |
| `delete()` idempotente                                  |
| TTL positivo ou `None`                                  |
| Expiração remove valor e retorna `None`                 |
| Namespace por aplicação                                 |
| Backend compartilhado isolado por namespace             |
| Última escrita concluída prevalece                      |
| Operações locais protegidas por lock                    |
| Falhas externas convertidas em `StorageError`           |
| Causa original preservada sem expor dados               |
| Chave e valor ausentes das mensagens                    |
| Storage preservado em inicialização duplicada           |
| Nenhum token ou fluxo MSAL criado                       |

## Identidade

Não iniciada.

## MSAL, login e token

Não iniciados.

## Release

Build, twine check, CI, tipagem, lint, Bandit, pip-audit, documentação e changelog permanecem configurados. Publicação não foi realizada.
