# Changelog

## Não lançado

### Segurança

- Claims de identidade rejeitam credenciais em qualquer nível de aninhamento;
- O destino pós-login é validado antes da persistência e novamente após a leitura do storage;
- Fluxos e identidades server-side possuem limite explícito de tamanho e rejeitam números JSON não finitos;
- Claims excessivamente aninhadas são recusadas antes de atingir recursão não controlada;
- Respostas das rotas de autenticação desabilitam cache e envio de referer;
- O cache MSAL possui limite explícito de payload antes da desserialização e persistência.

### Robustez

- Referências internas de fluxo ou sessão inválidas são descartadas com segurança;
- A referência no cookie é removida mesmo quando uma identidade persistida está corrompida;
- Uma referência antiga inválida não impede o estabelecimento de uma nova sessão autenticada;
- Relógios inválidos ou não finitos são rejeitados pelo storage em memória;
- Falhas ao serializar ou persistir uma nova identidade preservam a sessão autenticada anterior;
- Falhas secundárias de persistência do cache não ocultam o erro principal de autenticação.

## 1.0.0

### Segurança

- Publicação usa OIDC e não armazena API token no repositório;
- Tag de produção deve corresponder exatamente ao metadata do pacote;
- TestPyPI é manual e PyPI depende de GitHub Release protegida;
- Os mesmos artefatos imutáveis são validados e publicados.

### Limites

- Trusted Publishers e environments precisam ser configurados pelo mantenedor;
- A extensão continua sem Redis, Graph, UI ou autorização de negócio embutidos.
