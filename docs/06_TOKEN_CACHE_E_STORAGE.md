# Token cache e storage

## Estado atual: ETAPA 02

O contrato de storage, o backend em memória, namespace, TTL e erros estão implementados. Token cache MSAL, fluxo, identidade e dados reais de autenticação ainda não existem.

## Contrato público

```python
from typing import Protocol

class AuthStorage(Protocol):
    def load(self, key: str) -> bytes | None: ...
    def save(self, key: str, value: bytes, *, ttl: int | None = None) -> None: ...
    def delete(self, key: str) -> None: ...
```

O contrato é byte-oriented para não acoplar o núcleo a Redis, SQLAlchemy, Flask-Session ou formatos de serialização específicos.

## Implementação em memória

`MemoryStorage` fornece:

- Armazenamento em processo;
- Lock para operações atômicas;
- TTL baseado em relógio monotônico;
- Remoção preguiçosa em `load()`;
- Limpeza explícita por `purge_expired()`;
- `delete()` idempotente;
- Política last-write-wins.

Ele é destinado somente a desenvolvimento e testes. Dados são perdidos ao encerrar o processo e não são compartilhados entre workers.

## Namespace

A aplicação trabalha com chaves lógicas. Antes de delegar ao backend, a extensão aplica:

```text
msentra:<namespace>:<chave>
```

`MS_ENTRA_SESSION_NAMESPACE` pode definir o namespace explicitamente. Sem configuração, um valor determinístico é derivado do nome da aplicação, client ID e tenant ID.

Chaves não devem conter email, token, claim, client secret ou identificador previsível de usuário. Identificadores de sessão serão definidos em etapa posterior.

## TTL

| Dado futuro | Política planejada |
| ----------: | :----------------- |
|       Fluxo | Curto              |
|  Identidade | Duração da sessão  |
|  Cache MSAL | Alinhado à sessão  |

Na API atual, TTL deve ser inteiro positivo em segundos ou `None`. Zero, negativos, booleanos e outros tipos são rejeitados com `StorageError`.

## Concorrência

`MemoryStorage` protege operações com `RLock`. A última escrita concluída para uma chave prevalece. Locks distribuídos, CAS, versionamento e concorrência otimista permanecem fora do contrato e exigirão ADR próprio.

## Erros

Falhas de validação e operação usam `StorageError`. Adaptadores de backend:

- Preservam uma `StorageError` já segura;
- Encapsulam outras exceções com `raise ... from ...`;
- Não incluem chave, valor ou mensagem original na mensagem pública.

## Serialização futura

A serialização e desserialização do cache de autenticação deverão usar exclusivamente `msal.SerializableTokenCache`. Refresh tokens não serão manipulados diretamente pela aplicação ou pelo storage.

## Produção

Backends de produção devem considerar:

- TLS para serviços externos;
- TTL compatível com sessão e fluxo;
- Menor privilégio;
- Proteção em repouso;
- Múltiplos workers e processos;
- Disponibilidade e timeouts;
- Nenhum token, chave de sessão ou cache em logs.

Redis e outros backends de produção não foram implementados nesta etapa.