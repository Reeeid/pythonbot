

import discord
from discord.ext import commands, pages
import aiosqlite # sqlite3の代わりにaiosqliteをインポート
import os
import csv
from discord.commands import Option
from typing import Optional

class SpellbookCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'spells.db')
        self.bot.loop.create_task(self._async_setup_db()) # 非同期でDBセットアップを呼び出す

    async def _async_setup_db(self):
        await self._setup_db()
        await self._import_csv_to_db()

    async def _setup_db(self):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                CREATE TABLE IF NOT EXISTS spells (
                    ID INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE,
                    level INTEGER,
                    type TEXT,
                    Stime TEXT,
                    Range TEXT,
                    Ref TEXT,
                    mov TEXT,
                    TimeC TEXT,
                    save TEXT,
                    target TEXT,
                    description TEXT,
                    highlevel TEXT,
                    WIZ TEXT,
                    WAR TEXT,
                    CRE TEXT,
                    SOR TEXT,
                    DOR TEXT,
                    BRD TEXT,
                    PRD TEXT,
                    REN TEXT
                )
            ''')
            await db.commit()

    async def _import_csv_to_db(self):
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute('SELECT COUNT(*) FROM spells')
            count = (await cursor.fetchone())[0]
            if count == 0: # テーブルが空の場合のみインポート
                csv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'SRD.csv')
                with open(csv_path, 'r', encoding='utf-8-sig') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        data = {
                            'ID': row.get('ID'),
                            'name': row.get('name'),
                            'level': row.get('level'),
                            'type': row.get('type'),
                            'Stime': row.get('Stime'),
                            'Range': row.get('Range'),
                            'Ref': row.get('Ref'),
                            'mov': row.get('mov'),
                            'TimeC': row.get('TimeC'),
                            'save': row.get('save'),
                            'target': row.get('target'),
                            'description': row.get('description'),
                            'highlevel': row.get('highlevel'),
                            'WIZ': row.get('WIZ'),
                            'WAR': row.get('WAR'),
                            'CRE': row.get('CRE'),
                            'SOR': row.get('SOR'),
                            'DOR': row.get('DOR'),
                            'BRD': row.get('BRD'),
                            'PRD': row.get('PRD'),
                            'REN': row.get('REN')
                        }
                        if not data['ID']:
                            data['ID'] = None
                        else:
                            data['ID'] = int(data['ID'])
                        if data['level'] and data['level'].isdigit():
                            data['level'] = int(data['level'])
                        else:
                            data['level'] = None

                        await db.execute('''
                            INSERT OR IGNORE INTO spells (
                                ID, name, level, type, Stime, Range, Ref, mov, TimeC, save, target, description, highlevel,
                                WIZ, WAR, CRE, SOR, DOR, BRD, PRD, REN
                            ) VALUES (
                                :ID, :name, :level, :type, :Stime, :Range, :Ref, :mov, :TimeC, :save, :target, :description, :highlevel,
                                :WIZ, :WAR, :CRE, :SOR, :DOR, :BRD, :PRD, :REN
                            )
                        ''', data)
                await db.commit()

    async def get_spell_by_id(self, spell_id: int):
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute('SELECT * FROM spells WHERE ID = ?', (spell_id,))
            spell = await cursor.fetchone()
            return spell
        
    async def get_spell_by_name(self, spell_name: str):
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute('SELECT * FROM spells WHERE name = ?', (spell_name,))
            spell = await cursor.fetchone()
            return spell

    async def filter_spells(self, class_name: str = None, level: int = None):
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.cursor()

            query = "SELECT * FROM spells WHERE 1=1"
            params = []

            if class_name:
                class_col = class_name.upper()
                # クラス列が存在するか確認
                cursor_info = await db.execute(f"PRAGMA table_info(spells)")
                cols = [col[1] for col in await cursor_info.fetchall()]
                if class_col in cols:
                    query += f" AND {class_col} = ?"
                    params.append('Y')
                else:
                    return []

            if level is not None:
                query += " AND level = ?"
                params.append(level)

            query += " ORDER BY level"

            cursor = await db.execute(query, tuple(params))
            spells = await cursor.fetchall()
            return spells

    def create_spell_list_embeds(self, spells):
        chunked_spells = [spells[i:i + 6] for i in range(0, len(spells), 6)]
        if not chunked_spells:
            return [discord.Embed(title="検索結果", description="条件に合う呪文は見つかりませんでした。", color=discord.Color.red())]

        embeds = []
        for i, chunk in enumerate(chunked_spells):
            embed = discord.Embed(title=f"呪文リスト ({i+1}/{len(chunked_spells)})", color=discord.Color.blue())
            page_spell_ids = [str(spell['ID']) for spell in chunk]
            for spell in chunk:
                description = spell['description']
                if description and len(description) > 100:
                    description = description[:100] + "..."
                elif not description:
                    description = "(説明なし)"

                embed.add_field(
                    name=f"***▶ ID: {spell['ID']}                  {spell['name']}***",
                    value=f"レベル: {spell['level']}　　　|　　　タイプ: {spell['type']}　　　|　　　詠唱時間: {spell['Stime']}\n"
                          f"射程: {spell['Range']}　　　|　　　目標: {spell['target']}\n"
                          f"持続: {spell['TimeC']}　　　|　　　セーヴ: {spell['save']}\n\n"
                          f"説明: {description}\n\n"
                          f"------------------>>",
                    inline=False
                )
            embed.set_footer(text=f"spell_ids:{','.join(page_spell_ids)}")
            embeds.append(embed)
        return embeds

    def create_spell_detail_embed(self, spell):
        embed = discord.Embed(title=f"呪文詳細: {spell['name']}", color=discord.Color.green())

        display_info = [
            ('ID', 'ID', True),
            ('name', '名前', True),
            ('level', 'レベル', True),
            ('type', 'タイプ', True),
            ('Stime', '詠唱時間', True),
            ('Range', '射程', True),
            ('target', '対象', True),
            ('TimeC', '持続時間', True),
            ('save', 'セーヴ', True),
            ('Ref', '参照', True),
            ('mov', '構成要素', True),
            ('highlevel', '高レベル化', True)
        ]

        for key, display_name, inline_status in display_info:
            value = spell[key] or "(なし)"
            embed.add_field(name=display_name, value=f"**{value}**", inline=inline_status)

        description = spell['description']
        if description and len(description) > 1024:
            for i, chunk in enumerate([description[j:j+1024] for j in range(0, len(description), 1024)]):
                embed.add_field(name=f"説明 {i+1}/{len(description)//1024 + 1}", value=chunk, inline=False)
        elif description:
            embed.add_field(name="説明", value=description, inline=False)
        else:
            embed.add_field(name="説明", value="(説明なし)", inline=False)
        return embed

    @commands.slash_command(name="spell", description="呪文を検索し、一覧表示します。")
    async def spell(self, ctx: discord.ApplicationContext, class_name: Option(str, description="WIZ,WAR,CRE,SOR,DOR,BRD,PRD,REN", default=None), level: Option(int, description="0-9", default=None)):
        filtered_spells = await self.filter_spells(class_name, level)
        embeds = self.create_spell_list_embeds(filtered_spells)
        
        if not embeds:
            await ctx.respond("条件に合う呪文は見つかりませんでした。", ephemeral=True)
            return

        paginator = pages.Paginator(pages=embeds)
        message = await paginator.respond(ctx.interaction, ephemeral=False)

        # 最初のページに表示された呪文に対してのみリアクションを追加
        if len(embeds) > 0 and embeds[0].footer.text:
            emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣"]
            num_spells = len(embeds[0].footer.text.split(":")[1].split(","))
            for i in range(num_spells):
                if i < len(emojis):
                    await message.add_reaction(emojis[i])

    @commands.slash_command(name="spellid", description="指定したIDの呪文の詳細を表示します。")
    async def spellid(self, ctx: discord.ApplicationContext, spell_id: int):
        spell = await self.get_spell_by_id(spell_id)
        if spell:
            embed = self.create_spell_detail_embed(spell)
            await ctx.respond(embed=embed)
        else:
            await ctx.respond("指定されたIDの呪文は見つかりませんでした。", ephemeral=True)

    @commands.slash_command(name="spellname", description="指定した名前の呪文の詳細を表示します。")
    async def spellname(self, ctx: discord.ApplicationContext, spell_name: str):
        spell = await self.get_spell_by_name(spell_name)
        if spell:
            embed = self.create_spell_detail_embed(spell)
            await ctx.respond(embed=embed)
        else:
            await ctx.respond("指定されたIDの呪文は見つかりませんでした。", ephemeral=True)

    @commands.slash_command(name="spelladd", description="新しい呪文を登録します (ホワイトリストユーザーのみ)。")
    async def spelladd(
        self, 
        ctx: discord.ApplicationContext,
        name: str,
        level: int,
        type: str,
        stime: str,
        range: str,
        target: str,
        timec: str,
        save: str,
        description: str,
        ref: str = None,
        mov: str = None,
        highlevel: str = None,
        wiz: bool = False,
        war: bool = False,
        cre: bool = False,
        sor: bool = False,
        dor: bool = False,
        brd: bool = False,
        prd: bool = False,
        ren: bool = False
    ):
        glossary_cog = self.bot.get_cog("GlossaryCog")
        if not glossary_cog or (not await glossary_cog._is_whitelisted(ctx.author.id) and not await glossary_cog._is_admin(ctx.author.id)):
            await ctx.respond("このコマンドを実行する権限がありません。", ephemeral=True)
            return

        async with aiosqlite.connect(self.db_path) as db:
            try:
                await db.execute('''
                    INSERT INTO spells (
                        name, level, type, Stime, Range, Ref, mov, TimeC, save, target, description, highlevel,
                        WIZ, WAR, CRE, SOR, DOR, BRD, PRD, REN
                    ) VALUES (
                        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                        ?, ?, ?, ?, ?, ?, ?, ?
                    )
                ''',
                (
                    name, level, type, stime, range, ref, mov, timec, save, target, description, highlevel,
                    'Y' if wiz else '', 'Y' if war else '', 'Y' if cre else '', 'Y' if sor else '',
                    'Y' if dor else '', 'Y' if brd else '', 'Y' if prd else '', 'Y' if ren else ''
                ))
                await db.commit()
                await ctx.respond(f"呪文 `{name}` を登録しました。")
            except aiosqlite.IntegrityError:
                await ctx.respond(f"呪文 `{name}` は既に登録されています。", ephemeral=True)

    @commands.slash_command(name="spellremove", description="呪文を削除します (ホワイトリストユーザーのみ)。")
    async def spellremove(self, ctx: discord.ApplicationContext, id: str):
        glossary_cog = self.bot.get_cog("GlossaryCog")
        if not glossary_cog or (not await glossary_cog._is_whitelisted(ctx.author.id) and not await glossary_cog._is_admin(ctx.author.id)):
            await ctx.respond("このコマンドを実行する権限がありません。", ephemeral=True)
            return

        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute('DELETE FROM spells WHERE ID = ?', (id,))
            await db.commit()
            if cursor.rowcount > 0:
                await ctx.respond(f"ID: `{id}` を削除しました。")
            else:
                await ctx.respond(f"ID: `{id}` は見つかりませんでした。", ephemeral=True)

def setup(bot):
    bot.add_cog(SpellbookCog(bot))
