# Testes e compatibilidade

## Compatibilidade

- Python mínimo: 3.11;
- Matriz de CI: Python 3.11, 3.12, 3.13 e 3.14;
- Flask: série `3.1.x`;
- MSAL: série `1.x`, mínimo `1.37`.

## Casos implementados

### Fundação, configuração e storage

Permanecem cobertos os contratos das ETAPAS 00, 01 e 02: empacotamento, application factory, múltiplas apps, configuração imutável, namespace, TTL, concorrência local, falhas e artefatos.

### Identidade

- Construção por claims;
- Campos obrigatórios e opcionais;
- Tenant esperado;
- Fallback de username;
- `stable_id`;
- Imutabilidade rasa e profunda;
- Rejeição de credenciais;
- Claims JSON-compatible;
- Representação sanitizada;
- Isolamento entre requisições e apps;
- Falhas explícitas de `current_identity`.

### MSAL e token cache

- Cliente padrão lazy e PII logging desligado;
- Fábrica injetável e ausência de rede nos testes;
- Chave de cache por hash de conta;
- Cache ausente, válido, corrompido e não UTF-8;
- Persistência somente quando alterado;
- TTL aplicado;
- Conta correspondente e ausente;
- Scopes padrão e dinâmicos;
- Force refresh;
- Sucesso, interação necessária, erro do provedor e resultado inválido;
- Sanitização de metadata;
- Exceções inesperadas encapsuladas;
- Cache persistido após alteração mesmo quando interação é necessária;
- Integração request-local de `acquire_token()`.

## Artefatos

Após `python -m build`, a suíte valida wheel e sdist, metadata, `py.typed`, módulos de identidade, contexto, auth, storage e testes correspondentes.

## Ferramentas

pytest, pytest-cov, Ruff, mypy estrito, Bandit, pip-audit, build e twine check.

## Limitações de validação local

O ambiente de entrega executa uma versão local do Python. As demais versões são validadas pela matriz de CI após o usuário aplicar e enviar os arquivos.
