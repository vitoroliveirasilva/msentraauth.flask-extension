# Token cache e storage

## Contratos

`AuthStorage` define `load`, `save` e `delete`. `AtomicAuthStorage` adiciona `take`, que lê e remove um valor em uma única operação do backend.

## Implementação padrão

`MemoryStorage` usa `RLock`, TTL monotônico, last-write-wins e `take()` atômico dentro do processo. Ele perde dados ao encerrar e não é adequado para múltiplos workers.

## Namespace

Cada aplicação usa prefixo exclusivo. Chaves públicas não incluem email, token ou secret. Identificadores de conta usados no token cache são derivados por hash.

## Consumo único

Fluxo de login e identidade usam `take()` quando disponível. O adaptador namespaced oferece fallback `load()` e `delete()` protegido por lock local, apenas para compatibilidade.

Esse fallback não evita corrida entre processos. Em produção distribuída, implemente `AtomicAuthStorage` e habilite `MS_ENTRA_REQUIRE_ATOMIC_STORAGE=True`.

## Token cache

A serialização usa exclusivamente `SerializableTokenCache`. Refresh tokens não são lidos ou alterados diretamente. A política de persistência continua last-write-wins e não oferece CAS.

## Falhas

Falhas de leitura, escrita, remoção ou consumo são convertidas em `StorageError`, com causa preservada. Mensagens públicas não repetem chave, valor ou texto bruto do backend.

## Produção

Backend de produção deve considerar TLS, menor privilégio, TTL, proteção em repouso, múltiplos workers, indisponibilidade e operação atômica real.
