
import os
import asyncio
import discord
from discord.ext import commands
import yt_dlp

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

YDL_OPTIONS = {
    "format": "bestaudio/best",
    "noplaylist": True,
    "quiet": True,
    "default_search": "ytsearch",
}

FFMPEG_OPTIONS = {
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
    "options": "-vn",
}

@bot.event
async def on_ready():
    print(f"Bot conectado como {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"{len(synced)} comandos sincronizados.")
    except Exception as e:
        print(e)


@bot.tree.command(name="play", description="Toca uma música")
async def play(interaction: discord.Interaction, musica: str):

    if not interaction.user.voice:
        await interaction.response.send_message(
            "❌ Você precisa estar em uma chamada de voz primeiro."
        )
        return

    canal = interaction.user.voice.channel

    await interaction.response.defer()

    try:
        if interaction.guild.voice_client is None:
            voz = await canal.connect()
        else:
            voz = interaction.guild.voice_client
            if voz.channel != canal:
                await voz.move_to(canal)

        loop = asyncio.get_event_loop()

        def buscar():
            with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
                resultado = ydl.extract_info(
                    musica,
                    download=False
                )

                if "entries" in resultado:
                    resultado = resultado["entries"][0]

                return resultado

        dados = await loop.run_in_executor(None, buscar)

        url = dados["url"]
        titulo = dados.get("title", "Música desconhecida")

        if voz.is_playing():
            voz.stop()

        fonte = discord.FFmpegPCMAudio(
            url,
            **FFMPEG_OPTIONS
        )

        voz.play(fonte)

        await interaction.followup.send(
            f"🎵 Tocando agora: **{titulo}**"
        )

    except Exception as e:
        await interaction.followup.send(
            f"❌ Não consegui tocar a música.\n`{e}`"
        )


@bot.tree.command(name="stop", description="Para a música e sai da chamada")
async def stop(interaction: discord.Interaction):

    voz = interaction.guild.voice_client

    if voz:
        await voz.disconnect()
        await interaction
