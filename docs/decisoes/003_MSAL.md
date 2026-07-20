# ADR-003: MSAL como motor

## Decisão

Delegar fluxo e cache ao MSAL.

## Consequência

- Não reimplementar OAuth, OIDC ou refresh token;
- Mudança futura exige novo ADR e atualização da documentação relacionada.
