“I like the idea to expose parsing as a public API and support multiple backends.”

This is a great future direction.
When you’re ready, we can:
- Extract parsing into hl7engine/parsing/
- Add a backend registry
- Support HL7apy, custom parser, or even a Rust-backed parser
- Add normalization hooks
- Add a stable public API
