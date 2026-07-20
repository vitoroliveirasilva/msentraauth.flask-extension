# Identidade e hooks

## Identidade

`Identity` representa claims validadas, é profundamente imutável e não contém credenciais. `tenant_id` e `object_id` formam a chave estável. Email e username são apenas apresentação.

## `current_identity`

É request-local e fica disponível depois da restauração server-side ou da conclusão do callback. Sem autenticação, gera `AuthenticationRequired`.

## `on_authenticated`

Executado depois da validação do provedor e antes da persistência da sessão local.

- Pode vincular a identidade a um cadastro interno;
- Pode rejeitar explicitamente com `AuthenticationRejected`;
- Falhas inesperadas viram `LocalBindingError`;
- Rejeição remove o token cache criado durante o callback;
- O hook não deve implementar autorização por roles ou groups.

## `on_logout`

Executado depois da remoção de fluxo, identidade e token cache locais. Falha gera `HookExecutionError`, mas não recria a sessão removida.

## `on_error`

Recebe exceções previsíveis uma única vez. É best effort: falhas do observador são contabilizadas e não substituem o erro original.

## `on_event`

Recebe `AuthEvent` imutável e sanitizado. Falhas não interrompem o fluxo principal.

## Escopo e ordem

Hooks pertencem à instância da extensão, são thread-safe, ordenados e idempotentes por callable. Ao reutilizar uma instância em múltiplas aplicações, o registro é compartilhado.

## Fronteira de autorização

A extensão autentica. A aplicação decide roles, groups, permissões, status do usuário e acesso a recursos.
