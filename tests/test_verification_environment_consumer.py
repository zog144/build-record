import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from examples.verification_environment_consumer import environment_rows
from zog.build_record import canonical, inspect, make_record, record_id
from zog.build_record.cli import main
from zog.build_record.model import execution_environment_digest


def descriptor():
    return {
        "isolation": {"mount_namespace": True},
        "user": {"uid": 0, "gid": 0},
        "root": {"mode": "prepared-rootfs"},
        "network": {"mode": "host"},
        "timeout": {"seconds": 120},
        "runtime": {"executor": "systemd"},
    }


def common_data():
    return {
        "producer_observation": "sha256:" + "1" * 64,
        "check_id": "fixture/check/0",
        "definition_digest": "sha256:" + "2" * 64,
        "subject": {
            "kind": "generation-candidate",
            "generation_id": "fixture-generation",
            "root_inventory_digest": "sha256:" + "3" * 64,
        },
        "attempt_id": "fixture-attempt",
        "sequence": 0,
        "outcome": "PASS",
        "execution": {"exit_code": 0},
        "evidence": [{"kind": "fixture"}],
        "granularity": "command",
        "timing": {"started_at": None, "finished_at": None, "observed_at": None},
    }


def legacy_record():
    data = {
        **common_data(),
        "producer": {
            "name": "image-build",
            "contract": "image-build-verification-observation-v1",
        },
        "environment_digest": "sha256:" + "4" * 64,
    }
    return make_record("verification-execution", data)


def enriched_record():
    environment = descriptor()
    data = {
        **common_data(),
        "producer": {
            "name": "image-build",
            "contract": "image-build-verification-observation-v2",
        },
        "producer_observation": "sha256:" + "5" * 64,
        "execution_environment": {
            "contract": "image-build-verification-environment-v1",
            "digest": execution_environment_digest(environment),
            "descriptor": environment,
        },
        "producer_policy_digest": "sha256:" + "6" * 64,
    }
    return make_record("verification-execution", data)


def bundle():
    records = [legacy_record(), enriched_record()]
    by_id = {record_id(record): record for record in records}
    return {"schema_version": 1, "roots": sorted(by_id), "records": by_id}


class VerificationEnvironmentConsumerTests(unittest.TestCase):
    def test_standalone_consumer_uses_only_inspect_projection(self):
        report = inspect(bundle())
        rows = environment_rows(report)
        self.assertEqual({row["kind"] for row in rows},
                         {"legacy-opaque", "versioned"})
        legacy = next(row for row in rows if row["kind"] == "legacy-opaque")
        versioned = next(row for row in rows if row["kind"] == "versioned")
        self.assertEqual(legacy["legacy_environment_digest"],
                         "sha256:" + "4" * 64)
        self.assertIsNone(legacy["execution_environment_descriptor"])
        self.assertEqual(versioned["execution_environment_contract"],
                         "image-build-verification-environment-v1")
        self.assertEqual(versioned["execution_environment_descriptor"], descriptor())
        self.assertEqual(versioned["producer_policy_digest"], "sha256:" + "6" * 64)
        for row in rows:
            self.assertNotIn("comparable", row)
            self.assertNotIn("equivalent", row)
            self.assertNotIn("regression", row)

    def test_cli_inspect_json_contains_stable_environment_surface(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bundle.json"
            path.write_bytes(canonical(bundle()))
            with redirect_stdout(io.StringIO()) as output:
                self.assertEqual(main(["inspect", str(path)]), 0)
            report = json.loads(output.getvalue())
        rows = environment_rows(report)
        self.assertEqual(len(rows), 2)
        self.assertEqual({row["kind"] for row in rows},
                         {"legacy-opaque", "versioned"})

    def test_consumer_example_has_no_producer_or_build_record_dependency(self):
        source = (Path(__file__).resolve().parents[1] /
                  "examples" / "verification_environment_consumer.py").read_text(
                      encoding="utf-8")
        self.assertNotIn("zog.build_record", source)
        self.assertNotIn("image_build", source)


if __name__ == "__main__":
    unittest.main()
