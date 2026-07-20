# Changelog

## Segurança

- Backends distribuídos podem garantir consumo único sem janela entre `load()` e `delete()`;
- `MS_ENTRA_REQUIRE_ATOMIC_STORAGE=True` impede inicialização com backend sem garantia nativa;
- `MS_ENTRA_STRICT_SECURITY=True` bloqueia achados de severidade `error`;
- Auditoria verifica segredo de sessão, flags de cookie, storage em memória e consumo atômico;
- Eventos e logs não incluem tokens, auth code, claims, client secret, chave de storage ou payload bruto;
- Falhas de hooks de erro e evento nunca substituem o comportamento original;
- Rejeição pelo sistema local ocorre antes da persistência da identidade no navegador.

## Limites

- `MemoryStorage` continua inadequado para produção e não compartilha estado entre processos;
- A política do token cache continua last-write-wins, sem CAS distribuído;
- Hooks não implementam autorização, transação de banco ou rollback automático;
- Redis oficial, template consumidor, Graph e publicação permanecem fora desta versão.
