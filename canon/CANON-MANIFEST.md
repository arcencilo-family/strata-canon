---
arc-id: ARC_STRATA_CANON_MANIFEST
project: Strata
doctype: canon manifest — POINTER AND RECEIPT ONLY
status: CANONICAL
register: compact / operational
file-limit: six files total including this manifest
---

# Strata 0–3 — Canon Manifest

## Rule

The six-file canon, kept in `STRATA_CANON/` internally and `canon/` in the publication repository, contains only:

- four current human-facing stratum specifications;
- one current AI-facing kernel;
- this manifest.

Drafts, panels, adjudications, handoffs, pedagogical corpora, and build processes do not enter this directory.

## Current canon

| Layer | File | Version | Bytes | SHA-256 |
|---|---|---:|---:|---|
| Stratum 0 | `Stratum-0_Primitives_v1.2.md` | 1.2 | 4333 | `11FCA00390D6B0DEF22AD15BA6F41E78DB85F3D4B62A2F4BDC0C91AD49C2711E` |
| Stratum 1 | `Stratum-1_Minimal-Dynamics_v0.4.md` | 0.4 | 6663 | `CB5C0AF7DBD9F8BD0AE1DE147DDF627F4496FE6C7A67CB48B5921EB2FB550192` |
| Stratum 2 | `Stratum-2_Orientation_v0.4.md` | 0.4 | 7211 | `1BF559ACE4692656B8AC19D93308400431BA04F3922E8859D1EB89C0B8E07BB5` |
| Stratum 3 | `Stratum-3_Operational-Permissions_v0.4.md` | 0.4 | 18922 | `ADF9C7917B414182D2A79C9D3544A62C5AC525DF283BF43654393063B0921DF9` |
| AI kernel | `Strata-0-3_AI-Kernel_v0.5.md` | 0.5 | 10909 | `D04FDD5309C34C24AB542FB4255C0988F5D1BED6FCA19CC243F7C2ED0AD366F0` |

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

Development history is summarized in the repository changelog; the underlying review records remain in the internal archive.
