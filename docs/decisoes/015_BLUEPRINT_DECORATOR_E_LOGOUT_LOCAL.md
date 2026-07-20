# ADR-015: blueprint opcional, decorator e logout local

## Decisão

Fornecer blueprint padrão configurável, métodos públicos para rotas customizadas, `login_required` com políticas redirect/raise e logout local exclusivamente por `POST`.

## Motivos

- Aplicações simples recebem integração pronta;
- Aplicações avançadas mantêm controle de rotas e tratamento de erro;
- APIs podem falhar explicitamente sem redirecionamento HTML;
- Métodos de alteração de estado não são convertidos em navegação;
- Logout remove somente o estado local da sessão atual.

## Consequências

- A aplicação continua responsável pela política CSRF geral;
- Logout local não encerra todas as sessões Microsoft;
- Hooks públicos permanecem separados para a ETAPA 07.
