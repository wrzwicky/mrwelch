import unittest
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import discord

import main
from cogs.inventory import InventoryCog


@dataclass(frozen=True)
class FakeMember:
    id: int
    name: str
    mention: str


class BotSetupTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.bot = main.create_bot()
        self.temp_dir = TemporaryDirectory()
        self.bot.inventory_path = Path(self.temp_dir.name) / "inventories.json"
        await self.bot.setup_hook()

    async def asyncTearDown(self):
        await self.bot.close()
        self.temp_dir.cleanup()

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
        user = FakeMember(id=123, name="Ada", mention="<@123>")
        channel = SimpleNamespace(send=AsyncMock())
        ctx = SimpleNamespace(
            author=user,
            channel=channel,
            reply=AsyncMock(),
            message=SimpleNamespace(add_reaction=AsyncMock()),
        )

        await self.bot.get_command("give").callback(cog, ctx, user, "apples")
        await self.bot.get_command("inventory").callback(cog, ctx)

        ctx.message.add_reaction.assert_awaited_once_with("\N{THUMBS UP SIGN}")
        ctx.reply.assert_awaited_once_with("You have an apple.")
        restored = InventoryCog(self.bot, storage_path=self.bot.inventory_path)
        self.assertEqual(restored.allInventory[123].describe(), "an apple")

    async def test_giving_duplicate_item_reports_it(self):
        cog = self.bot.get_cog("InventoryCog")
        user = FakeMember(id=123, name="Ada", mention="<@123>")
        channel = SimpleNamespace(send=AsyncMock())
        ctx = SimpleNamespace(
            author=user,
            channel=channel,
            reply=AsyncMock(),
            message=SimpleNamespace(add_reaction=AsyncMock()),
        )

        await self.bot.get_command("give").callback(cog, ctx, user, "apple")
        await self.bot.get_command("give").callback(cog, ctx, user, "apple")

        ctx.reply.assert_awaited_once_with("Too many of those floating around.")

    async def test_inventory_is_restored_by_a_new_cog_instance(self):
        cog = self.bot.get_cog("InventoryCog")
        cog._add(FakeMember(id=123, name="Ada", mention="<@123>"), "apple")
        cog.allInventory[123].pocket("apple")
        cog._save_inventory()

        restored = InventoryCog(self.bot, storage_path=self.bot.inventory_path)

        self.assertEqual(restored.allInventory[123].pack, set())
        self.assertEqual(restored.allInventory[123].pock, {"apple"})

    async def test_take_transfers_an_item_and_persists_both_inventories(self):
        cog = self.bot.get_cog("InventoryCog")
        source = FakeMember(id=456, name="Bea", mention="<@456>")
        player = FakeMember(id=123, name="Ada", mention="<@123>")
        cog._add(source, "apple")
        ctx = SimpleNamespace(
            author=player,
            guild=None,
            reply=AsyncMock(),
        )

        await self.bot.get_command("take").callback(cog, ctx, "apple")
        ctx.reply.assert_awaited_once_with("You \"found\" user 456's apple!")
        restored = InventoryCog(self.bot, storage_path=self.bot.inventory_path)

        self.assertNotIn(456, restored.allInventory)
        self.assertEqual(restored.allInventory[123].describe(), "an apple")

    async def test_pocket_and_drop_changes_are_persisted(self):
        cog = self.bot.get_cog("InventoryCog")
        player = FakeMember(id=123, name="Ada", mention="<@123>")
        cog._add(player, "apple")
        ctx = SimpleNamespace(
            author=player,
            message=SimpleNamespace(add_reaction=AsyncMock()),
            channel=SimpleNamespace(send=AsyncMock()),
            reply=AsyncMock(),
        )

        await self.bot.get_command("pocket").callback(cog, ctx, "apple")
        restored = InventoryCog(self.bot, storage_path=self.bot.inventory_path)
        self.assertEqual(restored.allInventory[123].pock, {"apple"})

        await self.bot.get_command("drop").callback(cog, ctx, "apple")
        restored_after_drop = InventoryCog(
            self.bot, storage_path=self.bot.inventory_path
        )
        self.assertNotIn(123, restored_after_drop.allInventory)

    async def test_corrupt_inventory_file_fails_explicitly(self):
        self.bot.inventory_path.write_text("{broken json", encoding="utf-8")

        with self.assertRaisesRegex(
            RuntimeError, "Cannot load saved inventories"
        ):
            InventoryCog(self.bot, storage_path=self.bot.inventory_path)

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
        channel = SimpleNamespace(name="general")
        message = SimpleNamespace(
            content=f"<@{bot_user.id}> {quote_number}",
            author=FakeMember(id=123, name="Ada", mention="<@123>"),
            mentions=[bot_user],
            guild=SimpleNamespace(name="Test Server", roles=[]),
            channel=channel,
            reply=AsyncMock(),
            created_at="timestamp",
        )

        with patch.object(self.bot, "get_user", return_value=bot_user):
            await cog.on_message(message)

        message.reply.assert_awaited_once_with(
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
            author=FakeMember(id=123, name="Ada", mention="<@123>"),
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
