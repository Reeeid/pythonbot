import discord
from discord.ext import commands


EMOJI_TO_INDEX = {
    "1️⃣": 0,
    "2️⃣": 1,
    "3️⃣": 2,
    "4️⃣": 3,
    "5️⃣": 4,
    "6️⃣": 5,
}


class LSpellReactionHandlerCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        if user.bot:
            return

        embed = reaction.message.embeds[0] if reaction.message.embeds else None
        if not embed or not embed.footer or not embed.footer.text:
            return

        footer_text = embed.footer.text
        if not footer_text.startswith("lspell_ids:"):
            return

        try:
            spell_ids_part = footer_text.split(":", 1)[1]
            spell_ids_on_page = [
                int(spell_id)
                for spell_id in spell_ids_part.split(",")
                if spell_id.strip()
            ]
        except (IndexError, ValueError):
            return

        emoji_key = str(reaction.emoji)
        if emoji_key not in EMOJI_TO_INDEX:
            return

        index = EMOJI_TO_INDEX[emoji_key]
        if index >= len(spell_ids_on_page):
            await self._safe_remove_reaction(reaction, user)
            return

        target_spell_id = spell_ids_on_page[index]

        l_user_spell_sets_cog = self.bot.get_cog("LUserSpellSetsCog")
        if not l_user_spell_sets_cog:
            await self._safe_remove_reaction(reaction, user)
            return

        spell = await l_user_spell_sets_cog.get_spell_by_query(str(target_spell_id))
        if not spell:
            await self._notify(user, f"エラー: ID {target_spell_id} のL呪文が見つかりませんでした。")
            await self._safe_remove_reaction(reaction, user)
            return

        current_user_spells = await l_user_spell_sets_cog.get_user_spell_set_spells(user.id)
        spell_in_set = any(spell_data["ID"] == target_spell_id for spell_data in current_user_spells)

        if spell_in_set:
            if await l_user_spell_sets_cog.remove_spell_from_user_set(user.id, target_spell_id):
                result_message = f"あなたのL呪文セットから '{spell['name']}' を削除しました。"
            else:
                result_message = f"エラー: '{spell['name']}' をあなたのL呪文セットから削除できませんでした。"
        else:
            if await l_user_spell_sets_cog.add_spell_to_user_set(user.id, target_spell_id):
                result_message = f"あなたのL呪文セットに '{spell['name']}' を追加しました。"
            else:
                result_message = f"エラー: '{spell['name']}' をあなたのL呪文セットに追加できませんでした。"

        await self._notify(user, result_message)
        await self._safe_remove_reaction(reaction, user)

    async def _notify(self, user, message):
        try:
            await user.send(message)
        except discord.Forbidden:
            pass

    async def _safe_remove_reaction(self, reaction, user):
        try:
            await reaction.remove(user)
        except (discord.Forbidden, discord.NotFound, discord.HTTPException):
            pass


def setup(bot):
    bot.add_cog(LSpellReactionHandlerCog(bot))
