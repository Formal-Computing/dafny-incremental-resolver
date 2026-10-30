# Safety envelope (experimental and conditional)

| Context | Policy / evidence |
|---|---|
| Independent same-file module, stable token origins | Experimental precision HIT supported by October 29 focused test |
| Dependency type/rename edits | 30 October diagnostic comparison passed; only sampled |
| Shadowing and introducing name in local module | 30 October diagnostic comparison passed; negative scope dependencies not exhaustively represented |
| Adding duplicate/new module | Module roster hash mitigates; three revision fixture compared; not proof for all module scopes |
| Invalid intermediate source and recovery | Do not persist error-bearing results; four-revision diagnostic trace compared |
| Prefix/synthetic/multi-file module | Fall back locally to CloneId; global options still untracked |
| Shifting source position or URI | Position-sensitive token key causes conservative miss if covered locations move |
| Project/configuration/compiler option changes | Not qualified for production reuse; full fresh resolution required until options fingerprint and cache lifecycle audited |
| Plugin/rewriter state | Not qualified; safe conservative fresh resolution required |
| Intra-module declaration-level caching | Not implemented |

Run `scripts/compare_differential.py` over full four-mode JSON trace output; it fails closed on missing data or differences. This verifies extracted diagnostics, *not* complete semantic equivalence.
