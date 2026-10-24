# Mr. Welch Discord bot

## Run on Replit

- Runtime: Python 3.11. The project remains a Python Discord bot, not a website.
- Replit dependencies are in `pyproject.toml` and `uv.lock`; restore with `uv sync`.
  The imported Pipfile is retained for reference; its old lockfile is not used by Replit.
- Workflow: **Discord bot**, running `python -u main.py` from the project root.
- Add these in Replit Secrets:
  - `DISCORD_BOT_SECRET`: the bot token from the Discord Developer Portal's Bot page.
    This is not the application's OAuth client secret.
  - `DISCORD_AUTHOR_ID`: your numeric Discord user ID.
- `DISCORD_BOT_ID` is not needed by the code.
- Enable **Message Content Intent** on the application's Bot page in the Discord
  Developer Portal. The code also enables this gateway intent; both settings are
  required for `^` prefix commands to read message text.
- Give the bot role these server permissions in each channel where it should work:
  **View Channels**, **Send Messages**, **Add Reactions**, and **Embed Links**.
  Reactions are used by inventory commands, and embeds by `^help` and `^define`.
  Current commands do not need **Read Message History**.
- If connection fails with a privileged-intent error, enable Message Content Intent
  in the Developer Portal. If commands receive no response, check the intent and
  channel permissions/overrides first.
- Press Run. Successful connection logs `I'm in as ...`. No web preview is expected.
- The old Flask keep-alive helper is not started; it does not provide reliable
  continuous hosting.

## Checks

`python main.py --check` loads all six enabled cogs and reports the command names
without a token or Discord connection. This does not test sending messages or
server permissions. Run `python -m unittest discover -s tests` for offline tests
of cog loading, inventory command behavior, and startup failure messages. These
tests do not connect to Discord and do not require bot secrets. Music remains
disabled as in the imported project.

Discord.py 2.x requires async extension setup and explicit gateway intents.
Keep those requirements when adding new cogs. Player inventories are saved to
`data/inventories.json` after changes and restored when the inventory cog loads.
That runtime data file is local to the Replit project and is excluded from Git;
keep a backup if the inventory is important.
