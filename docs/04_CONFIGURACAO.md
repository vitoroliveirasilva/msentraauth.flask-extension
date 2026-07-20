# Configuração

## Prefixo

Todas as chaves públicas usam `MS_ENTRA_`.

## Obrigatórias

|                    Chave | Descrição               |
| -----------------------: | :---------------------- |
|     `MS_ENTRA_CLIENT_ID` | ID da aplicação         |
| `MS_ENTRA_CLIENT_SECRET` | Credencial confidencial |
|     `MS_ENTRA_TENANT_ID` | Tenant permitido        |
|  `MS_ENTRA_REDIRECT_URI` | URI absoluta registrada |

## Opcionais implementadas

|                               Chave | Padrão          | Uso                        |
| ----------------------------------: | :-------------- | :------------------------- |
|                `MS_ENTRA_AUTHORITY` | Derivada        | Authority MSAL             |
|                   `MS_ENTRA_SCOPES` | `['User.Read']` | Scopes delegados           |
|        `MS_ENTRA_SESSION_NAMESPACE` | Derivado        | Isolamento no storage      |
|          `MS_ENTRA_TOKEN_CACHE_TTL` | `28800`         | Cache por conta            |
|                 `MS_ENTRA_FLOW_TTL` | `600`           | Transação interativa       |
|             `MS_ENTRA_IDENTITY_TTL` | `28800`         | Identidade server-side     |
|               `MS_ENTRA_URL_PREFIX` | `/auth`         | Prefixo do blueprint       |
|  `MS_ENTRA_POST_LOGIN_REDIRECT_URI` | `/`             | Destino padrão após login  |
| `MS_ENTRA_POST_LOGOUT_REDIRECT_URI` | `/`             | Destino após logout local  |
|       `MS_ENTRA_ALLOWED_NEXT_HOSTS` | `[]`            | Hosts externos permitidos  |
|     `MS_ENTRA_AUTO_REGISTER_ROUTES` | `True`          | Registro do blueprint      |
|      `MS_ENTRA_HANDLE_ROUTE_ERRORS` | `True`          | Respostas internas seguras |
|     `MS_ENTRA_UNAUTHENTICATED_MODE` | `redirect`      | Política do decorator      |
|           `MS_ENTRA_ENABLE_PII_LOG` | `False`         | Deve permanecer desligado  |

## Navegação segura

Destinos locais devem começar com `/`, não podem começar com `//`, conter barra invertida, controles ou fragmento. URLs absolutas exigem host exato em `MS_ENTRA_ALLOWED_NEXT_HOSTS`; HTTP externo é rejeitado e só é tolerado em loopback.

## Rotas customizadas

Para aplicações que registram login, callback e logout manualmente:

```python
MS_ENTRA_AUTO_REGISTER_ROUTES = False
```

Nesse modo, `register_routes(app)` pode ser chamado depois ou a aplicação pode usar os métodos públicos do fluxo.

## Sessão Flask

Operações web exigem `SECRET_KEY` configurada. O cookie assinado contém somente referências aleatórias; conteúdo sensível permanece no storage.

## Precedência

1. Argumentos imutáveis da instância;
2. `app.config`;
3. Padrões seguros.

A extensão não carrega `.env`. Secret providers e rotação pertencem à aplicação.
