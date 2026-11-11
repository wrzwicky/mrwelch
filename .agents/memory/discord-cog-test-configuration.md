---
name: Discord cog test configuration
description: Isolate tests that load cogs through Discord's extension loader.
---

When tests load a cog through `Bot.load_extension` or `setup_hook`, configure
test-specific paths or settings on the bot before extension setup instead of
patching the imported cog class or module first. The extension loader may import
the module again, so an earlier patch can be discarded.

**Why:** Inventory tests showed that a pre-setup class or module patch did not
reach the cog created by extension loading.

**How to apply:** Put test configuration on the bot before calling `setup_hook`,
then have the cog read that value during initialization with a project default.
