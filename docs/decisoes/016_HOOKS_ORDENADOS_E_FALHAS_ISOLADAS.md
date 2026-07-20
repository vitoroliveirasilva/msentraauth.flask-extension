# ADR-016: hooks ordenados e falhas isoladas

## Contexto

A aplicação precisa vincular identidades externas ao seu domínio e observar autenticação sem acoplar o núcleo a banco, ORM ou biblioteca de telemetria.

## Decisão

Oferecer hooks ordenados na instância da extensão:

- `on_authenticated` antes da sessão local;
- `on_logout` depois da limpeza;
- `on_error` e `on_event` em modo best effort.

`AuthenticationRejected` preserva decisão local. Falhas inesperadas de vínculo viram `LocalBindingError`. Falhas de observadores não mascaram o fluxo original.

## Consequências

- Vínculo local é explícito e testável;
- Autorização permanece fora do núcleo;
- Hooks são compartilhados por aplicações que reutilizam a mesma instância;
- Não há rollback automático de efeitos externos;
- I/O lento em hook afeta a requisição e deve ser controlado pela aplicação.
