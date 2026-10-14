## Summary

What does this change do, and why?

## Type of change

- [ ] Skill content (orchestrator or a platform skill)
- [ ] Schema or example
- [ ] Validation script or tests
- [ ] Documentation only

## Validation

- [ ] `python scripts/build_manifest.py` was run after file changes.
- [ ] `python scripts/validate_repository.py` passes.
- [ ] `python -m unittest discover -s tests` passes.
- [ ] Fact packets touched by this change pass `python scripts/validate_fact_packet.py <file>`.

## Safety checks

- [ ] No real company, customer, price, credential, or account data is included.
- [ ] No machine-local absolute paths were introduced.
- [ ] Editorial preferences are not presented as official platform rules.
