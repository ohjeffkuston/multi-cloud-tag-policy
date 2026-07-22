import copy
import unittest

from multi_cloud_tag_policy.engine import audit_inventory


def resource(resource_id="r-1", provider="aws", resource_type="aws:ec2:instance", **tags):
    defaults = {
        "owner": "platform@example.com",
        "cost_center": "CC-1042",
        "environment": "prod",
        "data_classification": "internal",
    }
    defaults.update(tags)
    return {
        "provider": provider,
        "resource_id": resource_id,
        "resource_type": resource_type,
        "tags": defaults,
    }


class AuditInventoryTests(unittest.TestCase):
    def test_compliant_inventory_passes(self):
        result = audit_inventory({"resources": [resource()]})
        self.assertEqual("PASS", result["decision"])
        self.assertEqual(100, result["score"])

    def test_missing_owner_blocks(self):
        item = resource(owner="")
        result = audit_inventory({"resources": [item]})
        self.assertEqual("BLOCK", result["decision"])
        self.assertEqual("owner", result["findings"][0]["tag"])

    def test_invalid_environment_requires_review(self):
        result = audit_inventory({"resources": [resource(environment="production")]})
        self.assertEqual("REVIEW", result["decision"])
        self.assertEqual("ENVIRONMENT_INVALID", result["findings"][0]["code"])

    def test_provider_tag_names_are_normalised(self):
        item = resource()
        item["tags"] = {
            "Owner": "platform@example.com",
            "Cost-Center": "CC-1042",
            "Environment": "prod",
            "Data Classification": "internal",
        }
        self.assertEqual("PASS", audit_inventory({"resources": [item]})["decision"])

    def test_exempt_resource_is_not_audited(self):
        item = resource(resource_type="aws:iam:service-linked-role", owner="")
        result = audit_inventory({
            "policy": {"exempt_resource_types": ["aws:iam:service-linked-role"]},
            "resources": [item],
        })
        self.assertEqual("PASS", result["decision"])
        self.assertEqual(1, result["summary"]["resources_exempt"])

    def test_unknown_provider_blocks(self):
        result = audit_inventory({"resources": [resource(provider="other")]})
        self.assertEqual("BLOCK", result["decision"])
        self.assertEqual("UNSUPPORTED_PROVIDER", result["findings"][0]["code"])

    def test_output_is_deterministic_and_input_is_unchanged(self):
        payload = {"resources": [resource("z", owner=""), resource("a", environment="bad")]}
        original = copy.deepcopy(payload)
        first = audit_inventory(payload)
        second = audit_inventory(payload)
        self.assertEqual(first, second)
        self.assertEqual(original, payload)
        self.assertEqual(["a", "z"], [item["resource_id"] for item in first["findings"]])

    def test_malformed_inventory_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "resources must be a list"):
            audit_inventory({"resources": "not-a-list"})


if __name__ == "__main__":
    unittest.main()

