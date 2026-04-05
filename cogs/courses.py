# worked with team memebers to determine approriate imports needed for this cog
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
    # Prompt: "Create the remaining logic to handle the course reccomendation command given LEVEL_CHOICES (grade) selection, and a string of their intrests
    # using the AI client. include a list of reccommended courses and advising notes, and information about the prerequisites for the courses."
    
    # reccomend function that uses the information for the user to create output using the AI_Client
    async def recommend(
        self,
        interaction: discord.Interaction,
        interests: str,
        level: app_commands.Choice[str]
    ):
        await interaction.response.defer(thinking=True)
        #utilizing the AI Client to get reccomendations
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