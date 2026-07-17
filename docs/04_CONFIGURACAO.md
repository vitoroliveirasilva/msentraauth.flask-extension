# Configuração

## Estado

A configuração principal foi implementada na ETAPA 01. A ETAPA 02 adiciona namespace de storage. Nenhum cliente MSAL é criado durante `init_app()`.

## Prefixo

Todas as chaves públicas usam `MS_ENTRA_`.

## Obrigatórias

|                    Chave | Descrição               |
| -----------------------: | :---------------------- |
|     `MS_ENTRA_CLIENT_ID` | ID da aplicação         |
| `MS_ENTRA_CLIENT_SECRET` | Credencial confidencial |
|     `MS_ENTRA_TENANT_ID` | Tenant único permitido  |
|  `MS_ENTRA_REDIRECT_URI` | URI absoluta registrada |

## Opcionais implementadas

|                        Chave | Padrão                                       | Uso                                  |
| ---------------------------: | :------------------------------------------- | :----------------------------------- |
|         `MS_ENTRA_AUTHORITY` | `https://login.microsoftonline.com/<tenant>` | Authority futura do MSAL             |
|            `MS_ENTRA_SCOPES` | `("User.Read",)`                             | Scopes delegados futuros             |
| `MS_ENTRA_SESSION_NAMESPACE` | derivado                                     | Prefixo lógico das chaves de storage |

O namespace explícito aceita letras, números, ponto, sublinhado e hífen, com até 128 caracteres. Valores vazios, placeholders e caracteres fora desse conjunto geram `ConfigurationError`.

Na ausência de valor explícito, o namespace é derivado de forma determinística do nome da aplicação, client ID e tenant ID. O client secret não participa do cálculo.

Backends compartilhados por aplicações logicamente diferentes devem usar namespace explícito, exclusivo e estável entre reinícios e workers.

## Opcionais planejadas

|                               Chave | Padrão  | Uso futuro  |
| ----------------------------------: | :------ | :---------- |
|               `MS_ENTRA_URL_PREFIX` | `/auth` | Rotas       |
| `MS_ENTRA_POST_LOGOUT_REDIRECT_URI` | local   | Pós-logout  |
|     `MS_ENTRA_AUTO_REGISTER_ROUTES` | `True`  | Blueprint   |
|           `MS_ENTRA_ENABLE_PII_LOG` | `False` | PII do MSAL |

## Precedência

1. Argumentos imutáveis da instância;
2. `app.config`;
3. Padrões seguros.

Exemplo:

```python
entra_auth = MicrosoftEntraAuth(
    tenant_id="tenant-fixo",
    scopes=["User.Read"],
    session_namespace="app-principal",
)
```

## Imutabilidade e isolamento

A configuração resolvida é congelada. Alterar `app.config` após a primeira inicialização não modifica authority, scopes ou namespace já registrados.

## Segredos

- Client secret não possui padrão;
- Erros não incluem valores recebidos;
- A extensão não depende de `.env`;
- Secret providers continuam responsabilidade da aplicação;
- Namespace derivado não usa client secret.
