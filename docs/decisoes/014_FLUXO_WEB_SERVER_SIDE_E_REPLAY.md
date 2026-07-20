# ADR-014: fluxo web server-side e consumo único

## Decisão

Persistir o dicionário de Authorization Code Flow produzido pelo MSAL no `AuthStorage`, guardar no cookie somente uma referência aleatória e apagar o fluxo antes da redenção do código.

## Motivos

- Auth code, state, nonce e metadados não ficam no cookie;
- O fluxo completo permanece disponível para validação do MSAL;
- Consume-first impede replay e reduz corrida entre callbacks;
- TTL limita transações abandonadas.

## Consequências

- O storage precisa ser compartilhado entre workers em produção;
- Falha após consumo exige novo login, em vez de reutilizar callback;
- Concorrência distribuída mais sofisticada poderá exigir CAS em etapa futura.
