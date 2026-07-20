# Critérios de aceite

## Etapa 07: hooks

| Critério                               |
| -------------------------------------- |
| Hook autenticado antes da sessão local |
| Rejeição explícita preservada          |
| Falha inesperada vira erro tipado      |
| Hook de logout depois da limpeza       |
| Hooks de erro não mascaram exceção     |
| Hooks de evento não interrompem fluxo  |
| Ordem e registro idempotente           |
| Identidade permanece imutável          |
| Autorização continua fora do núcleo    |

## Etapa 08: hardening

| Critério                                |
| --------------------------------------- |
| Threat model documentado                |
| Eventos estruturados sanitizados        |
| Request ID seguro                       |
| Logging opcional sem payload sensível   |
| Contrato de consumo atômico             |
| Fallback explicitamente não distribuído |
| Exigência opcional de backend atômico   |
| Auditoria de secret e cookies           |
| Auditoria de storage                    |
| Modo estrito para erros                 |
| Falhas de backend encapsuladas          |
| API pública revisada e tipada           |

## Qualidade

Lint, formatação, tipagem, testes, 100% de cobertura, Bandit, pip-audit, build, metadata, artefatos e instalação limpa devem permanecer aprovados.

## Fora do escopo

Redis oficial, autorização, Graph, template consumidor, deploy, TestPyPI e publicação.
