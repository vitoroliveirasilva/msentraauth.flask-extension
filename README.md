# MS Entra Auth para Flask

Extensão Flask planejada para integrar aplicações web ao Microsoft Entra ID por meio do MSAL com fluxo de autorização, identidade autenticada, cache de tokens substituível e compatibilidade com o padrão de application factory.

## Objetivo

Reduzir repetição e falhas recorrentes na autenticação Microsoft Entra ID em aplicações Flask, sem esconder o protocolo e sem transformar a extensão em um framework paralelo.

- Inicialização e conclusão do Authorization Code Flow;
- Preservação e validação do fluxo entre login e callback;
- Integração com o MSAL e seu token cache;
- Aquisição silenciosa e renovação de tokens;
- Identidade autenticada imutável e sem credenciais;
- Rotas opcionais de login, callback e logout;
- Hooks para vinculação com usuários locais;
- Backends substituíveis para persistência;
- Erros públicos previsíveis e logs sem segredos.

## Fora do núcleo

O núcleo não deverá fornecer banco de usuários, painel administrativo, autorização completa, templates obrigatórios, cliente genérico da Microsoft Graph, Redis obrigatório, SQLAlchemy, criação de App Registration ou suporte a frameworks além do Flask.

## Relação com o template

```text
msentraauth.flask-extension
          ↓
  Núcleo reutilizável
          ↓
msentraauth.flask-template
```

O [msentraauth.flask-template](https://github.com/vitoroliveirasilva/msentraauth.flask-template) será o consumidor real, exemplo de integração e teste de uso da extensão.

## Estado

|           Componente | Estado        |
| -------------------: | :------------ |
|       Visão e escopo | Definidos     |
| Arquitetura proposta | Definida      |
|  API pública inicial | Especificada  |
|        Implementação | Não iniciada  |
|               Testes | Não iniciados |
|                 PyPI | Não publicado |
|       Versão estável | Inexistente   |

## Uso pretendido

```python
from flask import Flask
from flask_ms_entra_auth import MicrosoftEntraAuth

entra_auth = MicrosoftEntraAuth()


def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_mapping(
        MS_ENTRA_CLIENT_ID="...",
        MS_ENTRA_CLIENT_SECRET="...",
        MS_ENTRA_TENANT_ID="...",
        MS_ENTRA_REDIRECT_URI="http://localhost:5000/auth/callback",
    )
    entra_auth.init_app(app)
    entra_auth.register_routes(app)
    return app
```

```python
from flask_ms_entra_auth import current_identity, login_required

@app.get('/area-restrita')
@login_required
def area_restrita():
    return {
        'id': current_identity.object_id,
        'nome': current_identity.display_name,
        'tenant': current_identity.tenant_id,
    }
```

Os nomes acima são parte do contrato proposto, não de uma implementação disponível.

## Princípios

1. Segurança antes de conveniência;
2. Pouca mágica e comportamento observável;
3. Application factory como requisito;
4. Estado isolado por aplicação e sessão;
5. Dependências obrigatórias mínimas;
6. Tokens nunca expostos ao cliente por padrão;
7. API pública pequena, tipada e previsível.

## Documentação

O índice completo está disponível em [`docs/README.md`](docs/README.md).

## Branches

- `dev`: desenvolvimento e integração.
- `prod`: versão considerada estável.

## Identidade do pacote

|         Contexto | Nome planejado                |
| ---------------: | :---------------------------- |
|      Repositório | `msentraauth.flask-extension` |
|             PyPI | `flask-ms-entra-auth`         |
|           Import | `flask_ms_entra_auth`         |
| Classe principal | `MicrosoftEntraAuth`          |

## Segurança e contribuição

Consulte [`SECURITY.md`](SECURITY.md) e [`CONTRIBUTING.md`](CONTRIBUTING.md).

## Licença e marcas

Licenciado sob a [Licença MIT](LICENSE). Este é um projeto independente, não oficial e sem qualquer afiliação, manutenção ou endosso da Microsoft. Microsoft, Microsoft Entra, Microsoft Graph e MSAL são marcas registradas de seus respectivos proprietários.
