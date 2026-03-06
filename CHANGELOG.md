# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/), and this project adheres to [Semantic Versioning](https://semver.org/).

## [0.1.0] - 2026-03-01

### Added

- Configuration vulnerability scanner with 7 detection methods and 0-100 scoring
- JWT-based credential lifecycle manager (issue, rotate, revoke) with audit logging
- YAML-driven runtime policy engine with rate limiting and data-sensitivity gates
- Statistical behavioral anomaly detector with 12 detection methods (rug-pull, exfiltration, rate spike, privilege escalation, reconnaissance, persistence, defense evasion, lateral movement, C2 beaconing, supply chain)
- Real-time MCP security proxy with JSON-RPC interception and live traffic monitoring
- Penetration testing engine with 11 SAFE-MCP attack simulations (reconnaissance, persistence, defense evasion, lateral movement, C2 beaconing, supply chain, rug pull, data exfiltration, privilege escalation, rate spike, policy bypass)
- LLM-powered analysis: config analysis, anomaly explanation, policy generation, self-healing (Anthropic, OpenAI, Gemini, Ollama)
- Cloud dashboard (React/Vite) with fleet monitoring, alerting, gateway management, and pentest UI
- Adaptive behavioral baselines with pattern learning and feedback loop
- ML-based anomaly detection with Isolation Forest and clustering (optional `[ml]` extra)
- CLI with `scan`, `credential`, `policy`, `monitor`, `report`, `pentest`, `proxy`, `cloud`, `llm`, `adaptive`, and `feedback` commands
- CLI LLM commands support environment variable fallback for API keys (BYOK)
- Sample MCP server configurations (vulnerable and secure)
- Default security policy template
- Comprehensive test suite (198 tests)
- GitHub Actions CI (lint, type-check, test on Python 3.10-3.12, dashboard build)
- Pre-commit hooks configuration
- Apache 2.0 license

### Changed

- Production hardening: fetch timeouts, stable React list keys, error state handling, accessibility labels
