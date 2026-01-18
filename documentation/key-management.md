# Key Management

Prompt Fence relies on **Ed25519** public-key cryptography. Proper key management is critical for the security of your application.

## Generating Keys

### In Code (Development)

You can generate ephemeral keys for testing directly in Python:

```python
from prompt_fence import generate_keypair

private_key, public_key = generate_keypair()
print(f"Private: {private_key}")
print(f"Public:  {public_key}")
```

### Using CLI One-Liner (Production Setup)

For production, you typically want to generate keys once and inject them as environment variables. You can use this one-liner:

```bash
python3 -c "from prompt_fence import generate_keypair; p, pub = generate_keypair(); print(f'Private: {p}\nPublic:  {pub}')"
```

## Storing Keys

### Environment Variables

The SDK automatically looks for these environment variables if you don't pass keys explicitly:

-   `PROMPT_FENCE_PRIVATE_KEY`: Used by `PromptBuilder.build()`
-   `PROMPT_FENCE_PUBLIC_KEY`: Used by `validate()` and `validate_fence()`

**Example `.env` file:**

```bash
PROMPT_FENCE_PRIVATE_KEY="<base64_private_key>"
PROMPT_FENCE_PUBLIC_KEY="<base64_public_key>"
```

### Best Practices

1.  **Secret Management**: Never hardcode keys in your source code. Use a secrets manager (e.g., AWS Secrets Manager, HashiCorp Vault, GitHub Secrets).
2.  **Least Privilege**: The component that *builds* prompts needs the **Private Key**. The component that *validates* prompts (e.g., the checking gateway) only needs the **Public Key**.
3.  **Rotation**: Periodically rotate your keys. Since the signatures are ephemeral (per request), key rotation is straightforward—just update the configuration on your builder and validator services.

## Troubleshooting & Edge Cases

### Common Key Errors

The SDK raises `prompt_fence.CryptoError` for most key issues.

| Issue | Resulting Error |
| :--- | :--- |
| **Empty String** | `Invalid private key format: Expected 32 bytes, got 0` |
| **Invalid Base64** | `Base64 decode error: ...` |
| **Wrong Length** | `Invalid private key format: Expected 32 bytes, got X` |

### Key Confusion Pitfall

!!! failure "Public Key as Private Key"
    **Technically Possible, Logically Fatal**
    
    Ed25519 "Private Keys" are just 32 bytes of random seed data. Consequently, if you accidentally pass your **Public Key** (which is also 32 bytes) into the `private_key` argument of `PromptBuilder`, the SDK **will not error**.
    
    It will successfully sign the prompt using your public key as the seed. However, `validate()` will correctly **FAIL** because the signature won't match the actual public key.
    
    *Always verify you are using the correct variable.*

