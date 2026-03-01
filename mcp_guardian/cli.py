"""
Navil CLI

Command-line interface for MCP security scanning, credential management, policy evaluation,
and anomaly detection.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

from mcp_guardian.anomaly_detector import BehavioralAnomalyDetector
from mcp_guardian.credential_manager import CredentialManager, CredentialStatus
from mcp_guardian.policy_engine import PolicyEngine
from mcp_guardian.scanner import MCPSecurityScanner

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

        credentials = self.credential_manager.list_credentials(
            agent_name=agent_name, status=status
        )

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
    scan_parser.add_argument(
        "-o", "--output", help="Output file for JSON report", default=None
    )
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
    report_parser.add_argument(
        "-o", "--output", help="Output file for JSON report", default=None
    )
    report_parser.set_defaults(func=lambda cli, args: cli.report_command(args))

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    cli = MCPGuardianCLI()

    try:
        if hasattr(args, "func"):
            return args.func(cli, args)
        else:
            parser.print_help()
            return 1
    except Exception as e:
        logger.error(f"Error: {e!s}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
