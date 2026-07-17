# ADR-013: cliente MSAL lazy e cache serializado por conta

## Contexto

Criar cliente MSAL no startup pode provocar descoberta de authority e acoplar `init_app()` à rede. Web apps também precisam persistir token cache por usuário sem manipular refresh tokens diretamente.

## Decisão

- Registrar serviço MSAL em `app.extensions`, mas construir `ConfidentialClientApplication` somente durante operação;
- Permitir fábrica injetável para testes sem rede;
- Desligar PII logging no cliente padrão;
- Usar somente `SerializableTokenCache` para serialização;
- Persistir um cache por `home_account_id` dentro do namespace da aplicação;
- Derivar chave por SHA-256 para não expor o identificador;
- Salvar apenas quando `has_state_changed` for verdadeiro;
- Aplicar TTL configurável, com padrão de oito horas;
- Selecionar conta por correspondência exata de `home_account_id`;
- Usar aquisição silenciosa com erro detalhado para classificação segura;
- Retornar access token somente ao código servidor;
- Nunca ler ou alterar refresh tokens diretamente.

## Consequências

- `init_app()` permanece determinístico e sem rede;
- O cache pode suportar backend compartilhado e múltiplos workers quando o backend for adequado;
- Sem conta ou token silencioso, o fluxo futuro deverá iniciar interação;
- TTL poderá ser revisado quando a política de sessão for definida;
- Concorrência distribuída e CAS permanecem para hardening;
- Mudança futura exige novo ADR quando alterar isolamento, serialização ou política de escrita.
