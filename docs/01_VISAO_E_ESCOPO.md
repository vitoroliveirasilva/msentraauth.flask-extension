# Visão e escopo

## Problema

Aplicações Flask com Microsoft Entra ID repetem criação do cliente MSAL, autorização, callback, validação de estado, cache, renovação, sessão, identidade e logout. Quando isso fica espalhado por rotas e utilitários, segurança e manutenção degradam.

## Proposta

Fornecer uma extensão pequena e transparente para aplicações web confidenciais Flask.

## Público-alvo

- Desenvolvedores Flask com autenticação Microsoft Entra ID;
- Equipes com múltiplas aplicações Flask;
- Aplicações internas e produtos web com APIs delegadas;
- Sistemas que mantêm domínio de usuário próprio.

## Casos prioritários

1. Aplicação web single-tenant.
2. Application factory.
3. Sessão server-side.
4. Token delegado para APIs downstream.
5. Vínculo opcional com usuário local.

## Fora do escopo inicial

- Bearer authentication para APIs;
- On-Behalf-Of;
- Client credentials;
- Device code;
- Múltiplos provedores;
- External ID/B2C;
- Managed identities;
- Grupos e app roles;
- Graph genérica;
- Persistência SQLAlchemy;
- Interface visual.

## Métricas

- Nenhuma credencial em logs;
- Testes de sucesso e falha;
- Múltiplas aplicações no mesmo processo;
- Nenhum estado global por usuário;
- Documentação coerente com o pacote;
- Instalação editável em clone limpo.