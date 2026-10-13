# Verification environment consumer surface

Build-record 0.8 exposes verification execution-environment evidence through the
ordinary `inspect()` report and the JSON emitted by `build-record inspect`.
Read-only consumers do not need image-build code or image-build storage access.

For every entry in `report["verification"]`, consumers may inspect
`environment_evidence`.

Legacy executions have:

```json
{
  "kind": "legacy-opaque",
  "environment_digest": "sha256:...",
  "execution_environment": null,
  "producer_policy_digest": null
}
```

The legacy digest is historical opaque producer evidence. It must not be treated as
the versioned execution-environment identity.

Enriched executions have:

```json
{
  "kind": "versioned",
  "environment_digest": null,
  "execution_environment": {
    "contract": "image-build-verification-environment-v1",
    "digest": "sha256:...",
    "descriptor": {
      "isolation": {},
      "user": {},
      "root": {},
      "network": {},
      "timeout": {},
      "runtime": {}
    }
  },
  "producer_policy_digest": "sha256:..."
}
```

The descriptor and digest are canonical build-record evidence. The policy digest is a
separate broader producer identity. Build-record makes no equivalence, compatibility,
baseline, or regression judgment from these values.

The repository includes
`examples/verification_environment_consumer.py`, a standalone stdlib-only consumer
of an inspect JSON report. Its tests deliberately ensure it imports neither
`zog.build_record` nor image-build.

## Golden identities

The schema-1 fixture used by build-record's compatibility tests freezes:

- legacy v1 verification-execution:
  `sha256:dfdf36c52d3cdc209800c94385f4f854a9dfe8e5adcfea55d92ef73ad6dfdaca`;
- enriched descriptor digest:
  `sha256:4589f8b4389690d2097142fe57273b23b24ce9fd1e39b8be17871e74a0abdcc0`;
- enriched v2 verification-execution:
  `sha256:78220f767eddea75245bbbe378506d0a177d2dd1bada86bf826ded2451234fdb`.

These are regression fixtures, not special production IDs.

Build-record 0.8.2 also freezes a fixture copied from image-build
`a714fe8c0fb2e3a50183937d9f3869e42ee0587d`'s verification-environment tests. That
producer fixture has:

- environment digest:
  `sha256:4d80eb5935e36049f32de5d38480441857fce43d0574027d14b1fd16c2c57bee`;
- producer observation ID:
  `sha256:87afece69e6bdc74ab3cf1e66fc9e9f0d9de39a43b4f98ef306d3c3e38ecf86e`;
- canonical build-record verification-execution ID:
  `sha256:75c817a4bd7f42b6f83945b1af17a33ba0104836e8b316c038ea728721f94934`.

Its descriptor retains the producer's concrete semantics: device-profile digest,
UID/GID, prepared-rootfs/separate-workspace policy, network mode, decimal timeout
strings, BoxControl build-job executor, guest `working_directory`, sorted controlled
process environment and decimal-string resource limits. The guest working directory is
intentionally retained; host root/source/output filesystem paths remain excluded.

The enriched producer contract is
`image-build-verification-observation-v2`, carrying
`image-build-verification-environment-v1`. Build-record validates the full
descriptor contract and recomputes the descriptor digest before creating the canonical
execution record.
