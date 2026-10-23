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
  Developer Portal so the `^` prefix commands can read messages.
- Invite the bot to your server with View Channels, Send Messages, Read Message
  History, Embed Links, and Add Reactions permissions.
- Press Run. Successful connection logs `I'm in as ...`. No web preview is expected.
- The old Flask keep-alive helper is not started; it does not provide reliable
  continuous hosting.

## Checks

`python main.py --check` loads all six enabled cogs and reports the command names
without a token or Discord connection. This does not test sending messages or
server permissions. Music remains disabled as in the imported project.

Discord.py 2.x requires async extension setup and explicit gateway intents.
Keep those requirements when adding new cogs. Inventory is in memory and is lost
when the process restarts.
