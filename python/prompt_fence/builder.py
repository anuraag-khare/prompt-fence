"""Prompt builder for creating fenced prompts."""

from __future__ import annotations

import os
from datetime import datetime, timezone

from .types import FenceRating, FenceSegment, FenceType


class FencedPrompt:
    """A str-like object representing a complete fenced prompt.

    This class wraps the assembled fenced prompt and provides:
    - str-like behavior via __str__()
    - Explicit conversion via to_plain_string() for interop with other SDKs
    - Access to individual segments for inspection

    Example:
        >>> prompt = builder.build(private_key)
        >>> print(prompt)  # Uses __str__, includes fence-aware instructions
        >>> llm_call(prompt.to_plain_string())  # Explicit str for other SDKs
    """

    def __init__(
        self,
        segments: list[FenceSegment],
        awareness_instructions: str | None = None,
    ):
        """Initialize a FencedPrompt.

        Args:
            segments: List of signed fence segments.
            awareness_instructions: Optional fence-awareness instructions prepended.
        """
        self._segments = segments
        self._awareness_instructions = awareness_instructions
        self._cached_string: str | None = None

    @property
    def segments(self) -> list[FenceSegment]:
        """Get all fence segments in order."""
        return self._segments.copy()

    @property
    def trusted_segments(self) -> list[FenceSegment]:
        """Get all trusted fence segments."""
        return [s for s in self._segments if s.rating == FenceRating.TRUSTED]

    @property
    def untrusted_segments(self) -> list[FenceSegment]:
        """Get all untrusted fence segments."""
        return [s for s in self._segments if s.rating == FenceRating.UNTRUSTED]

    @property
    def has_awareness_instructions(self) -> bool:
        """Check if fence-awareness instructions are included."""
        return self._awareness_instructions is not None

    def _build_string(self) -> str:
        """Build the complete prompt string."""
        parts = []

        if self._awareness_instructions:
            parts.append(self._awareness_instructions)
            parts.append("")  # Empty line separator

        for segment in self._segments:
            parts.append(segment.xml)

        return "\n".join(parts)

    def to_plain_string(self) -> str:
        """Convert to a plain Python string.

        Use this method when passing the prompt to other SDKs or APIs
        that expect a regular string type.

        Returns:
            The complete fenced prompt as a plain str.
        """
        if self._cached_string is None:
            self._cached_string = self._build_string()
        return self._cached_string

    def __str__(self) -> str:
        """Return the prompt as a string.

        This is equivalent to to_plain_string() and can be used
        directly in string contexts.
        """
        return self.to_plain_string()

    def __repr__(self) -> str:
        return (
            f"FencedPrompt(segments={len(self._segments)}, "
            f"has_awareness={self.has_awareness_instructions})"
        )

    def __len__(self) -> int:
        """Return the length of the prompt string."""
        return len(self.to_plain_string())

    def __eq__(self, other: object) -> bool:
        if isinstance(other, str):
            return self.to_plain_string() == other
        if isinstance(other, FencedPrompt):
            return self.to_plain_string() == other.to_plain_string()
        return NotImplemented

    def __hash__(self) -> int:
        return hash(self.to_plain_string())

    def __add__(self, other: str) -> str:
        """Allow concatenation with strings."""
        return self.to_plain_string() + other

    def __radd__(self, other: str) -> str:
        """Allow reverse concatenation with strings."""
        return other + self.to_plain_string()


