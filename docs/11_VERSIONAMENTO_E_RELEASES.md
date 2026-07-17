# Versionamento e releases

## Esquema

O projeto usa Semantic Versioning. Durante a série `0.x`, a API permanece experimental.

## Versão atual

- Versão de desenvolvimento: `0.3.0`;
- Etapas concluídas: fundação, configuração e storage;
- Estado: não publicada no PyPI;
- Fonte única: `src/flask_ms_entra_auth/_version.py`;
- Metadata de build: lido dinamicamente pelo Hatchling.

A adição do contrato público de storage, `MemoryStorage` e `StorageError` elevou a versão minor da série experimental.

## Dependências diretas

- `Flask>=3.1,<3.2`;
- `msal>=1.37,<2`.

Nenhuma dependência obrigatória foi adicionada para storage.

## Artefatos

Source distribution, wheel universal, metadata completa, `py.typed`, changelog e documentação.

## Validação atual

1. Instalação editável;
2. Lint e formatação;
3. Tipagem estrita;
4. Testes e cobertura;
5. Bandit e pip-audit;
6. Build isolado;
7. `twine check`;
8. Inspeção de wheel e sdist;
9. Instalação do wheel e smoke test com configuração e storage.

## Processo futuro de publicação

TestPyPI, tags, GitHub Releases e PyPI permanecem fora do escopo atual.

## Branches

- `dev`: evolução;
- `prod`: estado estável.
