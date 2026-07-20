from __future__ import annotations


class MicrosoftEntraAuthError(Exception):
    """Base exeção para falhas previsíveis da extensão"""


class ConfigurationError(MicrosoftEntraAuthError):
    """Exceção levantada quando a configuração do Microsoft Entra está ausente ou inválida"""


class StorageError(MicrosoftEntraAuthError):
    """Exceção levantada quando o armazenamento de autenticação não pode concluir uma operação com segurança"""


class AuthenticationError(MicrosoftEntraAuthError):
    """Base exeção para falhas previsíveis de autenticação do usuário"""


class AuthenticationRequired(AuthenticationError):
    """Exceção levantada quando uma operação requer uma identidade ou conta autenticada"""


class AuthenticationCancelled(AuthenticationError):
    """Exceção levantada quando o usuário cancela previsivelmente a autenticação interativa"""


class InvalidCallbackError(AuthenticationError):
    """Exceção levantada quando um callback de autenticação está faltando, expirado ou inconsistente"""


class InvalidNavigationTarget(AuthenticationError):
    """Exceção levantada quando um destino pós-autenticação é inseguro"""


class IdentityValidationError(AuthenticationError):
    """Exceção levantada quando reivindicações de identidade estão ausentes, inconsistentes ou inseguras"""


class ConsentRequired(AuthenticationError):
    """Exceção levantada quando o MSAL não pode satisfazer uma solicitação sem interação do usuário"""


class TokenAcquisitionError(MicrosoftEntraAuthError):
    """Exceção levantada quando o MSAL retorna um resultado de token malsucedido ou malformado"""

    def __init__(
        self,
        message: str,
        *,
        code: str | None = None,
        correlation_id: str | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.correlation_id = correlation_id


class ProviderUnavailableError(MicrosoftEntraAuthError):
    """Exceção levantada quando o MSAL ou o provedor de identidade falha inesperadamente"""
