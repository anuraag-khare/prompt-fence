//! Prompt Fencing Core - Rust implementation for Python SDK.
//!
//! This crate provides the cryptographic foundation for the Prompt Fencing SDK,
//! implementing Ed25519 signing and verification for LLM prompt security boundaries.

use pyo3::create_exception;
use pyo3::prelude::*;

pub mod crypto;
pub mod fence;

create_exception!(_core, FenceError, pyo3::exceptions::PyValueError);
create_exception!(_core, CryptoError, pyo3::exceptions::PyValueError);

/// Python module definition.
/// Module is named `_core` to be imported as `prompt_fencing._core`
#[pymodule]
fn _core(py: Python, m: &Bound<'_, PyModule>) -> PyResult<()> {
    // Fence types
    m.add_class::<fence::FenceType>()?;
    m.add_class::<fence::FenceRating>()?;
    m.add_class::<fence::FenceMetadata>()?;
    m.add_class::<fence::Fence>()?;

    // Crypto functions
    m.add_function(wrap_pyfunction!(crypto::generate_keypair, m)?)?;
    m.add_function(wrap_pyfunction!(crypto::sign_fence, m)?)?;
    m.add_function(wrap_pyfunction!(crypto::verify_fence, m)?)?;
    m.add_function(wrap_pyfunction!(crypto::verify_all_fences, m)?)?;
    m.add_function(wrap_pyfunction!(crypto::build_fenced_prompt, m)?)?;

    // Awareness instructions
    m.add_function(wrap_pyfunction!(fence::py_get_awareness_instructions, m)?)?;
    m.add_function(wrap_pyfunction!(fence::py_set_awareness_instructions, m)?)?;

    // Exceptions
    m.add("FenceError", py.get_type::<FenceError>())?;
    m.add("CryptoError", py.get_type::<CryptoError>())?;

    Ok(())
}
