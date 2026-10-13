import copy
import hashlib
import tempfile
import unittest

from examples.local_pipeline import fixture
from zog.build_record import (RecordError, Store, canonical, ingest_image_build_candidate,
                              ingest_image_build_generation, ingest_image_build_snapshot,
                              inspect, record_id)
from zog.build_record.image_build import verification_execution
from zog.build_record.model import execution_environment_digest


V1_RECORD_ID = "sha256:dfdf36c52d3cdc209800c94385f4f854a9dfe8e5adcfea55d92ef73ad6dfdaca"
V2_ENVIRONMENT_DIGEST = "sha256:4589f8b4389690d2097142fe57273b23b24ce9fd1e39b8be17871e74a0abdcc0"
V2_RECORD_ID = "sha256:78220f767eddea75245bbbe378506d0a177d2dd1bada86bf826ded2451234fdb"
IMAGE_BUILD_V2_FIXTURE_HEAD = "a714fe8c0fb2e3a50183937d9f3869e42ee0587d"
IMAGE_BUILD_V2_ENVIRONMENT_DIGEST = "sha256:4d80eb5935e36049f32de5d38480441857fce43d0574027d14b1fd16c2c57bee"
IMAGE_BUILD_V2_OBSERVATION_ID = "sha256:87afece69e6bdc74ab3cf1e66fc9e9f0d9de39a43b4f98ef306d3c3e38ecf86e"
IMAGE_BUILD_V2_RECORD_ID = "sha256:75c817a4bd7f42b6f83945b1af17a33ba0104836e8b316c038ea728721f94934"


def producer_id(value):
    return "sha256:" + hashlib.sha256(canonical(value)).hexdigest()


def descriptor(*, network_mode="host"):
    return {
        "isolation": {
            "mount_namespace": True,
            "user_namespace": False,
            "root_read_only": True,
        },
        "user": {
            "uid": 0,
            "gid": 0,
            "supplementary_groups": [],
        },
        "root": {
            "mode": "prepared-rootfs",
            "writable_state": "explicit-only",
        },
        "network": {
            "mode": network_mode,
        },
        "timeout": {
            "seconds": 120,
        },
        "runtime": {
            "executor": "systemd",
            "kill_sequence": ["SIGINT", "SIGTERM"],
        },
    }


def image_build_v2_descriptor():
    """Exact descriptor shape emitted by image-build a714fe8c0fb2e3a50183937d9f3869e42ee0587d's fixture."""
    return {
        "isolation": {
            "mount_namespace": True,
            "user_namespace": False,
            "root_read_only": True,
            "device_profile_digest": None,
        },
        "user": {
            "uid": 1000,
            "gid": 1001,
        },
        "root": {
            "mode": "prepared-rootfs",
            "writable_output": "separate-workspace",
        },
        "network": {
            "mode": "none",
        },
        "timeout": {
            "execution_seconds": "60",
            "startup_seconds": "30",
            "termination_grace_seconds": "5",
        },
        "runtime": {
            "executor": "box-control-build-job-v1",
            "working_directory": "/image-build/source",
            "environment": [
                "HOME=/tmp",
                "LANG=C",
                "LC_ALL=C",
                "PATH=/usr/bin:/bin",
            ],
            "resource_limits": {
                "cpu-weight": "100",
                "memory-maximum-bytes": "1073741824",
                "thread-count-maximum": "128",
            },
        },
    }


def observation_v1(generation_id='["host","project","gen"]',
                   root_digest="sha256:" + "4" * 64):
    value = {
        "schema": "image-build-verification-observation-v1",
        "check_id": "image-build/installed-trust/command/0",
        "definition_digest": "sha256:" + "1" * 64,
        "subject": {
            "kind": "generation-candidate",
            "generation_id": generation_id,
            "root_inventory_digest": root_digest,
        },
        "attempt_id": '["host","project","attempt-1"]',
        "sequence": 0,
        "outcome": "PASS",
        "execution": {"invocation_id": "invocation-1", "exit_code": 0},
        "environment_digest": "sha256:" + "2" * 64,
        "evidence": [{"kind": "build-trace", "host_id": "host",
                      "build_id": "attempt:attempt-1"}],
        "granularity": "command",
        "timing": {"started_at": None, "finished_at": None,
                   "observed_at": "2026-10-06T12:00:00+00:00"},
        "producer": {"name": "image-build",
                     "contract": "image-build-verification-observation-v1"},
    }
    value["id"] = producer_id(value)
    return value


