import os
import asyncio
import discord
from discord.ext import commands
import yt_dlp

TOKEN = os.getenv("DISCORD_TOKEN")

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
        comandos = await bot.tree.sync()
        print(f"{len(comandos)} comandos sincronizados.")
    except Exception as erro:
        print(f"Erro ao sincronizar comandos: {erro}")


@bot.tree.command(name="play", description="Toca uma música")
async def play(interaction: discord.Interaction, musica: str):

    if not interaction.user.voice:
        await interaction.response.send_message(
            "❌ Entre em uma chamada de voz primeiro."
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

        loop = asyncio.get_running_loop()

        def buscar_musica():
            with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
                resultado = ydl.extract_info(
                    musica,
                    download=False
                )

                if "entries" in resultado:
                    resultado = resultado["entries"][0]

                return resultado

        dados = await loop.run_in_executor(
            None,
            buscar_musica
        )

        titulo = dados.get(
            "title",
            "Música desconhecida"
        )

        url = dados["url"]

        if voz.is_playing():
            voz.stop()

        fonte = discord.FFmpegPCMAudio(
            url,
            **FFMPEG_OPTIONS
        )

        voz.play(fonte)

        await interaction.followup.send(
            f"🎵 Tocando: **{titulo}**"
        )

    except Exception as erro:
        print(f"Erro ao tocar música: {erro}")

        await interaction.followup.send(
            f"❌ Erro ao tocar a música: `{erro}`"
        )


@bot.tree.command(name="stop", description="Para a música e sai da chamada")
async def stop(interaction: discord.Interaction):

    voz = interaction.guild.voice_client

    if voz:
        await voz.disconnect()
        await interaction.response.send_message(
            "⏹️ Música parada."
        )
    else:
        await interaction.response.send_message(
            "❌ O bot não está em uma chamada."
        )


@bot.tree.command(name="pause", description="Pausa a música")
async def pause(interaction: discord.Interaction):

    voz = interaction.guild.voice_client

    if voz and voz.is_playing():
        voz.pause()
        await interaction.response.send_message(
            "⏸️ Música pausada."
        )
    else:
        await interaction.response.send_message(
            "❌ Não há música tocando."
        )


@bot.tree.command(name="resume", description="Continua a música")
async def resume(interaction: discord.Interaction):

    voz = interaction.guild.voice_client

    if voz and voz.is_paused():
        voz.resume()
        await interaction.response.send_message(
            "▶️ Música continuando."
        )
    else:
        await interaction.response.send_message(
            "❌ A música não está pausada."
        )


if not TOKEN:
    print("ERRO: DISCORD_TOKEN não foi configurado.")
else:
    bot.run(TOKEN)
