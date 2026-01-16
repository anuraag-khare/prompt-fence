//! Cryptographic signing and verification for Prompt Fencing.
#![allow(clippy::useless_conversion)]
//!
//! Implements Ed25519 signatures with SHA-256 hashing per the paper:
//! - σ = Sign(SK, H(C || M_canonical))
//! - Verification uses the same deterministic process

use base64::{engine::general_purpose::STANDARD as BASE64, Engine};
use ed25519_dalek::{Signature, Signer, SigningKey, Verifier, VerifyingKey};
use pyo3::prelude::*;
use sha2::{Digest, Sha256};
use thiserror::Error;

use crate::fence::{parse_fence_xml, Fence, FenceMetadata, FenceRating, FenceType};

/// Errors related to cryptographic operations.
#[derive(Error, Debug)]
pub enum CryptoError {
    #[error("Invalid private key format: {0}")]
    InvalidPrivateKey(String),

    #[error("Invalid public key format: {0}")]
    InvalidPublicKey(String),

    #[error("Invalid signature format: {0}")]
    InvalidSignature(String),

    #[error("Signature verification failed")]
    VerificationFailed,

    #[error("Base64 decode error: {0}")]
    Base64Error(String),
}

impl From<CryptoError> for PyErr {
    fn from(err: CryptoError) -> PyErr {
        crate::CryptoError::new_err(err.to_string())
    }
}

/// Generate a new Ed25519 keypair.
/// Returns (private_key_base64, public_key_base64).
#[pyfunction]
pub fn generate_keypair() -> (String, String) {
    let mut rng = rand::thread_rng();
    let signing_key = SigningKey::generate(&mut rng);
    let verifying_key = signing_key.verifying_key();

    let private_b64 = BASE64.encode(signing_key.to_bytes());
    let public_b64 = BASE64.encode(verifying_key.to_bytes());

    (private_b64, public_b64)
}

/// Compute the signature input hash: SHA-256(content || metadata_canonical).
/// Per paper Definition 4.3: σ = Sign(SK, H(C || M_canonical))
fn compute_signature_hash(content: &str, metadata: &FenceMetadata) -> [u8; 32] {
    let canonical = metadata.canonicalize();
    let mut hasher = Sha256::new();
    hasher.update(content.as_bytes());
    hasher.update(canonical.as_bytes());
    hasher.finalize().into()
}

/// Sign content with metadata using Ed25519.
/// Returns base64-encoded signature.
fn sign_content(
    content: &str,
    metadata: &FenceMetadata,
    private_key_b64: &str,
) -> Result<String, CryptoError> {
    let key_bytes = BASE64
        .decode(private_key_b64)
        .map_err(|e| CryptoError::Base64Error(e.to_string()))?;

    if key_bytes.len() != 32 {
        return Err(CryptoError::InvalidPrivateKey(format!(
            "Expected 32 bytes, got {}",
            key_bytes.len()
        )));
    }

    let key_array: [u8; 32] = key_bytes
        .try_into()
        .map_err(|_| CryptoError::InvalidPrivateKey("Invalid key length".to_string()))?;

    let signing_key = SigningKey::from_bytes(&key_array);
    let hash = compute_signature_hash(content, metadata);
    let signature = signing_key.sign(&hash);

    Ok(BASE64.encode(signature.to_bytes()))
}

/// Verify a signature against content and metadata.
fn verify_signature(
    content: &str,
    metadata: &FenceMetadata,
    signature_b64: &str,
    public_key_b64: &str,
) -> Result<bool, CryptoError> {
    let key_bytes = BASE64
        .decode(public_key_b64)
        .map_err(|e| CryptoError::Base64Error(e.to_string()))?;

    if key_bytes.len() != 32 {
        return Err(CryptoError::InvalidPublicKey(format!(
            "Expected 32 bytes, got {}",
            key_bytes.len()
        )));
    }

    let key_array: [u8; 32] = key_bytes
        .try_into()
        .map_err(|_| CryptoError::InvalidPublicKey("Invalid key length".to_string()))?;

    let verifying_key = VerifyingKey::from_bytes(&key_array)
        .map_err(|e| CryptoError::InvalidPublicKey(e.to_string()))?;

    let sig_bytes = BASE64
        .decode(signature_b64)
        .map_err(|e| CryptoError::Base64Error(e.to_string()))?;

    if sig_bytes.len() != 64 {
        return Err(CryptoError::InvalidSignature(format!(
            "Expected 64 bytes, got {}",
            sig_bytes.len()
        )));
    }

    let sig_array: [u8; 64] = sig_bytes
        .try_into()
        .map_err(|_| CryptoError::InvalidSignature("Invalid signature length".to_string()))?;

    let signature = Signature::from_bytes(&sig_array);
    let hash = compute_signature_hash(content, metadata);

    Ok(verifying_key.verify(&hash, &signature).is_ok())
}

