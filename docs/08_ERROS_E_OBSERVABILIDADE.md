# Erros e observabilidade

## Hierarquia

```text
MicrosoftEntraAuthError
├── ConfigurationError
├── StorageError
├── AuthenticationError
│   ├── AuthenticationRequired
│   ├── InvalidCallbackError
│   ├── IdentityValidationError
│   └── ConsentRequired
├── TokenAcquisitionError
└── ProviderUnavailableError
```

## Garantias implementadas

- Configuração inválida gera `ConfigurationError` durante `init_app()`;
- Chave, valor, TTL ou operação de storage inválida gera `StorageError`;
- Falhas externas de storage preservam a causa original em `__cause__`;
- Mensagens públicas não repetem client secret, chave, valor ou erro bruto do backend;
- Client secret não aparece na representação da configuração;
- Erros surgem antes de qualquer chamada de rede.

## Observabilidade atual

Nenhum evento estruturado ou integração de logging foi implementado. A aplicação pode capturar `ConfigurationError` e `StorageError` no startup ou em operações próprias, sem registrar a causa bruta quando ela puder conter dados sensíveis.

## Eventos planejados

- `authentication_started`;
- `authentication_succeeded`;
- `authentication_cancelled`;
- `authentication_rejected`;
- `token_cache_hit`;
- `token_cache_miss`;
- `token_refreshed`;
- `logout_completed`;
- `storage_failure`.

## Permitido em logs futuros

Timestamp, nível, evento, request ID, endpoint, código normalizado, correlation ID, duração e versão.

## Proibido em logs

Client secret, Authorization, cookie, auth code, tokens, cache, claims completas, chaves internas, identificadores de sessão e query string completa do callback.
