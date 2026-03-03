# Changelog

All notable changes to this project will be documented in this file.

Changelog entry for v0.5.0

v0.5.0 — Stable Baseline Before Performance Phase (2026‑03‑03)
This release marks the first fully stable and internally consistent version of the HL7 v2 engine. All components—MLLP listener, parser, validator, router, and SQLite persistence—now operate reliably end‑to‑end, and the complete test suite passes without errors. This version serves as the foundation for the upcoming performance and concurrency improvements.
Highlights
• 	All tests pass across parsing, validation, routing, MLLP ingestion, and integration scenarios.
• 	Project paths fully normalized after migration out of Dropbox, eliminating stale imports and environment contamination.
• 	Validator and routing configuration now consistently loaded from config/.
• 	Database initialization corrected to use project‑relative paths (data/seed/ and data/hl7_messages.db).
• 	Test suite updated to reflect the new project layout and configuration structure.
• 	Cleaned up environment, removed legacy editable installs, and ensured reproducible imports.
Fixes and cleanup
• 	Removed absolute paths and replaced them with robust Path‑based resolution.
• 	Corrected validator initialization to avoid double‑prefixing config/.
• 	Ensured seed database is copied only when missing and from the correct location.
• 	Updated routing schema test to reference config/routes.yaml.
• 	Eliminated stale .pth and finder artifacts from previous editable installs.
• 	Reinstalled package cleanly to ensure correct module resolution.
Status
This version is functionally complete and stable but not yet optimized. It is the reference point for the upcoming performance phase, which will focus on:
• 	SQLite WAL mode and write optimization
• 	MLLP concurrency (threaded or async)
• 	Reduced file I/O overhead
• 	Logging performance tuning