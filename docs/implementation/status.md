# Status de implementação

## Etapa atual

ETAPAS 03 e 04 concluídas em conjunto: identidade e núcleo MSAL.

## Decisões tomadas

### Identidade

- `Identity` é dataclass pública, congelada, com slots e `repr` sanitizado;
- `oid`, `tid` e `home_account_id` são obrigatórios;
- `stable_id` é `(tenant_id, object_id)`;
- Username e display name são somente apresentação;
- Claims são copiadas e congeladas recursivamente;
- Somente valores compatíveis com JSON são aceitos;
- Claims de access token, refresh token, ID token bruto, client secret e token cache são rejeitadas;
- `current_identity` usa `LocalProxy` e contexto Flask por requisição;
- Ausência de contexto, extensão ou autenticação falha explicitamente;
- Vinculação da identidade permanece seam interna até o callback futuro.

### MSAL

- `MsalService` é registrado por aplicação, mas não mantém estado de usuário;
- `ConfidentialClientApplication` é criado somente durante operação MSAL;
- `init_app()` continua sem rede e sem inicialização de cliente;
- Fábrica de cliente é injetável para testes determinísticos sem rede;
- Cliente padrão usa `enable_pii_log=False`;
- Token cache usa exclusivamente `SerializableTokenCache`;
- Um cache é persistido por `home_account_id` dentro do namespace da aplicação;
- A chave de cache usa SHA-256 e não expõe o identificador em texto claro;
- Cache é salvo somente quando `has_state_changed` é verdadeiro;
- TTL padrão é 28.800 segundos e pode ser configurado por `MS_ENTRA_TOKEN_CACHE_TTL`;
- Conta é selecionada por correspondência exata de `home_account_id`;
- Aquisição usa `acquire_token_silent_with_error` para classificar falhas com segurança;
- Access token é retornado somente ao código servidor;
- Refresh tokens não são lidos ou manipulados diretamente.

### Erros

- Adicionados `AuthenticationError`, `AuthenticationRequired`, `IdentityValidationError`, `ConsentRequired`, `TokenAcquisitionError` e `ProviderUnavailableError`;
- `TokenAcquisitionError` expõe somente código e correlation ID sanitizados;
- `error_description`, resposta bruta, token e cache não entram na mensagem pública;
- Causas técnicas ficam em `__cause__` para diagnóstico controlado.

## Comandos

```bash
python -m venv .venv
.venv/bin/python -m pip install -e ".[dev]"

.venv/bin/ruff format src tests
.venv/bin/ruff check .
.venv/bin/ruff format --check .
.venv/bin/mypy src tests
.venv/bin/pytest
.venv/bin/bandit -c pyproject.toml -r src
.venv/bin/pip-audit . --dry-run
.venv/bin/pip-audit .

rm -rf dist build .package-venv
.venv/bin/python -m build
.venv/bin/python -m twine check dist/*
DIST_DIR=dist .venv/bin/pytest tests/test_distribution.py --no-cov

python -m venv .package-venv
.package-venv/bin/python -m pip install dist/*.whl
```

## Divergências resolvidas

- A documentação anterior marcava identidade, cliente MSAL, cache e aquisição silenciosa como não iniciados. Mas agora distingue os recursos implementados do fluxo web ainda ausente;
- A configuração não possuía TTL para cache real; foi adicionado `MS_ENTRA_TOKEN_CACHE_TTL`;
- A hierarquia de erros documentada era apenas planejada; os erros necessários às ETAPAS 03 e 04 foram implementados;
- O storage existia sem receber cache real; agora persiste apenas serialização produzida pelo MSAL;
- Os exemplos antigos não podiam demonstrar identidade nem token silencioso; foram atualizados com avisos de que o callback ainda não existe.

## Riscos e limitações

- A política de concorrência continua last-write-wins, sem CAS ou detecção de conflito;
- A identidade é request-local, mas ainda não é restaurada automaticamente entre requisições;
- `acquire_token()` depende de uma identidade vinculada, que somente o fluxo futuro fornecerá automaticamente;
- Criar o cliente ou renovar token pode acessar rede durante `acquire_token()`, nunca durante `init_app()`;
- Causas originais de exceções podem conter dados sensíveis e não devem ser registradas sem sanitização.

## Declaração de escopo

As ETAPAS 03 e 04 foram implementadas. A ETAPA 05 não foi iniciada. Não foram criados login, callback, Authorization Code Flow, state, nonce, replay protection, rotas, blueprint, logout, decorators, hooks, Redis, Flask-Login, Microsoft Graph, templates, frontend, Docker, deploy ou publicação no PyPI.
