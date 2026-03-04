# Security Ownership Map Status

## Result
The `security-ownership-map` workflow could not be executed end-to-end for this workspace yet.

## Prerequisite check
- Ownership script present: yes
- Python `networkx` import: yes
- Git commit graph available in this workspace: no

## Blocking issue
When this report was written, the workspace still had no Git history. The repository is now initialized, but you still need real commits (or imported legacy history) to build the people-to-file graph, bus factor metrics, and co-change communities required by the skill.

## Ready-to-run command after Git migration
```bash
python <codex-home>/skills/security-ownership-map/scripts/run_ownership_map.py --repo . --out ownership-map-out --since "12 months ago" --emit-commits
```

## Suggested follow-up queries after the first run
```bash
python <codex-home>/skills/security-ownership-map/scripts/query_ownership.py --data-dir ownership-map-out summary --section orphaned_sensitive_code
python <codex-home>/skills/security-ownership-map/scripts/query_ownership.py --data-dir ownership-map-out summary --section bus_factor_hotspots
python <codex-home>/skills/security-ownership-map/scripts/query_ownership.py --data-dir ownership-map-out people --sort sensitive_touches --limit 10
```

## Recommended next step
Create the first real commit or import the legacy Git history for this folder, then rerun the command above so the ownership map reflects meaningful authorship instead of an empty repository.
