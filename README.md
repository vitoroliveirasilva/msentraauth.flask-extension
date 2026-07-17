# MS Entra Auth para Flask

Extensão Flask reutilizável, em desenvolvimento, para integrar aplicações web ao Microsoft Entra ID por meio do MSAL. O projeto prioriza application factory, estado isolado por aplicação, API pública tipada e comportamento observável.

## Estado atual

A **ETAPA 01** está implementada. A versão de desenvolvimento `0.2.0` fornece a fundação instalável e a resolução validada de configuração por aplicação.

|                        Componente | Estado        |
| --------------------------------: | :------------ |
|              Empacotamento Python | Implementado  |
|                   Estrutura `src` | Implementada  |
| `MicrosoftEntraAuth` e `init_app` | Implementados |
|            Configuração fail-fast | Implementada  |
|            Testes, qualidade e CI | Implementados |
|   Autenticação Microsoft Entra ID | Não iniciada  |
|                       Fluxos MSAL | Não iniciados |
|                Publicação no PyPI | Não realizada |

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
python -m venv venv
venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

## Uso disponível na ETAPA 01

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
    )
    entra_auth.init_app(app)
    return app
```

Também é possível definir valores imutáveis na instância. Eles possuem precedência sobre `app.config`:

```python
entra_auth = MicrosoftEntraAuth(
    tenant_id="22222222-2222-2222-2222-222222222222",
    scopes=["User.Read", "Mail.Read"],
)
```

`init_app()` atualmente:

- Valida que o argumento é uma instância de `flask.Flask`;
- Resolve configuração por argumentos da instância, `app.config` e padrões seguros;
- Exige client ID, client secret, tenant ID e redirect URI;
- Deriva authority e aplica `User.Read` como scope padrão;
- Rejeita valores vazios, placeholders, tenants genéricos, authority divergente e redirect HTTP externo;
- Registra configuração imutável e estado isolado em `app.extensions["ms_entra_auth"]`;
- Aceita a mesma instância da extensão em múltiplas aplicações;
- Não armazena a aplicação em `self.app`;
- Preserva a configuração original quando a mesma aplicação é inicializada novamente;
- Não realiza chamadas de rede, não inicializa MSAL e não registra rotas.

Falhas previsíveis de configuração usam `ConfigurationError`:

```python
from flask_ms_entra_auth import ConfigurationError
```

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

No PowerShell, a última validação usa:

```powershell
$env:DIST_DIR = "dist"
pytest tests/test_distribution.py --no-cov
Remove-Item Env:DIST_DIR
```

## Escopo futuro

Storage, identidade autenticada, cliente MSAL, Authorization Code Flow, token cache, hooks, decorators e rotas permanecem planejados. Nenhum desses recursos faz parte da implementação atual.

O [msentraauth.flask-template](https://github.com/vitoroliveirasilva/msentraauth.flask-template) será futuramente a aplicação consumidora e de referência.

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
