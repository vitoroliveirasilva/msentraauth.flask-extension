# Política de segurança

Não abra issue pública para vulnerabilidades. Nesse caso, use reporte privado do GitHub quando disponível ou canal privado do mantenedor.

- Inclua versão ou commit, cenário, impacto, passos, evidências sanitizadas e sugestão de correção;
- Nunca envie client secret, access token, refresh token, cookie, cache, chave de storage, identificador de sessão ou claims reais;
- O escopo prioritário inclui configuração, redirect URI, authority, namespace, TTL, identidade, contexto Flask, seleção de conta, serialização do cache, aquisição silenciosa, state/nonce, callback, open redirect e supply chain;
- `Identity` não deve conter credenciais e username/email não devem ser usados como chave de autorização;
- PII logging do MSAL deve permanecer desligado por padrão;
- Refresh tokens são responsabilidade exclusiva do MSAL e não devem ser manipulados pela aplicação;
- Chaves de cache devem evitar identificadores de conta em texto claro;
- Mensagens públicas não devem incluir token, cache, claims completas, client secret, resposta bruta do provedor ou erro de backend;
- `MemoryStorage` não deve ser usado em produção;
- Backends externos devem usar TLS quando aplicável, menor privilégio, expiração adequada e proteção em repouso;
- A CI executa Bandit e pip-audit, mas essas ferramentas não substituem revisão manual.

A Licença [MIT](LICENSE) não representa garantia de segurança.