# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/), and this project adheres to [Semantic Versioning](https://semver.org/).

## [0.1.0] - 2026-03-01

### Added

- Configuration vulnerability scanner with 7 detection methods and 0-100 scoring
- JWT-based credential lifecycle manager (issue, rotate, revoke) with audit logging
- YAML-driven runtime policy engine with rate limiting and data-sensitivity gates
- Statistical behavioral anomaly detector (rug-pull, exfiltration, rate spike, privilege escalation)
- CLI with `scan`, `credential`, `policy`, `monitor`, and `report` commands
- Sample MCP server configurations (vulnerable and secure)
- Default security policy template
- Comprehensive test suite (50+ tests)
- GitHub Actions CI (lint, type-check, test on Python 3.10-3.12)
- Pre-commit hooks configuration
- Apache 2.0 license
