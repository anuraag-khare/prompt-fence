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
```