/// Create a signed fence from content and metadata.
/// Returns the complete Fence object with signature.
#[pyfunction]
#[pyo3(signature = (content, fence_type, rating, source, private_key, timestamp=None))]
pub fn sign_fence(
    content: String,
    fence_type: FenceType,
    rating: FenceRating,
    source: String,
    private_key: String,
    timestamp: Option<String>,
) -> PyResult<Fence> {
    let metadata = FenceMetadata::new(fence_type, rating, source, timestamp);
    let signature = sign_content(&content, &metadata, &private_key)?;
    Ok(Fence::new(content, metadata, signature))
}

/// Verify a fence XML and extract its components.
/// Returns (valid, content, type, rating, source, timestamp) or raises on parse error.
#[pyfunction]
pub fn verify_fence(
    fence_xml: String,
    public_key: String,
) -> PyResult<(bool, String, String, String, String, String)> {
    let (content, metadata, signature) = parse_fence_xml(&fence_xml)?;

    let valid = verify_signature(&content, &metadata, &signature, &public_key).unwrap_or(false);

    Ok((
        valid,
        content,
        metadata.fence_type.as_str().to_string(),
        metadata.rating.as_str().to_string(),
        metadata.source,
        metadata.timestamp,
    ))
}

/// Verify all fences in a fenced prompt string.
/// Returns true only if ALL fences have valid signatures.
/// Per paper Definition 4.5: "If any fence fails verification, the entire prompt is rejected"
#[pyfunction]
pub fn verify_all_fences(prompt: String, public_key: String) -> PyResult<bool> {
    let fences = extract_fence_xmls(&prompt);

    if fences.is_empty() {
        return Ok(false); // No fences found
    }

    for fence_xml in fences {
        let (content, metadata, signature) = parse_fence_xml(&fence_xml)?;

        let valid = verify_signature(&content, &metadata, &signature, &public_key).unwrap_or(false);

        if !valid {
            return Ok(false);
        }
    }

    Ok(true)
}

/// Extract all <sec:fence>...</sec:fence> blocks from a string.
fn extract_fence_xmls(prompt: &str) -> Vec<String> {
    let mut fences = Vec::new();
    let mut remaining = prompt;

    while let Some(start) = remaining.find("<sec:fence ") {
        if let Some(end_offset) = remaining[start..].find("</sec:fence>") {
            let end = start + end_offset + "</sec:fence>".len();
            fences.push(remaining[start..end].to_string());
            remaining = &remaining[end..];
        } else {
            break;
        }
    }

    fences
}

/// Build a complete fenced prompt from multiple fence XMLs.
#[pyfunction]
pub fn build_fenced_prompt(fences: Vec<String>, prepend_awareness: bool) -> String {
    let mut result = String::new();

    if prepend_awareness {
        result.push_str(&crate::fence::py_get_awareness_instructions());
        result.push_str("\n\n");
    }

    for fence in fences {
        result.push_str(&fence);
        result.push('\n');
    }

    result.trim_end().to_string()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_generate_keypair() {
        let (private_key, public_key) = generate_keypair();

        // Keys should be base64 encoded
        let priv_bytes = BASE64.decode(&private_key).unwrap();
        let pub_bytes = BASE64.decode(&public_key).unwrap();

        assert_eq!(priv_bytes.len(), 32);
        assert_eq!(pub_bytes.len(), 32);
    }

    #[test]
    fn test_sign_and_verify() {
        let (private_key, public_key) = generate_keypair();

        let content = "Test content";
        let metadata = FenceMetadata::new(
            FenceType::Instructions,
            FenceRating::Trusted,
            "test".to_string(),
            Some("2025-01-15T10:00:00.000Z".to_string()),
        );

        let signature = sign_content(content, &metadata, &private_key).unwrap();
        let valid = verify_signature(content, &metadata, &signature, &public_key).unwrap();

        assert!(valid);
    }

    #[test]
    fn test_tampered_content_fails() {
        let (private_key, public_key) = generate_keypair();

        let content = "Original content";
        let metadata = FenceMetadata::new(
            FenceType::Content,
            FenceRating::Untrusted,
            "user".to_string(),
            Some("2025-01-15T10:00:00.000Z".to_string()),
        );

        let signature = sign_content(content, &metadata, &private_key).unwrap();

        // Verify with tampered content
        let valid =
            verify_signature("Tampered content", &metadata, &signature, &public_key).unwrap();

        assert!(!valid);
    }

    #[test]
    fn test_extract_fence_xmls() {
        let prompt = r#"<sec:fence rating="trusted" signature="abc" source="sys" timestamp="2025" type="instructions">Hello</sec:fence>
<sec:fence rating="untrusted" signature="def" source="user" timestamp="2025" type="content">World</sec:fence>"#;

        let fences = extract_fence_xmls(prompt);
        assert_eq!(fences.len(), 2);
        assert!(fences[0].contains("Hello"));
        assert!(fences[1].contains("World"));
    }
}
