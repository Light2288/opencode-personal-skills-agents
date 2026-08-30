# Local document normalization

`document_ingest.py` is a narrowly scoped, local-only normalizer. It reads a
source directory without modifying it and writes normalized Markdown, extracted
media, and `extraction-report.json` beneath an explicit output directory.

```sh
python3 tools/document_ingest.py check-dependencies
python3 tools/document_ingest.py normalize /local/source --output /safe/output
```

DOCX, XLSX, and PPTX are parsed as OOXML with Python's standard library. It
does not execute macros. Media provenance is format-specific:

- DOCX preserves referenced media and may retain unreferenced `word/media/`
  package members, labeling them as unreferenced.
- XLSX includes only worksheet-owned tables, media, and charts reached through
  worksheet and drawing relationships. Orphan package members are omitted and
  reported as limitations that make coverage PARTIAL where applicable.
- When PPTX contains `presentation.xml`, only resolved declared slides and
  their reachable notes, media, and charts are included. Orphan package members
  are excluded.
- When `presentation.xml` is absent, PPTX uses the documented filename-based
  fallback and records that limitation.

Archive safety permits XML and relationships parts up to 64 MiB and bounds all
expanded package content to 200 MiB. Duplicate/encrypted members and unsafe
extracted-media paths fail that source. Compression-ratio checks apply only beyond the XML-part
bound so legitimate repetitive worksheets are not rejected solely for being
compressible.

LibreOffice headless is an optional local dependency for layout rendering. It
runs non-interactively with an isolated temporary profile and 120-second
timeout. Rendering supplements structured XLSX extraction; missing/failed
rendering and unsupported representations are recorded as PARTIAL coverage.
Office packages containing any external OOXML relationship are not rendered;
structured extraction is preserved and records a PARTIAL warning without
logging the external target. When `ppt/presentation.xml` exists, only its
declared slide relationships are ingested; filename fallback applies only when
the presentation part is absent. Declared slides retain their original 1-based
ordinals even when an earlier slide is unavailable. In authoritative mode,
only media, charts, and notes reachable from resolved declared slides are
included; orphan package members are excluded.

XLSX drawing ownership supports one-cell, two-cell, and absolute anchors.
Absolute anchors record safe position and extent values without inventing a
cell range; unresolved or uninterpretable anchors make coverage PARTIAL.

Direct text/Markdown input is limited to 10 MiB per source. Direct PDF and
image attachments are limited to 100 MiB per source. Limits are checked before
reading or copying the payload; oversized sources fail individually while the
remaining batch continues.

Install LibreOffice on macOS with `brew install --cask libreoffice`, or use the
package named `libreoffice` from the Linux distribution package manager. The
tool never installs dependencies itself.

Manual renderer smoke test: generate the synthetic fixtures, normalize them
with a real LibreOffice on `PATH`, then inspect `extraction-report.json` and
confirm readable DOCX, XLSX, and PPTX sources include `rendered.pdf` without a
rendering warning.
