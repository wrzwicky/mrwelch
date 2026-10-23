---
name: Python package installation
description: Package installer behavior that can unexpectedly upgrade imported dependencies.
---

The Replit Python package installer can normalize a pinned request to an unpinned
package name and install its latest version. It can also generate uv project
metadata and a sample package for a repository that only has a Pipfile.

**Why:** During setup, a request for discord.py 1.7.3 installed discord.py 2.7.1
instead. This changes extension initialization and gateway intent requirements.

**How to apply:** Inspect installation output and dependency constraints before
assuming the imported version was preserved. Keep generated metadata appropriate
to the real project and remove unrelated sample entry points.
