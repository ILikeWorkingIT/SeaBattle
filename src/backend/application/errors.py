"""Application errors for session and shot use cases."""


class SessionLimitReachedError(Exception):
    """Three active sessions already exist (FT-049)."""


class SessionStartFailedError(Exception):
    """No valid placement within the start window (FT-010 / NFT-015)."""


class SessionPersistError(Exception):
    """Internal failure after generation; slot must not remain occupied."""


class SessionNotFoundError(Exception):
    """Session id unknown, expired, or deleted (FT-067 / A0001)."""


class ShotChannelError(Exception):
    """Shot sent over REST instead of the party WebSocket (FT-055)."""


class LedgerReadError(Exception):
    """Failed to load a consistent statistics snapshot (UC-007 E1)."""


class LedgerWriteError(Exception):
    """Failed to persist a GAME_OVER record (UC-004 E1)."""
