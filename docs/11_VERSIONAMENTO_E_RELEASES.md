# Versionamento e releases

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

## Validação da ETAPA 00

1. Instalação editável em ambiente limpo;
2. Lint e formatação;
3. Tipagem estrita;
4. Testes e cobertura;
5. Bandit e pip-audit;
6. Build isolado;
7. `twine check`;
8. Inspeção automatizada dos conteúdos do wheel e do sdist;
9. Instalação do wheel em ambiente limpo na CI.

## Processo futuro de publicação

TestPyPI, tags, GitHub Releases e PyPI permanecem fora da ETAPA 00.

## Branches

- `dev`: evolução;
- `prod`: estado estável.
