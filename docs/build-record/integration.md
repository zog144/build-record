# Integration guide

The shared schema remains version 1. Image-build implements an opt-in package
producer and, with its owner configuration schema 2 (`generation_contract=rootfs-v1`),
a normal image assembly/generation producer. Saved owner configuration schema 1
retains package-only behavior. See [image-build producer integration](../image-build/build-record-integration.md).
Build-trace 0.7 consumes package, generation, reused-output and material records
read-only. Controlled live generation acceptance has passed; each real producer
path still needs coverage checks. Archive-mirror integration remains separate.
No deployment is migrated automatically. See the [independent generation audit](generation-audit.md).

Package output artifacts are inventories; the generation producer additionally
retains actual normalized rootfs archive bytes and a content inventory. Existing
upstream/runtime/patch-classification gaps propagate through the generation graph.
A valid closed graph must not be relabeled complete when those gaps remain.

## Ownership

| Owner | Required contribution |
|---|---|
| Monthly pins / image-build | Exact selected month, committed original pin-file bytes/revision, upstream selections |
| archive-mirror | Source bytes keyed by hash, stable retrieval and retention, license/source metadata |
| image-build | Resolved inputs, prepared binding, result, output and assembly records; serialization and recovery |
| build-trace | Job/build locators and retained evidence; read-only projection of captured owner facts |
| station-access | Authorized joined presentation; server-selected host/project scope |
| release-build | Collect generation closure and available artifacts; evaluate release policy separately |

## image-build producer sequence

1. Preserve the selected original monthly file as well as the materialized
   `commit-pin.py` snapshot. Hash raw bytes separately from image-build's normalized
   `monthly_identity` and `source_pins` digests. Those owner digests are not build-record
   record IDs. Put the materialized snapshot in the recipe/material inventory.
2. Resolve sources through the owner's mirror/fetch flow; check actual bytes against
   pins, retain sizes and source descriptors. Null upstream revision in the initial
   monthly set remains null with an explicit gap.
3. Materialize a complete recipe inventory with file digests, patches, resolved
   commands/options, tools and environment. Retain its bytes as a recipe artifact.
   Freeze dependency output/result bindings. Save source-selection and build-inputs.
4. Allocate the owner's immutable attempt identity. Save attempt-start and atomically
   bind its record ID into the existing prepared owner operation **before dispatch**.
   Recover only those inputs. build-record never executes or imports pin/recipe files.
5. Owner command checkpoints retain request/job identities during execution. Record
   stable host/job and build-trace `attempt:<owner-attempt>` locators in the result.
   A process crash before result publication does not authorize a fresh attempt.
6. After confirmed completion and output verification, save package-output, then
   attempt-result. A retry links the previous result and gets a fresh attempt identity.
   Missing outcome remains uncertain; use existing owner recovery controls.
7. Treat final rootfs assembly as its own attempt with purpose=assembly and exact
   package bindings. Capture configuration/deletion/generated-file operations in its
   recipe. Save the rootfs archive and content inventory as assembly output artifacts.
8. Save generation, export/check its closure, verify required bytes, then publish the
   owner generation pointer. A storage error blocks publication. Existing generations
   are imported only as legacy outputs with explicit gaps, without recompilation.

Consumer integration must supply the atomic owner pointer and retention rules;
`Store.put` alone cannot provide an atomic transaction with controller dispatch.
Do not install multiple final results for one attempt. Signing and later resolution
of uncertain results need a separate versioned extension.

## Integration observations for integrate-observe foundations

Image-build commit `6ef51f2d498159b7d667be0322a977563de994c5` introduced
`image-build-integration-observations-v1` and
`image-build-candidate-verifications-v1`. Build-record 0.8.2 has a strict adapter in
`zog.build_record.image_build`. It recomputes producer observation identities, rejects
unknown schema versions/fields, binds published envelopes to the canonical generation
root, and canonicalizes named terminal results as `verification-execution` records.

The canonical execution retains image-build's producer observation ID, logical check,
definition digest, candidate generation/root inventory, attempt/sequence, outcome,
environment evidence, execution evidence and timing. It intentionally omits
publication state. Therefore a captured candidate result and the same result observed
through a later generation export produce the same build-record record ID.
Unpublished failed candidates remain representable without inventing a generation
record.

Build-record 0.8.0 accepts both
`image-build-verification-observation-v1` and
`image-build-verification-observation-v2` inside the existing candidate/generation
adapter paths. V1 maps to the byte-compatible legacy canonical execution containing
only opaque `environment_digest`. V2 must contain
`execution_environment={contract,digest,descriptor}` using
`image-build-verification-environment-v1` plus a separate
`producer_policy_digest`; it maps to the enriched canonical execution variant and
does not contain the legacy field. The adapter recomputes both the producer
observation identity and the descriptor digest and rejects unknown contracts, extra
fields, forbidden mutable/secret descriptor keys, and digest mismatches. It never
derives missing v2 evidence from current policy or other producer files.

Build-record 0.4.0 canonicalizes the source portion of that envelope as separate
`source-repository`, `source-reference`, `source-archive`,
`source-archive-association` and `source-provenance` records. Repository strings
use exact-literal identity; Git commits, tags, opaque references and unknowns remain
distinct. Archive bytes are independent of filenames/download URLs, and the initial
archive/reference association remains explicitly
`declared-not-independently-reproduced`.

