# Changelog

## Adicionado

- Contrato público e tipado `AuthStorage`;
- `MemoryStorage` thread-safe para desenvolvimento e testes;
- TTL com relógio monotônico, expiração preguiçosa e limpeza explícita;
- Isolamento de chaves por namespace de aplicação;
- Configuração `MS_ENTRA_SESSION_NAMESPACE` e argumento equivalente no construtor;
- Injeção opcional de backend por `MicrosoftEntraAuth(storage=...)`;
- Exceção pública `StorageError`;
- Suíte contratual reutilizável e testes de concorrência, TTL, isolamento e falhas;
- ADR sobre contrato, namespace, TTL e política last-write-wins.

## Alterado

- `init_app()` passa a registrar storage namespaced no estado da aplicação;
- Versão elevada para `0.3.0`;
- Artefatos e smoke test passam a validar os módulos de storage;
- Documentação de arquitetura, API, segurança, testes e status atualizada.

## Segurança

- Chaves e valores não são repetidos em mensagens de erro;
- Falhas de backends externos são convertidas em `StorageError` com causa preservada;
- Backends compartilhados recebem prefixo de namespace antes de qualquer operação;
- TTL inválido, valores não binários e chaves inseguras são rejeitados.

## Limites

- `MemoryStorage` não é seguro para produção, não é distribuído entre workers e perde dados no encerramento;
- Nenhum token, fluxo MSAL, identidade, login, callback ou rota foi implementado.
