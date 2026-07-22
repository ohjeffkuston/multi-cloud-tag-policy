"""Deterministic, read-only multi-cloud tag policy engine."""

from __future__ import annotations

import re
from collections import Counter
from typing import Any

SUPPORTED_PROVIDERS = {"aws", "azure", "gcp"}
DEFAULT_POLICY = {
    "required_tags": ["owner", "cost_center", "environment", "data_classification"],
    "allowed_environments": ["dev", "test", "stage", "prod"],
    "exempt_resource_types": [],
}
SEVERITY_WEIGHT = {"critical": 25, "high": 15, "medium": 8, "low": 3}
TAG_SEVERITY = {
    "owner": "critical",
    "cost_center": "high",
    "environment": "high",
    "data_classification": "medium",
}


def _normalise_key(value: str) -> str:
    return re.sub(r"_+", "_", re.sub(r"[^a-z0-9]+", "_", value.strip().lower())).strip("_")


def _normalise_tags(tags: dict[str, Any]) -> dict[str, str]:
    return {
        _normalise_key(str(key)): str(value).strip()
        for key, value in tags.items()
        if str(key).strip()
    }


def _policy(payload: dict[str, Any]) -> dict[str, Any]:
    raw = payload.get("policy", {})
    if not isinstance(raw, dict):
        raise ValueError("policy must be an object")
    result = {**DEFAULT_POLICY, **raw}
    for field in ("required_tags", "allowed_environments", "exempt_resource_types"):
        if not isinstance(result[field], list) or not all(isinstance(item, str) for item in result[field]):
            raise ValueError(f"policy.{field} must be a list of strings")
    result["required_tags"] = [_normalise_key(item) for item in result["required_tags"]]
    result["allowed_environments"] = [item.strip().lower() for item in result["allowed_environments"]]
    return result


def _finding(resource_id: str, code: str, severity: str, message: str, tag: str | None = None) -> dict[str, str]:
    finding = {
        "resource_id": resource_id,
        "code": code,
        "severity": severity,
        "message": message,
    }
    if tag:
        finding["tag"] = tag
    return finding


def audit_inventory(payload: dict[str, Any]) -> dict[str, Any]:
    """Audit a resource inventory and return a stable, explainable report.

    The function has no I/O and never mutates the supplied payload.
    """
    if not isinstance(payload, dict):
        raise ValueError("input must be a JSON object")
    resources = payload.get("resources")
    if not isinstance(resources, list):
        raise ValueError("resources must be a list")

    policy = _policy(payload)
    findings: list[dict[str, str]] = []
    audited = 0
    exempt = 0
    provider_counts: Counter[str] = Counter()

    for index, raw in enumerate(resources):
        if not isinstance(raw, dict):
            raise ValueError(f"resources[{index}] must be an object")
        resource_id = str(raw.get("resource_id", "")).strip()
        provider = str(raw.get("provider", "")).strip().lower()
        resource_type = str(raw.get("resource_type", "")).strip().lower()
        tags = raw.get("tags", {})
        if not resource_id:
            raise ValueError(f"resources[{index}].resource_id is required")
        if not isinstance(tags, dict):
            raise ValueError(f"resources[{index}].tags must be an object")

        provider_counts[provider or "unknown"] += 1
        if resource_type in policy["exempt_resource_types"]:
            exempt += 1
            continue
        audited += 1

        if provider not in SUPPORTED_PROVIDERS:
            findings.append(
                _finding(resource_id, "UNSUPPORTED_PROVIDER", "critical", f"Provider '{provider or 'missing'}' is unsupported.")
            )
            continue

        normalised = _normalise_tags(tags)
        for tag in policy["required_tags"]:
            if not normalised.get(tag):
                severity = TAG_SEVERITY.get(tag, "medium")
                findings.append(
                    _finding(resource_id, "REQUIRED_TAG_MISSING", severity, f"Required tag '{tag}' is missing or empty.", tag)
                )

        environment = normalised.get("environment")
        if environment and environment.lower() not in policy["allowed_environments"]:
            findings.append(
                _finding(
                    resource_id,
                    "ENVIRONMENT_INVALID",
                    "medium",
                    f"Environment '{environment}' is not in the approved value set.",
                    "environment",
                )
            )

    findings.sort(key=lambda item: (item["resource_id"], item["code"], item.get("tag", "")))
    severity_counts = Counter(item["severity"] for item in findings)
    penalty = sum(SEVERITY_WEIGHT[item["severity"]] for item in findings)
    score = max(0, 100 - penalty)
    if severity_counts["critical"]:
        decision = "BLOCK"
    elif findings:
        decision = "REVIEW"
    else:
        decision = "PASS"

    compliant_resources = max(0, audited - len({item["resource_id"] for item in findings}))
    compliance_percent = 100.0 if audited == 0 else round((compliant_resources / audited) * 100, 1)

    return {
        "project": "Multi-Cloud Tag Policy Auditor",
        "decision": decision,
        "score": score,
        "summary": {
            "resources_received": len(resources),
            "resources_audited": audited,
            "resources_exempt": exempt,
            "compliant_resources": compliant_resources,
            "compliance_percent": compliance_percent,
            "findings": len(findings),
            "severity_counts": {level: severity_counts[level] for level in ("critical", "high", "medium", "low")},
            "provider_counts": dict(sorted(provider_counts.items())),
        },
        "findings": findings,
        "safety": {
            "mode": "read_only",
            "cloud_mutations": False,
            "human_approval_required": decision != "PASS",
        },
    }

