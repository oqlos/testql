#!/usr/bin/env python3
"""One-file script to generate a TestQL artifact bundle."""

import sys
from pathlib import Path

# Allow importing testql when running directly from the example directory
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from testql.results.analyzer import inspect_source
from testql.results.artifacts import write_inspection_artifacts


def main() -> None:
    source = "https://tom.sapletta.com/"
    out_dir = Path(".testql")

    print(f"Inspecting {source} ...")
    topology, envelope, plan = inspect_source(source, scan_network=True)

    print(f"Writing artifact bundle to {out_dir.resolve()} ...")
    written = write_inspection_artifacts(
        topology=topology,
        envelope=envelope,
        plan=plan,
        out_dir=out_dir,
    )

    print(f"Done. Wrote {len(written)} files:")
    for p in sorted(written):
        print(f"  - {p.name}")


if __name__ == "__main__":
    main()
