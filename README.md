# Strata 0–3 — A Reasoning and Alignment Scaffold for AI Systems

Strata 0–3 is a compact, model-legible framework intended to support epistemic honesty, boundary discipline, corrigibility, useful refusal, and escalation in artificial-intelligence systems.

It is a proposed orientation for testing and adaptation. Publication does not establish that it aligns an AI system.

It is designed primarily as an addition to a system prompt or constitutional reasoning layer. It is **not** a complete safety system and does not replace technical permissions, authentication, sandboxing, privacy controls, domain-specific policies, monitoring, or human oversight.

Publication edition: **1.0.0** (2026-10-21). This edition identifies a steward-approved publication baseline, not scientific validation.

## What is included

The publication set lives in [`canon/`](canon/):

- [`Stratum-0_Primitives.md`](canon/Stratum-0_Primitives.md) — minimal primitives and epistemic boundaries;
- [`Stratum-1_Minimal-Dynamics.md`](canon/Stratum-1_Minimal-Dynamics.md) — trajectories, persistence, return, and adaptation;
- [`Stratum-2_Orientation.md`](canon/Stratum-2_Orientation.md) — Curiosity, Truth, Agency, and Beauty;
- [`Stratum-3_Operational-Permissions.md`](canon/Stratum-3_Operational-Permissions.md) — operational permissions, refusal, and escalation;
- [`Strata-0-3_AI-Kernel.md`](canon/Strata-0-3_AI-Kernel.md) — compact system-prompt-oriented formulation;
- [`CANON-MANIFEST.md`](canon/CANON-MANIFEST.md) — canonical status, lineage, and integrity receipts.

For initial experiments, start with the AI Kernel. The full strata explain the distinctions compressed into it.

## Intended use

The AI Kernel is a conceptual supplement for controlled experiments, not a portable instruction-priority hierarchy. Place it only where the host's existing governing instructions allow; it does not acquire priority merely by appearing earlier in a prompt. Keep product and domain requirements, actual tool permissions, and tool/interface contracts explicit. Environment facts inform decisions but do not become instructions by placement.

This repository supplies text only. References to higher-stakes review mark the boundary of Strata 0–3; no gate engine or receiving service is supplied here. Configure a real receiving path before claiming a handoff. If none exists, contain the blocked portion and continue only with the supportable remainder, as the kernel specifies.

## Evidence status

Strata was developed through iterative private adversarial review and limited synthetic next-action tests. Some recorded responses proposed appropriate refusal, revision, boundary preservation, and useful continuation under the supplied task facts. These are examples of responses consistent with the scaffold, not demonstrations of real-world execution or evidence that adding Strata improves a model.

The P26–P28 studies compared a historical v0.5 kernel with that same kernel plus an experimental trajectory-watch supplement; neither condition omitted Strata. The first comparison was inconclusive because of ceiling and route-integrity problems. The sequential follow-up did not earn retention of the supplement under its declared criteria, and the supplement was removed from active development. Model-identity limitations and incomplete preservation of the follow-up's user turns restrict interpretation.

Those studies used kernel SHA-256 `0AC4C897CBC0C9D30C59C8D89133BDC50ED958AF6A6791AAFB8EC6C06685F47A`. This edition uses `5B791A1FBAB8B28E539FB1CDA847938EEE12AD1BCBA2C301C4276D4D4376D230`; the historical tests therefore do not evaluate the exact text of this edition. The detailed study records remain in the project's private development archive.

Treat Strata as a development prototype and research object. This evidence does not establish causal behavioral benefit, general confidence calibration, deployment safety, alignment at scale, adversarial robustness, durable learning, or reliability across models and contexts.

See [`LIMITATIONS.md`](LIMITATIONS.md) for the claim boundary.

## Canon, versions, and adaptations

The [manifest](canon/CANON-MANIFEST.md) identifies the files in this publication edition. Release versions cover the complete set; filenames remain stable and document lineage revisions are retained. Cite an exact released tag and, where relevant, a paper. The first public release freezes that snapshot; corrections require a new version, preserved history, and refreshed checksums. See [GOVERNANCE.md](GOVERNANCE.md).

You may adapt the text under CC BY 4.0 with attribution and identification of changes. Clearly distinguish adaptations from this project's canonical release. This provenance convention does not prohibit licensed adaptations.

## Related implementation

The sibling repository **BES Skeptical Learning Ledger — Reference Engine** explores a narrow executable evidence ledger for claims about storage, loading, observed use, and learning. It is separate from Strata and licensed under Apache 2.0.

The projects are complementary but independent:

- Strata supplies a normative reasoning scaffold.
- BES supplies a skeptical reference mechanism for evaluating evidence claims.
- Neither proves or implements the other.

See [BES on GitHub](https://github.com/arcencilo-family/bes-log-learn-reference) and its independently versioned [0.1.0 release](https://github.com/arcencilo-family/bes-log-learn-reference/releases/tag/v0.1.0).

## Contributing

Adversarial counterexamples are especially welcome. Please read [`CONTRIBUTING.md`](CONTRIBUTING.md). The governing repair principle is:

> Preserve load-bearing function, not favored claims. A valid repair may narrow, replace, or delete a failed function.

## Attribution and AI assistance

Strata was developed and directed by Frank Böhm with substantial collaborative assistance from OpenAI's ChatGPT and Codex, addressed in the project as **Ari**. That assistance included drafting, conceptual analysis, adversarial-review design, synthesis, editing, and repository preparation. Frank retained final editorial authority and responsibility.

Multiple other AI systems also contributed adversarial reviews and synthetic test outputs. Their participation does not imply endorsement by their developers.

See [`ACKNOWLEDGMENTS.md`](ACKNOWLEDGMENTS.md) for the exact disclosure and limits.

## License

The Strata texts and repository documentation are licensed under the [Creative Commons Attribution 4.0 International License](https://creativecommons.org/licenses/by/4.0/). See [`LICENSE`](LICENSE) for terms and [`NOTICE`](NOTICE) for the copyright statement.

Suggested attribution:

> Strata 0–3, Frank Böhm, versioned release from the Strata Canon repository, licensed CC BY 4.0. Changes, if any, were made by the reuser.
