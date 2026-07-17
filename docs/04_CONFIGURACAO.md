# Configuração

## Precedência

1. Argumentos do construtor;
2. `app.config`;
3. Padrões seguros.

A configuração é resolvida uma vez por aplicação e armazenada em dataclass congelada.

## Obrigatórias

|                    Chave | Descrição               |
| -----------------------: | :---------------------- |
|     `MS_ENTRA_CLIENT_ID` | ID da aplicação         |
| `MS_ENTRA_CLIENT_SECRET` | Credencial confidencial |
|     `MS_ENTRA_TENANT_ID` | Tenant único permitido  |
|  `MS_ENTRA_REDIRECT_URI` | URI absoluta registrada |

## Opcionais implementadas

|                        Chave | Padrão                                       | Uso                           |
| ---------------------------: | :------------------------------------------- | :---------------------------- |
|         `MS_ENTRA_AUTHORITY` | `https://login.microsoftonline.com/<tenant>` | Authority MSAL                |
|            `MS_ENTRA_SCOPES` | `("User.Read",)`                             | Scopes delegados padrão       |
| `MS_ENTRA_SESSION_NAMESPACE` | hash de app/client/tenant                    | Namespace do storage          |
|   `MS_ENTRA_TOKEN_CACHE_TTL` | `28800`                                      | TTL do cache MSAL em segundos |

O construtor aceita argumentos equivalentes em snake_case.

## `MS_ENTRA_TOKEN_CACHE_TTL`

Deve ser inteiro positivo. Booleanos, strings, zero e negativos são rejeitados. O valor padrão de oito horas é provisório para a série experimental e pode ser alinhado à política de sessão quando o fluxo web for implementado.

## Validação

- Vazios e placeholders falham cedo;
- Tenant genérico (`common`, `organizations`, `consumers`) é rejeitado;
- Authority exige HTTPS e tenant correspondente;
- Redirect HTTP é permitido somente em loopback;
- Scopes são aparados, deduplicados e congelados;
- Namespace aceita apenas letras, números, `.`, `_` e `-`;
- Client secret não aparece em representação ou mensagens;
- Configuração não muda após `init_app()`.

## Fábrica MSAL

`msal_client_factory` não é chave de `app.config`, mas sim argumento avançado do construtor para testes. Deve ser callable e não é serializado. O cliente padrão recebe client ID, client secret, authority, token cache e `enable_pii_log=False`.

## `.env`

A extensão não carrega `.env`. Secret providers, rotação e injeção de configuração permanecem responsabilidade da aplicação.
