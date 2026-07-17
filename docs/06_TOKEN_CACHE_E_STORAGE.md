# Token cache e storage

## Contrato de storage

```python
class AuthStorage(Protocol):
    def load(self, key: str) -> bytes | None: ...
    def save(self, key: str, value: bytes, *, ttl: int | None = None) -> None: ...
    def delete(self, key: str) -> None: ...
```

`MemoryStorage` é thread-safe e adequado somente para desenvolvimento e testes.

## Token cache implementado

A extensão usa exclusivamente `msal.SerializableTokenCache`.

- Um cache é carregado por `home_account_id`;
- O identificador não aparece na chave: é transformado por SHA-256;
- A chave lógica é `token-cache:<digest>` dentro do namespace da aplicação;
- Bytes são decodificados em UTF-8 e entregues a `deserialize()`;
- `serialize()` é chamado somente quando `has_state_changed` é verdadeiro;
- O cache é salvo com `MS_ENTRA_TOKEN_CACHE_TTL`;
- Conteúdo inválido gera `StorageError` sem copiar o cache para a mensagem;
- Refresh tokens nunca são lidos ou modificados diretamente.

## Isolamento

```text
backend compartilhado
└── msentra:<namespace-aplicacao>:
    └── token-cache:<sha256-home-account-id>
```

Aplicações que compartilham backend devem possuir namespace exclusivo e estável (contas diferentes não compartilham cache).

## TTL

|                   Dado | Política atual                             |
| ---------------------: | :----------------------------------------- |
|            Token cache | `MS_ENTRA_TOKEN_CACHE_TTL`, padrão 28800 s |
|         Fluxo de login | Planejado, TTL curto                       |
| Identidade persistente | Planejada, alinhada à sessão               |

O TTL do cache é experimental e poderá ser harmonizado com a política de sessão na ETAPA 05.

## Concorrência

`MemoryStorage` usa lock e last-write-wins. O contrato ainda não oferece CAS, versão ou detecção de conflito. Backends distribuídos devem documentar sua política e a ETAPA 08 revisará concorrência distribuída.

## Produção

- Use backend server-side persistente;
- Use TLS quando aplicável;
- Aplique menor privilégio e proteção em repouso;
- Defina TTL coerente com a sessão;
- Não registre chave, valor, cache, token ou causa bruta de exceções;
- Não use `MemoryStorage` em múltiplos workers.
