This is a bot that serves silly quotes to Discord.

+ `main.py` the Discord bot
+ `*.py` and `cogs/*.py` the bot code
+ `keep_alive.py` tool to run this bot from Repl.it
+ `mrwelch.txt` the main "things mr welch is not allowed to do" file
+ `shane.txt` some extra quotes from the Shane file
+ `critrole.txt` some quotes from the Critical Role vidcast
+ `DiscordKeepAlive.md` and `keep_alive.py` if you want to run this on replit.com
+ `poetry.lock` and `pyproject.toml` package managment for replit.com
+ `.env` secret file you create with your Discord keys

Don't forget to install required packages:

+ `python3 -m venv env`
+ `source env/bin/activate`
+ `pip3 install -r requirements.txt`

If you want to run this, you need to create a file named `.env` with your discord keys. *Do not check this file into version control.*

```
DISCORD_AUTHOR_ID=<author ID>
DISCORD_BOT_ID=<bot ID>
DISCORD_BOT_SECRET=<bot token>
```
