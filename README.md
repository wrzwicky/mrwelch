# mrwelch

This is a bot that serves silly quotes to Discord, plus has some other features accumulated over time.

## Inventory:

+ `main.py` the Discord bot
+ `*.py` and `cogs/*.py` the bot code
+ `mrwelch.txt` the main "things mr welch is not allowed to do" file
+ `shane.txt` some extra quotes from the Shane file
+ `critrole.txt` some quotes from the Critical Role vidcast
+ `badjoke.txt` some jokes
+ `DiscordKeepAlive.md` and `keep_alive.py` tool to run this bot from Repl.it, back when they allowed this
+ `.env` secret file you create with your Discord keys

- `requirements.txt` troditional dependency file, not used
- `pyproject.toml`, `poetry.lock`, `replit.nix` newer from replit.com, obsolete now
- `Pipfile` **current**, uses *pipenv*

## Install required packages

Install *pipenv* dependency manager, then:

```
mkdir .venv    #force pipenv to put venv here
pipenv install
pipenv shell
```

## Configure

Create a file named `.env` with your discord keys. *Do not check this file into version control.*

```
DISCORD_AUTHOR_ID=<author ID>
DISCORD_BOT_ID=<bot ID>
DISCORD_BOT_SECRET=<bot token>
```

## Run

Start as regular Python program:
```
python main.py
```
