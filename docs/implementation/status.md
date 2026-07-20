# Status de implementação

## Etapa atual

ETAPAS 05 e 06 concluídas em conjunto: fluxo web, rotas e decorator.

## Decisões tomadas

### Fluxo web

- Authorization Code Flow é iniciado e concluído exclusivamente pelos métodos do MSAL;
- State explícito usa aleatoriedade criptográfica e comparação em tempo constante;
- O dicionário completo do fluxo é persistido server-side com TTL;
- Cookie Flask guarda somente `flow_id` e `session_id` aleatórios;
- Fluxo é removido antes da redenção do código, aplicando consume-first contra replay;
- Callback rejeita campos duplicados, estruturas excessivas e state inconsistente;
- `access_denied` é cancelamento previsível;
- Claims, tenant e conta MSAL são validados antes de criar identidade;
- Identidade server-side é restaurada automaticamente em `before_request`;
- Referência interna é rotacionada após autenticação.

### Navegação

- `next` local deve ser absoluto dentro da aplicação e não pode usar `//`, barra invertida, controles ou fragmento;
- URL externa exige host e porta exatos em allowlist;
- HTTP externo é rejeitado, exceto loopback para desenvolvimento;
- Destinos configurados passam pela mesma validação.

### Rotas e decorator

- Blueprint padrão oferece `GET /login`, `GET /callback` e `POST /logout` sob `/auth`;
- Registro automático, prefixo e tratamento de erros são configuráveis;
- Aplicações podem registrar o blueprint manualmente ou usar métodos públicos em rotas próprias;
- `login_required` suporta uso direto e parametrizado;
- Usuário anônimo pode ser redirecionado apenas em `GET` e `HEAD`;
- Métodos que alteram estado geram `AuthenticationRequired`;
- Respostas internas de erro são curtas e sanitizadas.

### Logout

- Limpa somente o fluxo pendente, identidade, referência e token cache da sessão atual;
- Preserva outras chaves da sessão Flask;
- Não promete encerrar todas as sessões Microsoft;
- A rota padrão exige `POST`.

## Comandos

```bash
python -m pip install -e ".[dev]"
ruff format .
ruff check .
ruff format --check .
mypy src tests
pytest
bandit -c pyproject.toml -r src
pip-audit . --dry-run
pip-audit .
python -m build
python -m twine check dist/*
DIST_DIR=dist pytest tests/test_distribution.py --no-cov
```

## Riscos e limites

- `MemoryStorage` perde dados ao reiniciar e não compartilha estado entre workers;
- Produção exige backend compartilhado e política de disponibilidade;
- Consume-first prioriza proteção contra replay: falha depois do consumo exige novo login;
- A aplicação continua responsável por HTTPS, `SECRET_KEY`, flags de cookie, CSRF, proxy, rate limit e autorização;
- Logout local não encerra todas as sessões Microsoft;

## Declaração de escopo

Nenhum hook público, vínculo automático com usuário local, regra de autorização, concorrência distribuída com CAS, Redis oficial, Microsoft Graph, template, frontend, Docker, deploy, TestPyPI ou publicação foi iniciado. A ETAPA 07 permanece intacta.