Build-record 0.5.0 also canonicalizes the eight image-build v1 relationship types as
`relationship-observation` records. Artifact interface requirements/provisions and
interpreter observations remain factual interfaces, not inferred dependency
resolutions. Declared build/test/runtime package dependencies remain package-name
declarations. Only `used-build-output` binds a concrete dependency output, and its
target/evidence must already match the consuming package's canonical `build-inputs`.

Build-record 0.6.0 canonicalizes logical verification definitions separately as
`verification-check` records and translates image-build's declared collection scope,
collector identity, counts and explicit gaps into `observation-coverage` records.
A zero-count complete coverage record is distinguishable from partial or unavailable
collection. The schema also reserves explicit `not-performed` and
`not-applicable` states for future producers.

Build-record 0.7.0 adds `generation-observation-snapshot` as the stable consumer
boundary. One snapshot binds an immutable generation/root inventory to the exact
included canonical source, relationship, verification-definition, execution and
coverage records. Its record-set digest changes when the included set changes; the
generation and all earlier snapshots remain immutable. The image-build adapter can
canonicalize one whole v1 envelope and return the new records dependency-first with
the snapshot last.

Build-record 0.7.2 makes production publication responsibilities explicit. The
adapter constructs records only; image-build must persist them dependency-first,
persist the snapshot last, and then durably bind that exact snapshot ID into owner
state. `Store.put(snapshot)` does not make it current. Recovery must reuse the same
owner-selected snapshot identity after interruption. Store-wide discovery, newest-ID
heuristics and snapshot chronology inference are forbidden as publication mechanisms.

Inspection now exposes `reference_closure_complete`, `missing_record_count`,
`declared_gap_free`, `declared_gap_count`, `declared_gap_record_count` and
`declared_gap_summary`. The existing `complete` field is retained unchanged as the
compatibility aggregate of complete reference closure and zero declared gaps.
Observation coverage is independent and remains available in `coverage`.

Build-record 0.8.1 freezes both legacy and enriched verification-execution golden
identities and supplies a stdlib-only consumer example for the normalized
`environment_evidence` inspection surface. This is intended to let build-trace
consume canonical environment evidence without importing image-build or reconstructing
producer policy.

Build-record 0.8.2 pins the concrete descriptor emitted by image-build
`a714fe8c0fb2e3a50183937d9f3869e42ee0587d`'s v2 verification fixture. The fixture
confirms direct acceptance of device-profile digest, execution UID/GID, prepared-root
policy, network mode, timeout strings, BoxControl build-job executor, guest working
directory, sorted process environment and resource-limit strings. No adapter/schema
change was required.

This layer still does not classify regressions, select a preferred verification
execution, decide environment equivalence, resolve repository aliases, infer SONAME
providers, claim ABI compatibility, or claim that a declared source reference
reproduces an archive. Build-trace should consume the explicit closure/gap/coverage
fields and the normalized verification `environment_evidence` projection rather
than importing image-build logic.

## build-trace

Retain existing source ownership: image-build owns build facts; build-trace projects
them. Add record IDs to owner captures, then expose a provenance link in inspection.
Do not infer a retry from directory names or reconstruct inputs from today's recipes.
The locator shape is `{host_id, build_id}`; inspection still selects the authorized
project root. The library does not dereference these locators or assess log retention.
If durable evidence is exported, preserve its bytes and digest as an artifact in
addition to the live locator. No new build-trace database or daemon is required.

## archive-mirror and release consumers

Resolve source digests to authorized retrieval locations. Neither URLs nor registry
credentials belong in the canonical identity. A mirror move therefore does not
change provenance. For an offline release, copy the exported record closure and
required external artifacts into the release transport and supply an explicit local
path map for byte verification. The JSON export itself contains only metadata.
Keep expected missing artifacts and log retention separate from declared build
outcomes. License inventories can be retained materials/reports; build-record does
not decide whether their contents satisfy release licensing policy.

## Acceptance gate for the first real adapter

Use one disposable package pipeline with a monthly pin, mirror bytes and retained
trace. Exercise a failed attempt and successful retry; reopen after preparation;
change today's pin and prove recovery still uses the original binding; remove a
required material and prove execution/publication blocks. Tamper source and recipe
bytes and prove verification fails. Check final assembly configuration is covered.
Export the closure, inspect it independently, and verify the final artifact bytes.
Keep old generations accurately marked as legacy. The example in this repository
is a local fixture, not evidence of a live deployment. Cross-program live evidence
and exact tested revisions were retained as private dated verification evidence. This page does not independently establish their current deployment or acceptance.


## Implemented generation owner references

Image-build publishes the canonical root in the immutable generation manifest's
`build_record.record` field after validating the closure and artifact bytes. Its
assembly-start identity is JSON `[host, project, owner_attempt, "@rootfs-assembly"]`;
its canonical generation subject identity is JSON `[host, project, owner_generation]`.
These are adapter conventions; the library still treats owner identities as opaque.
The canonical SHA256 record ID remains distinct from the owner generation fingerprint.

`Store.bundle([generation_record_id])` exports installed package bindings, transitive
build dependencies, original sources/pins/recipes and failed retry history through
the existing typed edges. No image-build or build-trace import is needed for inspection.
Trace/job references are locators; live log availability remains outside this library.

Image-build's replayable membership indexes point canonical output/attempt-start IDs
to generation roots. Readers must validate membership from the canonical graph and
respect scope; an index is not an alternative provenance record. Installed, assembly
and dependency/history membership are distinguished. The indexes are owner state,
not a new build-record schema. Rootfs serialization/retention and publication remain
producer responsibilities; the schema's artifact descriptor is not an inventory-file
substitute for actual rootfs archive bytes.
