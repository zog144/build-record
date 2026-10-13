# build-record

**Documentation:** [Canonical contract](docs/build-record/contract.md) · [Producer/consumer integration](docs/build-record/integration.md) · [Verification environment](docs/build-record/verification-environment.md) · [Generation audit](docs/build-record/generation-audit.md).

A small Python library and offline CLI for the Zog build provenance contract.
It joins monthly source selections, exact build inputs, attempts, package outputs,
rootfs generations and build-trace evidence references. Version **0.8.2**, Python
**3.10+**, no runtime dependencies or daemon. Development branch: **unstable**.

The first pass implements the contract and controlled integration fixtures.
An opt-in image-build package/generation producer and read-only build-trace package
consumer are implemented; see the [integration guide](docs/build-record/integration.md). Existing
installations are not migrated automatically. Generation/material inspection in
build-trace and controlled live acceptance are implemented; real-generation coverage
must still be checked for each producer path. Archive-mirror integration remains
separate work. First-party source in this public repository is available under
`BSD-3-Clause OR GPL-3.0-only`; third-party obligations remain separate.

Image-build integration-observation v1 envelopes can now be validated and their named
terminal checks canonicalized as immutable `verification-execution` records. Candidate
and later-published views preserve the same execution identity; generation publication
is validated by the adapter rather than written into the execution record.

Version 0.4.0 also canonicalizes frozen source-development provenance without changing
legacy `source-selection` records. Exact repository literals, typed Git/tag/opaque/
unknown references, exact archive-byte identities and explicitly declared
archive-to-reference associations are separate records. Download URLs remain retained
producer facts, not repository or archive identities.

Version 0.5.0 canonicalizes image-build's typed integration relationships as
`relationship-observation` records. ELF SONAME requirements/provisions and
interpreter observations remain interface facts; declared package dependencies remain
declarations. Only `used-build-output` may bind a dependency to a concrete canonical
package output, and that binding must already exist in the declaring package's frozen
`build-inputs`.

Version 0.6.0 separates logical verification checks from their executions with
immutable `verification-check` records, and adds canonical
`observation-coverage` records. Coverage records carry a declared scope, collector
implementation digest, explicit outcome and observation count, so zero observations
can mean “examined and empty” without being confused with partial, unavailable,
not-performed or not-applicable collection.

Version 0.7.0 adds immutable `generation-observation-snapshot` records. A snapshot
binds one canonical generation to the exact categorized set of source, relationship,
verification-check, verification-execution and coverage records plus a digest of that
record set. Later observations create a new snapshot; they never rewrite the
generation or an earlier snapshot.

Version 0.7.1 keeps schema-1 timestamp syntax unchanged while parsing its permitted
1–6 fractional second digits consistently on Python 3.10 and newer.

Version 0.7.2 separates reference closure from declared provenance/evidence gaps in
inspection output. The compatibility `complete` field keeps its historical meaning:
it is true only when reference closure is complete **and** no reachable record declares
a gap. Observation coverage remains a separate third concept.

Version 0.8.0 keeps legacy verification execution records byte-for-byte valid while
adding an enriched `verification-execution` variant with an explicit versioned
execution-environment descriptor and a separately retained broader producer-policy
digest. Inspection exposes the distinction as factual environment evidence; build-record
does not decide whether two environments are comparable or whether a change is a
regression.

Version 0.8.1 hardens that contract with frozen legacy/enriched canonical identities,
adversarial descriptor-boundary coverage, and a standalone consumer fixture for the
stable `inspect().verification[].environment_evidence` JSON surface. See
`docs/build-record/verification-environment.md`.

Version 0.8.2 pins a compatibility fixture to image-build
`a714fe8c0fb2e3a50183937d9f3869e42ee0587d`, including its concrete
`image-build-verification-environment-v1` descriptor shape. No canonical schema or
adapter behavior changes in this release.

The installable Python component now lives at `src/zog/build_record/` and its
canonical import path is `zog.build_record`. The repository deliberately does not
provide a top-level `build_record` compatibility package. Public PyPI publication is
owned by release-build and occurs only in the aggregate `zog` distribution; this
repository's project metadata exists for development installation and testing.

## Start

