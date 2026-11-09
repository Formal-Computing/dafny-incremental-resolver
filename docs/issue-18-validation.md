# Issue 18 differential revisions

The pinned LSP differential trace now includes two cases:

- `provider_visibility` changes the export/type visibility in `VisibilityA`
  while the consumer module text remains byte-identical. The fresh resolver is
  expected to report the consumer's `int` assignment invalid when `T` becomes
  `bool`, valid again when it returns to `int`, and invalid when `T` is no
  longer exported. `VisibilityB` remains an imported control provider until the
  final revision.
- `negative_alias` looks up `P.Missing()` through `import P = Provider`. The
  provider's export set transitions through missing, present, missing, present.
  Expected fresh observations are diagnostic counts `(1, 0, 1, 0)` and semantic
  definition/hover observations `(absent, present, absent, present)`.

The pinned immutable-export workflow compares fresh and candidate traces. It
requires byte-identical consumer source, checks fresh-oracle diagnostics and
definition/hover observations against expected states, then compares candidate
observations. Python selftests and `calibrate_differential.py` mutate the
withdrawn-member revision into a stale positive result and require rejection.
The integration workflow runs against upstream Dafny commit
`de36f2ec1f9c530080eff7929ae28229f45da069`.

**Syntax verification: NOT VERIFIED locally.** This environment has neither
`dotnet` nor a Dafny executable and cannot access GitHub. The pinned integration
workflow build and LSP run are the acceptance gate for Dafny syntax and actual
resolution behavior. The test deliberately does not assume that hover exists
for unresolved lookups.

Run locally where the pinned integration environment is available:

```sh
python3 scripts/test_compare_differential.py
python3 scripts/compare_immutable_export.py research-results
python3 scripts/calibrate_differential.py research-results
```
