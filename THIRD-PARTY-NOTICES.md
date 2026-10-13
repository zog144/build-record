# build-record: public source and dependency notices

The original first-party software and documentation in this public repository
are licensed, at your option, under `BSD-3-Clause OR GPL-3.0-only`; see
[LICENSE](LICENSE) and the full text in [LICENSES](LICENSES/).

## Dependency boundaries

build-record 0.8.2 is an offline Python library with no declared runtime
third-party dependencies. Its build-system tool (setuptools) is obtained
separately and retains its original license. Its integration adapters describe
image-build and build-trace protocols; this repository does not copy or
relicense their implementation or third-party build inputs.

## Scope of the source publication

Examples and tests use synthetic records and controlled local fixtures;
they do not contain deployed host evidence, runtime credentials, release
artifacts or live build records. The private repository's historical commits,
handoff tags, private operational evidence and old GitHub Actions logs are not
included in the clean public repository. Preserve provenance to previous
private records separately, rather than presenting new public Git identities
as the identities of previously verified generations.

This component is developed independently but is published to PyPI only
inside release-build's aggregate `zog` distribution.
