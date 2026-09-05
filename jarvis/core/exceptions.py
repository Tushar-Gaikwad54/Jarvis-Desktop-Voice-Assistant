"""
Custom exception hierarchy for J.A.R.V.I.S.
"""


class JarvisError(Exception):
    """Base exception for all J.A.R.V.I.S. errors."""
    pass


class ToolExecutionError(JarvisError):
    """Raised when a tool fails during execution."""
    def __init__(self, tool_name: str, message: str, original_exception: Exception = None):
        self.tool_name = tool_name
        self.original_exception = original_exception
        super().__init__(f"Tool '{tool_name}' failed: {message}")


class PermissionDeniedError(JarvisError):
    """Raised when an operation is rejected by the permission system."""
    def __init__(self, operation: str, risk_level: str, reason: str = "User denied permission"):
        self.operation = operation
        self.risk_level = risk_level
        self.reason = reason
        super().__init__(f"Permission denied for [{risk_level}] operation '{operation}': {reason}")


class LLMProviderError(JarvisError):
    """Raised when an LLM provider fails to respond or produces invalid output."""
    def __init__(self, provider: str, message: str, status_code: int = None):
        self.provider = provider
        self.status_code = status_code
        super().__init__(f"LLM Provider '{provider}' error: {message}")


class ConfigurationError(JarvisError):
    """Raised when configuration is invalid or missing required settings."""
    pass
