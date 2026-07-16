# Token cache e storage

## Objetivo

Persistir fluxo, identidade e cache MSAL sem acoplar o núcleo a Redis, SQLAlchemy ou Flask-Session.

## Contrato inicial

```python
from typing import Protocol

class AuthStorage(Protocol):
    def load(self, key: str) -> bytes | None: ...
    def save(self, key: str, value: bytes, *, ttl: int | None = None) -> None: ...
    def delete(self, key: str) -> None: ...
```

O contrato poderá evoluir para operações específicas e compare-and-set.

## Implementação padrão

A extensão não deve armazenar cache de token em cookie Flask no cliente. Para desenvolvimento, pode fornecer um armazenamento em memória com aviso explícito de que não é seguro para produção (o template deve demonstrar sessão server-side e Redis).

## Chaves

- Namespace exclusivo;
- Identificador de sessão imprevisível;
- Sem email;
- Sem token;
- Sem colisão entre aplicações.

## TTL

| Dado       | Política          |
| ---------: | :---------------- |
| Fluxo      | Curto             |
| Identidade | Duração da sessão |
| Cache      | Alinhado à sessão |
| Expirados  | Removidos         |

## Concorrência

O comportamento do sistema em cenários de concorrência deve ser explícito, previsível e coberto por testes automatizados. Para esta etapa inicial, será adotada a estratégia **last-write-wins**, na qual a última operação de escrita concluída prevalece sobre as anteriores. Dessa forma, os testes devem comprovar esse comportamento e garantir que ele permaneça determinístico e qualquer evolução que introduza mecanismos como locks, operações CAS (*compare-and-swap*), controle de versão, detecção de conflitos ou concorrência otimista será documentada por meio de um ADR específico.

## Serialização

A serialização e a desserialização do cache de autenticação devem utilizar exclusivamente o `SerializableTokenCache` fornecido pelo MSAL.

Refresh tokens não devem ser acessados, armazenados, alterados ou manipulados diretamente pela aplicação. Logo, o gerenciamento desses dados permanece sob responsabilidade do MSAL.

## Produção

Em ambientes de produção, a implementação deve adotar controles compatíveis com o nível de sensibilidade dos dados armazenados, incluindo:

* Uso de TLS nas conexões com serviços externos de armazenamento;
* Definição de TTLs adequados ao ciclo de vida das sessões;
* Aplicação do princípio do menor privilégio nas credenciais e permissões;
* Proteção dos dados em repouso, quando aplicável;
* Prevenção do registro de tokens, identificadores de sessão ou outros valores sensíveis em logs.

## Limpeza e encerramento de sessão

O logout deve remover exclusivamente os dados associados à sessão atual, sem afetar sessões pertencentes a outros usuários, dispositivos ou contextos de autenticação.

Falhas ocorridas durante operações de leitura, escrita, expiração ou remoção no mecanismo de armazenamento devem ser encapsuladas e propagadas como `StorageError`, preservando a causa original para diagnóstico sem expor dados sensíveis.