# Day 6 Project Guide — Multi-Cloud Tag Policy Auditor

To: ohjeffkuston@yahoo.ca

## What you built

You built a read-only policy-as-code tool that audits resource metadata from AWS, Azure, and Google Cloud. It normalizes differences in tag naming, checks an explicit policy, and returns an auditable `PASS`, `REVIEW`, or `BLOCK` decision.

The business problem is cost and operational accountability. A cloud bill can identify a resource, but teams still need reliable metadata to identify the owner, application, environment, cost center, and data sensitivity. Without it, cost allocation, incident routing, lifecycle management, and governance become slower and less trustworthy.

## Architecture, step by step

1. **Inventory input:** A scheduled export or CI job provides synthetic or read-only resource inventory JSON.
2. **Normalization:** The engine converts keys such as `Cost-Center`, `cost_center`, and `Cost Center` to one provider-neutral form.
3. **Policy evaluation:** Required tags, allowed environment values, and documented exemptions are evaluated with deterministic code.
4. **Decision:** The engine assigns stable finding codes and severity levels, calculates a score, and returns `PASS`, `REVIEW`, or `BLOCK`.
5. **Routing:** CI can use the exit code, while n8n can route non-compliant reports to a human review queue.
6. **Safety boundary:** The project never authenticates to a cloud account and never applies a tag change.

## Important code concepts

- `audit_inventory()` is a pure function: the same input produces the same output and the input is not modified.
- `_normalise_key()` creates a provider-neutral key format.
- `_policy()` validates policy structure and fails closed on malformed input.
- Findings have stable codes such as `REQUIRED_TAG_MISSING`, `ENVIRONMENT_INVALID`, and `UNSUPPORTED_PROVIDER`.
- Critical findings create `BLOCK`; other findings create `REVIEW`; no findings create `PASS`.
- Results are sorted so reports remain stable in tests and source-control comparisons.

## How to demonstrate it

```bash
cd career-ops-agent/generated/day-06-multi-cloud-tag-policy
python -m pip install -e .
python -m unittest discover -s tests -v
multi-cloud-tag-audit examples/resources.json
```

The sample intentionally includes one compliant AWS resource, one non-compliant Azure resource, and one compliant GCP resource. The expected decision is `BLOCK` because the Azure resource has no owner.

## How to deploy it safely

For a personal demo, run it locally or in Docker with the sample inventory. For an enterprise pattern:

1. Use read-only provider APIs or inventory exports.
2. Place the policy in a reviewed repository.
3. Run the auditor in CI or a scheduled job.
4. Store the JSON report as an artifact.
5. Send only the report—not cloud credentials—to the n8n workflow.
6. Require a human to approve any separate remediation job.

Do not connect this reference implementation directly to production write permissions.

## What the eight tests prove

- A compliant inventory passes.
- A missing owner blocks.
- An invalid environment requires review.
- Different tag-name formats normalize correctly.
- Explicitly exempt resource types are not audited.
- Unknown providers fail closed.
- Output ordering is deterministic and input data remains unchanged.
- Malformed inventory data is rejected.

## Interview positioning

Use this concise explanation:

> I built a deterministic multi-cloud tag-policy auditor that normalizes AWS tags, Azure tags, and GCP labels, then evaluates ownership, cost, environment, and governance requirements. It produces explainable CI-ready decisions but deliberately separates detection from remediation, so production changes still require human approval.

If asked why no LLM makes the decision, explain that governance controls need reproducibility and auditability. An LLM can summarize findings or propose a remediation plan, but deterministic code should own the policy verdict.

## Ways to extend it

- Add read-only adapters for AWS Resource Groups Tagging API, Azure Resource Graph, and Google Cloud Asset Inventory.
- Load policy from YAML and validate it with JSON Schema.
- Add trend reporting for compliance percentage over time.
- Create team-specific policy overlays.
- Add signed evidence artifacts and pull-request annotations.
- Use an LLM only for plain-language explanations grounded in the deterministic report.

## Skills demonstrated

Python, multi-cloud governance, FinOps, policy-as-code, deterministic testing, CLI design, Docker, GitHub Actions, n8n, JSON contracts, safety boundaries, and technical communication.

