# ADR-018: template consumidor como prova de integração

## Decisão

Validar a API estável da extensão em uma aplicação Flask separada que usa Redis, Graph, interface, health checks e Docker.

## Consequência

- A extensão permanece sem dependências de infraestrutura ou apresentação;
- Fricções de consumo são descobertas antes da publicação;
- O template fixa a série compatível `flask-ms-entra-auth>=1.0,<2`;
- Testes cruzados instalam o wheel candidato, não apenas o checkout editável.
