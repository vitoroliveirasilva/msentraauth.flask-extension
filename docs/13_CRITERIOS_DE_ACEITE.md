# Critérios de aceite

## Fundação

- Instala com `pip install -e .`;
- Import funciona;
- Duas apps inicializam a mesma instância;
- Nenhum `self.app`.

## Login

- Fluxo persistido;
- State inválido, fluxo ausente e replay rejeitados;
- Cancelamento previsível;
- Next externa rejeitada.

## Identidade

- Tenant validado;
- ID estável;
- E-mail não é chave;
- Imutável;
- Sem token.

## Token

- Cache MSAL;
- Silent primeiro;
- Refresh salva cache;
- Ausência exige interação;
- Zero token em logs.

## Storage

- Contrato e TTL testados;
- Delete testado;
- Falha tipada;
- Namespace sem colisão.

## Flask

- Factory;
- Blueprint opcional;
- Config prefixada;
- Contexto;
- Múltiplas apps.

## Release

CI pass, tipagem, lint, auditoria, docs e changelog.