def observation_v2(generation_id='["host","project","gen"]',
                   root_digest="sha256:" + "4" * 64, *,
                   environment=None, producer_policy_digest=None,
                   invocation="invocation-2"):
    environment = copy.deepcopy(environment or descriptor())
    value = {
        "schema": "image-build-verification-observation-v2",
        "check_id": "image-build/installed-trust/command/0",
        "definition_digest": "sha256:" + "1" * 64,
        "subject": {
            "kind": "generation-candidate",
            "generation_id": generation_id,
            "root_inventory_digest": root_digest,
        },
        "attempt_id": '["host","project","attempt-2"]',
        "sequence": 0,
        "outcome": "PASS",
        "execution": {"invocation_id": invocation, "exit_code": 0},
        "execution_environment": {
            "contract": "image-build-verification-environment-v1",
            "digest": execution_environment_digest(environment),
            "descriptor": environment,
        },
        "producer_policy_digest": producer_policy_digest or ("sha256:" + "5" * 64),
        "evidence": [{"kind": "build-trace", "host_id": "host",
                      "build_id": "attempt:attempt-2"}],
        "granularity": "command",
        "timing": {"started_at": None, "finished_at": None,
                   "observed_at": "2026-10-09T20:00:00+00:00"},
        "producer": {"name": "image-build",
                     "contract": "image-build-verification-observation-v2"},
    }
    value["id"] = producer_id(value)
    return value


def candidate(generation_id, results):
    return {
        "schema": "image-build-candidate-verifications-v1",
        "generation_id": generation_id,
        "results": results,
        "coverage": "captured terminal commands only; absence is not SKIP",
    }


def generation_export(bundle, results):
    generation_id = bundle["records"][bundle["roots"][0]]["data"]["generation_id"]
    root_digest = results[0]["subject"]["root_inventory_digest"]
    value = {
        "schema": "image-build-integration-observations-v1",
        "producer": {
            "name": "image-build",
            "contract": "image-build-integration-observations-v1",
            "implementation_digest": "sha256:" + "3" * 64,
        },
        "context": {
            "generation_id": generation_id,
            "generation_record": bundle["roots"][0],
            "root_inventory_digest": root_digest,
        },
        "verification": {
            "checks": [{
                "check_id": results[0]["check_id"],
                "definition_digest": results[0]["definition_digest"],
                "granularity": "command",
            }],
            "results": results,
            "coverage": "named installed command checks only; no parsed upstream subtests",
        },
        "relationships": [],
        "sources": [],
        "coverage": {
            "elf_files": 0,
            "script_files": 0,
            "readelf": {"name": "readelf", "sha256": "f" * 64},
            "symlinks": "not-followed",
            "resolution": "interfaces-only",
            "unsupported": ["dlopen", "ABI-compatibility", "service-dependencies",
                            "env-PATH-resolution"],
        },
        "gaps": [],
        "derivation": "post-build-inspection; does not retrofit canonical pre-execution evidence",
    }
    value["id"] = producer_id(value)
    return value


