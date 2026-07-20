# Erros e observabilidade

## Hierarquia implementada

```text
MicrosoftEntraAuthError
├── ConfigurationError
├── StorageError
├── AuthenticationError
│   ├── AuthenticationRequired
│   ├── AuthenticationCancelled
│   ├── InvalidCallbackError
│   ├── InvalidNavigationTarget
│   ├── IdentityValidationError
│   └── ConsentRequired
├── TokenAcquisitionError
└── ProviderUnavailableError
```

## Respostas do blueprint

Com tratamento interno habilitado:

|                                         Erro | HTTP |
| -------------------------------------------: | ---- |
| Cancelamento, callback ou navegação inválida | 400  |
|                     Autenticação obrigatória | 401  |
|                           Falha de aquisição | 502  |
|             Provedor ou storage indisponível | 503  |
|                        Configuração inválida | 500  |

As respostas usam texto curto e não copiam detalhes internos. Com `MS_ENTRA_HANDLE_ROUTE_ERRORS=False`, as exceções são propagadas.

## Garantias

- Client secret, auth code, token, cache, claims completas e identifiers não entram em mensagens públicas;
- `TokenAcquisitionError` expõe apenas `code` e `correlation_id` sanitizados;
- Causas originais ficam em `__cause__` para diagnóstico controlado;
- PII logging do MSAL permanece desligado;
- Callback duplicado ou consumido falha previsivelmente.

## Observabilidade futura

Eventos estruturados e hooks ainda não foram implementados. Permanecem planejados para ETAPA 07 e hardening.
