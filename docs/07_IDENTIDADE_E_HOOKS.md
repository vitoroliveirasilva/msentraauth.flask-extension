# Identidade e hooks

A identidade representa claims validadas. Assim, ela não é automaticamente o usuário de negócio da aplicação.

## Campos mínimos

|             Campo | Regra                                    |
| ----------------: | :--------------------------------------- |
|       `object_id` | Identificador do objeto                  |
|       `tenant_id` | Tenant emissor                           |
|         `subject` | Subject OIDC quando disponível           |
| `home_account_id` | Conta no cache                           |
|    `display_name` | Apresentação                             |
|        `username` | Apresentação, nunca chave de autorização |
|          `claims` | Somente leitura                          |

Email não deve ser identificador estável. Logo, para multi-tenant é preciso combinar tenant e object ID.

## Imutabilidade

A identidade não muda durante a requisição e não contém access token.

## `current_identity`

Deve ser compatível com contexto Flask. Fora de contexto, falha explicitamente ou representa anônimo conforme contrato final.

## Hook principal

```python
@entra_auth.on_authenticated
def sincronizar(identity):
    ...
```

Usos: localizar usuário local, criar registro, atualizar apresentação, registrar login ou recusar acesso.

## Fronteira

A extensão autentica, a aplicação autoriza e roles, groups e permissões não entram no núcleo inicial.

## Erros

Falha no vínculo local deve ser distinguida de falha do Entra e de indisponibilidade de banco.