Run from this checkout (no installation required):

```sh
python3 -m unittest discover -s tests -v
python3 -m zog.build_record --help
PYTHONPATH=. python3 examples/local_pipeline.py /tmp/build-record-demo
python3 -m zog.build_record inspect /tmp/build-record-demo/bundle.json
python3 -m zog.build_record verify /tmp/build-record-demo/bundle.json \
  --artifacts /tmp/build-record-demo/artifact-paths.json
```

Use an unused destination for the example. Its files represent a controlled failed
attempt, successful retry and assembled generation; they are not real source
archives, compiled packages or bootable rootfs artifacts. Restart/reopen behavior
is exercised locally, not through a host reboot or controller.

Optional installation exposes `build-record` as a command:

```sh
python3 -m pip install .
```

## Library

```python
from zog.build_record import Store, make_record, inspect, verify_artifacts

store = Store('/trusted/state/build-record/records')
# data is a schema-1 field mapping; see the contract and runnable example.
prepared = make_record('attempt-start', {
    'attempt_id': 'host-identity:project-identity:attempt-identity',
    'inputs': inputs_record_id,
    'prepared_at': '2026-10-02T12:00:00Z',
    'retry_of': None,
})
prepared_id = store.put(prepared)  # complete this before dispatch
# Persist prepared_id in the owner's operation record. Recover that same binding.
bundle = store.bundle([generation_record_id])
report = inspect(bundle)
verified = verify_artifacts(bundle, authorized_digest_to_local_path_mapping)
```

`Store.put` writes one immutable content-addressed record. It does not schedule a
build, allocate global attempt IDs, finalize owner operations, authorize a retry,
resolve uncertainty or make multi-record transactions. Persisting a
`generation-observation-snapshot` likewise does not publish it as current or
preferred. Owner serialization, durable snapshot selection/publication and recovery
remain image-build's responsibility; consumers must not scan the record store and
infer a newest snapshot.

## CLI

| Command | Result |
|---|---|
| `validate RECORD.json` | Validate a record and compute its SHA256 identity |
| `put STORE RECORD.json` | Durably insert one record, idempotently |
| `export STORE ROOT_ID [ROOT_ID ...]` | Emit the complete reachable metadata bundle |
| `inspect BUNDLE.json` | Check graph bindings and report gaps/missing records |
| `verify BUNDLE.json --artifacts PATHS.json` | Verify bytes at explicit local paths |
| `compare BEFORE.json AFTER.json` | Compare package input identities/fields and assembly input identity |
| `audit-generation BUNDLE.json --expected EXPECTED.json [--artifacts PATHS.json]` | Check the independent owner-selected record, generation identity and exact installed package set, plus closure/gaps and optional bytes |

Output is JSON on stdout; export can be redirected to a file. Exit 0 means the
requested operation succeeded, 2 means invalid/unavailable data or an I/O failure,
and 3 means inspection found gaps or requested byte verification was incomplete
or mismatched. Argparse syntax errors use conventional stderr. `inspect` never
claims that artifact bytes or producer authenticity were verified.

Generation audit expectations must come independently from the owner publication,
not be inferred from the export under test. See [generation audit](docs/build-record/generation-audit.md).

## Contract and integration

- [Schema, identity and durability contract](docs/build-record/contract.md)
- [Producer/consumer integration](docs/build-record/integration.md)
- [Runnable local fixture](examples/local_pipeline.py)

Records use SHA256 over a specified canonical JSON encoding. Immutable references
are independent of mutable download URLs and human labels. Exports contain all
reachable **records**, not source archives or log bytes. Artifact and evidence
availability are separate concerns. Signature verification, automatic collection,
retention enforcement, remote APIs and UI are future integrations.

## Public source and history

This component is publicly licensed under `BSD-3-Clause OR GPL-3.0-only`;
see [LICENSE](LICENSE), [LICENSES](LICENSES/) and
[THIRD-PARTY-NOTICES.md](THIRD-PARTY-NOTICES.md). This repository starts a new
public Git history. Earlier private branches, tags, operational evidence and
handoffs are not included. Existing release-build source pins to private commits
must remain historically accurate until a separate public-source selection is
approved and its provenance inventory is regenerated.
