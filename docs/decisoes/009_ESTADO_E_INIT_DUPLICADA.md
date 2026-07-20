# ADR-009: estado por aplicação e inicialização duplicada

## Contexto

A ETAPA 00 precisa suportar application factory, a mesma instância da extensão em várias aplicações e ausência de referência permanente à aplicação.

Também é necessário definir o que ocorre quando `init_app()` é chamado novamente.

## Decisão

- Armazenar todo estado específico em `app.extensions["ms_entra_auth"]`;
- Manter `MicrosoftEntraAuth` sem atributo `app` e sem estado mutável por aplicação;
- Criar um objeto de estado diferente para cada aplicação;
- Tratar a repetição com a mesma instância como operação idempotente;
- Rejeitar com `RuntimeError` outra instância ou valor incompatível que tente ocupar a mesma chave.

## Consequências

- Uma instância pode ser compartilhada entre factories sem compartilhar dados mutáveis;
- A inicialização repetida não apaga estado existente;
- Conflitos de registro não são ocultados;
- Mudança futura exige novo ADR e atualização da documentação relacionada.
