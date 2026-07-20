# Arquitetura

## Estado atual: ETAPAS 07 e 08

```text
Aplicação Flask
      |
      v
MicrosoftEntraAuth.init_app(app)
      |
      +-- Configuração validada e imutável
      +-- Storage namespaced
      +-- Auditoria de postura
      +-- Serviços MSAL e fluxo lazy
      +-- Observabilidade por aplicação
      +-- Blueprint opcional
      |
      v
app.extensions["ms_entra_auth"]
```

## Fronteiras

- `config.py`: resolução e validação;
- `storage/`: contrato mínimo, consumo atômico opcional, namespace e TTL;
- `identity.py` e `context.py`: identidade imutável e request-local;
- `auth/`: cliente MSAL, token cache e Authorization Code Flow;
- `web/`: sessão, navegação, blueprint e respostas;
- `hooks.py`: callbacks ordenados e thread-safe;
- `observability.py`: eventos e logging sanitizados;
- `security.py`: auditoria somente leitura;
- `extension.py`: composição e API pública.

## Hooks

A instância `MicrosoftEntraAuth` mantém um registro ordenado de hooks. A mesma instância pode inicializar múltiplas aplicações, portanto os hooks são compartilhados entre essas aplicações. Estado de usuário não é armazenado no registro.

O vínculo local ocorre antes de estabelecer a sessão. Logout ocorre antes de executar seu hook. Hooks de erro e evento são best effort e não mudam o resultado principal.

## Concorrência

`MemoryStorage` usa lock local. `AtomicAuthStorage.take()` representa consumo único nativo no backend. O adaptador namespaced oferece fallback local para compatibilidade, mas não promete atomicidade entre processos.

Fluxo e identidade usam `take()` quando disponível. Token cache permanece last-write-wins. CAS, versionamento ou locks distribuídos continuam fora do contrato.

## Observabilidade

Cada aplicação possui `Observability` próprio e usa o registro de hooks da extensão. Request ID é request-local. Os eventos não contêm objetos de identidade nem payloads do provedor.

## Segurança

`audit_security()` inspeciona configuração Flask e capacidades do backend, sem alterar a aplicação. O modo estrito bloqueia somente achados de severidade `error`.
