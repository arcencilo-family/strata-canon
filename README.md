# Strata 0–3 — A Reasoning and Alignment Scaffold for AI Systems

Strata 0–3 is a compact, model-legible framework intended to support epistemic honesty, boundary discipline, corrigibility, useful refusal, and escalation in artificial-intelligence systems.

It is designed primarily as an addition to a system prompt or constitutional reasoning layer. It is **not** a complete safety system and does not replace technical permissions, authentication, sandboxing, privacy controls, domain-specific policies, monitoring, or human oversight.

## What is included

The publication set lives in [`canon/`](canon/):

- [`Stratum-0_Primitives_v1.2.md`](canon/Stratum-0_Primitives_v1.2.md) — minimal primitives and epistemic boundaries;
- [`Stratum-1_Minimal-Dynamics_v0.4.md`](canon/Stratum-1_Minimal-Dynamics_v0.4.md) — trajectories, persistence, return, and adaptation;
- [`Stratum-2_Orientation_v0.4.md`](canon/Stratum-2_Orientation_v0.4.md) — Curiosity, Truth, Agency, and Beauty;
- [`Stratum-3_Operational-Permissions_v0.4.md`](canon/Stratum-3_Operational-Permissions_v0.4.md) — ten operational permissions, refusal, and escalation;
- [`Strata-0-3_AI-Kernel_v0.5.md`](canon/Strata-0-3_AI-Kernel_v0.5.md) — compact system-prompt-oriented formulation;
- [`CANON-MANIFEST.md`](canon/CANON-MANIFEST.md) — canonical status, lineage, and integrity receipts.

For initial experiments, start with the AI Kernel. The full strata explain the distinctions compressed into it.

## Intended use

A typical placement is:

```text
platform safety and authority rules
    → Strata 0–3 AI Kernel
    → task-specific operating instructions
    → tool permissions and environment facts
    → user request
```

Higher-priority platform rules still control. Strata provides a reasoning orientation inside those boundaries; it does not grant access or override authority.

## Evidence status

The framework has undergone iterative adversarial review and small synthetic behavioral tests across several model families. Those tests provide encouraging design evidence that the text is legible and can support appropriate stopping, revision, refusal, useful continuation, and epistemic qualification.

They do **not** establish alignment at scale, deployment safety, immunity to adversarial pressure, durable learning, or reliable behavior across all models and contexts. Treat Strata as a tested prototype scaffold and research object—not a scientifically proven alignment solution.

See [`LIMITATIONS.md`](LIMITATIONS.md) for the claim boundary.

## Canon and adaptations

Files under [`canon/`](canon/) are the exact publication release identified by the manifest. You may adapt them under CC BY 4.0, but modified versions must be clearly marked as adaptations and must not be represented as the canonical Strata release maintained by this project.

The license itself already requires attribution and indication of changes. The request not to call modified versions canonical is a provenance and naming rule, not an attempt to prohibit adaptation.

## Related implementation

The sibling repository **BES Skeptical Learning Ledger — Reference Engine** explores a narrow executable evidence ledger for claims about storage, loading, observed use, and learning. It is separate from Strata and licensed under Apache 2.0.

The projects are complementary but independent:

- Strata supplies a normative reasoning scaffold.
- BES supplies a skeptical reference mechanism for evaluating evidence claims.
- Neither proves or implements the other.

Until public GitHub URLs are assigned, the local sibling is `../bes-log-learn-reference/`.

## Contributing

Adversarial counterexamples are especially welcome. Please read [`CONTRIBUTING.md`](CONTRIBUTING.md). The governing repair principle is:

> Preserve load-bearing function, not favored claims. A valid repair may narrow, replace, or delete a failed function.

## Attribution and AI assistance

Strata was developed and directed by Frank with substantial collaborative assistance from OpenAI's ChatGPT and Codex, addressed in the project as **Ari**. That assistance included drafting, conceptual analysis, adversarial-review design, synthesis, editing, and repository preparation. Frank retained final editorial authority and responsibility.

Multiple other AI systems also contributed adversarial reviews and synthetic test outputs. Their participation does not imply endorsement by their developers.

See [`ACKNOWLEDGMENTS.md`](ACKNOWLEDGMENTS.md) for the exact disclosure and limits.

## License

The Strata texts and repository documentation are licensed under the [Creative Commons Attribution 4.0 International License](https://creativecommons.org/licenses/by/4.0/). See [`LICENSE`](LICENSE).

Suggested attribution:

> Strata 0–3, Frank and Strata Project contributors, versioned release from the Strata Canon repository, licensed CC BY 4.0. Changes, if any, were made by the reuser.
