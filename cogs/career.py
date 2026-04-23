import re
import discord
from discord import app_commands
from discord.ext import commands
from utils import ai_client

# create the choices for academic level option
LEVEL_CHOICES = [
    app_commands.Choice(name="Freshman", value="freshman"),
    app_commands.Choice(name="Sophomore", value="sophomore"),
    app_commands.Choice(name="Junior", value="junior"),
    app_commands.Choice(name="Senior", value="senior"),
]

# constant values for output colors
MAROON = 0x861F41
ORANGE = 0xE5751F


class CareerCog(commands.Cog):
       # setup the cog with a reference to the bot
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    # register the command
    @app_commands.command(
        name="career",
        description="Get career advice and VT club recommendations based on your interests."
    )
        # let the user know what info to input about the fields for the command
    @app_commands.describe(
        interests="What areas interest you? (e.g. 'cybersecurity, machine learning, web dev')",
        level="Your current academic level"
    )
        # creates choices for the user to select from acadmic level options
    @app_commands.choices(level=LEVEL_CHOICES)
    async def career(
        self,
        interaction: discord.Interaction,
        interests: str,
        level: app_commands.Choice[str]
    ):
        await interaction.response.defer(thinking=True)
        try:
            result = await ai_client.get_career_advice(interests, level.value)
        except Exception as e:
            await interaction.followup.send(
                embed=_error_embed(f"AI service error: {e}"),
                ephemeral=True
            )
            return

        clubs, tips = _format_career_payload(result)

        embed = discord.Embed(
            title=f"🎯 Career Advice for {level.name}",
            description=f"Interests: **{interests}**",
            color=ORANGE,
        )
        embed.add_field(name="VT Clubs & Organizations", value=clubs, inline=False)
        embed.add_field(name="Career Tips", value=tips, inline=False)
        embed.set_footer(text="CourseCompass Career Adviser • Get involved early!")
        embed.set_author(
            name="CourseCompass Career Adviser",
            icon_url="https://upload.wikimedia.org/wikipedia/commons/thumb/1/1f/Virginia_Tech_seal.svg/240px-Virginia_Tech_seal.svg.png"
        )
        await interaction.followup.send(embed=embed)


def _format_career_payload(raw: str) -> tuple[str, str]:
    lines = [l.strip().lstrip("-*• ").strip() for l in raw.splitlines() if l.strip()]

    club_lines = []
    tip_lines = []

    # Lines that mention known club keywords go into clubs; the rest into tips
    club_keywords = re.compile(
        r"\b(cyber vt|aws builder club|ieee|CMDA club|google dev club|VT Asian Engineer Association|"
        r"wics|women in computer|robotics|game dev|vtgd|app team|open source|vtlosc|"
        r"blockchain|web dev|quantum|vtluug|linux)\b",
        re.IGNORECASE
    )

    for line in lines:
        if not line:
            continue
        if club_keywords.search(line):
            club_lines.append(f"• {line}")
        else:
            tip_lines.append(f"• {line}")

    clubs = "\n".join(club_lines[:5]) if club_lines else "• Explore https://students.cs.vt.edu/undergraduate-programs/current-students/getting-involved.html to find organizations matching your interests."
    tips = "\n".join(tip_lines[:4]) if tip_lines else "• Build projects, contribute to open source, and apply for internships early."

    # Discord field value limit is 1024 chars
    return clubs[:1020], tips[:1020]

# handling error messages
def _error_embed(message: str) -> discord.Embed:
    return discord.Embed(
        title="Something went wrong",
        description=message,
        color=discord.Color.red()
    )

# more setup for the bot
async def setup(bot: commands.Bot):
    await bot.add_cog(CareerCog(bot))
