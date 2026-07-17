# Versionamento e releases

## Esquema

O projeto usa Semantic Versioning. Durante a série `0.x`, a API permanece em desenvolvimento.

## Versão atual

- Versão de desenvolvimento: `0.2.0`;
- Etapas concluídas: fundação e configuração;
- Estado: não publicada no PyPI;
- Fonte única: `src/flask_ms_entra_auth/_version.py`;
- Metadata de build: lido dinamicamente pelo Hatchling.

A adição de configuração validada elevou a versão minor da série experimental. Correções compatíveis dentro da mesma etapa usam patch.

## Dependências diretas

- `Flask>=3.1,<3.2`;
- `msal>=1.37,<2`.

Dependências transitivas não são fixadas sem necessidade técnica comprovada.

## Artefatos

- Source distribution;
- Wheel universal Python;
- Metadata completa;
- `py.typed`;
- Changelog e documentação.

## Validação atual

1. Instalação editável em ambiente limpo;
2. Lint e formatação;
3. Tipagem estrita;
4. Testes e cobertura;
5. Bandit e pip-audit;
6. Build isolado;
7. `twine check`;
8. inspeção automatizada dos conteúdos do wheel e do sdist;
9. instalação do wheel e smoke test em ambiente limpo na CI.

Os testes e o smoke test comparam o metadata instalado com `__version__`, evitando repetir a versão em arquivos de validação.

## Processo futuro de publicação

TestPyPI, tags, GitHub Releases e PyPI permanecem fora do escopo atual.

## Branches

- `dev`: evolução;
- `prod`: estado estável.
