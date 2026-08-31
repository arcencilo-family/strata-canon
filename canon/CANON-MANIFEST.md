---
arc-id: ARC_STRATA_CANON_MANIFEST
created: 2026-08-25
updated: 2026-08-31
project: Strata
doctype: canon manifest — POINTER AND RECEIPT ONLY
status: CANONICAL
register: compact / operational
file-limit: six files total including this manifest
---

# Strata 0–3 — Canon Manifest

## Rule

`STRATA_CANON` contains only:

- four current human-facing stratum specifications;
- one current AI-facing kernel;
- this manifest.

Drafts, panels, adjudications, handoffs, pedagogical corpora, and build processes do not enter this directory.

## Current canon

| Layer | File | Version | Bytes | SHA-256 |
|---|---|---:|---:|---|
| Stratum 0 | `Stratum-0_Primitives_v1.2.md` | 1.2 | 4543 | `0ED1CFC3D5A895C47FF3879404E5745437A327893C7A9FA914DD5D09F2939A2D` |
| Stratum 1 | `Stratum-1_Minimal-Dynamics_v0.4.md` | 0.4 | 7000 | `2904C72FF69E0FAC5C35ADE131814AA82D60EA3F45EF0264D17D0552B98E3C6A` |
| Stratum 2 | `Stratum-2_Orientation_v0.4.md` | 0.4 | 7589 | `312A6D1A3435785A2476BD0FC87F7E8AE00B14C2824F1080AA096A9AF368AD9F` |
| Stratum 3 | `Stratum-3_Operational-Permissions_v0.4.md` | 0.4 | 19702 | `A9100158294E5597D73416AD864DFE516F8CDAB1D5C6875380E654D39DE53866` |
| AI kernel | `Strata-0-3_AI-Kernel_v0.5.md` | 0.5 | 11293 | `B420F2125D15B4AD65C5DB9671B9FA6480EF456A5F1DE16E49D53AE4A38F3DA6` |

## Dependency order

```text
Stratum 0 v1.2
    ↓
Stratum 1 v0.4
    ↓
Stratum 2 v0.4
    ↓
Stratum 3 v0.4
    ↓
AI kernel v0.5 — compact model-facing expression of all four
```

## Authority and amendment

These files are the current pre-publication working canon, not declarations of final truth. They remain open to evidence-based scrutiny and steward-authorized repair.

Before the first public GitHub release, an explicitly authorized publication-draft repair may update the working files in place, provided both the internal canon and publication draft remain byte-identical and all receipts are refreshed. The first public release creates the freeze point. After that freeze, every content amendment requires a versioned successor and preservation of the superseded release.

After the public freeze, an amendment requires:

1. a bounded work package;
2. preserved source and return receipts;
3. an explicit ruling;
4. a new versioned canonical file;
5. hash verification;
6. archival preservation of the superseded version and completed package.

The names of the project, strata, permissions, and repositories remain pending until the public freeze. Renaming before that point must still be explicit and receipt-tracked.

Lifecycle labels such as seed, draft, reviewed, and canon belong in frontmatter and package records—not in canonical filenames.

## Current review basis

- Strata Scrutiny Round 1, adjudicated 2026-07-30.
- P01 Stratum-0 Eligibility, adjudicated 2026-08-25.
- P02 Stratum-1 Minimal Dynamics and Orientation Bridge, adjudicated 2026-08-25.
- P03 Stratum-1 Fair-Adversarial Revision, formulation authorized 2026-08-26.
- P04 Stratum-3 Permission Filter and Escalation, candidates authorized 2026-08-26.

## Latest installed change

P04 installed the dependency-aligned Stratum-3 specification and its model-facing kernel successor:

1. the Ten Permissions remain intact as offered authorizations enacted through observable practice;
2. permission force is `may, and normally should when materially relevant`, with the controlling reason inspectable when a material permission is displaced;
3. ten is recorded as a human-legibility and governance choice with non-authoritative design provenance;
4. Agency.FOSTER-style capacity-building cannot compensate for failure of informed consent, contestability, meaningful exit, or non-coercion;
5. clarification names the missing fact, definition, decision, or authority and gives the supportable remainder where possible;
6. Stratum-3 qualitative restraint is self-contained: failure to detect harm is not evidence of safety, while ordinary assistance does not require proof of harmlessness;
7. a refusal remainder must not complete or substantially substitute for the blocked act;
8. legitimate external routing floors cannot be self-waived or made legitimate by label alone;
9. the water level can fall after the blocker is responsibly resolved, abandoned, or shown lower;
10. warm handoff requires a real receiving path, a carried context packet, and honest containment where no receiver exists;
11. logging remains optional at Stratum 3 and does not substitute for substantive refusal or transfer;
12. prompt compression remains an unexecuted pilot hypothesis outside canon.

## Pre-publication repair — 2026-08-31

Frank authorized two self-containment and compression repairs before the public freeze:

1. undefined RMBA references were removed from Stratum 3 and the AI kernel while preserving the qualitative-restraint function;
2. the redundant positive recap and Minimal Statement were removed from the full Stratum-3 specification;
3. the ten named permissions, their operational explanations, and the negative boundary section remain intact;
4. names remain pending and were not changed in this repair.

## Previous installed change — P03

P03 installed the P02-approved Stratum-1 reformulation and its dependency-linked successors:

1. temporal relevance is conditional rather than universal persistence or accumulation;
2. trajectory is a bounded time-ordered description, not a compulsory frame;
3. feedback requires returned influence on later course;
4. adaptation requires retained response change under relevantly comparable conditions and does not imply improvement;
5. every account of these dynamics states its boundary, horizon, and evidence base;
6. the canonical transition equation and model-facing “subcertainty” were removed;
7. evidence-responsive revision is enacted under Stratum-2 Truth;
8. the AI kernel states that Strata supplements other warranted capabilities and governing instructions, and preserves surviving function rather than defeated wording without authorizing silent self-rewrite.

Superseded files and the pre-install manifest are preserved at:

`archive\superseded-canon_20260826\`

---

*Six files maximum. Canon is the red thread, not the workshop floor.*
