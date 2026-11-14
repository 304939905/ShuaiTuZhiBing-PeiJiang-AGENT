# GitHub Publishing and Attachment Policy

This repository is optimized for a fast first clone. The main branch contains
the agent logic, rules, structured reference data, indexes, and generated DOCX
reports. Large source media is optional and should not block ordinary use.

## What belongs in the main repository

- Python tools and their tests.
- Markdown rules, handoffs, indexes, audits, and learning notes.
- Structured JSON catalogs and evidence records.
- The small set of final DOCX reports that are part of the searchable library.
- Repository-level instructions such as `AGENTS.md` and this policy.

## What stays outside the main repository

- `.tools/`: the portable LibreOffice installation. Users should install their
  own Office/LibreOffice runtime instead of downloading this local bundle.
- `待蒸馏/`: original videos, saved HTML, extracted frames, and archives. These
  are useful provenance material but are large and not needed for most agents.
- `临时/` and `.codex_tmp/`: scratch plans, render QA pages, and intermediate
  generation files.
- `_tmp_madai_review_*/`: temporary review output.
- Raw account exports, tokens, cookies, keys, credentials, and local secrets.

The source-media attachment pack is published separately on the GitHub Release
named `source-attachments-v1`. It is optional and can be skipped by users who
only need the agent and knowledge base.

## Why not Git LFS for this project

The main repository is small enough to clone directly. Moving source media into
Git LFS would make every clone request the large objects and would consume the
account's Git LFS storage and bandwidth quota. Keeping the default clone small
and putting optional provenance media in a release is the better traffic tradeoff.

GitHub currently blocks individual repository files above 100 MiB and recommends
keeping repositories below 1 GiB. Release assets are separate; each release file
must be below 2 GiB, with up to 1,000 assets per release.

Official references:

- https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-large-files-on-github
- https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases
- https://docs.github.com/en/billing/concepts/product-billing/git-lfs

## Visibility and licensing

The initial GitHub repository is private. It includes internal logs and
third-party reference material that has not been license-cleared for public
redistribution. Do not make it public until the content owner reviews:

- third-party HTML, videos, screenshots, and report extracts;
- internal paths and development logs;
- the appropriate license and attribution for the original code;
- whether any account-derived material should remain private.

No open-source license is granted by the presence of these files.

## Verification before publishing

Run the service and data checks documented in `README.md` and `AGENTS.md`.
Before a release, also verify:

1. No file in the Git index exceeds the GitHub repository file limit.
2. No raw account export, token, or secret is staged.
3. The working tree contains only intended changes.
4. Optional archives have a published SHA-256 checksum.

