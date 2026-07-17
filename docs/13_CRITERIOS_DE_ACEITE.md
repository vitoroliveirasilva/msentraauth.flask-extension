# Critérios de aceite

## Fundação: ETAPA 00

Todos os critérios permanecem atendidos: instalação, import, application factory, múltiplas apps, ausência de `self.app`, isolamento, pacote tipado, build, CI, qualidade e auditoria.

## Configuração: ETAPA 01

| Critério                                       |
| ---------------------------------------------- |
| Chaves obrigatórias validadas em `init_app()`  |
| Precedência instância, `app.config` e padrões  |
| Authority segura e coerente com tenant         |
| Redirect URI absoluta e HTTPS fora de loopback |
| Scopes normalizados e imutáveis                |
| Placeholders rejeitados                        |
| Client secret ausente dos erros e repr         |
| Configuração congelada após inicialização      |
| Configuração isolada entre aplicações          |
| `ConfigurationError` público e tipado          |
| Nenhuma rede, MSAL ou rota em `init_app()`     |
| Testes de sucesso e falha                      |

## Storage

Não iniciado.

## Identidade

Não iniciada.

## MSAL, login e token

Não iniciados.

## Release

Build, twine check, CI, tipagem, lint, Bandit, pip-audit, documentação e changelog permanecem configurados. Publicação não foi realizada.
