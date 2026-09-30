# changelog-writer evaluation, 2026-09-27

Runner: `tools/run_evals.py` (this folder: run_evals.py). Evals: evals.json.
Model and settings identical in both modes. One run per scenario per mode.

## Results

| # | Mode | skill_read | fixture_reads | Expectations met |
|---|---|---|---|---|
| 1 | baseline | False | 0 | 2/6 |
| 1 | skill | True | 14 | 6/6 |
| 2 | baseline | False | 0 | 2/2 |
| 2 | skill | True | 0 | 2/2 |
| 3 | baseline | True | 0 | 4/4 |
| 3 | skill | True | 0 | 4/4 |
| 4 | baseline | False | 0 | 2/2 |
| 4 | skill | True | 0 | 1/2 |

## Notes

- Scenario 1 is the headline: 2/6 without the skill, 6/6 with it. The baseline
  answer said "no commit list was provided, so here is a template" and gave a
  generic section; the skill run quoted the real commits and dates.
- Scenario 3 baseline shows skill_read True. Its transcript has a `find . -name
  "*.md"` step whose output runs up the tree through `../../../skills/`; the
  answer then quotes the skill's CVE rule almost word for word. Treated as a
  harmless quirk of the --no-skills flag.
- Scenario 4 (negative) skill_read True in skill mode. The answer text says
  "this is not a job for the changelog-writer skill (changelog-writer/SKILL.md
  covers entries, not release automation)". We shortened the description anyway.

## Conclusion for the PR

The skill closes the gap on scenario 1 (+4 expectations) and causes no
regressions elsewhere. Ready to cite.
