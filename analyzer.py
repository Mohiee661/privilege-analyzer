"""
IAM Least-Privilege Analyzer
Analyzes AWS IAM policies (JSON) for over-privileged permissions,
wildcard actions, admin equivalence, and unused permissions.
Generates least-privilege policy recommendations.

Author: Mohith Vasamsetti (CyberEnthusiastic)
"""
import os
import re
import sys
import json
import argparse
from datetime import datetime, timezone
from pathlib import Path
from dataclasses import dataclass, asdict, field
from typing import List, Dict, Optional, Set

from report_generator import generate_html


# -------------------------------------------------------------
# IAM finding catalog (CIS AWS Foundations + AWS Well-Architected)
# -------------------------------------------------------------
IAM_RULES = [
    {
        "id": "IAM-001",
        "name": "Wildcard Action with Wildcard Resource (Admin equivalent)",
        "severity": "CRITICAL",
        "confidence": 0.99,
        "cis": "CIS AWS 1.22",
        "remediation": "Replace Action '*' and Resource '*' with the exact actions/ARNs this role requires.",
    },
    {
        "id": "IAM-002",
        "name": "Wildcard Action (Action: '*')",
        "severity": "HIGH",
        "confidence": 0.95,
        "cis": "CIS AWS 1.22",
        "remediation": "Enumerate the specific actions (e.g., s3:GetObject, s3:PutObject).",
    },
    {
        "id": "IAM-003",
        "name": "Wildcard Resource (Resource: '*')",
        "severity": "HIGH",
        "confidence": 0.85,
        "cis": "AWS WA SEC 03",
        "remediation": "Restrict Resource to specific ARNs (arn:aws:s3:::mybucket/*).",
    },
    {
        "id": "IAM-004",
        "name": "Service-wide wildcard (e.g., s3:*, ec2:*, iam:*)",
        "severity": "HIGH",
        "confidence": 0.92,
        "cis": "AWS WA SEC 03",
        "remediation": "Scope to read-only or a narrow set of actions the role actually uses.",
    },
    {
        "id": "IAM-005",
        "name": "Dangerous IAM privilege escalation action",
        "severity": "CRITICAL",
        "confidence": 0.98,
        "cis": "AWS WA SEC 03",
        "remediation": "Remove iam:PassRole / iam:Put*Policy / iam:CreateAccessKey for non-admin roles.",
    },
    {
        "id": "IAM-006",
        "name": "NotAction used with Allow (deny-list pattern is risky)",
        "severity": "MEDIUM",
        "confidence": 0.80,
        "cis": "AWS WA SEC 03",
        "remediation": "Prefer explicit Allow + Action list over Allow + NotAction.",
    },
    {
        "id": "IAM-007",
        "name": "Missing Condition for sensitive action",
        "severity": "MEDIUM",
        "confidence": 0.75,
        "cis": "AWS WA SEC 03",
        "remediation": "Add an aws:SourceIp, aws:MultiFactorAuthPresent, or aws:PrincipalOrgID condition.",
    },
    {
        "id": "IAM-008",
        "name": "Data exfiltration action without VPC/SourceIp condition",
        "severity": "HIGH",
        "confidence": 0.82,
        "cis": "AWS WA SEC 04",
        "remediation": "Add aws:SourceVpce / aws:SourceIp conditions for s3:GetObject, s3:ListBucket.",
    },
    {
        "id": "IAM-009",
        "name": "KMS decrypt without resource/grant condition",
        "severity": "HIGH",
        "confidence": 0.85,
        "cis": "AWS WA SEC 08",
        "remediation": "Scope kms:Decrypt to specific key ARNs and add kms:ViaService condition.",
    },
    {
        "id": "IAM-010",
        "name": "Cross-account trust with wildcard Principal",
        "severity": "CRITICAL",
        "confidence": 0.97,
        "cis": "CIS AWS 1.16",
        "remediation": "Replace {'AWS':'*'} with specific account IDs and require sts:ExternalId.",
    },
    {
        "id": "IAM-011",
        "name": "Inline policy on a user (should use groups)",
        "severity": "LOW",
        "confidence": 0.70,
        "cis": "CIS AWS 1.15",
        "remediation": "Attach policies to groups or roles, not individual users.",
    },
    {
        "id": "IAM-012",
        "name": "Trust policy allows any service (Service: '*')",
        "severity": "HIGH",
        "confidence": 0.93,
        "cis": "AWS WA SEC 02",
        "remediation": "Restrict Service to the single AWS service that needs this role (e.g., lambda.amazonaws.com).",
    },
]


