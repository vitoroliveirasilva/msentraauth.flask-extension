# Identidade e hooks

## Identidade implementada

`Identity` representa claims validadas e não é automaticamente o usuário de negócio da aplicação.

Campos principais: `object_id`, `tenant_id`, `subject`, `home_account_id`, `display_name`, `username` e `claims` somente leitura.

A identidade é persistida no servidor após callback válido e restaurada automaticamente no início das requisições. Ela não contém access token, refresh token ou cache.

## `current_identity`

É request-local e fica disponível após restauração da sessão ou conclusão do callback. Sem autenticação, gera `AuthenticationRequired`.

## Fronteira de autorização

A extensão autentica. Roles, groups, permissões, vínculo com cadastro interno e regras de acesso pertencem à aplicação.

## Hooks futuros

A ETAPA 07 ainda poderá oferecer callbacks como `on_authenticated`, `on_logout` e `on_error`. Nenhum hook público foi iniciado nesta entrega.
