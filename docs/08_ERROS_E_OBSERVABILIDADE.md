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

## Garantias implementadas

- Configuração ausente ou inválida gera `ConfigurationError` durante `init_app()`;
- Mensagens indicam a chave ou a regra violada sem repetir o valor recebido;
- Client secret não aparece na representação da configuração resolvida;
- Erros de configuração surgem antes de qualquer chamada de rede;
- A causa é previsível e pode ser tratada pela aplicação durante o startup.

## Garantias futuras

- Erros previsíveis de autenticação não devem virar `500` por padrão;
- Correlation ID poderá ser preservado;
- Auth code, token e cache nunca entrarão na exceção pública.

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

Nenhum evento ou integração de logging foi implementado na ETAPA 01.

## Permitido em logs futuros

Timestamp, nível, evento, request ID, endpoint, código normalizado, correlation ID, duração e versão.

## Proibido em logs

Client secret, Authorization, cookie, auth code, tokens, cache, claims completas e query string completa do callback.

## Métricas

O núcleo poderá expor hooks, mas não imporá biblioteca de telemetria. Logging de PII permanece desligado por padrão.
