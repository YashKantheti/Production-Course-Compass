# worked with team memebers to determine approriate imports needed for this cog
import discord
from discord import app_commands
from discord.ext import commands
from utils import ai_client
import re
import textwrap


# create the choices for academic level option
LEVEL_CHOICES = [
    app_commands.Choice(name="Freshman", value="freshman"),
    app_commands.Choice(name="Sophomore", value="sophomore"),
    app_commands.Choice(name="Junior", value="junior"),
    app_commands.Choice(name="Senior", value="senior"),
    app_commands.Choice(name="Graduate", value="graduate"),
]

# constant values for output colors
MAROON = 0x861F41   # VT maroon
ORANGE = 0xE5751F   # VT orange


class CoursesCog(commands.Cog):
   # setup the cog with a reference to the bot
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    # register the command
    @app_commands.command(
        name="recommend",
        description="Get AI-powered course recommendations based on your interests and year."
    )
    # let the user know what info to input about the fields for the command
    @app_commands.describe(
        interests="What topics or skills interest you? (e.g. 'machine learning, web dev, systems')",
        level="Your current academic level"
    )
    # creates choices for the user to select from acadmic level options
    @app_commands.choices(level=LEVEL_CHOICES)

    # This is where the bot will utilze the AI client to create the output for the user
    # AI (ChatGPT) was used to help write this following code
    # Not sure if it is an official "prompt" (because it did not give back code to be used yet or specific help)
    # but started out with telling ChatGpt the idea of our project, planned files 
    # (such as the cogs, utils and how the AI client setup would be based on our group discussions), 
    # then giving background of what this specific file/feature end goal would look like)
    # Prompt: "Create the remaining logic to handle the course reccomendation command given LEVEL_CHOICES (grade) selection, and a string of their intrests
    # using the AI client. include a list of reccommended courses and advising notes, and information about the prerequisites for the courses."
    # Prompt: "Using the information in this file so far complete the helper functions for the _format_recommendation_payload function to format
    # the output from the AI client so it can be used in the embed" 
    
    # reccomend function that uses the information for the user to create output using the AI_Client
    async def recommend(
        self,
        interaction: discord.Interaction,
        interests: str,
        level: app_commands.Choice[str]
    ):
        await interaction.response.defer(thinking=True)
        #utilizing the AI Client to get reccomendations output to create output for the user
        try:
            result = await ai_client.get_course_recommendations(interests, level.value)
        except Exception as e:
            await interaction.followup.send(
                embed=_error_embed(f"AI service error: {e}"),
                ephemeral=True
            )
            return
        # output reccomendations back to the user
        rows, notes = _format_recommendation_payload(result)

        embed = discord.Embed(
            title=f"🗂️ Recommended {level.name} Plan",
            description=f"Interests: **{interests}**",
            color=MAROON,
        )
        embed.add_field(name="Course Picks", value=rows, inline=False)
        embed.add_field(name="Advising Notes", value=notes, inline=False)
        embed.set_footer(text="CourseCompass planner • Validate prerequisites before registration")
        embed.set_author(
            name="CourseCompass AI Advisor",
            icon_url="https://upload.wikimedia.org/wikipedia/commons/thumb/1/1f/Virginia_Tech_seal.svg/240px-Virginia_Tech_seal.svg.png"
        )
        await interaction.followup.send(embed=embed)

# function to format the AI info for the user
def _format_recommendation_payload(raw: str) -> tuple[str, str]:
    picks = _extract_course_picks(raw)
    if not picks:
        return raw[:1000], "Compare risks before finalizing your schedule."

    lines = []
    for code, title in picks[:5]:
        fit = _course_fit_label(code)
        clean_title = _clean_course_title(title)
        wrapped = textwrap.wrap(clean_title, width=34) or ["Recommended course"]
        lines.append(f"• **{code}** [{fit}]")
        for idx, chunk in enumerate(wrapped[:2]):
            prefix = "  " if idx == 0 else "    "
            lines.append(f"{prefix}{chunk}")

    rows = "\n".join(lines)
    notes = _notes_block(raw)
    return rows, notes

# helper function for the fromat that cleans the course title and sends back to the formatting function
def _clean_course_title(title: str) -> str:
    title = re.sub(r"^[-:]+", "", title).strip()
    title = re.sub(r"\s+", " ", title)
    return title

# helper function to extract the course reccomendations from the AI output to be used in the formatting function
def _extract_course_picks(raw: str) -> list[tuple[str, str]]:
    picks: list[tuple[str, str]] = []
    seen: set[str] = set()
    for line in raw.splitlines():
        match = re.search(r"([A-Z]{2,4}\s?\d{4})", line.upper())
        if not match:
            continue

        code = match.group(1).replace("  ", " ").strip()
        if code in seen:
            continue
        seen.add(code)

        title_part = line.split(match.group(1), 1)[-1].strip(" :-\u2014\t")
        title = title_part if title_part else "Recommended course"
        picks.append((code, title))
    return picks

# helper function to make labels for the courses to tell the user what course the class is for (elective, core, or support)
def _course_fit_label(code: str) -> str:
    code = code.upper()
    core = {"CS 1114", "CS 2114", "CS 2505", "CS 2506", "CS 3114", "CS 3214"}
    if code in core:
        return "Core"
    if code.startswith("MATH"):
        return "Support"
    return "Elective"

# helper function to clean the notes returned from the AI client
def _notes_block(raw: str) -> str:
    note_lines = []
    for line in raw.splitlines():
        cleaned = line.strip().lstrip("-*• ").strip()
        if not cleaned:
            continue
        if re.search(r"[A-Z]{2,4}\s?\d{4}", cleaned.upper()):
            continue
        note_lines.append(f"• {cleaned}")
        if len(note_lines) >= 4:
            break

    if not note_lines:
        return "• Keep workload balanced; avoid stacking multiple high-intensity courses."
    return "\n".join(note_lines)


# handling error messages
def _error_embed(message: str) -> discord.Embed:
    return discord.Embed(
        title="Something went wrong",
        description=message,
        color=discord.Color.red()
    )
# more setup for the bot
async def setup(bot: commands.Bot):
    await bot.add_cog(CoursesCog(bot))