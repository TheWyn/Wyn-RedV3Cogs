import random

from discord import Colour, Embed
from redbot.core.utils.chat_formatting import humanize_number

from .api.formatters import format_birth_date, format_description, format_media_type
from .api.media import MediaData


def do_media_embed(data: MediaData, is_channel_nsfw: bool) -> Embed:
    description = format_description(data.description or "", 500) + "\n\n"
    embed = Embed(colour=data.prominent_colour, title=str(data.title), url=data.siteUrl or "")

    if data.isAdult and not is_channel_nsfw:
        embed.colour = 0xFF0000
        embed.description = f"This {data.type.lower()} is marked as 🔞 NSFW on AniList."
        embed.set_footer(text="Try again in NSFW channel to see full embed!")
        return embed

    # if data.coverImage.large and data.type == "MANGA":
    #     embed.set_thumbnail(url=data.coverImage.large)
    embed.set_image(url=f"https://img.anili.st/media/{data.id}")

    if data.type == "ANIME":
        if data.status == "RELEASING":
            if (next_ep := data.nextAiringEpisode) and next_ep.episode:
                next_airing = f" (⏩ Next <t:{next_ep.airingAt}:R>)" if next_ep.airingAt else ""
                description += f"**Episodes:**  {next_ep.episode - 1}{next_airing}\n"
        elif data.episodes and data.format != "MOVIE":
            description += f"**Episodes:**  {data.episodes}\n"
        if data.duration:
            description += f"**Duration:**  {data.humanize_duration} (average)\n"
    elif data.type == "MANGA":
        if data.chapters:
            description += f"**Chapters:**  {data.chapters}\n"
        if data.volumes:
            description += f"**Volumes:**  {data.volumes or 0}\n"
    if data.source:
        description += f"**Source:**  {data.media_source}\n"

    start_date = str(data.startDate)
    end_date = str(data.endDate)
    if_same_dates = f" to {end_date}" if start_date != end_date else ""
    description += f"**{data.release_mode}**  {start_date}{if_same_dates}\n"

    # if data.synonyms:
    #     embed.add_field(name="Synonyms", value=', '.join(f'`{x}`' for x in data.synonyms))
    if data.externalLinks:
        embed.add_field(name="External Links", value=data.external_links, inline=False)

    stats = [f'Type: {format_media_type(data.format or "N/A")}', data.media_status]
    embed.set_footer(text=" • ".join(stats))
    embed.description = description
    return embed
