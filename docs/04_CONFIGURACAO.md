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

## Opcionais planejadas

| Chave                               | Padrão          | Uso              |
| ----------------------------------- | --------------- | ---------------- |
| `MS_ENTRA_AUTHORITY`                | Derivada        | Authority MSAL   |
| `MS_ENTRA_SCOPES`                   | `['User.Read']` | Scopes delegados |
| `MS_ENTRA_URL_PREFIX`               | `/auth`         | Rotas            |
| `MS_ENTRA_POST_LOGOUT_REDIRECT_URI` | local           | Pós-logout       |
| `MS_ENTRA_AUTO_REGISTER_ROUTES`     | `True`          | Blueprint        |
| `MS_ENTRA_SESSION_NAMESPACE`        | Exclusivo       | Chaves internas  |
| `MS_ENTRA_ENABLE_PII_LOG`           | `False`         | PII do MSAL      |

## Validação

- Vazios e placeholders falham cedo;
- Redirect URI deve ser absoluta;
- Produção deve usar HTTPS;
- Client secret não possui padrão;
- Valores sensíveis não aparecem no erro;
- Configuração não muda após início do servidor.

## Precedência

1. Argumentos imutáveis da instância;
2. `app.config`;
3. Padrões seguros.

A extensão não depende de `.env`. Portanto, secret providers são responsabilidade da aplicação.
