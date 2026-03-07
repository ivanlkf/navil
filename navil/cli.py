"""
Navil CLI

Command-line interface for MCP security scanning, credential management, policy evaluation,
and anomaly detection.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from navil._compat import has_llm, has_ml
from navil.anomaly_detector import BehavioralAnomalyDetector
from navil.credential_manager import CredentialManager, CredentialStatus
from navil.policy_engine import PolicyEngine
from navil.scanner import MCPSecurityScanner

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class MCPGuardianCLI:
    """CLI interface for Navil (MCP Guardian)."""

    def __init__(self) -> None:
        """Initialize CLI."""
        self.scanner = MCPSecurityScanner()
        self.credential_manager = CredentialManager()
        self.policy_engine = PolicyEngine()
        self.anomaly_detector = BehavioralAnomalyDetector()

    def scan_command(self, args: argparse.Namespace) -> int:
        """Handle scan command."""
        config_path = args.config_path

        if not Path(config_path).exists():
            print(f"Error: Configuration file not found: {config_path}", file=sys.stderr)
            return 1

        print(f"\nScanning MCP configuration: {config_path}")
        print("-" * 60)

        result = self.scanner.scan(config_path)

        # Display results
        print(f"\nStatus: {result.get('status', 'unknown')}")
        print(f"Security Score: {result.get('security_score', 0)}/100")
        print(f"Total Vulnerabilities: {result.get('total_vulnerabilities', 0)}")

        # Show vulnerabilities by level
        vulns_by_level = result.get("vulnerabilities_by_level", {})
        if vulns_by_level:
            print("\nVulnerabilities by Severity:")
            for level, count in vulns_by_level.items():
                if count > 0:
                    print(f"  {level}: {count}")

        # Show vulnerabilities
        vulns = result.get("vulnerabilities", [])
        if vulns:
            print("\nDetailed Vulnerabilities:")
            for i, vuln in enumerate(vulns, 1):
                print(f"\n  {i}. {vuln.get('title')}")
                print(f"     Risk Level: {vuln.get('risk_level')}")
                print(f"     Description: {vuln.get('description')}")
                print(f"     Remediation: {vuln.get('remediation')}")

        # Show recommendations
        print(f"\nRecommendation: {result.get('recommendation', 'N/A')}")

        # Save report if requested
        if args.output:
            output_path = Path(args.output)
            with open(output_path, "w") as f:
                json.dump(result, f, indent=2)
            print(f"\nReport saved to: {output_path}")

        return 0 if result.get("security_score", 0) >= 60 else 1

    def credential_issue_command(self, args: argparse.Namespace) -> int:
        """Handle credential issue command."""
        agent_name = args.agent
        scope = args.scope
        ttl = int(args.ttl)

        print(f"\nIssuing credential for agent: {agent_name}")
        print(f"Scope: {scope}")
        print(f"TTL: {ttl} seconds")
        print("-" * 60)

        try:
            result = self.credential_manager.issue_credential(
                agent_name=agent_name, scope=scope, ttl_seconds=ttl
            )

            print("\nCredential Issued Successfully")
            print(f"Token ID: {result['token_id']}")
            print(f"Agent: {result['agent_name']}")
            print(f"Scope: {result['scope']}")
            print(f"Issued At: {result['issued_at']}")
            print(f"Expires At: {result['expires_at']}")
            print("\nToken (save this securely):")
            print(result["token"])

            return 0
        except Exception as e:
            print(f"Error: {e!s}", file=sys.stderr)
            return 1

    def credential_revoke_command(self, args: argparse.Namespace) -> int:
        """Handle credential revoke command."""
        token_id = args.token_id

        print(f"\nRevoking credential: {token_id}")
        print("-" * 60)

        try:
            self.credential_manager.revoke_credential(token_id, reason="CLI revocation")
            print("Credential revoked successfully")
            return 0
        except ValueError as e:
            print(f"Error: {e!s}", file=sys.stderr)
            return 1

    def credential_list_command(self, args: argparse.Namespace) -> int:
        """Handle credential list command."""
        agent_name = args.agent
        status = args.status

        print("\nListing Credentials")
        print("-" * 60)

        credentials = self.credential_manager.list_credentials(agent_name=agent_name, status=status)

        if not credentials:
            print("No credentials found")
            return 0

        print(f"{'Token ID':<20} {'Agent':<15} {'Status':<10} {'Expires At':<20}")
        print("-" * 65)

        for cred in credentials:
            print(
                f"{cred['token_id']:<20} {cred['agent_name']:<15} "
                f"{cred['status']:<10} {cred['expires_at']:<20}"
            )

        return 0

    def policy_check_command(self, args: argparse.Namespace) -> int:
        """Handle policy check command."""
        tool_name = args.tool
        agent_name = args.agent
        action = args.action

        print("\nChecking Policy")
        print(f"Agent: {agent_name}, Tool: {tool_name}, Action: {action}")
        print("-" * 60)

        allowed, reason = self.policy_engine.check_tool_call(
            agent_name=agent_name, tool_name=tool_name, action=action
        )

        status = "ALLOWED" if allowed else "DENIED"
        print(f"\nPolicy Decision: {status}")
        print(f"Reason: {reason}")

        return 0 if allowed else 1

    def monitor_start_command(self, args: argparse.Namespace) -> int:
        """Handle monitor start command."""
        print("\nStarting Monitoring Mode")
        print("-" * 60)
        print("Monitoring active. Press Ctrl+C to stop.")
        print("\nMonitoring features enabled:")
        print("  - Real-time policy evaluation")
        print("  - Behavioral anomaly detection")
        print("  - Credential usage tracking")
        print("  - Rate limit enforcement")

        print("\nNote: This is a demo. In production, this would start a monitoring service.")

        return 0

    def report_command(self, args: argparse.Namespace) -> int:
        """Handle report generation command."""
        print("\nGenerating Security Report")
        print("-" * 60)

        report = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "summary": {
                "total_credentials": len(self.credential_manager.credentials),
                "active_credentials": sum(
                    1
                    for c in self.credential_manager.credentials.values()
                    if c.status == CredentialStatus.ACTIVE
                ),
                "total_alerts": len(self.anomaly_detector.alerts),
                "policy_decisions": len(self.policy_engine.decisions_log),
            },
            "credentials": self.credential_manager.list_credentials(),
            "anomalies": self.anomaly_detector.get_alerts(),
            "policy_decisions": self.policy_engine.get_decisions_log()[-10:],
        }

        print(json.dumps(report, indent=2))

        if args.output:
            output_path = Path(args.output)
            with open(output_path, "w") as f:
                json.dump(report, f, indent=2)
            print(f"\nReport saved to: {output_path}")

        return 0

    # ── Adaptive commands ───────────────────────────────────────

    def adaptive_status_command(self, args: argparse.Namespace) -> int:
        """Show adaptive baseline status for an agent."""
        agent = args.agent
        info = self.anomaly_detector.get_adaptive_baseline(agent)
        print(f"\nAdaptive Baseline for: {agent}")
        print("-" * 60)
        print(json.dumps(info, indent=2))
        return 0

    def adaptive_reset_command(self, args: argparse.Namespace) -> int:
        """Reset adaptive baseline for an agent."""
        agent = args.agent
        from navil.adaptive.baselines import AgentAdaptiveBaseline

        self.anomaly_detector.adaptive_baselines[agent] = AgentAdaptiveBaseline(agent_name=agent)
        print(f"Adaptive baseline reset for agent: {agent}")
        return 0

    def adaptive_export_command(self, args: argparse.Namespace) -> int:
        """Export all adaptive baselines to JSON."""
        data = {name: bl.to_dict() for name, bl in self.anomaly_detector.adaptive_baselines.items()}
        output = json.dumps(data, indent=2)
        if args.output:
            Path(args.output).write_text(output)
            print(f"Exported baselines to {args.output}")
        else:
            print(output)
        return 0

    # ── Feedback commands ───────────────────────────────────────

    def feedback_submit_command(self, args: argparse.Namespace) -> int:
        """Submit feedback on an anomaly alert."""
        from navil.adaptive.feedback import FeedbackLoop

        loop = self.anomaly_detector.feedback_loop or FeedbackLoop()
        loop.submit_feedback(
            alert_timestamp=datetime.now(timezone.utc).isoformat(),
            anomaly_type="manual",
            agent_name=args.alert_id,
            verdict=args.verdict,
            operator_notes=args.notes or "",
        )
        print(f"Feedback recorded: {args.verdict} for alert {args.alert_id}")
        return 0

    def feedback_stats_command(self, args: argparse.Namespace) -> int:
        """Show feedback statistics."""
        from navil.adaptive.feedback import FeedbackLoop

        loop = self.anomaly_detector.feedback_loop or FeedbackLoop()
        stats = loop.get_stats()
        print("\nFeedback Statistics")
        print("-" * 60)
        print(json.dumps(stats, indent=2))
        return 0

    # ── ML commands ─────────────────────────────────────────────

    def ml_train_command(self, args: argparse.Namespace) -> int:
        """Train the isolation forest model on recorded invocations."""
        if not has_ml():
            print(
                "Error: ML dependencies not installed. Run: pip install navil[ml]",
                file=sys.stderr,
            )
            return 1

        from navil.ml.isolation_forest import IsolationForestDetector

        invocations = self.anomaly_detector.invocations
        if len(invocations) < 10:
            print("Error: Need at least 10 recorded invocations to train.", file=sys.stderr)
            return 1

        detector = IsolationForestDetector()
        detector.train(invocations)
        if args.output:
            detector.save(args.output)
            print(f"Model saved to {args.output}")
        print(f"Trained isolation forest on {len(invocations)} invocations.")
        return 0

    def ml_status_command(self, args: argparse.Namespace) -> int:
        """Show ML model status."""
        if not has_ml():
            print(
                "Error: ML dependencies not installed. Run: pip install navil[ml]",
                file=sys.stderr,
            )
            return 1

        print("\nML Model Status")
        print("-" * 60)
        print("  scikit-learn: installed")
        print(f"  Recorded invocations: {len(self.anomaly_detector.invocations)}")
        print(f"  Adaptive baselines tracked: {len(self.anomaly_detector.adaptive_baselines)}")
        return 0

    def ml_cluster_command(self, args: argparse.Namespace) -> int:
        """Cluster agents by behavior."""
        if not has_ml():
            print(
                "Error: ML dependencies not installed. Run: pip install navil[ml]",
                file=sys.stderr,
            )
            return 1

        from navil.ml.clustering import AgentClusterer

        invocations = self.anomaly_detector.invocations
        if not invocations:
            print("Error: No recorded invocations to cluster.", file=sys.stderr)
            return 1

        # Group invocations by agent
        profiles: dict[str, list] = {}
        for inv in invocations:
            profiles.setdefault(inv.agent_name, []).append(inv)

        n_clusters = min(int(args.n_clusters), len(profiles))
        clusterer = AgentClusterer(n_clusters=n_clusters)
        result = clusterer.fit(profiles)
        print("\nAgent Clustering Results")
        print("-" * 60)
        print(json.dumps(result, indent=2, default=str))
        return 0

    # ── LLM commands ────────────────────────────────────────────

    @staticmethod
    def _resolve_llm_api_key(args: argparse.Namespace) -> str | None:
        """Resolve API key from --api-key flag or environment variables."""
        if args.api_key:
            return str(args.api_key)
        env_map: dict[str, str] = {
            "anthropic": "ANTHROPIC_API_KEY",
            "openai": "OPENAI_API_KEY",
            "gemini": "GEMINI_API_KEY",
            "openai_compatible": "OPENAI_API_KEY",
        }
        env_var = env_map.get(args.provider)
        if env_var:
            key = os.environ.get(env_var)
            if key:
                return key
        if args.provider == "ollama":
            return "ollama"
        return None

    def llm_analyze_config_command(self, args: argparse.Namespace) -> int:
        """Analyze MCP config using LLM."""
        if not has_llm():
            print(
                "Error: LLM dependencies not installed. Run: pip install navil[llm]",
                file=sys.stderr,
            )
            return 1

        from navil.llm.analyzer import LLMAnalyzer
        from navil.llm.client import LLMClient

        config_path = Path(args.config_path)
        if not config_path.exists():
            print(f"Error: File not found: {config_path}", file=sys.stderr)
            return 1

        config = json.loads(config_path.read_text())
        api_key = self._resolve_llm_api_key(args)
        if not api_key:
            print(
                f"Error: No API key. Pass --api-key or set "
                f"{args.provider.upper()}_API_KEY env var.",
                file=sys.stderr,
            )
            return 1
        client = LLMClient(
            provider=args.provider,
            api_key=api_key,
            model=args.model or None,
            base_url=args.base_url,
        )
        analyzer = LLMAnalyzer(client=client)
        result = analyzer.analyze_config(config)
        print("\nLLM Config Analysis")
        print("-" * 60)
        print(json.dumps(result, indent=2))
        return 0

    def llm_explain_anomaly_command(self, args: argparse.Namespace) -> int:
        """Explain an anomaly using LLM."""
        if not has_llm():
            print(
                "Error: LLM dependencies not installed. Run: pip install navil[llm]",
                file=sys.stderr,
            )
            return 1

        from navil.llm.analyzer import LLMAnalyzer
        from navil.llm.client import LLMClient

        anomaly_data = json.loads(args.anomaly_json)
        api_key = self._resolve_llm_api_key(args)
        if not api_key:
            print(
                f"Error: No API key. Pass --api-key or set "
                f"{args.provider.upper()}_API_KEY env var.",
                file=sys.stderr,
            )
            return 1
        client = LLMClient(
            provider=args.provider,
            api_key=api_key,
            model=args.model or None,
            base_url=args.base_url,
        )
        analyzer = LLMAnalyzer(client=client)
        result = analyzer.explain_anomaly(anomaly_data)
        print("\nLLM Anomaly Explanation")
        print("-" * 60)
        print(json.dumps(result, indent=2))
        return 0

    def llm_generate_policy_command(self, args: argparse.Namespace) -> int:
        """Generate policy YAML from natural language."""
        if not has_llm():
            print(
                "Error: LLM dependencies not installed. Run: pip install navil[llm]",
                file=sys.stderr,
            )
            return 1

        import yaml

        from navil.llm.client import LLMClient
        from navil.llm.policy_gen import PolicyGenerator

        api_key = self._resolve_llm_api_key(args)
        if not api_key:
            print(
                f"Error: No API key. Pass --api-key or set "
                f"{args.provider.upper()}_API_KEY env var.",
                file=sys.stderr,
            )
            return 1
        client = LLMClient(
            provider=args.provider,
            api_key=api_key,
            model=args.model or None,
            base_url=args.base_url,
        )
        gen = PolicyGenerator(client=client)
        policy = gen.generate(args.description)
        output = yaml.dump(policy, default_flow_style=False)
        if args.output:
            Path(args.output).write_text(output)
            print(f"Policy saved to {args.output}")
        else:
            print("\nGenerated Policy")
            print("-" * 60)
            print(output)
        return 0

    def llm_suggest_healing_command(self, args: argparse.Namespace) -> int:
        """Suggest self-healing remediations using LLM."""
        if not has_llm():
            print(
                "Error: LLM dependencies not installed. Run: pip install navil[llm]",
                file=sys.stderr,
            )
            return 1

        from navil.llm.client import LLMClient
        from navil.llm.self_healing import SelfHealingEngine

        api_key = self._resolve_llm_api_key(args)
        if not api_key:
            print(
                f"Error: No API key. Pass --api-key or set "
                f"{args.provider.upper()}_API_KEY env var.",
                file=sys.stderr,
            )
            return 1
        client = LLMClient(
            provider=args.provider,
            api_key=api_key,
            model=args.model or None,
            base_url=args.base_url,
        )
        engine = SelfHealingEngine(client=client)
        alerts = self.anomaly_detector.get_alerts()
        policy = self.policy_engine.policy
        result = engine.suggest_remediation(alerts, policy)
        print("\nSelf-Healing Suggestions")
        print("-" * 60)
        print(json.dumps(result, indent=2))
        return 0


def _pentest_print_report(report: dict) -> None:  # type: ignore[type-arg]
    """Pretty-print a pentest report to the terminal."""
    print("\n  Navil Pentest \u2014 SAFE-MCP Attack Simulation")
    print("  \u2550" * 51)
    print()
    print(f"  {'Scenario':<24} {'Verdict':<10} {'Alerts':<8} {'Severity'}")
    sep = "\u2500"
    print(f"  {sep * 24} {sep * 10} {sep * 8} {sep * 10}")

    for r in report.get("results", []):
        verdict = r.get("verdict", "?")
        mark = "\u2713" if verdict == "PASS" else "\u2717" if verdict == "FAIL" else "~"
        alerts_count = len(r.get("alerts_fired", []))
        severity = r.get("severity", "\u2014")
        print(f"  {r['scenario']:<24} {mark} {verdict:<8} {alerts_count:<8} {severity}")

    total = report.get("total_scenarios", 0)
    passed = report.get("passed", 0)
    rate = report.get("detection_rate", 0.0)
    print()
    print(f"  Detection Rate: {passed}/{total} ({rate}%)")
    print()


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Navil - Supply Chain Security for MCP Servers",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  navil scan config.json
  navil credential issue --agent my-agent --scope "read:tools" --ttl 3600
  navil credential revoke --token-id cred_abc123
  navil policy check --tool file_system --agent my-agent --action read
  navil monitor start
  navil report
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Scan command
    scan_parser = subparsers.add_parser("scan", help="Scan MCP configuration file")
    scan_parser.add_argument("config_path", help="Path to MCP configuration file (JSON)")
    scan_parser.add_argument("-o", "--output", help="Output file for JSON report", default=None)
    scan_parser.set_defaults(func=lambda cli, args: cli.scan_command(args))

    # Credential commands
    credential_parser = subparsers.add_parser("credential", help="Manage credentials")
    credential_subparsers = credential_parser.add_subparsers(dest="credential_command")

    # Issue credential
    issue_parser = credential_subparsers.add_parser("issue", help="Issue new credential")
    issue_parser.add_argument("--agent", required=True, help="Agent name")
    issue_parser.add_argument("--scope", required=True, help="Permission scope")
    issue_parser.add_argument(
        "--ttl", default="3600", help="Time to live in seconds (default: 3600)"
    )
    issue_parser.set_defaults(func=lambda cli, args: cli.credential_issue_command(args))

    # Revoke credential
    revoke_parser = credential_subparsers.add_parser("revoke", help="Revoke credential")
    revoke_parser.add_argument("--token-id", required=True, help="Token ID to revoke")
    revoke_parser.set_defaults(func=lambda cli, args: cli.credential_revoke_command(args))

    # List credentials
    list_parser = credential_subparsers.add_parser("list", help="List credentials")
    list_parser.add_argument("--agent", help="Filter by agent name", default=None)
    list_parser.add_argument("--status", help="Filter by status", default=None)
    list_parser.set_defaults(func=lambda cli, args: cli.credential_list_command(args))

    # Policy command
    policy_parser = subparsers.add_parser("policy", help="Evaluate security policies")
    policy_subparsers = policy_parser.add_subparsers(dest="policy_command")

    check_parser = policy_subparsers.add_parser("check", help="Check policy decision")
    check_parser.add_argument("--tool", required=True, help="Tool name")
    check_parser.add_argument("--agent", required=True, help="Agent name")
    check_parser.add_argument("--action", required=True, help="Action (read/write/delete)")
    check_parser.set_defaults(func=lambda cli, args: cli.policy_check_command(args))

    # Monitor command
    monitor_parser = subparsers.add_parser("monitor", help="Start monitoring")
    monitor_subparsers = monitor_parser.add_subparsers(dest="monitor_command")
    start_parser = monitor_subparsers.add_parser("start", help="Start monitoring")
    start_parser.set_defaults(func=lambda cli, args: cli.monitor_start_command(args))

    # Report command
    report_parser = subparsers.add_parser("report", help="Generate security report")
    report_parser.add_argument("-o", "--output", help="Output file for JSON report", default=None)
    report_parser.set_defaults(func=lambda cli, args: cli.report_command(args))

    # ── Adaptive commands ───────────────────────────────────────
    adaptive_parser = subparsers.add_parser("adaptive", help="Manage adaptive baselines")
    adaptive_sub = adaptive_parser.add_subparsers(dest="adaptive_command")

    adaptive_status = adaptive_sub.add_parser("status", help="Show baseline status")
    adaptive_status.add_argument("--agent", required=True, help="Agent name")
    adaptive_status.set_defaults(func=lambda cli, args: cli.adaptive_status_command(args))

    adaptive_reset = adaptive_sub.add_parser("reset", help="Reset baseline")
    adaptive_reset.add_argument("--agent", required=True, help="Agent name")
    adaptive_reset.set_defaults(func=lambda cli, args: cli.adaptive_reset_command(args))

    adaptive_export = adaptive_sub.add_parser("export", help="Export baselines")
    adaptive_export.add_argument("-o", "--output", help="Output file", default=None)
    adaptive_export.set_defaults(func=lambda cli, args: cli.adaptive_export_command(args))

    # ── Feedback commands ───────────────────────────────────────
    feedback_parser = subparsers.add_parser("feedback", help="Submit operator feedback on alerts")
    feedback_sub = feedback_parser.add_subparsers(dest="feedback_command")

    feedback_submit = feedback_sub.add_parser("submit", help="Submit feedback")
    feedback_submit.add_argument("--alert-id", required=True, help="Alert ID")
    feedback_submit.add_argument(
        "--verdict",
        required=True,
        choices=["confirmed", "dismissed", "escalated"],
        help="Feedback verdict",
    )
    feedback_submit.add_argument("--notes", default="", help="Operator notes")
    feedback_submit.set_defaults(func=lambda cli, args: cli.feedback_submit_command(args))

    feedback_stats = feedback_sub.add_parser("stats", help="Show feedback stats")
    feedback_stats.set_defaults(func=lambda cli, args: cli.feedback_stats_command(args))

    # ── ML commands ─────────────────────────────────────────────
    ml_parser = subparsers.add_parser(
        "ml", help="ML-powered anomaly detection (requires navil[ml])"
    )
    ml_sub = ml_parser.add_subparsers(dest="ml_command")

    ml_train = ml_sub.add_parser("train", help="Train isolation forest model")
    ml_train.add_argument("-o", "--output", help="Save model to file", default=None)
    ml_train.set_defaults(func=lambda cli, args: cli.ml_train_command(args))

    ml_status = ml_sub.add_parser("status", help="Show ML status")
    ml_status.set_defaults(func=lambda cli, args: cli.ml_status_command(args))

    ml_cluster = ml_sub.add_parser("cluster", help="Cluster agents by behavior")
    ml_cluster.add_argument("--n-clusters", default="3", help="Number of clusters (default: 3)")
    ml_cluster.set_defaults(func=lambda cli, args: cli.ml_cluster_command(args))

    # ── LLM commands ────────────────────────────────────────────
    llm_parser = subparsers.add_parser("llm", help="LLM-powered analysis (requires navil[llm])")
    llm_sub = llm_parser.add_subparsers(dest="llm_command")

    # Shared LLM args helper
    def _add_llm_args(p: argparse.ArgumentParser) -> None:
        p.add_argument(
            "--provider",
            default="anthropic",
            choices=["anthropic", "openai", "gemini", "ollama", "openai_compatible"],
            help="LLM provider (default: anthropic)",
        )
        p.add_argument(
            "--api-key",
            default=None,
            help="API key (or set ANTHROPIC_API_KEY / OPENAI_API_KEY / GEMINI_API_KEY env var)",
        )
        p.add_argument("--model", default=None, help="Model name override")
        p.add_argument(
            "--base-url", default=None, help="Custom API base URL (for ollama or openai_compatible)"
        )

    llm_analyze = llm_sub.add_parser("analyze-config", help="Analyze config with LLM")
    llm_analyze.add_argument("config_path", help="Path to MCP config (JSON)")
    _add_llm_args(llm_analyze)
    llm_analyze.set_defaults(func=lambda cli, args: cli.llm_analyze_config_command(args))

    llm_explain = llm_sub.add_parser("explain-anomaly", help="Explain anomaly with LLM")
    llm_explain.add_argument("anomaly_json", help="Anomaly data as JSON string")
    _add_llm_args(llm_explain)
    llm_explain.set_defaults(func=lambda cli, args: cli.llm_explain_anomaly_command(args))

    llm_genpol = llm_sub.add_parser("generate-policy", help="Generate policy from description")
    llm_genpol.add_argument("description", help="Natural language policy description")
    llm_genpol.add_argument("-o", "--output", help="Save policy YAML to file", default=None)
    _add_llm_args(llm_genpol)
    llm_genpol.set_defaults(func=lambda cli, args: cli.llm_generate_policy_command(args))

    llm_heal = llm_sub.add_parser("suggest-healing", help="Suggest self-healing actions")
    _add_llm_args(llm_heal)
    llm_heal.set_defaults(func=lambda cli, args: cli.llm_suggest_healing_command(args))

    # ── Proxy commands ─────────────────────────────────────────
    proxy_parser = subparsers.add_parser("proxy", help="MCP security proxy (requires navil[cloud])")
    proxy_sub = proxy_parser.add_subparsers(dest="proxy_command")

    proxy_start = proxy_sub.add_parser("start", help="Start the MCP security proxy")
    proxy_start.add_argument(
        "--target", required=True, help="Upstream MCP server URL (e.g., http://localhost:3000)"
    )
    proxy_start.add_argument("--port", default="9090", help="Port to listen on (default: 9090)")
    proxy_start.add_argument("--host", default="0.0.0.0", help="Host to bind (default: 0.0.0.0)")
    proxy_start.add_argument("--policy", default=None, help="Path to policy YAML file")
    proxy_start.add_argument(
        "--no-auth", action="store_true", help="Disable JWT authentication requirement"
    )

    def _proxy_start(cli: MCPGuardianCLI, args: argparse.Namespace) -> int:
        try:
            from navil.proxy import MCPSecurityProxy, create_proxy_app
        except ImportError:
            print(
                "Error: Cloud dependencies not installed. Run: pip install navil[cloud]",
                file=sys.stderr,
            )
            return 1
        import uvicorn

        # Load policy if provided
        if args.policy:
            cli.policy_engine.policy_file = Path(args.policy)
            cli.policy_engine._load_policy()

        proxy = MCPSecurityProxy(
            target_url=args.target,
            policy_engine=cli.policy_engine,
            anomaly_detector=cli.anomaly_detector,
            credential_manager=cli.credential_manager,
            require_auth=not args.no_auth,
        )
        app = create_proxy_app(proxy)
        port = int(args.port)
        print("\n  Navil MCP Security Proxy")
        print(f"  Target: {args.target}")
        print(f"  Listening: http://{args.host}:{port}")
        print(f"  Auth: {'required' if not args.no_auth else 'disabled'}")
        print(f"  Health: http://{args.host}:{port}/health\n")
        uvicorn.run(app, host=args.host, port=port, log_level="info")
        return 0

    proxy_start.set_defaults(func=_proxy_start)

    # ── Pentest commands ────────────────────────────────────────
    pentest_parser = subparsers.add_parser(
        "pentest", help="Simulate SAFE-MCP attack patterns against detectors"
    )
    pentest_parser.add_argument(
        "--scenario",
        default=None,
        help="Run a specific scenario (e.g., reconnaissance, persistence, c2_beaconing). "
        "Omit to run all 11 scenarios.",
    )
    pentest_parser.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        help="Output raw JSON instead of formatted table",
    )
    pentest_parser.add_argument("-o", "--output", default=None, help="Save JSON report to file")

    def _pentest_run(cli: MCPGuardianCLI, args: argparse.Namespace) -> int:
        from navil.pentest import SCENARIOS, PentestEngine

        engine = PentestEngine(cli.anomaly_detector, cli.policy_engine)

        if args.scenario:
            if args.scenario not in SCENARIOS:
                print(
                    f"Unknown scenario: {args.scenario}\nAvailable: {', '.join(SCENARIOS.keys())}",
                    file=sys.stderr,
                )
                return 1
            result = engine.run_scenario(args.scenario)
            report = {
                "status": "completed",
                "total_scenarios": 1,
                "passed": 1 if result.verdict == "PASS" else 0,
                "failed": 1 if result.verdict == "FAIL" else 0,
                "partial": 1 if result.verdict == "PARTIAL" else 0,
                "detection_rate": 100.0 if result.verdict == "PASS" else 0.0,
                "results": [result.to_dict()],
            }
        else:
            report = engine.run_all()

        if args.json_output:
            import json as _json

            print(_json.dumps(report, indent=2))
        else:
            _pentest_print_report(report)

        if args.output:
            import json as _json

            with open(args.output, "w") as f:
                _json.dump(report, f, indent=2)
            print(f"\n  Report saved to {args.output}")

        return 0 if report["failed"] == 0 else 1

    pentest_parser.set_defaults(func=_pentest_run)

    # ── Cloud commands ──────────────────────────────────────────
    cloud_parser = subparsers.add_parser(
        "cloud", help="Launch Navil Cloud dashboard (requires navil[cloud])"
    )
    cloud_sub = cloud_parser.add_subparsers(dest="cloud_command")

    cloud_serve = cloud_sub.add_parser("serve", help="Start the dashboard server")
    cloud_serve.add_argument("--port", default="8484", help="Port to serve on (default: 8484)")
    cloud_serve.add_argument("--host", default="0.0.0.0", help="Host to bind (default: 0.0.0.0)")
    cloud_serve.add_argument("--no-demo", action="store_true", help="Don't seed demo data")

    def _cloud_serve(cli: MCPGuardianCLI, args: argparse.Namespace) -> int:
        try:
            from navil.cloud.app import create_app
        except ImportError:
            print(
                "Error: Cloud dependencies not installed. Run: pip install navil[cloud]",
                file=sys.stderr,
            )
            return 1
        import uvicorn

        app = create_app(with_demo=not args.no_demo)
        print(f"\n  Navil Cloud starting at http://localhost:{args.port}\n")
        uvicorn.run(app, host=args.host, port=int(args.port), log_level="info")
        return 0

    cloud_serve.set_defaults(func=_cloud_serve)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    cli = MCPGuardianCLI()

    try:
        if hasattr(args, "func"):
            return int(args.func(cli, args))
        else:
            parser.print_help()
            return 1
    except Exception as e:
        logger.error(f"Error: {e!s}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
