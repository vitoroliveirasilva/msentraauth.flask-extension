# MS Entra Auth para Flask

Extensão Flask reutilizável, em desenvolvimento, para integrar aplicações web ao Microsoft Entra ID por meio do MSAL. O projeto prioriza application factory, estado isolado por aplicação, API pública tipada e comportamento observável.

## Estado atual

A **ETAPA 02** está implementada. A versão de desenvolvimento `0.3.0` fornece fundação instalável, configuração validada e contrato inicial de storage com TTL e isolamento por namespace.

| Componente                           |
| ------------------------------------ |
| Empacotamento Python                 |
| `MicrosoftEntraAuth` e `init_app`    |
| Configuração fail-fast               |
| Contrato `AuthStorage`               |
| `MemoryStorage` para desenvolvimento |
| Namespace e TTL                      |
| Testes, qualidade e CI               |
| Autenticação Microsoft Entra ID      |
| Fluxos MSAL                          |
| Publicação no PyPI                   |

O status detalhado está em [`docs/implementation/status.md`](docs/implementation/status.md).

## Instalação para desenvolvimento

Requer Python 3.11 ou superior.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

No PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

## Uso disponível na ETAPA 02

```python
from flask import Flask
from flask_ms_entra_auth import MicrosoftEntraAuth

entra_auth = MicrosoftEntraAuth()


def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_mapping(
        MS_ENTRA_CLIENT_ID="11111111-1111-1111-1111-111111111111",
        MS_ENTRA_CLIENT_SECRET="obtido-de-um-secret-provider",
        MS_ENTRA_TENANT_ID="22222222-2222-2222-2222-222222222222",
        MS_ENTRA_REDIRECT_URI="https://app.example.com/auth/callback",
        MS_ENTRA_SCOPES=["User.Read"],
        MS_ENTRA_SESSION_NAMESPACE="minha-aplicacao",
    )
    entra_auth.init_app(app)
    return app
```

Sem backend explícito, cada aplicação recebe um `MemoryStorage` próprio. Esse backend perde todos os dados ao encerrar o processo e não é adequado para produção.

Um backend próprio pode implementar o contrato público:

```python
from flask_ms_entra_auth import AuthStorage, MicrosoftEntraAuth


class MeuStorage:
    def load(self, key: str) -> bytes | None:
        ...

    def save(self, key: str, value: bytes, *, ttl: int | None = None) -> None:
        ...

    def delete(self, key: str) -> None:
        ...


storage: AuthStorage = MeuStorage()
entra_auth = MicrosoftEntraAuth(storage=storage)
```

A extensão adiciona automaticamente o namespace antes de delegar as chaves ao backend. Backends compartilhados por aplicações distintas devem usar `MS_ENTRA_SESSION_NAMESPACE` exclusivo e estável.

`init_app()` atualmente:

- Valida a aplicação e a configuração;
- Registra configuração imutável e estado isolado em `app.extensions["ms_entra_auth"]`;
- Registra uma visão namespaced do backend de storage;
- Usa `MemoryStorage` por aplicação quando nenhum backend é fornecido;
- Suporta a mesma instância em múltiplas aplicações;
- Não armazena a aplicação em `self.app`;
- Não realiza chamadas de rede, não inicializa MSAL e não registra rotas.

Falhas previsíveis usam exceções públicas:

```python
from flask_ms_entra_auth import ConfigurationError, StorageError
```

## Garantias de storage

- Valores são bytes;
- Chaves vazias, excessivas ou com byte nulo são rejeitadas;
- TTL deve ser inteiro positivo ou `None`;
- Valores expirados retornam `None` e são removidos;
- `delete()` é idempotente;
- `MemoryStorage` é protegido por lock;
- Escrita usa estratégia last-write-wins;
- Falhas de backends externos são encapsuladas em `StorageError` com causa preservada;
- Mensagens de erro não repetem chave nem conteúdo.

## Validação local

```bash
ruff check .
ruff format --check .
mypy src tests
pytest
bandit -c pyproject.toml -r src
pip-audit .
python -m build
python -m twine check dist/*
DIST_DIR=dist pytest tests/test_distribution.py --no-cov
```

No PowerShell:

```powershell
$env:DIST_DIR = "dist"
pytest tests/test_distribution.py --no-cov
Remove-Item Env:DIST_DIR
```

## Escopo futuro

Identidade autenticada, cliente MSAL, `SerializableTokenCache`, Authorization Code Flow, hooks, decorators e rotas permanecem planejados. O storage desta etapa ainda não recebe tokens ou dados de autenticação reais.

O [msentraauth.flask-template](https://github.com/vitoroliveirasilva/msentraauth.flask-template) será futuramente a aplicação consumidora e de referência. Ele não foi alterado nesta etapa.

## Princípios

1. Segurança antes de conveniência;
2. Pouca mágica e comportamento observável;
3. Application factory como requisito;
4. Estado isolado por aplicação e sessão;
5. Dependências obrigatórias mínimas;
6. Tokens nunca expostos ao cliente por padrão;
7. API pública pequena, tipada e previsível.

## Identidade do pacote

|         Contexto | Nome                          |
| ---------------: | :---------------------------- |
|      Repositório | `msentraauth.flask-extension` |
|     Distribuição | `flask-ms-entra-auth`         |
|           Import | `flask_ms_entra_auth`         |
| Classe principal | `MicrosoftEntraAuth`          |

## Documentação

O índice completo está em [`docs/README.md`](docs/README.md).

## Branches

- `dev`: desenvolvimento e integração;
- `prod`: estado considerado estável.

## Segurança e contribuição

Consulte [`SECURITY.md`](SECURITY.md) e [`CONTRIBUTING.md`](CONTRIBUTING.md).

## Licença e marcas

Licenciado sob a [Licença MIT](LICENSE). Este é um projeto independente, não oficial e sem afiliação, manutenção ou endosso da Microsoft. Microsoft, Microsoft Entra, Microsoft Graph e MSAL são marcas de seus respectivos proprietários.
