"""Tests for prompt_fence builder."""

from prompt_fence import get_awareness_instructions
from prompt_fence.builder import (
    FencedPrompt,
    PromptBuilder,
    _iso_timestamp,
)
from prompt_fence.types import FenceRating, FenceSegment, FenceType


class TestFencedPrompt:
    def test_str_conversion(self):
        segment = FenceSegment(
            content="Hello",
            fence_type=FenceType.INSTRUCTIONS,
            rating=FenceRating.TRUSTED,
            source="test",
            timestamp="2025-01-15T10:00:00.000Z",
            signature="sig",
            xml="<sec:fence>Hello</sec:fence>",
        )

        prompt = FencedPrompt([segment], awareness_instructions=None)

        assert str(prompt) == "<sec:fence>Hello</sec:fence>"
        assert prompt.to_plain_string() == "<sec:fence>Hello</sec:fence>"

    def test_with_awareness_instructions(self):
        segment = FenceSegment(
            content="Hello",
            fence_type=FenceType.INSTRUCTIONS,
            rating=FenceRating.TRUSTED,
            source="test",
            timestamp="2025-01-15T10:00:00.000Z",
            signature="sig",
            xml="<sec:fence>Hello</sec:fence>",
        )

        prompt = FencedPrompt([segment], awareness_instructions="AWARENESS")

        result = prompt.to_plain_string()
        assert result.startswith("AWARENESS")
        assert "<sec:fence>Hello</sec:fence>" in result
        assert prompt.has_awareness_instructions

    def test_segments_property(self):
        segment1 = FenceSegment(
            content="One",
            fence_type=FenceType.INSTRUCTIONS,
            rating=FenceRating.TRUSTED,
            source="sys",
            timestamp="2025-01-15T10:00:00.000Z",
            signature="sig1",
            xml="<fence>One</fence>",
        )
        segment2 = FenceSegment(
            content="Two",
            fence_type=FenceType.CONTENT,
            rating=FenceRating.UNTRUSTED,
            source="user",
            timestamp="2025-01-15T10:00:01.000Z",
            signature="sig2",
            xml="<fence>Two</fence>",
        )

        prompt = FencedPrompt([segment1, segment2])

        assert len(prompt.segments) == 2
        assert prompt.segments[0].content == "One"
        assert prompt.segments[1].content == "Two"

    def test_len(self):
        segment = FenceSegment(
            content="Test",
            fence_type=FenceType.DATA,
            rating=FenceRating.UNTRUSTED,
            source="test",
            timestamp="2025-01-15T10:00:00.000Z",
            signature="sig",
            xml="<sec:fence>Test</sec:fence>",
        )

        prompt = FencedPrompt([segment])

        assert len(prompt) == len("<sec:fence>Test</sec:fence>")

    def test_equality_with_string(self):
        segment = FenceSegment(
            content="X",
            fence_type=FenceType.DATA,
            rating=FenceRating.TRUSTED,
            source="t",
            timestamp="2025-01-15T10:00:00.000Z",
            signature="s",
            xml="<f>X</f>",
        )

        prompt = FencedPrompt([segment])

        # FencedPrompt compares equal to its string representation
        assert prompt == "<f>X</f>"
        # str also compares equal when FencedPrompt.__eq__ is called
        assert prompt == str(prompt)

    def test_concatenation(self):
        segment = FenceSegment(
            content="A",
            fence_type=FenceType.DATA,
            rating=FenceRating.TRUSTED,
            source="t",
            timestamp="2025-01-15T10:00:00.000Z",
            signature="s",
            xml="A",
        )

        prompt = FencedPrompt([segment])

        assert prompt + "B" == "AB"
        assert "B" + prompt == "BA"


class TestPromptBuilder:
    def test_empty_builder(self):
        builder = PromptBuilder()

        # No segments added, should have empty segments list
        assert len(builder._segments) == 0

    def test_trusted_instructions(self):
        builder = PromptBuilder()
        builder.trusted_instructions("Test instruction", source="system")

        assert len(builder._segments) == 1
        segment = builder._segments[0]
        assert segment.content == "Test instruction"
        assert segment.fence_type == FenceType.INSTRUCTIONS
        assert segment.rating == FenceRating.TRUSTED
        assert segment.source == "system"

    def test_untrusted_content(self):
        builder = PromptBuilder()
        builder.untrusted_content("User input", source="user_upload")

        assert len(builder._segments) == 1
        segment = builder._segments[0]
        assert segment.content == "User input"
        assert segment.fence_type == FenceType.CONTENT
        assert segment.rating == FenceRating.UNTRUSTED
        assert segment.source == "user_upload"

    def test_method_chaining(self):
        builder = (
            PromptBuilder()
            .trusted_instructions("Instruction 1")
            .untrusted_content("Content 1")
            .data_segment("Data 1")
        )

        assert len(builder._segments) == 3

    def test_data_segment_with_rating(self):
        builder = PromptBuilder()
        builder.data_segment("Some data", rating=FenceRating.PARTIALLY_TRUSTED)

        segment = builder._segments[0]
        assert segment.fence_type == FenceType.DATA
        assert segment.rating == FenceRating.PARTIALLY_TRUSTED

    def test_custom_segment(self):
        builder = PromptBuilder()
        builder.custom_segment(
            text="Custom",
            fence_type=FenceType.CONTENT,
            rating=FenceRating.TRUSTED,
            source="custom_source",
        )

        segment = builder._segments[0]
        assert segment.content == "Custom"
        assert segment.fence_type == FenceType.CONTENT
        assert segment.rating == FenceRating.TRUSTED
        assert segment.source == "custom_source"


class TestIsoTimestamp:
    def test_format(self):
        ts = _iso_timestamp()

        # Should be ISO-8601 format with Z suffix
        assert ts.endswith("Z")
        assert "T" in ts
        assert len(ts) == 24  # YYYY-MM-DDTHH:MM:SS.mmmZ


class TestAwarenessInstructions:
    def test_default_instructions_exist(self):
        instructions = get_awareness_instructions()
        assert instructions is not None
        assert "CRITICAL SECURITY RULES" in instructions
        assert "untrusted" in instructions
        assert "trusted" in instructions
