# Advanced Usage & Under the Hood

## How It Works

Prompt Fence isn't magic; it's a strongly-typed signature scheme applied to string data.

### The XML Structure

When you call `.build()`, the SDK wraps your content in XML tags.

```xml
<sec:fence
    id="sig_..."
    type="Instructions"
    rating="Trusted"
    source="system"
    ts="2025-01-17T..."
    sig="...Ed25519_Signature..."
>
    Your Content Here
</sec:fence>
```

-   `sec:fence`: The namespaced tag used to avoid collisions with normal HTML/XML.
-   `id`: A unique identifier for the segment.
-   `sig`: The Ed25519 signature of the content + attributes.

### Cryptography (Core Rust)

The heavy lifting is done in Rust (`prompt_fence/rust`).

1.  **Canonicalization**: Before signing, attributes are sorted and content is normalized to ensure consistent hashing.
2.  **Hashing**: We use **SHA-256** to hash the canonicalized data.
3.  **Signing**: We use **Ed25519** (via the `ed25519-dalek` crate) to sign the hash.

This ensures that even a single bit flip in the content or metadata invalidates the fence.

## Gotchas & Common Mistakes

### 1. Modifying the String
**Never** modify the prompt string after it's built.

```python
# ❌ INCORRECT
prompt = builder.build(key)
modified = prompt + "\n\nPlease answer." 
# This breaks the awareness instructions context or might be interpreted outside a fence.
```

While appending *outside* a fence doesn't invalidate the individual fence signatures, it weakens the security model because the LLM sees content that isn't fenced.

### 2. Key Exposure
If your private key leaks, an attacker can sign malicious prompts that look trusted.

-   **Mitigation**: Rotate keys immediately if compromised. The SDK validates signatures, not the key's age.

### 3. Context Window Limits
Fenced prompts are verbose due to XML overhead.

-   **Overhead**: Expect ~200-300 extra characters per segment (due to Base64 signatures and XML tags).
-   **Mitigation**: Use fewer, larger segments rather than many tiny ones.

## Performance

The critical path (signing and verification) is implemented in Rust with PyO3 bindings.

-   **Signing**: < 1ms overhead per segment.
-   **Verification**: < 1ms overhead per segment.
-   **Threads**: The GIL is released during cryptographic operations, allowing multi-threaded validation in web servers (FastAPI/Django).
