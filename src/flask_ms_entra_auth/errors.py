from __future__ import annotations


class MicrosoftEntraAuthError(Exception):
    """Base exeção para falhas previsíveis da extensão"""

    _ms_entra_auth_notified: bool = False


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


class AuthenticationRejected(AuthenticationError):
    """Exceção levantada quando a aplicação rejeita uma identidade externa válida"""


class InvalidCallbackError(AuthenticationError):
    """Exceção levantada quando um callback de autenticação está faltando, expirado ou inconsistente"""


class InvalidNavigationTarget(AuthenticationError):
    """Exceção levantada quando um destino pós-autenticação é inseguro"""


class IdentityValidationError(AuthenticationError):
    """Exceção levantada quando reivindicações de identidade estão ausentes, inconsistentes ou inseguras"""


class ConsentRequired(AuthenticationError):
    """Exceção levantada quando o MSAL não pode satisfazer uma solicitação sem interação do usuário"""


class HookExecutionError(MicrosoftEntraAuthError):
    """Exceção levantada quando um gancho de aplicação falha após a entrada no código da extensão"""

    def __init__(self, message: str, *, event: str) -> None:
        super().__init__(message)
        self.event = event


class LocalBindingError(HookExecutionError):
    """Exceção levantada quando um hook autenticado não consegue vincular a identidade externa localmente"""


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
