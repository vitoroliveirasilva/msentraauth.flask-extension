# Política de segurança

Não abra issue pública para vulnerabilidades. Nesse caso, use reporte privado do GitHub quando disponível ou canal privado do mantenedor.

- Inclua versão ou commit, cenário, impacto, passos, evidências sanitizadas e sugestão de correção;
- Nunca envie client secret, auth code, access token, refresh token, cookie, cache, chave de storage, identificador de sessão ou claims reais;
- O escopo prioritário inclui configuração, authority, redirect URI, state, nonce, callback, replay, open redirect, cookie, sessão, namespace, TTL, identidade, seleção de conta e supply chain;
- O cookie da extensão deve conter somente referências aleatórias;
- Fluxos devem ser consumidos uma única vez e expirar;
- Destinos externos exigem allowlist exata;
- Logout padrão usa `POST` e não promete logout global Microsoft;
- `Identity` não contém credenciais e username/email não são chave de autorização;
- PII logging do MSAL permanece desligado;
- Refresh tokens são responsabilidade exclusiva do MSAL;
- Mensagens públicas não incluem token, auth code, cache, claims completas, client secret, resposta bruta do provedor ou erro de backend;
- `MemoryStorage` não deve ser usado em produção;
- Backends externos devem usar TLS quando aplicável, menor privilégio, expiração e proteção em repouso;
- A aplicação é responsável por `SECRET_KEY`, HTTPS, flags de cookie, CSRF, proxy, rate limit e autorização;
- Bandit e pip-audit não substituem revisão manual.

A Licença [MIT](LICENSE) não representa garantia de segurança.