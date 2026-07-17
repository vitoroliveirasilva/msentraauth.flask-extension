# Política de segurança

Não abra issue pública para vulnerabilidades. Nesse caso, use reporte privado do GitHub quando disponível ou canal privado do mantenedor.

- Inclua versão ou commit, cenário, impacto, passos, evidências sanitizadas e sugestão de correção;
- Nunca envie client secret, access token, refresh token, cookie, cache ou dados pessoais reais;
- O escopo prioritário inclui configuração, redirect URI, authority, state/nonce, callback, open redirect, cache, vazamento de token, isolamento entre apps, storage e supply chain;
- Mensagens de erro e representações não devem incluir valores sensíveis;
- Redirect HTTP é permitido somente para desenvolvimento em loopback;
- A CI executa Bandit e pip-audit, mas essas ferramentas não substituem revisão manual;
- Dependências diretas usam faixas compatíveis e dependências transitivas não são fixadas sem necessidade.

A Licença [MIT](LICENSE) não representa garantia de segurança.