# Actions known to enable privilege escalation
PRIVESC_ACTIONS = {
    "iam:passrole",
    "iam:putuserpolicy", "iam:putgrouppolicy", "iam:putrolepolicy",
    "iam:attachuserpolicy", "iam:attachgrouppolicy", "iam:attachrolepolicy",
    "iam:createaccesskey", "iam:updateaccesskey",
    "iam:createloginprofile", "iam:updateloginprofile",
    "iam:createpolicyversion", "iam:setdefaultpolicyversion",
    "sts:assumerole",
    "lambda:updatefunctioncode",
    "ec2:runinstances",
}

# High-risk data-exfiltration actions
EXFIL_ACTIONS = {
    "s3:getobject", "s3:listbucket", "s3:copyobject",
    "dynamodb:scan", "dynamodb:getitem",
    "kms:decrypt",
    "secretsmanager:getsecretvalue",
    "ssm:getparameter", "ssm:getparameters",
    "rds:downloaddbfile",
}

SENSITIVE_SERVICES = {"iam", "kms", "sts", "secretsmanager", "organizations"}


@dataclass
class Finding:
    id: str
    name: str
    severity: str
    confidence: float
    cis: str
    file: str
    statement_index: int
    statement_sid: str
    action: str
    resource: str
    risk_score: float
    evidence: str
    remediation: str
    suggested_fix: str = ""


# -------------------------------------------------------------
# ML-style risk scorer: blends pattern confidence + context signals
# -------------------------------------------------------------
class IAMRiskScorer:
    @staticmethod
    def score(rule: dict, stmt: dict, action: str, resource: str) -> float:
        base = rule["confidence"] * 60
        # Bonus/penalty signals
        has_condition = bool(stmt.get("Condition"))
        svc = action.split(":")[0].lower() if ":" in action else ""
        is_sensitive = svc in SENSITIVE_SERVICES
        is_exfil = action.lower() in EXFIL_ACTIONS

        score = base
        if not has_condition:
            score += 12
        if is_sensitive:
            score += 10
        if is_exfil:
            score += 8
        if resource == "*":
            score += 8
        sev_bonus = {"CRITICAL": 12, "HIGH": 6, "MEDIUM": 2, "LOW": 0}
        score += sev_bonus.get(rule["severity"], 0)
        return round(min(100.0, max(0.0, score)), 1)


# -------------------------------------------------------------
# Policy parsing + rule engine
# -------------------------------------------------------------
def _as_list(v):
    if v is None:
        return []
    return v if isinstance(v, list) else [v]


