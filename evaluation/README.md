# Evaluation — methods, findings and inspectable records

Two small development studies compared Strata-containing prompts. They do not establish benefit over a model without Strata. All data concern text responses or proposed conduct, not observed external execution. See [limitations](../LIMITATIONS.md).

## Studies and findings

Each request supplied the same short host line plus the full arm-specific kernel as high-priority content, with no tools. Sampling controls were omitted for provider defaults. Exact requests are reconstructable offline from shared configurations, tested kernels and per-call records. Provider-side additions, hidden processing and learned constraints were not observable or controlled.

| Study | Design | Preserved results |
|---|---|---|
| Initial comparison | Seven cases × two kernels × three model families, one sample per cell | 43 attempts for 42 answers; initial scoring: released 21/21 acceptable, proposed 19/21 acceptable and two concerns |
| Haiku diagnostic | Two kernels × five repetitions of a fixed objection and a two-turn stop | 30 calls: ten objection targets, ten setup replies and ten stop targets |

The initial run stopped after 21 successful replies and a transport failure. One approved replacement attempt and the 20 unattempted cells completed the study; no successful reply was replaced. The failed attempt and its uncertain charge remain recorded. Conservative reservations were EUR 3.1373775 for that campaign and EUR 2.0838915 for the separate diagnostic, each under its own EUR 5 cap. These are reservations, not invoices.

| Diagnostic judgment | Released 1.0.0 | Proposed test kernel |
|---|---|---|
| Stops, initial scoring | 5 acceptable | 5 acceptable |
| Objection, initial scoring | 1 concern of 5 | 4 concerns of 5 |
| Objection, contextual supplement | 2 concerns of 5 | 4 concerns of 5 |

The diagnostic's initial scoring packet omitted the fact that the supplied source text was system content. The [context addendum](data/diagnostic-30/SCORER-CONTEXT-ADDENDUM_20261111.md) supplied that fact; the scorer reconsidered all ten objection answers after inferring the arms. One baseline label changed for consistency. Five of the six supplemental concerns were low-confidence. The supplement is not a second blind evaluation. Both rounds remain available.

The earlier stop-authority challenge did not recur in the diagnostic, whose first turn was already waiting; this is not proof of reliable interruption of external actions. Objection responses sometimes confused local interpretation with configuration changes or cited escalation rules outside their scope. One asked an unnecessary framing question while also offering ordinary help; no summary source was supplied, so actual refusal of available summary work was not observed. The overlap argument did not establish that demoting Beauty preserved all its functions: declining it could be justified. Both specified foundation challenges selected Beauty by design, not because a study established anything special about its name or independence. The original no-receiver case let models generate different objections.

## Models, reviewers and versions

Requested and returned API identifiers matched:

- `gpt-5.4-mini-2026-03-17`
- `claude-haiku-4-5-20251001`
- `grok-4.3` — an alias, not a guarantee of immutable weights

Reviewer A scored the initial comparison in a fresh worker context with prior project exposure disclosed. Reviewer B scored the diagnostic and later performed the comprehension read. Both identify as Grok-based; exact underlying models were not disclosed or independently verified. Reviewer B was not a text author, but its later reads were not naive independent replications. ChatGPT and Claude contributed to the text and were named in the tested signature. Masking was imperfect: text, metadata and style could reveal arms or families.

Public reviewer labels are normalized. Scoring judgments, evidence, reasons and exposure disclosures are unchanged; original source hashes and transformations are in [provenance](PROVENANCE.json). Historical hash lists inside returns refer to the original files used then, not necessarily later identity-normalized copies. The maps are public, so these materials cannot provide a new blind evaluation.

| Artifact | SHA-256 |
|---|---|
| Released 1.0.0 kernel | `5B791A1FBAB8B28E539FB1CDA847938EEE12AD1BCBA2C301C4276D4D4376D230` |
| API-tested proposed kernel | `D34BB79F3B661AB63B80F2BEE8A12798E6EF0CF240086963A502E126930ADA0C` |

Both tested files are in `runners/check-run_20261111/artifacts/`. The final 1.1.0 kernel adds a 36-word, two-sentence repair clarification, relocates/rephrases attribution and updates metadata. Its hash is in the [canon manifest](../canon/CANON-MANIFEST.md); those final bytes were not API-tested. The [non-author comprehension response](comprehension/reader-response.md) understood three scope cases but had prior diagnostic exposure. Its [brief](comprehension/brief.md) and [actual Use excerpt](comprehension/proposed/USE-FOR-COMPREHENSION.md) are preserved; attribution was relocated afterward. Neither the clarification nor the footer is established as a behavioral cure.

Earlier private P26–P28 studies used kernel SHA-256 `0AC4C897CBC0C9D30C59C8D89133BDC50ED958AF6A6791AAFB8EC6C06685F47A`, comparing it with itself plus an experimental trajectory-watch supplement; neither arm omitted Strata. The first study was inconclusive because of ceiling and route-integrity problems. A follow-up did not earn retention of the supplement, which was removed. Model-identity limitations and incomplete user-turn preservation restrict interpretation. Those records remain private and do not test this edition.

## Data and offline inspection

`data/initial-42/` and `data/diagnostic-30/` contain compact attempt records, score maps and unchanged scoring entries. Shared prompts and kernels are stored once. Request bodies and duplicated scorer packets are reconstructed with their original hashes checked; no answer is shortened. Setup history is retained through explicit dependencies. Provider headers/identifiers and redundant raw response envelopes were omitted from the original public export; source-record hashes identify the preserved private originals, not publicly reconstructable full envelopes.

From the repository root, verify all payload hashes, exact request reconstruction, historical scorer-packet bytes, scores and local links:

```sh
python -I -B tools/verify_publication.py
python -I -B tools/test_verify_publication.py
```

To materialize an inspectable copy outside the repository (no network):

```sh
python -I -B tools/reconstruct_evaluation.py initial-42 --output ../inspect-initial-42
python -I -B tools/reconstruct_evaluation.py diagnostic-30 --output ../inspect-diagnostic-30
```

The three runner fixture suites use temporary files and block network transport:

```sh
cd evaluation/runners/check-run_20261111
python -I -B test_runner_offline.py
python -I -B test_continuation_offline.py
cd ../diagnostic-proposal_20261111
python -I -B test_runner_offline.py
```

These are software checks, not subject evidence. Standard-library Python only. For a new study use a disposable copy: `runner.py prepare` and `runner.py preflight` are offline. Historical models, API contracts and prices are not promises of availability; stale prices deliberately block execution. Any paid run needs reviewed current inputs, environment-only keys and an explicit budget. No automatic retry or substitution is supplied. The original runner expects a `results/` directory; its continuation wrapper applies only to the recorded interruption. The diagnostic's public freeze list omits three obsolete preparation documents; model-facing requests and budget logic are unchanged. Original-source hashes are recorded in provenance.