class VerificationExecutionEnvironmentTests(unittest.TestCase):
    def test_v1_record_identity_is_unchanged(self):
        record = verification_execution(observation_v1())
        self.assertEqual(record_id(record), V1_RECORD_ID)
        self.assertEqual(set(record["data"]), {
            "producer", "producer_observation", "check_id", "definition_digest",
            "subject", "attempt_id", "sequence", "outcome", "execution",
            "environment_digest", "evidence", "granularity", "timing"})
        self.assertNotIn("execution_environment", record["data"])

    def test_current_image_build_v2_fixture_is_canonical_compatible(self):
        self.assertEqual(
            IMAGE_BUILD_V2_FIXTURE_HEAD,
            "a714fe8c0fb2e3a50183937d9f3869e42ee0587d")
        environment = image_build_v2_descriptor()
        self.assertEqual(
            execution_environment_digest(environment),
            IMAGE_BUILD_V2_ENVIRONMENT_DIGEST)

        value = observation_v2(environment=environment)
        self.assertEqual(value["id"], IMAGE_BUILD_V2_OBSERVATION_ID)
        record = verification_execution(value)
        self.assertEqual(record_id(record), IMAGE_BUILD_V2_RECORD_ID)
        self.assertEqual(
            record["data"]["execution_environment"]["descriptor"],
            environment)
        self.assertEqual(
            record["data"]["execution_environment"]["digest"],
            IMAGE_BUILD_V2_ENVIRONMENT_DIGEST)

    def test_current_image_build_v2_execution_semantics_are_retained(self):
        environment = image_build_v2_descriptor()
        runtime = environment["runtime"]
        self.assertEqual(runtime["working_directory"], "/image-build/source")
        self.assertEqual(
            runtime["environment"],
            ["HOME=/tmp", "LANG=C", "LC_ALL=C", "PATH=/usr/bin:/bin"])
        self.assertEqual(
            runtime["resource_limits"],
            {
                "cpu-weight": "100",
                "memory-maximum-bytes": "1073741824",
                "thread-count-maximum": "128",
            })
        self.assertIsNone(environment["isolation"]["device_profile_digest"])
        self.assertEqual(environment["network"]["mode"], "none")

    def test_enriched_execution_golden_identity(self):
        value = observation_v2()
        self.assertEqual(value["execution_environment"]["digest"], V2_ENVIRONMENT_DIGEST)
        self.assertEqual(record_id(verification_execution(value)), V2_RECORD_ID)

    def test_descriptor_key_order_does_not_change_digest_or_record_identity(self):
        ordered = descriptor()
        reordered = {
            key: dict(reversed(list(value.items())))
            for key, value in reversed(list(ordered.items()))
        }
        self.assertEqual(execution_environment_digest(ordered),
                         execution_environment_digest(reordered))
        left = verification_execution(observation_v2(environment=ordered))
        right = verification_execution(observation_v2(environment=reordered))
        self.assertEqual(record_id(left), record_id(right))

    def test_descriptor_unicode_is_not_silently_normalized(self):
        composed = descriptor()
        decomposed = descriptor()
        composed["runtime"]["label"] = "\u00e9"
        decomposed["runtime"]["label"] = "e\u0301"
        self.assertNotEqual(execution_environment_digest(composed),
                            execution_environment_digest(decomposed))

    def test_descriptor_integer_boundary_is_interoperable(self):
        accepted = descriptor()
        accepted["timeout"]["budget"] = 9007199254740991
        execution_environment_digest(accepted)
        rejected = descriptor()
        rejected["timeout"]["budget"] = 9007199254740992
        with self.assertRaises(RecordError):
            execution_environment_digest(rejected)

    def test_descriptor_rejects_float_and_invalid_unicode(self):
        floating = descriptor()
        floating["timeout"]["ratio"] = 1.5
        with self.assertRaises(RecordError):
            execution_environment_digest(floating)
        surrogate = descriptor()
        surrogate["runtime"]["label"] = "\ud800"
        with self.assertRaises(RecordError):
            execution_environment_digest(surrogate)

    def test_descriptor_rejects_size_member_and_nesting_overflow(self):
        long_string = descriptor()
        long_string["runtime"]["label"] = "x" * 4097
        with self.assertRaises(RecordError):
            execution_environment_digest(long_string)

        long_list = descriptor()
        long_list["runtime"]["features"] = list(range(129))
        with self.assertRaises(RecordError):
            execution_environment_digest(long_list)

        deep = descriptor()
        nested = {}
        cursor = nested
        for index in range(9):
            child = {}
            cursor["level" + str(index)] = child
            cursor = child
        deep["runtime"]["nested"] = nested
        with self.assertRaises(RecordError):
            execution_environment_digest(deep)

    def test_descriptor_rejects_extra_domain_and_forbidden_key_variants(self):
        extra = descriptor()
        extra["filesystem"] = {}
        with self.assertRaises(RecordError):
            execution_environment_digest(extra)

        for key in ("Api-Token", "ROOT-PATH", "session_id", "Observed-Timestamp"):
            with self.subTest(key=key):
                value = descriptor()
                value["runtime"][key] = "forbidden"
                with self.assertRaises(RecordError):
                    execution_environment_digest(value)

    def test_producer_policy_change_changes_record_identity_without_environment_change(self):
        left_value = observation_v2(producer_policy_digest="sha256:" + "5" * 64)
        right_value = observation_v2(producer_policy_digest="sha256:" + "6" * 64)
        self.assertEqual(left_value["execution_environment"],
                         right_value["execution_environment"])
        self.assertNotEqual(record_id(verification_execution(left_value)),
                            record_id(verification_execution(right_value)))

    def test_enriched_execution_validates_and_policy_is_distinct(self):
        value = observation_v2()
        record = verification_execution(value)
        self.assertEqual(record["data"]["execution_environment"],
                         value["execution_environment"])
        self.assertEqual(record["data"]["producer_policy_digest"],
                         "sha256:" + "5" * 64)
        self.assertNotEqual(record["data"]["producer_policy_digest"],
                            record["data"]["execution_environment"]["digest"])
        self.assertNotIn("environment_digest", record["data"])

    def test_changing_only_descriptor_changes_canonical_identity(self):
        left = verification_execution(observation_v2())
        right = verification_execution(observation_v2(
            environment=descriptor(network_mode="none")))
        self.assertNotEqual(record_id(left), record_id(right))

    def test_mismatched_descriptor_digest_is_rejected(self):
        value = observation_v2()
        value["execution_environment"]["digest"] = "sha256:" + "0" * 64
        value["id"] = producer_id({k: v for k, v in value.items() if k != "id"})
        with self.assertRaises(RecordError):
            verification_execution(value)

    def test_malformed_environment_contract_is_rejected(self):
        value = observation_v2()
        value["execution_environment"]["contract"] = "image-build-verification-environment-v2"
        value["execution_environment"]["digest"] = execution_environment_digest(
            value["execution_environment"]["descriptor"])
        value["id"] = producer_id({k: v for k, v in value.items() if k != "id"})
        with self.assertRaises(RecordError):
            verification_execution(value)

    def test_descriptor_rejects_mutable_locator_and_secret_fields(self):
        for domain, key in (("runtime", "invocation_id"),
                            ("root", "root_path"),
                            ("network", "api_token")):
            env = descriptor()
            env[domain][key] = "not-canonical-environment-evidence"
            value = observation_v2()
            value["execution_environment"]["descriptor"] = env
            value["execution_environment"]["digest"] = (
                "sha256:" + hashlib.sha256(canonical(env)).hexdigest())
            value["id"] = producer_id({k: v for k, v in value.items() if k != "id"})
            with self.assertRaises(RecordError):
                verification_execution(value)

    def test_image_build_v1_candidate_ingestion_still_works(self):
        value = observation_v1()
        records = ingest_image_build_candidate(candidate(value["subject"]["generation_id"], [value]))
        self.assertEqual(record_id(records[0]), V1_RECORD_ID)

    def test_image_build_v2_candidate_ingestion_creates_enriched_record(self):
        value = observation_v2()
        record = ingest_image_build_candidate(
            candidate(value["subject"]["generation_id"], [value]))[0]
        self.assertEqual(record["data"]["producer"]["contract"],
                         "image-build-verification-observation-v2")
        self.assertEqual(record["data"]["execution_environment"]["contract"],
                         "image-build-verification-environment-v1")

    def test_mixed_legacy_and_enriched_records_coexist_in_store(self):
        legacy = verification_execution(observation_v1())
        enriched = verification_execution(observation_v2())
        with tempfile.TemporaryDirectory() as directory:
            store = Store(directory)
            legacy_id = store.put(legacy)
            enriched_id = store.put(enriched)
            self.assertNotEqual(legacy_id, enriched_id)
            self.assertEqual(store.get(legacy_id), legacy)
            self.assertEqual(store.get(enriched_id), enriched)

    def test_generation_v2_ingestion_and_snapshot_closure(self):
        bundle, _, _ = fixture()
        generation_id = bundle["records"][bundle["roots"][0]]["data"]["generation_id"]
        root_digest = "sha256:" + "4" * 64
        enriched = observation_v2(generation_id, root_digest)
        export = generation_export(bundle, [enriched])

        execution = ingest_image_build_generation(export, bundle)[0]
        self.assertIn("execution_environment", execution["data"])

        new_records = ingest_image_build_snapshot(export, bundle)
        snapshot = new_records[-1]
        self.assertIn(record_id(execution),
                      snapshot["data"]["observations"]["verification_executions"])

        records = {**bundle["records"],
                   **{record_id(record): record for record in new_records}}
        report = inspect({"schema_version": 1, "roots": [record_id(snapshot)],
                          "records": records})
        self.assertTrue(report["reference_closure_complete"])
        self.assertEqual(report["snapshots"][0]["record_set_digest"],
                         snapshot["data"]["record_set_digest"])
        env = report["verification"][0]["environment_evidence"]
        self.assertEqual(env["kind"], "versioned")
        self.assertEqual(env["execution_environment"]["descriptor"], descriptor())
        self.assertEqual(env["producer_policy_digest"], "sha256:" + "5" * 64)

    def test_snapshot_can_mix_legacy_and_enriched_executions(self):
        bundle, _, _ = fixture()
        generation_id = bundle["records"][bundle["roots"][0]]["data"]["generation_id"]
        root_digest = "sha256:" + "4" * 64
        legacy = observation_v1(generation_id, root_digest)
        enriched = observation_v2(generation_id, root_digest)
        export = generation_export(bundle, [legacy, enriched])
        new_records = ingest_image_build_snapshot(export, bundle)
        snapshot = new_records[-1]
        self.assertEqual(
            len(snapshot["data"]["observations"]["verification_executions"]), 2)
        records = {**bundle["records"],
                   **{record_id(record): record for record in new_records}}
        report = inspect({"schema_version": 1, "roots": [record_id(snapshot)],
                          "records": records})
        kinds = {item["environment_evidence"]["kind"]
                 for item in report["verification"]}
        self.assertEqual(kinds, {"legacy-opaque", "versioned"})

    def test_inspection_exposes_evidence_not_comparability_policy(self):
        legacy = verification_execution(observation_v1())
        enriched = verification_execution(observation_v2())
        records = {record_id(legacy): legacy, record_id(enriched): enriched}
        report = inspect({"schema_version": 1, "roots": sorted(records),
                          "records": records})
        evidence = {item["environment_evidence"]["kind"]:
                    item["environment_evidence"] for item in report["verification"]}
        self.assertEqual(evidence["legacy-opaque"], {
            "kind": "legacy-opaque",
            "environment_digest": "sha256:" + "2" * 64,
            "execution_environment": None,
            "producer_policy_digest": None,
        })
        self.assertEqual(set(evidence["versioned"]), {
            "kind", "environment_digest", "execution_environment",
            "producer_policy_digest"})
        for item in report["verification"]:
            self.assertNotIn("comparable", item)
            self.assertNotIn("regression", item)
            self.assertNotIn("equivalent", item)


if __name__ == "__main__":
    unittest.main()
