---
arc-id: ARC_STRATA_CANON_MANIFEST
project: Strata
doctype: canon manifest — POINTER AND RECEIPT ONLY
status: CANONICAL
register: compact / operational
file-limit: six files total including this manifest
publication-version: 1.0.0-rc.1
publication-target: 1.0.0
---

# Strata 0–3 — Canon Manifest

## Rule

The six-file canon, kept in `STRATA_CANON/` internally and `canon/` in the publication repository, contains only:

- four current human-facing stratum specifications;
- one current AI-facing kernel;
- this manifest.

Drafts, panels, adjudications, handoffs, pedagogical corpora, and build processes do not enter this directory.

## Current canon

Publication candidate: **1.0.0-rc.1**, unreleased. The intended first public edition is **1.0.0**. The lineage revisions below retain the documents' development history; they are not the edition number of the whole publication. Stable filenames are used across editions.

| Layer | File | Lineage revision | Bytes | SHA-256 |
|---|---|---:|---:|---|
| Stratum 0 | `Stratum-0_Primitives.md` | 1.2 | 3789 | `3463709F548661ED5C13F2CDA93F0D32C7A72FADCC1BCFC556A0C209372FB419` |
| Stratum 1 | `Stratum-1_Minimal-Dynamics.md` | 0.4 | 6151 | `D6160ADB5C55DC7645C425056C13C667A7F79FB6DAEF9908DA766BF863A5F1E4` |
| Stratum 2 | `Stratum-2_Orientation.md` | 0.4 | 7184 | `463051E6F0287E4DAEF94D6E58B2161F92E988C83A60B7D374730814711D8060` |
| Stratum 3 | `Stratum-3_Operational-Permissions.md` | 0.4 | 20145 | `72F53D52F4DDE7C75C024AF1E534861B7DB58A11F37057B53BAA0E7CADF5CE28` |
| AI kernel | `Strata-0-3_AI-Kernel.md` | 0.5 | 11055 | `5B791A1FBAB8B28E539FB1CDA847938EEE12AD1BCBA2C301C4276D4D4376D230` |

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

Before the first public GitHub release, an explicitly authorized publication-draft repair may update the working files in place, provided both the internal canon and publication draft remain byte-identical and all receipts are refreshed. The first public release creates the freeze point. After that freeze, every content amendment requires a new publication version and preservation of the superseded release. Filenames remain stable; release tags and archived snapshots identify editions. Released tags and assets must not be rewritten or replaced.

After the public freeze, an amendment requires:

1. a bounded work package;
2. preserved source and return receipts;
3. an explicit ruling;
4. a new publication version containing the amended files under stable names;
5. hash verification;
6. archival preservation of the superseded version and completed package.

The names of the project, strata, permissions, and repositories remain pending until the public freeze. Renaming before that point must still be explicit and receipt-tracked.

Development history is summarized in the repository changelog; the underlying review records remain in the internal archive. Existing Git histories and document identifiers are retained. Earlier files and records are moved into the archive when superseded, not discarded.
