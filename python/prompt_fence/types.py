"""Type definitions for the Prompt Fencing SDK."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class FenceType(str, Enum):
    """Standardized content type for fenced segments.
    Values: {instructions, content, data}
    """

    INSTRUCTIONS = "instructions"
    CONTENT = "content"
    DATA = "data"


class FenceRating(str, Enum):
    """Standardized trust rating for fenced segments.
    Values: {trusted, untrusted, partially-trusted}
    """

    TRUSTED = "trusted"
    UNTRUSTED = "untrusted"
    PARTIALLY_TRUSTED = "partially-trusted"


@dataclass(frozen=True)
class FenceSegment:
    """A fenced prompt segment with metadata and signature.

    Attributes:
        content: The actual content of the segment.
        fence_type: The semantic type (instructions, content, data).
        rating: The trust rating (trusted, untrusted, partially-trusted).
        source: Identifier for the data origin.
        timestamp: ISO-8601 timestamp of fence creation.
        signature: Base64-encoded Ed25519 signature.
        xml: The full XML representation of the fence.
    """

    content: str
    fence_type: FenceType
    rating: FenceRating
    source: str
    timestamp: str
    signature: str
    xml: str

    @property
    def is_trusted(self) -> bool:
        """Check if this segment is fully trusted."""
        return self.rating == FenceRating.TRUSTED

    @property
    def is_untrusted(self) -> bool:
        """Check if this segment is untrusted."""
        return self.rating == FenceRating.UNTRUSTED

    def __str__(self) -> str:
        return self.xml

    def __repr__(self) -> str:
        return (
            f"FenceSegment(type={self.fence_type.value}, "
            f"rating={self.rating.value}, source='{self.source}', "
            f"content_len={len(self.content)})"
        )


@dataclass
class VerificationResult:
    """Result of fence verification.

    Attributes:
        valid: Whether the signature is valid.
        content: The extracted content (if valid).
        fence_type: The segment type.
        rating: The trust rating.
        source: The data source.
        timestamp: The creation timestamp.
        error: Error message if verification failed.
    """

    valid: bool
    content: str | None = None
    fence_type: FenceType | None = None
    rating: FenceRating | None = None
    source: str | None = None
    timestamp: str | None = None
    error: str | None = None

    def __bool__(self) -> bool:
        return self.valid
