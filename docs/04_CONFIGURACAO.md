# Configuração

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
|  `MS_ENTRA_POST_LOGIN_REDIRECT_URI` | `/`             | Destino após login         |
| `MS_ENTRA_POST_LOGOUT_REDIRECT_URI` | `/`             | Destino após logout        |
|       `MS_ENTRA_ALLOWED_NEXT_HOSTS` | `[]`            | Hosts externos permitidos  |
|     `MS_ENTRA_AUTO_REGISTER_ROUTES` | `True`          | Registro do blueprint      |
|      `MS_ENTRA_HANDLE_ROUTE_ERRORS` | `True`          | Respostas internas seguras |
|     `MS_ENTRA_UNAUTHENTICATED_MODE` | `redirect`      | Política do decorator      |
|            `MS_ENTRA_EVENT_LOGGING` | `False`         | Logging estruturado        |
|        `MS_ENTRA_REQUEST_ID_HEADER` | `X-Request-ID`  | Header de correlação       |
|   `MS_ENTRA_REQUIRE_ATOMIC_STORAGE` | `False`         | Exigir `AtomicAuthStorage` |
|          `MS_ENTRA_STRICT_SECURITY` | `False`         | Bloquear achados `error`   |

`MS_ENTRA_ENABLE_PII_LOG` permanece reservado e desligado.

## Regras de hardening

- Request ID header aceita somente letras, números e hífen;
- Valores recebidos no request aceitam formato seguro limitado a 128 caracteres;
- Storage atômico é capacidade do backend, não uma simulação com duas operações;
- Modo estrito não bloqueia avisos automaticamente;
- A auditoria não imprime o valor do `SECRET_KEY`.

## Precedência

1. Argumentos imutáveis da instância;
2. `app.config`;
3. Padrões seguros.

A extensão não carrega `.env`. Secret providers e rotação pertencem à aplicação.
