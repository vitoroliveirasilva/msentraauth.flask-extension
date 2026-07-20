# ADR-011: storage, namespace, TTL e concorrência local

## Contexto

A extensão precisa persistir bytes de fluxo, identidade e cache em etapas futuras sem acoplar o núcleo a Redis, SQLAlchemy ou Flask-Session. O contrato também precisa evitar colisões entre aplicações e definir expiração e concorrência antes de armazenar dados sensíveis.

## Decisão

- Expor `AuthStorage` com `load`, `save` e `delete`;
- Fornecer `MemoryStorage` somente para desenvolvimento e testes;
- Aplicar namespace antes de delegar qualquer chave ao backend;
- Aceitar TTL inteiro positivo ou `None`;
- Usar relógio monotônico para expiração em memória;
- Tornar `delete()` idempotente;
- Proteger operações em memória com `RLock`;
- Adotar last-write-wins para escritas concorrentes;
- Converter falhas externas em `StorageError`, preservando a causa sem expor chave ou valor.

## Consequências

- Backends externos podem ser injetados sem dependência obrigatória adicional;
- Aplicações que compartilham backend devem manter namespace exclusivo e estável;
- `MemoryStorage` não atende produção, múltiplos processos ou reinício;
- Locks distribuídos, CAS e concorrência otimista permanecem fora do contrato;
- Token cache e serialização MSAL continuam fora desta etapa.
