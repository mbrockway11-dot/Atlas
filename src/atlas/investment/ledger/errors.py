"""Portfolio ledger errors for Atlas G.21."""


class LedgerError(RuntimeError):
    """Base portfolio ledger error."""


class LedgerValidationError(LedgerError):
    """Ledger event or state validation failed."""


class DuplicateFillError(LedgerError):
    """Fill ID has already been processed."""


class InsufficientPositionError(LedgerError):
    """Sell quantity exceeds the current long position."""


class LedgerIntegrityError(LedgerError):
    """Hash chain or persistence integrity failed."""


__all__ = [
    "DuplicateFillError",
    "InsufficientPositionError",
    "LedgerError",
    "LedgerIntegrityError",
    "LedgerValidationError",
]
