# Validation & Security

Validation is the process of verifying the cryptographic signatures on a prompt to ensure it hasn't been tampered with and that the trust ratings are authentic.

## Where to Validate?

You typically validate in two places:

1.  **Security Gateway / Middle Layer**: A service that sits between your user-facing app and the LLM.
2.  **LLM Tool/Function**: If the LLM calls a tool, that tool can validate the input it received to ensure the LLM isn't hallucinating fake instructions.

## Validating a Prompt

Use the `validate()` function to check an entire prompt string.

```python
from prompt_fence import validate

# prompt_str = ... received from network ...
is_valid = validate(prompt_str, public_key)

if is_valid:
    # All fences are intact and signatures match.
    # The structure of the prompt is exactly as signed.
    proceed()
else:
    # ALARM! Someone tampered with the prompt or
    # tried to forge a trusted instruction.
    block_request()
```

!!! warning "Validation and Caching"
    When you pass a `FencedPrompt` object directly to `validate()`, the function uses the **cached string representation** of that object. This ensures you validate exactly what `to_plain_string()` returns, but be aware that modifying the internal `segments` list of a `FencedPrompt` (which you shouldn't do anyway) won't invalidate the cache.

### Protocol

The validation protocol follows **Definition 4.5** from the Prompt Fence paper:
> "If *any* fence fails verification, the *entire* prompt is rejected."

This ensures a fail-safe default.

## Inspecting Fences

If you need deeper inspection—for example, to log *which* specific user caused a validation failure—you can use `validate_fence()` on individual XML blocks.

```python
from prompt_fence import validate_fence, VerificationResult

# Assume you extracted a regex match for <sec:fence>...</sec:fence>
fence_xml = "<sec:fence>...</sec:fence>"

result: VerificationResult = validate_fence(fence_xml, public_key)

if result.valid:
    print(f"Authorized content from: {result.source}")
    print(f"Trust Rating: {result.rating}")
else:
    print(f"Validation failed: {result.error}")
```

## Handling Fence Errors

The SDK provides `FenceError` and `CryptoError` for handling exceptions during the signing or validation process, though the high-level `validate` function typically returns a boolean `False` for simplicity.
