# Plano mestre

## Etapa 00: fundação (Concluída)

Documentação, estrutura `src`, empacotamento, qualidade, testes, auditoria, build e CI.

## Etapa 01: configuração (Concluída)

Validação fail-fast, precedência, configuração imutável, authority, redirect URI, scopes e erros públicos.

## Etapa 02: storage (Concluída)

Protocol, backend em memória, namespace, TTL, `StorageError`, concorrência local e last-write-wins.

## Etapa 03: identidade (Concluída)

Modelo imutável, claims, tenant, contexto request-local e `current_identity`.

## Etapa 04: MSAL (Concluída)

Cliente confidencial lazy, `SerializableTokenCache`, seleção de conta e aquisição silenciosa.

## Etapa 05: fluxo web (Concluída)

Login, callback, state, cancelamento, replay, next URL e persistência da identidade.

## Etapa 06: rotas e decorator (Concluída)

Blueprint opcional, `login_required`, logout e tratamento configurável.

## Etapa 07: hooks (Concluída)

Autenticação, logout, erros, eventos e vínculo local.

## Etapa 08: hardening (Concluída)

Threat model, logs sanitizados, consumo atômico distribuído opcional, auditoria de postura, falhas de storage e revisão de API.

## Etapa 09: template

Dependência local, Redis no template, Graph e testes cruzados.

## Etapa 10: publicação

Documentação final, TestPyPI, validação de consumidor e publicação.
