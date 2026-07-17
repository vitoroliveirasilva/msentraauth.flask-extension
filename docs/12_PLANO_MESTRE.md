# Plano mestre

## Etapa 00: fundação

Documentação coerente, estrutura `src`, empacotamento, qualidade, testes, auditoria, build e CI.

## Etapa 01: configuração (Concluída)

Validação fail-fast, precedência, configuração imutável, authority, redirect URI, scopes e erros públicos.

## Etapa 02: storage (Concluída)

Protocol, backend em memória, namespace, TTL, `StorageError`, concorrência local, last-write-wins e suíte contratual.

## Etapa 03: identidade

Modelo imutável, claims, tenant, contexto e `current_identity`.

## Etapa 04: MSAL

Construção do client, `SerializableTokenCache`, seleção de conta e aquisição silenciosa.

## Etapa 05: fluxo web

Login, callback, state, cancelamento, replay e next URL.

## Etapa 06: rotas e decorator

Blueprint opcional, `login_required`, logout e tratamento configurável.

## Etapa 07: hooks

Autenticação, logout, erros e vínculo local.

## Etapa 08: hardening

Threat model, logs, concorrência distribuída, falhas de storage e revisão de API.

## Etapa 09: template

Dependência local, Redis no template, Graph e testes cruzados.

## Etapa 10: publicação

Documentação final, TestPyPI, validação de consumidor e publicação.
