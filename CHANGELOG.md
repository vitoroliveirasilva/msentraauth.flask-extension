# Changelog

## Segurança

- O cookie Flask contém somente referências aleatórias, nunca identidade, auth code ou token;
- Fluxos são removidos antes da troca do código, impedindo replay do mesmo callback;
- Callback rejeita campos duplicados, state inconsistente e estruturas excessivas;
- Destinos de navegação são validados contra open redirect;
- Logout usa `POST` e remove somente o estado da sessão atual;
- Erros das rotas são sanitizados e não copiam detalhes internos.

## Limites

- Hooks públicos, vínculo automático com usuário local e hardening distribuído permanecem fora desta versão;
- `MemoryStorage` continua inadequado para produção;
- Logout local não encerra todas as sessões Microsoft.
