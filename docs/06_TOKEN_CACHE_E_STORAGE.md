# Token cache e storage

## Contrato

```python
class AuthStorage(Protocol):
    def load(self, key: str) -> bytes | None: ...
    def save(self, key: str, value: bytes, *, ttl: int | None = None) -> None: ...
    def delete(self, key: str) -> None: ...
```

## Dados persistidos

|             Dado | TTL padrão | Chave                        |
| ---------------: | :--------- | :--------------------------- |
| Fluxo interativo | 600 s      | Referência aleatória         |
|       Identidade | 28800 s    | Hash de session ID aleatório |
|      Token cache | 28800 s    | Hash de `home_account_id`    |

Todos recebem também o namespace da aplicação.

## Cookie

O cookie Flask não contém fluxo, claims, identidade, auth code nem cache. Ele guarda apenas referências aleatórias assinadas pela `SECRET_KEY` da aplicação.

## Cache MSAL

- A serialização usa exclusivamente `SerializableTokenCache`;
- Refresh tokens não são lidos ou manipulados diretamente;
- O cache só é gravado quando `has_state_changed` indica alteração.

## Concorrência

- Fluxo interativo: consume-first, uma única redenção;
- Escritas gerais: last-write-wins;
- `MemoryStorage`: protegido por `RLock`, somente para desenvolvimento;
- Concorrência distribuída e CAS permanecem para hardening futuro.

## Logout

Remove somente fluxo, identidade e cache associados à sessão atual. Falhas de storage são encapsuladas em `StorageError`, com causa preservada e mensagem sanitizada.

## Produção

Use backend compartilhado entre workers, TLS quando aplicável, menor privilégio, TTL, proteção em repouso e política explícita de indisponibilidade. Nunca registre chaves, identificadores de sessão, cache ou tokens.
