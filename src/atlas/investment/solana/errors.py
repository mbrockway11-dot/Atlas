"""Solana/Jupiter integration errors for Atlas G.24."""


class SolanaIntegrationError(RuntimeError):
    """Base read-only integration error."""


class SolanaValidationError(SolanaIntegrationError):
    """Invalid public key, network, or payload."""


class SolanaRpcError(SolanaIntegrationError):
    """Solana RPC request failed."""


class JupiterApiError(SolanaIntegrationError):
    """Jupiter API request failed."""


class JupiterApiKeyRequired(JupiterApiError):
    """Jupiter production API requires a developer key."""


class SigningDisabledError(SolanaIntegrationError):
    """Signing or submission was attempted in G.24."""


__all__ = [
    "JupiterApiError",
    "JupiterApiKeyRequired",
    "SigningDisabledError",
    "SolanaIntegrationError",
    "SolanaRpcError",
    "SolanaValidationError",
]
