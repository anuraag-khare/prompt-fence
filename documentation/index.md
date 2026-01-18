# Prompt Fence SDK

[![PyPI version](https://badge.fury.io/py/prompt-fence.svg)](https://badge.fury.io/py/prompt-fence)
[![CI](https://github.com/anuraag-khare/prompt-fence/actions/workflows/ci.yml/badge.svg)](https://github.com/anuraag-khare/prompt-fence/actions/workflows/ci.yml)
[![Python Versions](https://img.shields.io/pypi/pyversions/prompt-fence.svg)](https://pypi.org/project/prompt-fence/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Secure your specific LLM prompts with cryptographic boundaries.**

The Prompt Fence SDK provides an easy-to-use API for implementing cryptographic trust boundaries in LLM applications. It allows you to mathematically prove which parts of a prompt came from your trusted system and which parts came from untrusted users.

> [!NOTE]
> This is an **unofficial implementation** of the concept described in the paper [Prompt Fence: A Cryptographic Approach to Establishing Security Boundaries in Large Language Model Prompts](https://arxiv.org/abs/2511.19727).

## Why Prompt Fence?

LLMs cannot inherently distinguish between "instructions" and "data". This vulnerability leads to **Prompt Injection**, where user input hijacks the model's behavior.

**Prompt Fence solves this by:**

1.  **Signing**: Your application cryptographically signs trusted instructions using Ed25519.
2.  **Fencing**: Trusted and untrusted content is wrapped in XML "fences" with digital signatures.
3.  **Verifying**: A security gateway (or the LLM itself) validates these signatures before processing.

## Core Features

-   **🛡️ Cryptographic Integrity**: Uses Ed25519 signatures to prevent tampering.
-   **⚡ High Performance**: Core cryptography is implemented in Rust.
-   **🔒 Zero-Trust Architecture**: Treat all inputs as untrusted until validated.
-   **📝 Flexible Builders**: Easy-to-use Python API for constructing complex prompts.

## Get Started

Ready to secure your prompts?

[Get Started with Installation](getting-started.md){ .md-button .md-button--primary } [View API Reference](api.md){ .md-button }
