# Validation

Run deterministic repository checks with:

```sh
python3 -m json.tool opencode.json >/dev/null
python3 -m unittest discover -s tests -p 'test_*.py'
python3 tools/document_ingest.py check-dependencies
```

Tests generate only synthetic Office, PDF, and image fixtures in temporary
directories. They validate deterministic source IDs, structured extraction,
source immutability, partial coverage, frontmatter, routing, model settings,
permissions, and isolated installation. Generated fixtures, evidence,
deliverables, and conversion output must remain untracked.

After `./install.sh`, restart OpenCode before a live smoke test. Run `/ingest`
against a generated fixture directory, then run every summary type, `/estimate`,
`/compare`, and `/analyze` against the resulting evidence. Confirm collision
prompts and that `/compare` does not write an ADR.

LibreOffice unit tests use a fake executable boundary. When LibreOffice is
installed, manually normalize the synthetic fixtures and verify each readable
Office source includes `rendered.pdf`; otherwise report that real-renderer path
as not environment-tested.

If live invocation fails with `NOT NULL constraint failed:
session_message.seq`, record it as an unrelated environment blocker. Do not
infer a model limitation; the deterministic lower-level checks remain valid.
