# Changelog

## Não lançado

### Segurança

- Claims de identidade rejeitam credenciais em qualquer nível de aninhamento;
- O destino pós-login é validado antes da persistência e novamente após a leitura do storage;
- Fluxos e identidades server-side possuem limite explícito de tamanho e rejeitam números JSON não finitos;
- Claims excessivamente aninhadas são recusadas antes de atingir recursão não controlada;
- Respostas das rotas de autenticação desabilitam cache e envio de referer;
- O cache MSAL possui limite explícito de payload antes da desserialização e persistência;
- Campos estruturais da identidade devem coincidir com `oid` e `tid` quando essas claims estiverem presentes;
- Variações de nomes de claims sensíveis, como `refreshToken` ou `client-secret`, também são rejeitadas;
- A auditoria classifica `DEBUG=True` como erro de postura para cargas de autenticação;
- Redirecionamentos produzidos por `login_required` recebem os mesmos headers `no-store` e `no-referrer` das rotas de autenticação;
- IDs de requisição externos ficam restritos ao subconjunto ASCII seguro e destinos de navegação rejeitam o caractere de controle DEL;
- Releases de produção somente avançam quando a tag aponta para um commit pertencente à branch `prod`.

### Robustez

- Referências internas de fluxo ou sessão inválidas são descartadas com segurança;
- A referência no cookie é removida mesmo quando uma identidade persistida está corrompida;
- Uma referência antiga inválida não impede o estabelecimento de uma nova sessão autenticada;
- Relógios inválidos ou não finitos são rejeitados pelo storage em memória;
- Falhas ao serializar ou persistir uma nova identidade preservam a sessão autenticada anterior;
- Falhas secundárias de persistência do cache não ocultam o erro principal de autenticação;
- Falhas de relógio durante `take()` não removem valores válidos e TTLs que excedam o intervalo numérico falham de forma controlada;
- A rotação de sessão remove o novo payload quando a referência anterior não pode ser revogada;
- Identidades persistidas corrompidas são removidas do storage após a invalidação da referência local;
- Contas MSAL duplicadas e access tokens compostos apenas por espaços são recusados;
- Falhas ao remover um fluxo recém-criado não mascaram a falha original ao gravar sua referência na sessão;
- Logout limpa identidade e token cache antes de tentar remover um fluxo pendente potencialmente indisponível;
- Falhas ao atualizar metadados da sessão removem o novo payload, restauram a sessão anterior quando válida e mantêm a exceção principal;
- O gate de release valida identidade e metadata exatas tanto no wheel quanto no sdist, incluindo arquivos ambíguos ou corrompidos;
- A limpeza da identidade preserva fluxos pendentes e mantém a referência autenticada quando o storage falha antes da revogação;
- Falhas ao limpar metadados de uma identidade corrompida não ocultam o erro original;
- Falhas do backend de sessão são convertidas em `StorageError` antes de alcançar as rotas públicas;
- Leitura de artefatos de release trata formatos de compactação não suportados como falhas sanitizadas;
- Recursão excessiva durante serialização ou leitura de identidade e token cache é convertida em `StorageError`.

## 1.0.0

### Segurança

- Publicação usa OIDC e não armazena API token no repositório;
- Tag de produção deve corresponder exatamente ao metadata do pacote;
- TestPyPI é manual e PyPI depende de GitHub Release protegida;
- Os mesmos artefatos imutáveis são validados e publicados.

### Limites

- Trusted Publishers e environments precisam ser configurados pelo mantenedor;
- A extensão continua sem Redis, Graph, UI ou autorização de negócio embutidos.
