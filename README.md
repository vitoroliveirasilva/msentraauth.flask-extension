# MS Entra Auth para Flask

Extensão Flask reutilizável, em desenvolvimento, para integrar aplicações web ao Microsoft Entra ID por meio do MSAL. O projeto prioriza application factory, estado isolado por aplicação, API pública tipada e comportamento observável.

## Estado atual

A **ETAPA 00** está implementada e com isso é fornecido apenas a fundação executável e instalável da extensão.

|                        Componente | Estado        |
| --------------------------------: | :------------ |
|              Empacotamento Python | Implementado  |
|                   Estrutura `src` | Implementada  |
| `MicrosoftEntraAuth` e `init_app` | Implementados |
|                Testes e qualidade | Implementados |
|                         CI mínima | Implementada  |
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
venv\scripts\activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

## Uso disponível na ETAPA 00

```python
from flask import Flask
from flask_ms_entra_auth import MicrosoftEntraAuth

entra_auth = MicrosoftEntraAuth()


def create_app() -> Flask:
    app = Flask(__name__)
    entra_auth.init_app(app)
    return app
```

Atualmente, `init_app()`:

- Valida que o argumento é uma instância de `flask.Flask`;
- Registra estado isolado em `app.extensions["ms_entra_auth"]`;
- Aceita a mesma instância da extensão em múltiplas aplicações;
- Não armazena a aplicação em `self.app`;
- É idempotente quando a mesma instância inicializa novamente a mesma aplicação;
- Rejeita uma segunda instância tentando ocupar a chave já registrada;
- Não realiza chamadas de rede, não inicializa MSAL e não registra rotas.

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

## Escopo futuro

A documentação descreve a direção planejada para Authorization Code Flow, identidade autenticada, token cache, storage, hooks e rotas opcionais (esses recursos não fazem parte da implementação atual).

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
