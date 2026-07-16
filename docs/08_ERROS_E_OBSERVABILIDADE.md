# Erros e observabilidade

## Hierarquia

```text
MicrosoftEntraAuthError
├── ConfigurationError
├── AuthenticationError
│   ├── AuthenticationRequired
│   ├── InvalidCallbackError
│   ├── IdentityValidationError
│   └── ConsentRequired
├── TokenAcquisitionError
├── StorageError
└── ProviderUnavailableError
```

## Garantias

- Erros previsíveis não viram `500` por padrão;
- Mensagens públicas são seguras;
- Correlation ID pode ser preservado;
- Auth code, token e cache nunca entram na exceção pública.

## Eventos

- `authentication_started`;
- `authentication_succeeded`;
- `authentication_cancelled`;
- `authentication_rejected`;
- `token_cache_hit`;
- `token_cache_miss`;
- `token_refreshed`;
- `logout_completed`;
- `storage_failure`.

## Permitido em logs

Timestamp, nível, evento, request ID, endpoint, código normalizado, correlation ID, duração e versão.

## Proibido em logs

Client secret, Authorization, cookie, auth code, tokens, cache, claims completas e query string completa do callback.

## Métricas

O núcleo pode expor hooks, mas não impor biblioteca de telemetria e logging de PII permanece desligado por padrão.
