---
name: Inventory persistence
description: Storage decision for the Discord bot's player inventories.
---

Keep player inventory persistence as a versioned JSON file in the Replit project
data directory, keyed by numeric Discord user IDs. Replace the file atomically
after each inventory mutation, exclude runtime data from Git, and fail startup
with a clear error when existing data is malformed rather than silently resetting it.

**Why:** This bot is a single process and does not otherwise need a database.
File storage avoids adding a service while making inventories survive a bot
process restart; strict loading protects player data from accidental loss.

**How to apply:** For future inventory fields, update the file schema deliberately
and preserve existing entries. If the bot is moved to an ephemeral deployment
filesystem or multiple processes, revisit this storage choice.
