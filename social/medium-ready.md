# Multi-Cloud Tag Policy Auditor: Turning Inconsistent Metadata into an Auditable FinOps Decision

Cloud teams rarely lose cost accountability because billing data is unavailable. They lose it because the metadata needed to connect a resource to an owner, environment, or cost center is missing or inconsistent.

AWS calls them tags. Azure also uses tags. Google Cloud commonly uses labels. Across multiple accounts and teams, the same intent can appear as `Cost-Center`, `cost_center`, or not appear at all. That inconsistency weakens showback, incident routing, lifecycle reviews, and policy enforcement.

For Day 6 of my Cloud + AI portfolio series, I built the **Multi-Cloud Tag Policy Auditor**: a deterministic, read-only control that converts an exported AWS, Azure, and Google Cloud inventory into an explainable compliance decision.

![Multi-Cloud Tag Policy Auditor architecture](https://raw.githubusercontent.com/ohjeffkuston/multi-cloud-tag-policy/main/docs/architecture.png)

## The potential solution

The useful pattern is not to let an AI model decide whether metadata is compliant. The safer pattern is to make the policy deterministic, then allow AI to explain or summarize the evidence.

The auditor follows that separation:

1. Accept a read-only multi-cloud inventory.
2. Normalize provider-specific tag and label keys.
3. Check required ownership, cost, environment, and data-classification fields.
4. Validate controlled values and documented exemptions.
5. Produce stable finding codes, severity counts, a score, and a `PASS`, `REVIEW`, or `BLOCK` decision.

## Why this matters operationally

A missing owner is more than a FinOps inconvenience. It can delay incident escalation and leave idle resources without an accountable decision-maker. A missing cost center weakens allocation. An uncontrolled environment value makes reporting unreliable. Missing data classification can undermine governance.

The project therefore weights findings by operational impact while keeping the rules visible in code. The same input always produces the same ordered output, which makes the control testable in CI and defensible during review.

## Approval-first by design

The project contains no cloud credentials, performs no network calls, and never changes tags. Non-compliant results can be routed through the included n8n workflow, but remediation remains a separate, human-approved action.

That boundary matters: automation should make the safe decision easier, not make ownership disappear.

## What I learned

The hardest part of multi-cloud governance is often not writing a rule. It is defining a provider-neutral contract that stays useful across cost management, platform operations, security, and reliability.

This implementation demonstrates Python automation, policy-as-code, multi-cloud normalization, deterministic testing, CI integration, containerization, n8n orchestration, and human-in-the-loop design.

The repository includes the implementation, eight unit tests, synthetic sample data, Docker packaging, GitHub Actions CI, and the architecture visual.

What metadata rule would create the greatest operational improvement in your cloud estate today?

