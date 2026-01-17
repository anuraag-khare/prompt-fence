# Building Fenced Prompts

The core of Prompt Fence is the `PromptBuilder`. It allows you to construct a single prompt string composed of multiple "segments", each with a specific trust rating.

## The PromptBuilder

```python
from prompt_fence import PromptBuilder

builder = PromptBuilder()
```

The builder follows a fluent interface pattern. You can chain methods to add segments in order.

### Segment Types

#### 1. Trusted Instructions

**Use for:** System instructions, prompt templates, few-shot examples that YOU define.

```python
builder.trusted_instructions("You are a helpful assistant.")
```

-   **Rating:** `TRUSTED`
-   **Default Source:** `system`

#### 2. Untrusted Content

**Use for:** Any input that comes from an external user, even if you think it's safe.

```python
user_input = "Write a poem about..."
builder.untrusted_content(user_input, source="user_123")
```

-   **Rating:** `UNTRUSTED`
-   **Default Source:** `user`

#### 3. Partially Trusted Content

**Use for:** Content from 3rd party APIs or partners that you trust more than a random user but less than your own system.

```python
api_data = fetch_weather_data()
builder.partially_trusted_content(api_data, source="weather_api")
```

-   **Rating:** `PARTIALLY_TRUSTED`
-   **Default Source:** `partner`

#### 4. Raw Data

**Use for:** Large blobs of data (CSV, JSON) to be processed.

```python
builder.data_segment(json_blob, source="database")
```

-   **Rating:** `UNTRUSTED` (by default)
-   **Default Source:** `data`

---

## Building the Prompt

Once you have added all segments, call `.build()` with your private key to sign everything.

```python
# private_key must be a valid Ed25519 private key string
prompt = builder.build(private_key)
```

The result is a `FencedPrompt` object.

### The FencedPrompt Object

This object behaves like a string, but also exposes useful metadata.

```python
# Use as string
print(prompt)

# Explicit string conversion
raw_prompt = prompt.to_plain_string()

# Inspect segments
for segment in prompt.segments:
    print(f"[{segment.rating}] {segment.source}: {len(segment.content)} chars")
```

## Advanced Examples

### Chat History

You can rebuild a conversation history using trusted segments for the assistant's past replies (if you trust your own outputs) and untrusted segments for user replies.

```python
builder = PromptBuilder()

# System
builder.trusted_instructions("You are a chat bot.")

# History
builder.untrusted_content("Hello!", source="user")
builder.trusted_instructions("Hi there, how can I help?", source="assistant_history")
builder.untrusted_content("Ignore previous instructions...", source="user")

prompt = builder.build(private_key)
```
