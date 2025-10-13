import json
from pathlib import Path

import discord
from discord.ext import commands
from discord.ui import Select, View

# --------------------------------------------------------------------------------
#  Data load utilities
# --------------------------------------------------------------------------------
def _resolve_data_path() -> Path:
    data_dir = Path(__file__).resolve().parent.parent / 'data'
    for candidate_name in ('data.json', 'races.json'):
        candidate = data_dir / candidate_name
        if candidate.exists():
            return candidate
    raise FileNotFoundError('Race data file not found. Expected data.json or races.json in the data directory.')


DATA_PATH = _resolve_data_path()


def _load_race_data() -> dict:
    """Load race data from the resolved JSON file."""
    try:
        with DATA_PATH.open(encoding='utf-8') as data_file:
            return json.load(data_file)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f'Race data file is invalid JSON: {DATA_PATH}') from exc


RACE_DATA = _load_race_data()

# --------------------------------------------------------------------------------
#  Autocomplete helper
# --------------------------------------------------------------------------------
async def race_autocomplete(ctx: discord.AutocompleteContext):
    """Return race names matching user input for slash command autocomplete."""
    # 現在入力中の文字を取得
    user_input = ctx.value.lower()
    
    # RACE_DATAのキー（種族名）から、入力中の文字で始まるものを候補として抽出
    return [
        race for race in RACE_DATA.keys() if race.lower().startswith(user_input)
    ]

# --------------------------------------------------------------------------------
#  Embedを作成するためのヘルパー関数群
# --------------------------------------------------------------------------------
def create_base_embed(race_name: str, data: dict) -> discord.Embed:
    """基本概要のEmbedを作成する"""
    embed = discord.Embed(
        title=f"{data['emoji']} {race_name}",
        description=data["description"],
        color=data["color"]
    )
    for name, value in data["basic_info"].items():
        embed.add_field(name=name, value=value, inline=True)
    
    embed.add_field(name="能力値上昇", value=data["ability_score"], inline=False)

    traits_text = "\n".join(f"**● {name}:** {desc}" for name, desc in data["main_traits"].items())
    embed.add_field(name="主な種族特性", value=traits_text, inline=False)
    
    embed.set_footer(text="下のメニューから詳細情報を選択してください。")
    return embed

def create_subrace_embed(race_name: str, data: dict) -> discord.Embed:
    """サブ種族一覧のEmbedを作成する"""
    embed = discord.Embed(
        title=f"🧬 {race_name}のサブ種族",
        color=data["color"]
    )
    for name, desc in data["subraces"].items():
        embed.add_field(name=name, value=desc, inline=False)
    return embed

def create_legacy_trait_embed(race_name: str, data: dict) -> discord.Embed:
    """レガシー・トレイト一覧のEmbedを作成する"""
    embed = discord.Embed(
        title=f"📜 {race_name}のレガシー・トレイト",
        description="キャラクター作成時に以下から2つを選択します。",
        color=data["color"]
    )
    embed.add_field(name="選択肢", value="\n".join(data["legacy_traits"]))
    return embed

def create_mixed_blood_embed(race_name: str, data: dict) -> discord.Embed:
    """混血の特性一覧のEmbedを作成する"""
    embed = discord.Embed(
        title=f"🔗 {race_name}の混血の特性",
        description=f"この種族を主要な種族として**選ばなかった**場合に、レガシー・トレイトの選択肢として追加されます。",
        color=data["color"]
    )
    for name, desc in data["mixed_blood_traits"].items():
        embed.add_field(name=name, value=desc, inline=False)
    return embed


# --------------------------------------------------------------------------------
#  UIコンポーネント (ドロップダウンメニュー)
# --------------------------------------------------------------------------------
class RaceInfoSelect(Select):
    def __init__(self, race_name: str):
        self.race_name = race_name
        self.race_data = RACE_DATA[race_name]

        options = [
            discord.SelectOption(label="基本概要", description=f"{race_name}の基本情報を表示", emoji=self.race_data['emoji']),
            discord.SelectOption(label="サブ種族", description="サブ種族の一覧と能力を表示", emoji="🧬"),
            discord.SelectOption(label="レガシー・トレイト", description="選択可能な共通特性を表示", emoji="📜"),
            discord.SelectOption(label="混血の特性", description="混血時に選択可能な専用特性を表示", emoji="🔗"),
        ]
        super().__init__(placeholder=f"{race_name}の詳細情報を選択...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        selection = self.values[0]
        
        if selection == "基本概要":
            new_embed = create_base_embed(self.race_name, self.race_data)
        elif selection == "サブ種族":
            new_embed = create_subrace_embed(self.race_name, self.race_data)
        elif selection == "レガシー・トレイト":
            new_embed = create_legacy_trait_embed(self.race_name, self.race_data)
        elif selection == "混血の特性":
            new_embed = create_mixed_blood_embed(self.race_name, self.race_data)
        else:
            await interaction.response.send_message("エラーが発生しました。", ephemeral=True)
            return

        await interaction.response.edit_message(embed=new_embed)


class RaceInfoView(View):
    def __init__(self, race_name: str):
        super().__init__(timeout=180)
        self.add_item(RaceInfoSelect(race_name))


# --------------------------------------------------------------------------------
#  Cog本体 (コマンドの定義)
# --------------------------------------------------------------------------------
class RaceCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ▼▼▼ コマンドの定義を修正 ▼▼▼
    @commands.slash_command(name="race", description="種族の詳細情報を表示します。")
    async def race(
        self,
        ctx: discord.ApplicationContext,
        # choices=... を削除し、autocomplete=... を追加
        race_name: discord.Option(
            str,
            description="情報を表示したい種族名を入力してください。",
            autocomplete=race_autocomplete
        )
    ):
        """種族の基本情報と詳細オプションを表示するコマンド"""
        if race_name not in RACE_DATA:
            await ctx.respond(f"指定された種族「{race_name}」は見つかりませんでした。", ephemeral=True)
            return

        race_data = RACE_DATA[race_name]
        
        initial_embed = create_base_embed(race_name, race_data)
        view = RaceInfoView(race_name)
        
        await ctx.respond(embed=initial_embed, view=view)
        
        # ▼▼▼ 新しい `/racelist` コマンドをここに追加 ▼▼▼
    @commands.slash_command(name="racelist", description="利用可能な全ての種族を一覧表示します。")
    async def racelist(self, ctx: discord.ApplicationContext):
        """Display the list of available races with their emoji."""
        if not RACE_DATA:
            await ctx.respond("利用可能な種族データが見つかりません。", ephemeral=True)
            return

        sorted_items = sorted(RACE_DATA.items(), key=lambda item: item[0])
        lines = [f"{info.get('emoji', '🔹')} {name}" for name, info in sorted_items]

        embed = discord.Embed(
            title="📖 利用可能な種族一覧",
            description="`/race <種族名>` で詳細を確認できます。",
            color=discord.Color.blue()
        )

        chunk_size = 10
        for index in range(0, len(lines), chunk_size):
            chunk = lines[index:index + chunk_size]
            embed.add_field(name='\u200b', value='\n'.join(chunk), inline=True)

        embed.set_footer(text=f"合計: {len(lines)}種族")

        await ctx.respond(embed=embed, ephemeral=True)


# CogをBOTに登録するための必須関数
def setup(bot: commands.Bot):
    bot.add_cog(RaceCog(bot))
