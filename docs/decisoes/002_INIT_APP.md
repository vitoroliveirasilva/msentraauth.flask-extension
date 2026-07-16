# ADR-002: padrão `init_app`

## Decisão

Usar classe inicializável sem aplicação e método `init_app`.

## Consequência

- Suportar factory e múltiplas apps além de não armazenar `self.app`;
- Mudança futura exige novo ADR e atualização da documentação relacionada.
