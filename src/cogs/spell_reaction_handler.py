import discord
from discord.ext import commands
import asyncio

class SpellReactionHandlerCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.tracked_messages = {} # {message_id: [spell_id1, spell_id2, ...] }

    def register_spell_list_message(self, message_id: int, spell_ids: list[int]):
        self.tracked_messages[message_id] = spell_ids

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        # ボット自身のリアクションやDMでのリアクションは無視
        if user.bot or not reaction.message.guild:
            return

        # 追跡対象のメッセージか確認
        if reaction.message.id not in self.tracked_messages:
            return

        spell_ids_on_message = self.tracked_messages[reaction.message.id]
        emojis = {"1️⃣": 0, "2️⃣": 1, "3️⃣": 2, "4️⃣": 3, "5️⃣": 4, "6️⃣": 5}

        # 有効な絵文字か確認
        if str(reaction.emoji) not in emojis:
            return

        index = emojis[str(reaction.emoji)]

        # 絵文字が指す呪文がリストの範囲内か確認
        if index >= len(spell_ids_on_message):
            await reaction.remove(user) # 無効なリアクションは削除
            return

        target_spell_id = spell_ids_on_message[index]

        user_spell_sets_cog = self.bot.get_cog("UserSpellSetsCog")
        if not user_spell_sets_cog:
            print("Error: UserSpellSetsCog not found.")
            await reaction.remove(user)
            return

        # 呪文の詳細情報を取得
        spell = await user_spell_sets_cog.get_spell_by_query(str(target_spell_id))
        if not spell:
            await user.send(f"エラー: ID {target_spell_id} の呪文が見つかりませんでした。")
            await reaction.remove(user)
            return

        # ユーザーの現在の呪文セットを取得
        current_user_spells = await user_spell_sets_cog.get_user_spell_set_spells(user.id)
        spell_in_set = any(s['ID'] == target_spell_id for s in current_user_spells)

        if spell_in_set:
            # 既にセットにあれば削除
            if await user_spell_sets_cog.remove_spell_from_user_set(user.id, target_spell_id):
                await user.send(f"あなたの呪文セットから '{spell['name']}' を削除しました。")
            else:
                await user.send(f"エラー: '{spell['name']}' をあなたの呪文セットから削除できませんでした。")
        else:
            # セットになければ追加
            if await user_spell_sets_cog.add_spell_to_user_set(user.id, target_spell_id):
                await user.send(f"あなたの呪文セットに '{spell['name']}' を追加しました。")
            else:
                await user.send(f"エラー: '{spell['name']}' をあなたの呪文セットに追加できませんでした。")
        
        # ユーザーのリアクションを削除
        try:
            await reaction.remove(user)
        except discord.Forbidden: # ボットにリアクション削除権限がない場合
            pass

def setup(bot):
    bot.add_cog(SpellReactionHandlerCog(bot))
