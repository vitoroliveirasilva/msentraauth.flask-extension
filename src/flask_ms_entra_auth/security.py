from __future__ import annotations

from dataclasses import dataclass
from ipaddress import ip_address
from typing import Literal
from urllib.parse import urlsplit

from flask import Flask

from .config import MicrosoftEntraAuthConfig
from .storage import MemoryStorage
from .storage.namespaced import NamespacedStorage

SecuritySeverity = Literal["info", "warning", "error"]


@dataclass(frozen=True, slots=True)
class SecurityFinding:
    # Sanitização e anonimização de informações sensíveis, como chaves secretas, para evitar vazamentos de dados

    code: str
    severity: SecuritySeverity
    message: str


@dataclass(frozen=True, slots=True)
class SecurityReport:
    # Imutabilidade e encapsulamento de dados para garantir que o relatório de segurança não seja alterado após a criação

    findings: tuple[SecurityFinding, ...]

    @property
    def passed(self) -> bool:
        # Retorna True se não houver achados de severidade de erro, indicando que a auditoria de segurança foi bem-sucedida
        return all(finding.severity != "error" for finding in self.findings)

    @property
    def hardened(self) -> bool:
        # Retorna True se não houver achados de severidade de aviso ou erro, indicando que a aplicação está em um estado seguro e endurecido
        return not self.findings


def audit_security(
    app: Flask,
    config: MicrosoftEntraAuthConfig,
    storage: NamespacedStorage,
) -> SecurityReport:
    # Inspecionar as configurações do framework e do backend sem ler valores secretos, garantindo que a auditoria de segurança não exponha informações sensíveis
    findings: list[SecurityFinding] = []
    secret_key = app.secret_key
    if not secret_key:
        findings.append(
            SecurityFinding(
                "secret-key-missing",
                "error",
                "Flask SECRET_KEY is required for signed authentication references.",
            )
        )
    elif len(_secret_key_bytes(secret_key)) < 32:
        findings.append(
            SecurityFinding(
                "secret-key-short",
                "warning",
                "Flask SECRET_KEY should provide at least 32 bytes of entropy.",
            )
        )

    if app.config.get("SESSION_COOKIE_HTTPONLY") is not True:
        findings.append(
            SecurityFinding(
                "session-cookie-httponly-disabled",
                "error",
                "SESSION_COOKIE_HTTPONLY must remain enabled.",
            )
        )

    same_site = app.config.get("SESSION_COOKIE_SAMESITE")
    if not isinstance(same_site, str) or same_site.casefold() not in {"lax", "strict"}:
        findings.append(
            SecurityFinding(
                "session-cookie-samesite-weak",
                "warning",
                "SESSION_COOKIE_SAMESITE should be Lax or Strict.",
            )
        )

    if not app.config.get("SESSION_COOKIE_SECURE") and not _is_loopback_redirect(
        config.redirect_uri
    ):
        findings.append(
            SecurityFinding(
                "session-cookie-secure-disabled",
                "warning",
                "SESSION_COOKIE_SECURE should be enabled outside loopback development.",
            )
        )

    if isinstance(storage.backend, MemoryStorage) and not (app.testing or app.debug):
        findings.append(
            SecurityFinding(
                "memory-storage-production",
                "warning",
                "MemoryStorage is process-local and unsuitable for production.",
            )
        )

    if not storage.supports_atomic_take:
        findings.append(
            SecurityFinding(
                "atomic-consume-unavailable",
                "warning",
                "The storage backend cannot guarantee distributed one-time consumption.",
            )
        )
    return SecurityReport(tuple(findings))


def _secret_key_bytes(value: object) -> bytes:
    if isinstance(value, bytes):
        return value
    return str(value).encode("utf-8")


def _is_loopback_redirect(value: str) -> bool:
    host = urlsplit(value).hostname
    if host is None:
        return False
    if host.casefold() == "localhost":
        return True
    try:
        return ip_address(host).is_loopback
    except ValueError:
        return False
