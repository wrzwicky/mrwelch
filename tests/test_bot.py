import unittest
from dataclasses import dataclass
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import discord

import main
from cogs.inventory import InventoryCog


@dataclass(frozen=True)
class FakeMember:
    name: str
    mention: str


class BotSetupTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.bot = main.create_bot()
        InventoryCog.allInventory = {}
        await self.bot.setup_hook()

    async def asyncTearDown(self):
        await self.bot.close()

    async def test_loads_enabled_cogs_and_prefix_commands(self):
        self.assertEqual(set(self.bot.cogs), {
            "InventoryCog", "mrwelch", "DictionaryCog", "DiceCog",
            "StoryCog", "HelpCog",
        })
        self.assertTrue(self.bot.intents.message_content)
        self.assertEqual(self.bot.command_prefix, main.COMMAND_PREFIX)
        self.assertTrue({
            "give", "take", "drop", "use", "inventory", "pocket",
            "roll", "help",
        }.issubset({command.name for command in self.bot.commands}))
        self.assertIs(self.bot.get_command("i"), self.bot.get_command("inventory"))

    async def test_give_and_inventory_commands_work(self):
        cog = self.bot.get_cog("InventoryCog")
        user = FakeMember(name="Ada", mention="<@123>")
        channel = SimpleNamespace(send=AsyncMock())
        ctx = SimpleNamespace(
            author=user,
            channel=channel,
            message=SimpleNamespace(add_reaction=AsyncMock()),
        )

        await self.bot.get_command("give").callback(cog, ctx, user, "apples")
        await self.bot.get_command("inventory").callback(cog, ctx)

        ctx.message.add_reaction.assert_awaited_once_with("\N{THUMBS UP SIGN}")
        channel.send.assert_awaited_once_with("You have an apple.")

    async def test_giving_duplicate_item_reports_it(self):
        cog = self.bot.get_cog("InventoryCog")
        user = FakeMember(name="Ada", mention="<@123>")
        channel = SimpleNamespace(send=AsyncMock())
        ctx = SimpleNamespace(
            author=user,
            channel=channel,
            message=SimpleNamespace(add_reaction=AsyncMock()),
        )

        await self.bot.get_command("give").callback(cog, ctx, user, "apple")
        await self.bot.get_command("give").callback(cog, ctx, user, "apple")

        channel.send.assert_awaited_once_with("Too many of those floating around.")

    async def test_mentioned_quote_request_returns_requested_entry(self):
        bot_user = discord.User(
            state=self.bot._connection,
            data={
                "id": "123456789012345678",
                "username": "MrWelch",
                "discriminator": "0",
                "avatar": None,
            },
        )
        self.bot._connection.user = bot_user
        cog = self.bot.get_cog("mrwelch")
        quote_number = min(cog.mrwelch)
        channel = SimpleNamespace(name="general", send=AsyncMock())
        message = SimpleNamespace(
            content=f"<@{bot_user.id}> {quote_number}",
            author=FakeMember(name="Ada", mention="<@123>"),
            mentions=[bot_user],
            guild=SimpleNamespace(name="Test Server", roles=[]),
            channel=channel,
            created_at="timestamp",
        )

        with patch.object(self.bot, "get_user", return_value=bot_user):
            await cog.on_message(message)

        channel.send.assert_awaited_once_with(
            f"{quote_number}. {cog.mrwelch[quote_number]}"
        )

    async def test_quote_request_without_bot_mention_is_ignored(self):
        bot_user = discord.User(
            state=self.bot._connection,
            data={
                "id": "123456789012345678",
                "username": "MrWelch",
                "discriminator": "0",
                "avatar": None,
            },
        )
        self.bot._connection.user = bot_user
        cog = self.bot.get_cog("mrwelch")
        channel = SimpleNamespace(name="general", send=AsyncMock())
        message = SimpleNamespace(
            content="1",
            author=FakeMember(name="Ada", mention="<@123>"),
            mentions=[],
            guild=SimpleNamespace(name="Test Server", roles=[]),
            channel=channel,
            created_at="timestamp",
        )

        await cog.on_message(message)

        channel.send.assert_not_awaited()


class StartupFailureTests(unittest.TestCase):
    def test_missing_secrets_are_reported_without_connecting(self):
        with self.assertRaisesRegex(
            SystemExit, "Missing Replit Secrets: DISCORD_AUTHOR_ID, DISCORD_BOT_SECRET"
        ):
            main.validate_runtime_config({})

    def test_non_numeric_author_id_is_rejected(self):
        with self.assertRaisesRegex(SystemExit, "DISCORD_AUTHOR_ID must be your numeric"):
            main.validate_runtime_config({
                "DISCORD_AUTHOR_ID": "not-numeric",
                "DISCORD_BOT_SECRET": "unused",
            })

    def test_discord_rejected_token_has_actionable_error(self):
        with patch.object(main.bot, "run", side_effect=discord.LoginFailure):
            with self.assertRaisesRegex(SystemExit, "Discord rejected DISCORD_BOT_SECRET"):
                main.run_discord_bot("unused")

    def test_missing_message_content_intent_has_actionable_error(self):
        with patch.object(
            main.bot, "run", side_effect=discord.PrivilegedIntentsRequired(0)
        ):
            with self.assertRaisesRegex(SystemExit, "Enable Message Content Intent"):
                main.run_discord_bot("unused")


if __name__ == "__main__":
    unittest.main()
