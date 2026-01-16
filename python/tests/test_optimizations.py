import os

import pytest

from prompt_fence import (
    FenceError,
    PromptBuilder,
    generate_keypair,
    get_awareness_instructions,
    set_awareness_instructions,
)


class TestOptimizations:
    def setup_method(self):
        self.private_key, self.public_key = generate_keypair()

    def teardown_method(self):
        # Reset awareness instructions to default after each test
        # We need to know the default or just restore it if we cared about other tests,
        # but for this suite it's fine as long as we don't bleed too much.
        # However, since it's a global state, good practice to reset.
        # But we don't have the constant exposed anymore!
        # We can construct it or just leave it modified (other tests might fail if they expect specific text).
        # Let's save it in setup.
        pass

    @pytest.fixture(autouse=True)
    def preserve_awareness(self):
        original = get_awareness_instructions()
        yield
        set_awareness_instructions(original)

    def test_awareness_override(self):
        custom_instr = "CUSTOM AWARENESS INSTRUCTIONS"
        set_awareness_instructions(custom_instr)

        assert get_awareness_instructions() == custom_instr

        prompt = PromptBuilder().trusted_instructions("Foo").build(self.private_key)

        # Verify custom instructions are present
        assert custom_instr in prompt.to_plain_string()
        assert prompt.has_awareness_instructions

    def test_external_key_env_var(self):
        # Unset just in case
        if "PROMPT_FENCE_PRIVATE_KEY" in os.environ:
            del os.environ["PROMPT_FENCE_PRIVATE_KEY"]

        # Should raise ValueError if no key provided
        with pytest.raises(ValueError, match="Private key must be provided"):
            PromptBuilder().trusted_instructions("Foo").build()

        # Set env var
        os.environ["PROMPT_FENCE_PRIVATE_KEY"] = self.private_key

        try:
            prompt = PromptBuilder().trusted_instructions("Foo").build()
            assert len(prompt.segments) == 1
        finally:
            del os.environ["PROMPT_FENCE_PRIVATE_KEY"]

    def test_public_key_env_var(self):
        from prompt_fence import validate

        # Unset just in case
        if "PROMPT_FENCE_PUBLIC_KEY" in os.environ:
            del os.environ["PROMPT_FENCE_PUBLIC_KEY"]

        prompt = PromptBuilder().trusted_instructions("Foo").build(self.private_key)
        prompt_str = prompt.to_plain_string()

        # Should raise ValueError if no key provided
        with pytest.raises(ValueError, match="Public key must be provided"):
            validate(prompt_str)

        # Set env var
        os.environ["PROMPT_FENCE_PUBLIC_KEY"] = self.public_key

        try:
            assert validate(prompt_str)
        finally:
            del os.environ["PROMPT_FENCE_PUBLIC_KEY"]

    def test_segment_properties(self):
        builder = PromptBuilder()
        builder.trusted_instructions("Trusted")
        builder.untrusted_content("Untrusted")

        prompt = builder.build(self.private_key)

        assert len(prompt.segments) == 2
        assert len(prompt.trusted_segments) == 1
        assert len(prompt.untrusted_segments) == 1

        assert prompt.trusted_segments[0].content == "Trusted"
        assert prompt.untrusted_segments[0].content == "Untrusted"

    def test_fence_error_exception(self):
        # To trigger a FenceError, we might need to pass invalid XML or invalid type string if exposed?
        # Directly using _core functions might be easier to trigger error,
        # but let's see if we can trigger it via builder or types.
        # Or better, invalid fence type string construction if we were allowed.
        # But PromptBuilder uses Enums.
        # Let's try to set awareness instructions to something that breaks? No, string is fine.

        # Maybe import _core and call verify with bad xml?
        from prompt_fence._core import verify_fence

        with pytest.raises(FenceError):
            verify_fence("Invalid XML", self.public_key)

    def test_no_awareness_via_override(self):
        # If we want NO awareness, we set it to empty string?
        # The code prepends if awareness is not None (in FencedPrompt logic check?).
        # Builder.build calls get_awareness().
        # FencedPrompt treats it as string. if string is empty, it might still prepend empty string line?
        # FencedPrompt logic:
        # if self._awareness_instructions:
        #    parts.append(...)

        set_awareness_instructions("")
        prompt = PromptBuilder().trusted_instructions("Foo").build(self.private_key)

        # Should NOT have the awareness block effectively (or just empty string appended?)
        plain = prompt.to_plain_string()
        # It shouldn't match the default text
        assert "CRITICAL SECURITY RULES" not in plain
