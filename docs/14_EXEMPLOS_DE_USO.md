# Exemplos de uso

## Vínculo local

```python
@entra_auth.on_authenticated
def bind(identity: Identity) -> None:
    account = users.find(identity.tenant_id, identity.object_id)
    if account is None:
        raise AuthenticationRejected("local account is not available")
```

## Auditoria de logout

```python
@entra_auth.on_logout
def audit(identity: Identity | None) -> None:
    logger.info("local logout", extra={"had_identity": identity is not None})
```

Não registre username, email, claims ou tokens quando não forem necessários.

## Métricas

```python
@entra_auth.on_event
def metric(event: AuthEvent) -> None:
    metrics.increment(event.name)
```

## Auditoria de segurança em startup

```python
report = entra_auth.audit_security(app)
for finding in report.findings:
    app.logger.warning(
        "auth security finding",
        extra={"code": finding.code, "severity": finding.severity},
    )
```

## Backend distribuído

```python
class RedisStorage:
    def take(self, key: str) -> bytes | None:
        # Deve usar script Lua, GETDEL ou primitiva equivalente do backend.
        ...
```

Configure `MS_ENTRA_REQUIRE_ATOMIC_STORAGE=True` para impedir fallback não distribuído.
