"""Standalone consumer of build-record inspect() verification environment evidence.

This example intentionally imports no Zog component. It demonstrates the read-only
surface available to build-trace or another consumer after build-record inspection.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def environment_rows(report):
    """Project factual environment evidence without making compatibility judgments."""
    verification = report.get("verification")
    if type(verification) is not list:
        raise ValueError("inspect report must contain a verification list")
    rows = []
    for execution in verification:
        evidence = execution.get("environment_evidence")
        if type(evidence) is not dict:
            raise ValueError("verification execution lacks environment_evidence")
        kind = evidence.get("kind")
        if kind == "legacy-opaque":
            rows.append({
                "record": execution["record"],
                "kind": kind,
                "legacy_environment_digest": evidence["environment_digest"],
                "execution_environment_contract": None,
                "execution_environment_digest": None,
                "execution_environment_descriptor": None,
                "producer_policy_digest": None,
            })
        elif kind == "versioned":
            environment = evidence.get("execution_environment")
            if type(environment) is not dict:
                raise ValueError("versioned evidence lacks execution_environment")
            rows.append({
                "record": execution["record"],
                "kind": kind,
                "legacy_environment_digest": None,
                "execution_environment_contract": environment["contract"],
                "execution_environment_digest": environment["digest"],
                "execution_environment_descriptor": environment["descriptor"],
                "producer_policy_digest": evidence["producer_policy_digest"],
            })
        else:
            raise ValueError("unsupported environment evidence kind")
    return rows


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("report", help="JSON output from build-record inspect")
    args = parser.parse_args(argv)
    report = json.loads(Path(args.report).read_text(encoding="utf-8"))
    print(json.dumps(environment_rows(report), sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
