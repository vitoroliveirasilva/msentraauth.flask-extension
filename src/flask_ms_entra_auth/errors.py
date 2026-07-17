class MicrosoftEntraAuthError(Exception):
    """Base exeção para falhas previsíveis da extensão"""


class ConfigurationError(MicrosoftEntraAuthError):
    """Exceção levantada quando a configuração do Microsoft Entra está ausente ou inválida"""


class StorageError(MicrosoftEntraAuthError):
    """Exceção levantada quando o armazenamento de autenticação não pode concluir uma operação com segurança"""
