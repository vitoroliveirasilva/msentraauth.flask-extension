# Erros e observabilidade

## Hierarquia

```text
MicrosoftEntraAuthError
├── ConfigurationError
├── StorageError
├── AuthenticationError
│   ├── AuthenticationRequired
│   ├── IdentityValidationError
│   └── ConsentRequired
├── TokenAcquisitionError
└── ProviderUnavailableError
```

## Semântica

- `AuthenticationRequired`: falta identidade ou conta MSAL correspondente;
- `IdentityValidationError`: claims ou campos de identidade inválidos;
- `ConsentRequired`: aquisição silenciosa não basta e interação será necessária;
- `TokenAcquisitionError`: resultado MSAL inválido ou erro retornado pelo provedor;
- `ProviderUnavailableError`: exceção inesperada ao construir ou usar cliente MSAL;
- `StorageError`: falha de persistência, serialização ou cache corrompido.

`TokenAcquisitionError` pode expor `code` e `correlation_id` sanitizados. `error_description` e resposta bruta não são copiadas.

## Garantias

- Client secret não aparece em representação;
- `Identity.__repr__` não expõe PII ou claims;
- Token, cache, chave e identificador de conta não aparecem em mensagens públicas;
- Causas originais são preservadas apenas em `__cause__` para diagnóstico controlado;
- `init_app()` falha antes de rede;
- PII logging do MSAL permanece desativado.

## Observabilidade futura

Eventos estruturados ainda não foram implementados. Permanecem planejados: autenticação iniciada, sucesso, cancelamento, rejeição, cache hit/miss, refresh, logout e falha de storage.
