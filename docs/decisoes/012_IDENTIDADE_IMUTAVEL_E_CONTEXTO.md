# ADR-012: identidade imutável e contexto por requisição

## Contexto

A extensão precisa representar uma identidade externa validada sem confundi-la com usuário local, autorização ou credencial. Também precisa expor a identidade atual de forma compatível com Flask e sem estado global.

## Decisão

- Implementar `Identity` como dataclass congelada com slots;
- Exigir `object_id`, `tenant_id` e `home_account_id`;
- Usar `(tenant_id, object_id)` como identificador estável;
- Tratar display name e username apenas como apresentação;
- Copiar e congelar claims recursivamente;
- Rejeitar credenciais dentro das claims;
- Não incluir claims ou PII em `repr`;
- Expor `current_identity` como `LocalProxy` request-local;
- Falhar explicitamente fora de contexto, sem extensão ou sem autenticação;
- Manter a vinculação da identidade como seam interna até o fluxo web.

## Consequências

- A aplicação continua responsável por usuário local e autorização;
- Não existe singleton de usuário;
- Identidade não pode ser usada para transportar token;
- A ETAPA 05 deverá restaurar/vincular identidade em cada requisição autenticada;
- Mudança futura exige atualização de API, testes e documentação.
