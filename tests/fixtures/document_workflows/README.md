# Synthetic document fixtures

`generate.py` creates a corpus containing only explicit synthetic content. It
covers text, Markdown, PDF, PNG, DOCX text/table/image structures, a multi-sheet
XLSX with a formula and chart, a PPTX with notes and an image, legacy Office
placeholders, and one unreadable DOCX.

Generate outside the repository when possible:

```sh
python3 tests/fixtures/document_workflows/generate.py --output "$TMPDIR/opencode-document-fixtures"
```

Generated binaries are disposable and must never be committed.
