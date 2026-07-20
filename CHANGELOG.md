# Changelog

## 1.0.0

### Segurança

- Publicação usa OIDC e não armazena API token no repositório;
- Tag de produção deve corresponder exatamente ao metadata do pacote;
- TestPyPI é manual e PyPI depende de GitHub Release protegida;
- Os mesmos artefatos imutáveis são validados e publicados.

### Limites

- Trusted Publishers e environments precisam ser configurados pelo mantenedor;
- A extensão continua sem Redis, Graph, UI ou autorização de negócio embutidos.
