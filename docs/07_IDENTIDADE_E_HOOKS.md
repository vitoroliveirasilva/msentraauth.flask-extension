# Identidade e hooks

## `Identity`

A identidade representa claims validadas do Microsoft Entra ID. Ela não é automaticamente o usuário de negócio e não carrega permissões locais.

|             Campo | Regra                                            |
| ----------------: | :----------------------------------------------- |
|       `object_id` | Claim `oid`, obrigatório                         |
|       `tenant_id` | Claim `tid`, obrigatório                         |
|         `subject` | Claim `sub`, opcional                            |
| `home_account_id` | Identificador da conta MSAL, obrigatório         |
|    `display_name` | Claim `name`, opcional                           |
|        `username` | `preferred_username` ou fallback `upn`, opcional |
|          `claims` | Cópia profundamente imutável                     |
|       `stable_id` | Tupla `(tenant_id, object_id)`                   |

## Validação

- Tenant pode ser comparado ao tenant configurado;
- Claims obrigatórias devem ser strings não vazias;
- Claims opcionais, quando presentes, também devem ser strings não vazias;
- Nomes de claims devem ser strings;
- Valores devem ser compatíveis com JSON;
- Access token, refresh token, ID token bruto, client secret e token cache são rejeitados;
- Username e email nunca são chave de autorização.

## Imutabilidade

A dataclass é congelada e usa slots. Mappings aninhados tornam-se `MappingProxyType` e listas tornam-se tuplas. A representação textual não expõe PII nem claims.

## `current_identity`

`current_identity` é um `LocalProxy` para a identidade da requisição.

- Fora de request context: `RuntimeError`;
- Aplicação sem extensão: `RuntimeError`;
- Requisição sem identidade: `AuthenticationRequired`;
- Identidade vinculada: retorna o objeto imutável.

A vinculação é uma seam interna. A ETAPA 05 deverá restaurar ou criar a identidade durante o fluxo web.

## Isolamento

A identidade vive no contexto Flask e não é compartilhada entre requisições ou aplicações. Não existe singleton global de usuário.

## Hooks

Hooks permanecem planejados para a ETAPA 07. A aplicação continuará responsável por mapear `(tenant_id, object_id)` para usuário local, autorização e auditoria.
