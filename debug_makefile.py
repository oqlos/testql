#!/usr/bin/env python3
"""Debug script to test Makefile parsing."""

from pathlib import Path
from testql.generators.sources.config_source import ConfigSource

MAKEFILE = """\
.PHONY: test
test:
\tpytest -q
"""

# Write to temp file
import tempfile
with tempfile.NamedTemporaryFile(mode='w', suffix='Makefile', delete=False) as f:
    f.write(MAKEFILE)
    mf_path = Path(f.name)

try:
    source = ConfigSource()
    plan = source.load(mf_path)
    print(f"Plan steps: {len(plan.steps)}")
    print(f"Plan config: {plan.config}")
    for step in plan.steps:
        print(f"Step: {step}")
finally:
    mf_path.unlink()
