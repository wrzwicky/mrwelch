---
name: Bundled data paths
description: Stable path resolution for text assets loaded by bot modules and cogs.
---

Resolve project text assets relative to the source file that uses them rather
than relying on `sys.path[0]` or the process working directory.

**Why:** `python -m unittest discover -s tests` sets `sys.path[0]` to the tests
directory, causing cogs that use it to look for project data in the wrong place.

**How to apply:** For data shipped beside the project code, derive the path from
`Path(__file__).resolve()` and the module's known location in the project tree.
