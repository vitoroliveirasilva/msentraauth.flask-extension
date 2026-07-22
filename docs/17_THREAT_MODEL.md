# Threat model

## Escopo

Aplicação web Flask confidencial, single-tenant, usando Authorization Code Flow, sessão assinada com referências e storage server-side substituível.

## Ativos

- Client secret;
- Auth code;
- Access e refresh tokens;
- Token cache serializado;
- Identidade e claims;
- Referências de fluxo e sessão;
- Configuração de tenant, authority e redirect;
- Eventos operacionais.

## Fronteiras de confiança

1. Navegador e cookie Flask;
2. Aplicação Flask;
3. Backend de storage;
4. Microsoft Entra ID e MSAL;
5. Hooks e banco de domínio da aplicação;
6. Pipeline, wheel e sdist.

## Ameaças e controles

### Replay e corrida de callback

- State imprevisível;
- Consumo antes da redenção;
- `AtomicAuthStorage.take()` para múltiplos workers;
- Fallback local documentado como não distribuído.

Risco residual: backend sem atomicidade pode permitir janela entre leitura e remoção em processos diferentes.

### Roubo ou exposição de credenciais

- Cookie contém referências, não tokens;
- Identidade rejeita chaves de credencial em qualquer nível de claims aninhadas;
- Cache é serializado pelo MSAL;
- Logging e eventos usam campos fechados;
- Mensagens públicas não copiam payloads.

Risco residual: causa de exceção externa pode conter dados sensíveis e não deve ser logada sem filtragem.

### Redirecionamento pós-login adulterado

- Destinos são validados antes de iniciar o fluxo;
- O destino persistido é validado novamente após ser carregado do storage;
- URLs absolutas exigem HTTPS e host explicitamente permitido;
- Fragmentos, credenciais embutidas e caminhos ambíguos são rejeitados.

Risco residual: a aplicação consumidora precisa manter a allowlist de hosts mínima e correta.

### Vínculo indevido com usuário local

- Tenant e object ID validados;
- Hook roda antes da sessão local;
- Aplicação pode rejeitar com erro explícito;
- Username e email não são chaves de autorização.

Risco residual: regras de domínio e transações pertencem à aplicação.

### Sessão fraca

- Auditoria de `SECRET_KEY`, HttpOnly, SameSite e Secure;
- Referência rotacionada após login;
- Logout remove somente a sessão atual;
- Referências internas inválidas são descartadas sem manter o navegador preso a estado corrompido;
- Modo estrito bloqueia erros de postura.

Risco residual: CSRF geral, proxy e headers permanecem responsabilidade do consumidor.

### Storage indisponível ou inconsistente

- Erros convertidos em `StorageError`;
- Causa preservada sem exposição pública;
- TTL e namespace;
- Capacidade atômica detectável;
- Payloads de fluxo e identidade possuem limite de tamanho antes de serialização ou decode;
- Identidades corrompidas removem a referência local para evitar falha persistente em toda requisição;
- Token cache last-write-wins explicitado.

Risco residual: não há CAS, reconciliação, retry ou circuit breaker no núcleo.

### Exaustão por estruturas adversariais

- Claims possuem profundidade máxima explícita;
- Valores numéricos não finitos são rejeitados;
- Payloads server-side têm tamanho máximo antes do decode;
- Tipos fora do subconjunto JSON suportado são recusados.

Risco residual: limites de requisição HTTP, rate limiting e proteção de infraestrutura pertencem à aplicação e ao proxy.

### Hooks hostis ou defeituosos

- Identidade imutável;
- Rejeição explícita separada de falha inesperada;
- Hooks de erro e evento não mascaram resultado;
- Logout limpa estado antes do hook;
- Ordem determinística e snapshot thread-safe.

Risco residual: hook pode executar I/O lento, bloquear worker ou alterar sistemas externos sem rollback.

## Não objetivos

- Autorização por groups ou roles;
- Bearer API, OBO, client credentials e B2C;
- Redis embutido;
- Rate limiting e WAF;
- Encerramento global de sessões Microsoft;
- Detecção de comprometimento de conta.

## Revisão

Este documento deve ser revisto quando houver alteração em cookie, storage, callback, hooks, eventos, cache, superfície pública ou modelo de deployment.