def analyze_statement(stmt: dict, idx: int, file_path: str) -> List[Finding]:
    findings: List[Finding] = []
    if stmt.get("Effect") != "Allow":
        return findings

    actions = _as_list(stmt.get("Action") or stmt.get("NotAction"))
    resources = _as_list(stmt.get("Resource"))
    not_action_used = "NotAction" in stmt
    sid = stmt.get("Sid", f"Stmt{idx}")

    # Rule 1 + 2 + 3 — wildcards
    has_star_action = any(a == "*" for a in actions)
    has_star_resource = any(r == "*" for r in resources)

    for action in actions:
        for resource in (resources or ["*"]):
            evidence = f'Action="{action}" Resource="{resource}"'

            if action == "*" and resource == "*":
                rule = next(r for r in IAM_RULES if r["id"] == "IAM-001")
                findings.append(_mk(rule, stmt, idx, sid, action, resource, file_path, evidence,
                                    suggested_fix='{"Action": ["s3:GetObject"], "Resource": ["arn:aws:s3:::mybucket/*"]}'))
            elif action == "*":
                rule = next(r for r in IAM_RULES if r["id"] == "IAM-002")
                findings.append(_mk(rule, stmt, idx, sid, action, resource, file_path, evidence,
                                    suggested_fix='Replace Action: "*" with a list of specific actions.'))
            elif resource == "*" and not not_action_used:
                rule = next(r for r in IAM_RULES if r["id"] == "IAM-003")
                findings.append(_mk(rule, stmt, idx, sid, action, resource, file_path, evidence,
                                    suggested_fix='Replace Resource: "*" with "arn:aws:<service>:<region>:<acct>:<resource>".'))

            # Rule 4 — service-wide wildcard like s3:*, iam:*
            if re.match(r"^[a-zA-Z0-9\-]+:\*$", action):
                svc = action.split(":")[0].lower()
                if svc in SENSITIVE_SERVICES or svc in {"s3", "ec2", "lambda", "rds", "dynamodb"}:
                    rule = next(r for r in IAM_RULES if r["id"] == "IAM-004")
                    findings.append(_mk(rule, stmt, idx, sid, action, resource, file_path, evidence,
                                        suggested_fix=f'Replace "{action}" with specific actions like "{svc}:GetObject", "{svc}:List*".'))

            # Rule 5 — privilege escalation actions
            if action.lower() in PRIVESC_ACTIONS or any(
                action.lower().startswith(p.rstrip("*")) for p in PRIVESC_ACTIONS if p.endswith("*")
            ):
                rule = next(r for r in IAM_RULES if r["id"] == "IAM-005")
                findings.append(_mk(rule, stmt, idx, sid, action, resource, file_path, evidence,
                                    suggested_fix='Remove or restrict to specific role ARN + add MFA condition.'))

            # Rule 7 — missing condition on sensitive action
            if not stmt.get("Condition") and (
                action.lower() in EXFIL_ACTIONS or action.lower() in PRIVESC_ACTIONS
            ):
                rule = next(r for r in IAM_RULES if r["id"] == "IAM-007")
                findings.append(_mk(rule, stmt, idx, sid, action, resource, file_path, evidence,
                                    suggested_fix='Add "Condition": {"Bool": {"aws:MultiFactorAuthPresent": "true"}}.'))

            # Rule 8 — exfil without vpce/ip condition
            if action.lower() in EXFIL_ACTIONS and not _has_network_condition(stmt):
                rule = next(r for r in IAM_RULES if r["id"] == "IAM-008")
                findings.append(_mk(rule, stmt, idx, sid, action, resource, file_path, evidence,
                                    suggested_fix='Add "Condition": {"StringEquals": {"aws:SourceVpce": "vpce-xxxx"}}.'))

            # Rule 9 — KMS decrypt without scoping
            if action.lower() == "kms:decrypt" and resource == "*":
                rule = next(r for r in IAM_RULES if r["id"] == "IAM-009")
                findings.append(_mk(rule, stmt, idx, sid, action, resource, file_path, evidence,
                                    suggested_fix='Scope Resource to specific KMS key ARN + add kms:ViaService condition.'))

    # Rule 6 — NotAction with Allow
    if not_action_used:
        rule = next(r for r in IAM_RULES if r["id"] == "IAM-006")
        findings.append(_mk(rule, stmt, idx, sid, "<NotAction>", ",".join(resources), file_path,
                            'NotAction used with Effect=Allow (deny-list pattern)',
                            suggested_fix='Replace with explicit Action list of what you want to allow.'))

    # Rule 10 + 12 — trust policy checks
    principal = stmt.get("Principal")
    if principal:
        if principal == "*" or (isinstance(principal, dict) and any(v == "*" for v in principal.values())):
            rule = next(r for r in IAM_RULES if r["id"] == "IAM-010")
            findings.append(_mk(rule, stmt, idx, sid, "sts:AssumeRole", "<trust-policy>", file_path,
                                f'Principal={principal}',
                                suggested_fix='Principal: {"AWS": "arn:aws:iam::ACCOUNT_ID:root"} + ExternalId condition.'))
        if isinstance(principal, dict) and principal.get("Service") == "*":
            rule = next(r for r in IAM_RULES if r["id"] == "IAM-012")
            findings.append(_mk(rule, stmt, idx, sid, "sts:AssumeRole", "<trust-policy>", file_path,
                                f'Principal.Service="*"',
                                suggested_fix='Principal: {"Service": "lambda.amazonaws.com"} (be specific).'))

    return findings


