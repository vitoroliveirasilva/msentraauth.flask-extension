# ADR-019: publicação com artefato único e Trusted Publishing

## Decisão

Construir uma única vez, validar o conteúdo e publicar por OIDC usando environments separados para TestPyPI e PyPI.

## Consequência

- Tokens estáticos não são armazenados no GitHub;
- TestPyPI é acionado manualmente;
- PyPI exige GitHub Release e tag igual à versão;
- Os mesmos artefatos atravessam validação e publicação;
- Publicação externa continua sendo uma ação explícita do mantenedor.