class PromptBuilder:
    """Builder for constructing fenced prompts with cryptographic signatures.

    This is the main entry point for creating secure LLM prompts with
    explicit trust boundaries.

    Example:
        >>> from prompt_fence import PromptBuilder, generate_keypair
        >>>
        >>> private_key, public_key = generate_keypair()
        >>>
        >>> prompt = (
        ...     PromptBuilder()
        ...     .trusted_instructions("Analyze the following review...")
        ...     .untrusted_content("User review text here...")
        ...     .build(private_key)
        ... )
        >>>
        >>> # Use with any LLM SDK
        >>> response = llm.generate(prompt.to_plain_string())
    """

    def __init__(self):
        """Initialize a new PromptBuilder."""
        self._segments: list[_PendingSegment] = []

    def trusted_instructions(
        self,
        text: str,
        source: str = "system",
        timestamp: str | None = None,
    ) -> PromptBuilder:
        """Add trusted instructions to the prompt.

        Use this for system prompts and instructions that should be
        treated as authoritative commands.

        Args:
            text: The instruction text.
            source: Source identifier (default: "system").
            timestamp: ISO-8601 timestamp (default: current time).

        Returns:
            Self for method chaining.
        """
        self._segments.append(
            _PendingSegment(
                content=text,
                fence_type=FenceType.INSTRUCTIONS,
                rating=FenceRating.TRUSTED,
                source=source,
                timestamp=timestamp or _iso_timestamp(),
            )
        )
        return self

    def untrusted_content(
        self,
        text: str,
        source: str = "user",
        timestamp: str | None = None,
    ) -> PromptBuilder:
        """Add untrusted content to the prompt.

        Use this for user inputs, external data, or any content that
        should NOT be treated as instructions.

        Args:
            text: The content text.
            source: Source identifier (default: "user").
            timestamp: ISO-8601 timestamp (default: current time).

        Returns:
            Self for method chaining.
        """
        self._segments.append(
            _PendingSegment(
                content=text,
                fence_type=FenceType.CONTENT,
                rating=FenceRating.UNTRUSTED,
                source=source,
                timestamp=timestamp or _iso_timestamp(),
            )
        )
        return self

    def partially_trusted_content(
        self,
        text: str,
        source: str = "partner",
        timestamp: str | None = None,
    ) -> PromptBuilder:
        """Add partially-trusted content to the prompt.

        Use this for content from verified partners or curated sources
        that has some level of trust but is not fully authoritative.

        Args:
            text: The content text.
            source: Source identifier (default: "partner").
            timestamp: ISO-8601 timestamp (default: current time).

        Returns:
            Self for method chaining.
        """
        self._segments.append(
            _PendingSegment(
                content=text,
                fence_type=FenceType.CONTENT,
                rating=FenceRating.PARTIALLY_TRUSTED,
                source=source,
                timestamp=timestamp or _iso_timestamp(),
            )
        )
        return self

    def data_segment(
        self,
        text: str,
        rating: FenceRating = FenceRating.UNTRUSTED,
        source: str = "data",
        timestamp: str | None = None,
    ) -> PromptBuilder:
        """Add a data segment to the prompt.

        Use this for raw data that should be processed but not interpreted
        as instructions.

        Args:
            text: The data content.
            rating: Trust rating for the data.
            source: Source identifier (default: "data").
            timestamp: ISO-8601 timestamp (default: current time).

        Returns:
            Self for method chaining.
        """
        self._segments.append(
            _PendingSegment(
                content=text,
                fence_type=FenceType.DATA,
                rating=rating,
                source=source,
                timestamp=timestamp or _iso_timestamp(),
            )
        )
        return self

    def custom_segment(
        self,
        text: str,
        fence_type: FenceType,
        rating: FenceRating,
        source: str,
        timestamp: str | None = None,
    ) -> PromptBuilder:
        """Add a custom segment with explicit type and rating.

        Use this when you need full control over segment attributes.

        Args:
            text: The segment content.
            fence_type: The semantic type.
            rating: The trust rating.
            source: Source identifier.
            timestamp: ISO-8601 timestamp (default: current time).

        Returns:
            Self for method chaining.
        """
        self._segments.append(
            _PendingSegment(
                content=text,
                fence_type=fence_type,
                rating=rating,
                source=source,
                timestamp=timestamp or _iso_timestamp(),
            )
        )
        return self

    def build(self, private_key: str | None = None) -> FencedPrompt:
        """Build the fenced prompt with cryptographic signatures.

        This signs all segments using the provided private key and
        assembles them into a complete FencedPrompt.

        Args:
            private_key: Base64-encoded Ed25519 private key for signing.
                If None, tries to load from PROMPT_FENCE_PRIVATE_KEY env var.

        Returns:
            A FencedPrompt object that can be used with LLM APIs.

        Raises:
            ValueError: If the private key is missing or invalid.
            CryptoError: If signing fails.
            ImportError: If Rust core is missing.
        """
        # Import here to avoid circular dependency and allow graceful fallback
        try:
            from prompt_fence._core import (
                get_awareness_instructions as _get_awareness,
            )
            from prompt_fence._core import (
                sign_fence as _sign_fence,
            )
        except ImportError:
            # Fallback for development/testing without compiled Rust
            raise ImportError(
                "Rust core not compiled. Run 'maturin develop' in the python/ directory."
            ) from None

        if private_key is None:
            private_key = os.environ.get("PROMPT_FENCE_PRIVATE_KEY")

        if private_key is None:
            raise ValueError("Private key must be provided or set in PROMPT_FENCE_PRIVATE_KEY")

        signed_segments: list[FenceSegment] = []

        for pending in self._segments:
            # Map Python enums to Rust enums
            # Python uses UPPER_CASE, Rust/PyO3 uses PascalCase
            from prompt_fence._core import FenceRating as RustFenceRating
            from prompt_fence._core import FenceType as RustFenceType

            # Map: INSTRUCTIONS -> Instructions, CONTENT -> Content, DATA -> Data
            type_name_map = {
                "INSTRUCTIONS": "Instructions",
                "CONTENT": "Content",
                "DATA": "Data",
            }
            rust_type = getattr(RustFenceType, type_name_map[pending.fence_type.name])
            rust_rating = RustFenceRating.from_str(pending.rating.value)

            # Sign the fence using Rust core
            fence = _sign_fence(
                content=pending.content,
                fence_type=rust_type,
                rating=rust_rating,
                source=pending.source,
                private_key=private_key,
                timestamp=pending.timestamp,
            )

            signed_segments.append(
                FenceSegment(
                    content=pending.content,
                    fence_type=pending.fence_type,
                    rating=pending.rating,
                    source=pending.source,
                    timestamp=pending.timestamp,
                    signature=fence.signature,
                    xml=fence.to_xml(),
                )
            )

        # Get central awareness instructions
        awareness = _get_awareness()

        return FencedPrompt(signed_segments, awareness)


class _PendingSegment:
    """Internal representation of a segment before signing."""

    def __init__(
        self,
        content: str,
        fence_type: FenceType,
        rating: FenceRating,
        source: str,
        timestamp: str,
    ):
        self.content = content
        self.fence_type = fence_type
        self.rating = rating
        self.source = source
        self.timestamp = timestamp


def _iso_timestamp() -> str:
    """Generate current UTC timestamp in ISO-8601 format."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