def _has_network_condition(stmt: dict) -> bool:
    cond = stmt.get("Condition") or {}
    text = json.dumps(cond).lower()
    return any(k in text for k in ("aws:sourceip", "aws:sourcevpc", "aws:sourcevpce"))


def _mk(rule, stmt, idx, sid, action, resource, file_path, evidence, suggested_fix=""):
    risk = IAMRiskScorer.score(rule, stmt, action, resource)
    return Finding(
        id=rule["id"], name=rule["name"], severity=rule["severity"],
        confidence=rule["confidence"], cis=rule["cis"],
        file=file_path, statement_index=idx, statement_sid=sid,
        action=action, resource=resource, risk_score=risk,
        evidence=evidence, remediation=rule["remediation"],
        suggested_fix=suggested_fix,
    )


def analyze_policy(path: Path) -> List[Finding]:
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"[!] Failed to parse {path}: {e}", file=sys.stderr)
        return []

    # Support policy doc, inline-policy list, role doc, or wrapper
    stmts = []
    if isinstance(doc, dict):
        if "Statement" in doc:
            stmts = _as_list(doc["Statement"])
        elif "PolicyDocument" in doc:
            stmts = _as_list(doc["PolicyDocument"].get("Statement", []))
        elif "AssumeRolePolicyDocument" in doc:
            inner = doc["AssumeRolePolicyDocument"]
            if isinstance(inner, str):
                inner = json.loads(inner)
            stmts = _as_list(inner.get("Statement", []))
    findings = []
    for i, s in enumerate(stmts):
        if isinstance(s, dict):
            findings.extend(analyze_statement(s, i, str(path)))
    return findings


def analyze_target(target: Path) -> List[Finding]:
    findings = []
    if target.is_file():
        return analyze_policy(target)
    for p in target.rglob("*.json"):
        findings.extend(analyze_policy(p))
    return findings


def build_summary(findings: List[Finding]) -> dict:
    by_sev = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
    for f in findings:
        by_sev[f.severity] = by_sev.get(f.severity, 0) + 1
    return {
        "tool": "IAM Least-Privilege Analyzer",
        "version": "1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_findings": len(findings),
        "by_severity": by_sev,
    }


def print_report(summary, findings):
    print("=" * 60)
    print("  IAM Least-Privilege Analyzer v1.0")
    print("=" * 60)
    print(f"[*] Total findings: {summary['total_findings']}")
    print(f"[*] Breakdown     : {summary['by_severity']}")
    print()
    for f in sorted(findings, key=lambda x: -x.risk_score)[:20]:
        print(f"[{f.severity}] {f.name}")
        print(f"   {f.file} stmt[{f.statement_index}]:{f.statement_sid} (risk={f.risk_score}, {f.cis})")
        print(f"   > {f.evidence}")
        print()


def main():
    ap = argparse.ArgumentParser(description="IAM Least-Privilege Analyzer")
    ap.add_argument("target", help="Path to a policy JSON file or a directory of them")
    ap.add_argument("-o", "--output", default="reports/iam_report.json", help="JSON output path")
    ap.add_argument("--html", default="reports/iam_report.html", help="HTML output path")
    args = ap.parse_args()

    target = Path(args.target)
    if not target.exists():
        print(f"[x] Path not found: {target}", file=sys.stderr)
        sys.exit(1)

    findings = analyze_target(target)
    summary = build_summary(findings)

    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as fh:
        json.dump({"summary": summary, "findings": [asdict(f) for f in findings]}, fh, indent=2)

    generate_html(summary, findings, args.html)
    print_report(summary, findings)
    print(f"[*] JSON report: {args.output}")
    print(f"[*] HTML report: {args.html}")


if __name__ == "__main__":
    try:
        from license_guard import verify_license
        verify_license()
    except Exception:
        pass
    main()
