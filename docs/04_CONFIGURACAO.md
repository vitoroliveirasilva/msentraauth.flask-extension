# Configuração

## Estado

A resolução e validação descritas neste documento estão implementadas na ETAPA 01. Nenhum cliente MSAL é criado durante `init_app()`.

## Prefixo

Todas as chaves públicas usam `MS_ENTRA_`.

## Obrigatórias

|                    Chave | Descrição               |
| -----------------------: | :---------------------- |
|     `MS_ENTRA_CLIENT_ID` | ID da aplicação         |
| `MS_ENTRA_CLIENT_SECRET` | Credencial confidencial |
|     `MS_ENTRA_TENANT_ID` | Tenant único permitido  |
|  `MS_ENTRA_REDIRECT_URI` | URI absoluta registrada |

Valores ausentes, não textuais, vazios ou reconhecidos como placeholders geram `ConfigurationError`.

## Opcionais implementadas

|                Chave | Padrão                                       | Uso                      |
| -------------------: | :------------------------------------------- | :----------------------- |
| `MS_ENTRA_AUTHORITY` | `https://login.microsoftonline.com/<tenant>` | Authority futura do MSAL |
|    `MS_ENTRA_SCOPES` | `("User.Read",)`                             | Scopes delegados futuros |

A authority deve:

- Usar HTTPS;
- Ser absoluta e não conter credenciais, query string ou fragmento;
- Conter exatamente um segmento de tenant;
- Usar o mesmo tenant configurado em `MS_ENTRA_TENANT_ID`.

Os scopes devem ser um iterável que não seja string. Entradas são aparadas, duplicatas exatas são removidas preservando a ordem e o resultado é armazenado como tupla imutável.

## Opcionais planejadas

|                               Chave | Padrão    | Uso futuro      |
| ----------------------------------: | :-------- | :-------------- |
|               `MS_ENTRA_URL_PREFIX` | `/auth`   | Rotas           |
| `MS_ENTRA_POST_LOGOUT_REDIRECT_URI` | local     | Pós-logout      |
|     `MS_ENTRA_AUTO_REGISTER_ROUTES` | `True`    | Blueprint       |
|        `MS_ENTRA_SESSION_NAMESPACE` | exclusivo | Chaves internas |
|           `MS_ENTRA_ENABLE_PII_LOG` | `False`   | PII do MSAL     |

Essas chaves ainda não são interpretadas.

## Redirect URI

A URI deve ser absoluta, usar HTTP ou HTTPS, não conter credenciais nem fragmento e possuir host válido.

- HTTPS é aceito para hosts externos;
- HTTP é aceito somente para desenvolvimento em loopback: `localhost`, `127.0.0.0/8` ou IPv6 loopback;
- HTTP para hosts externos gera `ConfigurationError`.

A extensão não descobre redirect URI por request, proxy ou header de host.

## Tenant

A implementação aceita identificadores compostos por letras, números, ponto e hífen. Os aliases `common`, `organizations` e `consumers` são rejeitados porque o escopo inicial é single-tenant.

## Precedência

1. Argumentos imutáveis da instância;
2. `app.config`;
3. Padrões seguros.

Exemplo:

```python
entra_auth = MicrosoftEntraAuth(
    tenant_id="tenant-fixo",
    scopes=["User.Read"],
)
```

O `tenant_id` acima prevalece sobre `MS_ENTRA_TENANT_ID`, enquanto as demais chaves ainda podem vir de cada aplicação.

## Imutabilidade e isolamento

- A configuração resolvida é armazenada em objeto congelado no estado da aplicação;
- Alterar `app.config` após a primeira inicialização não modifica a configuração já registrada;
- Aplicações distintas recebem objetos de configuração distintos.