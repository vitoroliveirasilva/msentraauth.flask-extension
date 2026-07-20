# Política de segurança

- Não abra issue pública para vulnerabilidades. Nesse caso, use reporte privado do GitHub quando disponível ou canal privado do mantenedor;
- Inclua versão ou commit, cenário, impacto, passos, evidências sanitizadas e sugestão de correção;
- Nunca envie client secret, access token, refresh token, auth code, cookie, cache, claims completas, chave de storage, identificador de sessão ou dados pessoais reais.

## Escopo prioritário

- State, callback, replay e open redirect;
- Isolamento entre aplicações, sessões e contas;
- Atomicidade de consumo em múltiplos workers;
- Token cache e falhas de storage;
- Hooks de vínculo e rejeição local;
- Vazamento em logs, eventos e mensagens públicas;
- Flags de cookie, secret de sessão e configuração insegura;
- Dependências, build e artefatos publicados.

## Garantias da biblioteca

- Tokens e auth code permanecem server-side;
- `Identity` não contém credenciais;
- Eventos são sanitizados;
- PII logging do MSAL permanece desativado;
- Erros previsíveis possuem mensagens públicas controladas;
- Fluxos e identidades usam consumo atômico quando o backend oferece `AtomicAuthStorage`;
- A auditoria não lê nem imprime valores de secrets.

## Responsabilidade da aplicação

Produção exige HTTPS, secret forte, cookies seguros, CSRF, proxy confiável, rate limiting, storage compartilhado, menor privilégio, proteção em repouso, disponibilidade e autorização de domínio.

`MemoryStorage` não deve ser usado em produção. Em múltiplos workers, configure backend atômico e `MS_ENTRA_REQUIRE_ATOMIC_STORAGE=True`.

Consulte [`docs/17_THREAT_MODEL.md`](docs/17_THREAT_MODEL.md).
