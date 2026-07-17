# Changelog

## Adicionado

- Resolução de configuração por argumentos da instância, `app.config` e padrões seguros;
- Configuração imutável e isolada por aplicação;
- Validação fail-fast de client ID, client secret, tenant ID e redirect URI;
- Derivação e validação de authority;
- Normalização e deduplicação de scopes;
- Exceções públicas `MicrosoftEntraAuthError` e `ConfigurationError`;
- Testes de configuração, precedência, isolamento, segurança e imutabilidade;
- ADR sobre configuração validada por aplicação.

## Alterado

- `init_app()` passa a validar configuração antes de registrar estado;
- Versão elevada para `0.2.0`;
- Validação de distribuição deixa de fixar a versão em múltiplos arquivos;
- README, API pública, arquitetura, exemplos, critérios e status atualizados.

## Segurança

- Client secret é omitido de representações e mensagens de erro;
- Redirects HTTP externos são rejeitados;
- Authority exige HTTPS e tenant coerente;
- Placeholders e tenants genéricos são rejeitados.

## Limites

- Nenhum cliente MSAL, storage, identidade, token, login, callback, rota ou chamada de rede foi implementado.
