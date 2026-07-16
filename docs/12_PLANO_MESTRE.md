# Plano mestre

## Etapa 00: fundação

Documentação, estrutura `src`, `pyproject.toml`, pacote importável, qualidade e testes mínimos.

## Etapa 01: configuração

Validação fail-fast, authority, redirect URI, scopes e testes.

## Etapa 02: storage

Protocol, storage de testes, namespace, TTL, erros e suíte contratual.

## Etapa 03: identidade

Modelo imutável, claims, tenant, contexto e `current_identity`.

## Etapa 04: MSAL

Construção do client, token cache, seleção de conta e aquisição silenciosa.

## Etapa 05: fluxo web

Login, callback, state, cancelamento, replay e next URL.

## Etapa 06: rotas e decorator

Blueprint opcional, `login_required`, logout e tratamento configurável.

## Etapa 07: hooks

Autenticação, logout, erros e vínculo local.

## Etapa 08: hardening

Threat model, logs, concorrência, falhas de storage e revisão de API.

## Etapa 09: template

Dependência local, Redis no template, Graph e testes cruzados.

## Etapa 10: publicação

Docs, build, TestPyPI e validação.
