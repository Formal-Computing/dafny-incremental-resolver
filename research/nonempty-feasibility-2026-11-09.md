# Nonempty resolver skip feasibility audit (2026-11-09)

**Decision: NO-GO.** No genuinely nonempty Dafny module or resolver branch is currently justified for skipping resolution. The narrowest supported optimization remains the pinned `ModuleExportDecl` no-op dispatch, whose semantic payload is empty. It is not a nonempty-module result. This audit makes no implementation or test claim and does not authorize a nonempty cache.

## Scope and evidence boundary

Target upstream is `dafny-lang/dafny@de36f2ec1f9c530080eff7929ae28229f45da069`. The source checkout is not available in this workspace, and network lookup is unavailable. Consequently, this audit independently verifies repository artifacts (the #21/#22 maps, pinned-source audit documents, and patches 0005/0006/0007) but does not claim fresh line-by-line inspection of upstream C#. The concrete dispatch facts below are inherited source-pinned claims recorded in `research/nonempty-real-dafny-eligibility-audit.md` and `research/immutable-export-summary-refinement.md`; re-open the pinned source before implementation.

Issue #29's request is a feasibility audit only. The current branch is `codex/nonempty-01-20261109`, based on `codex/bridge-02-20261109` (#37), which contains #22 and is stacked on #35. The explicit research dependencies are #17, #18, #21, #22, and #25. This deliverable does not resolve or supersede them.

## Branch and class assessment

| Candidate | What is known from pinned audit artifacts | Feasibility |
|---|---|---|
| `ModuleExportDecl` empty dispatch | `ModuleResolver.ResolveModuleDeclaration` is recorded as having an empty branch; patch 0005 validates a fresh result has current declaration identity, empty signatures, empty class members, and no messages, and on later hits constructs a new wrapper with fresh empty collections. | Existing narrow GO only for this empty branch, subject to pin. Excluded from the nonempty question. |
| Ordinary `LiteralModuleDecl` | Recorded to call `literalModuleDecl.Resolve` and publish `ModuleSignature`; the result can carry signatures, class-member mappings, reporter output and resolved AST. | NO-GO. No complete key or current-compilation graph reconstruction contract. |
| `AliasModuleDecl` | Recorded to resolve target/export visibility and potentially update `Signature`. | NO-GO. Imports, target identity, export view, substitutions/refinement and resulting signature are not fully represented. |
| `AbstractModuleDecl` | Recorded to resolve exports / make an abstract signature and update `Signature`. | NO-GO. Same graph and context gaps; no isolated no-op subbranch is justified. |
| “No declarations”, no diagnostics, or symbol-name-equal literal module | Not a source branch contract. Empty observed names/messages do not establish absence of resolver side effects or dependencies. Patch 0006 stores names only after fresh resolution; patch 0007 deliberately collides only that audit bucket. | NO-GO. Observation equality does not authorize skipped work. |

Thus there is no justified nonempty class at this time. A literal module may be the smallest useful *research target* because it is the normal nonempty path, but it is not an eligible cache class absent a stronger source contract.

## Why the nonempty cases are not safe to skip

**Input semantic context.** Patch 0001's candidate key and the source-context audit cover token text/origin/trivia, dependency hashes, module roster and builtins in the experimental path, but explicitly do not certify complete context. The registry marks successful and failed lookup dependencies, import/export views, shadowing, aliases/refinements, options/builtins, plugins/rewriters and cancellation incomplete or unverified. A new declaration can make a previously failed lookup succeed while consumer text is unchanged. Opened imports/export selection and nearer shadowing can alter binding without changing the candidate module body. An unknown dependency or environment input must therefore force fresh resolution.

**Imports and exports.** The architecture audit records explicit module dependency binding and a topological resolver walk, but says completeness for implicit/failed lookups, exported views and plugins is unestablished. Alias and abstract branches have export visibility semantics. A module's apparent positive dependency list cannot prove all negative or visibility dependencies are captured. Registry categories are obligations, not demonstrated key fields.

**Options, plugins, and rewriters.** The registry requires all resolver/compiler options and builtin identity, plus plugin/rewriter identity, version, configuration, order, state and effects. These are not proven in the key. The source mapping names pre/post rewriters in `ProgramResolver`; their effects could modify declarations, signatures, diagnostics or later observations. The resolver should run fresh whenever this environment cannot be proven identical and effect-free.

**AST, signatures, and ownership.** The source-to-proof map describes `ModuleResolutionResult` as holding a resolved `ModuleDecl`, mutable signature and class-member dictionaries, and a `BatchErrorReporter`. The architecture audit says the result is reattached into the current `Program`. No nonempty serializer/reconstructor establishes current-compilation ownership for all AST links, tokens, scopes, `ModuleSignature`, members, type references, and declaration identities. Reusing the previous graph risks stale object identity even where names match. Reconstructing only names or a top-level wrapper is insufficient.

**Reporter and observable effects.** A fresh resolution may produce messages with source provenance, and reporter state is part of the result. Empty diagnostic snapshots on one execution do not prove that skipping preserves diagnostic production on another context. Beyond LSP diagnostics and definition/hover, final verification inputs/outcomes and resolver side effects are relevant. Existing differential runs are finite sampled evidence, not a universal refinement proof.

**Resolver work and boundary.** The architecture audit records program-wide binding/dependency graph construction, cycle handling, topological ordering, rewriter setup and result composition. A module-level hit may still leave much of that work intact, while skipping `ModuleResolver` risks omitting module-specific side effects. No nonempty end-to-end savings claim follows from candidate key equality.

## Actual anchors versus unknowns

**Pinned anchors documented in repository artifacts:** `ModuleResolver.ResolveModuleDeclaration` branch labels (`ModuleExportDecl`, `LiteralModuleDecl`, `AliasModuleDecl`, `AbstractModuleDecl`); `ModuleResolutionResult` fields; `ProgramResolver` dependency graph, declaration result processing and rewriter lifecycle; `CachingResolver.GetHash` and persistent cache; `ModuleDecl` clone/token origin. Relevant artifact anchors include `research/nonempty-real-dafny-eligibility-audit.md`, `research/architecture-audit.md`, `research/source-context-audit.json`, `research/source-to-proof-mapping.json`, and patches 0005-0007.

**Not independently confirmed here / unknown:** exact pinned C# statements and complete call graph; every lookup call site including absent-name probes; export/open-import visibility propagation; exhaustive option and plugin state inputs; pre/post rewriter mutation set; cancellation and partial-result/cache-insertion behavior; all object-identity edges and reporter ownership; whether any narrower nonempty dispatch branch has a provably empty side-effect trace. Treat these as open source audits, not implicit negatives.

## Strict operational gate (fail closed)

Until every prerequisite below is completed and reviewed against the exact pin, every truly nonempty module MUST take the fresh resolver path. A candidate hit, matching hash, matching immutable names, empty diagnostics, or matching selected LSP observations MUST NOT skip resolver work. Missing, ambiguous, unsupported, or changed context means MISS and fresh resolution. There is no nonempty opt-in flag authorized by this report.

## Prerequisites before reconsidering GO

1. Re-audit exact source at the pinned SHA and record hashes/line anchors for complete dispatch and side-effect call graph.
2. Select one nonempty source branch and specify all direct and indirect semantic inputs, including successful and failed lookups, scope precedence, imports/exports/refinements, module roster, source origin, options, builtins, rewriters/plugins and cancellation.
3. Define a sufficient immutable summary and key, with collision-safe equality or a structural identity contract; explicitly account for negative dependencies.
4. Specify a current-compilation reconstruction for every AST/signature/type/member/scope/token/reporting edge and all observable side effects; show how diagnostics and verifier inputs are preserved.
5. Establish a source-to-model refinement argument for the actual C# transition, not merely abstract Dafny lemmas or name-only observations.
6. Run a minimal pinned integration experiment and adversarial differential suite, including negative lookup becoming positive, import/export changes, shadowing, options, rewriter/plugin effects, cancellation/recovery, ownership checks, exact diagnostics/bindings and terminal verifier results. Demonstrate that resolver work is actually skipped and measure the skipped work; do not infer speedup from a hit counter.

## Exact minimal experiment

After prerequisites 1-5 identify one candidate branch, create a separate, opt-in **audit-only** instrumented build at the exact pin. Keep baseline parsing and resolver behavior unchanged except for counters around the candidate's resolver call. Prepare two adjacent revisions of one smallest candidate module: (A) stable nonempty module with one declaration and a client reference; (B) unchanged candidate text with one context mutation that the proposed key claims to track (start with adding a declaration that changes a previously absent lookup to present). Run baseline fresh resolution and instrumented candidate side by side in isolated processes. On a candidate HIT, assert (i) resolver-call counter decreases exactly for that branch, (ii) every returned graph object belongs to the current compilation, and (iii) exact diagnostic snapshots, bindings/definition targets, and terminal verifier outcomes match baseline. Then inject one omitted-context mutation at a time (opened import/export view, shadowing, option, rewriter/plugin, cancellation/recovery); the gate must produce a MISS for each, otherwise reject the key. Archive source hashes, inputs, traces, and results. This is a falsification experiment, not a theorem; do not launch it before a complete candidate contract exists, and do not report success until actually run.

## Recommendation

**NO-GO for any nonempty resolver skip.** Continue research only: re-audit the pinned call graph and semantic inputs; resolve the #17/#18/#21/#22/#25 dependencies; define one candidate's full side-effect and ownership contract; then propose the minimal experiment above for review. The only established narrow skip in the repository is the separately validated, pinned empty export-dispatch summary. No theorem or successful new Dafny run is claimed here.
