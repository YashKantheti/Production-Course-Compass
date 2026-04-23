import discord
from discord import app_commands
from discord.ext import commands
from utils.rmp import search_professor, ProfessorResult

#color constants
MAROON = 0x861F41
ORANGE = 0xE5751F

#AI USAGE NOTE: some function headers in this document were expanded/formatted with the help of AI.

# translates numbers into avisual bar for the rating
def rating_bar(rating: float, max_rating: float = 5.0, length: int = 10) -> str:
    filled = round((rating / max_rating) * length)  # figure out how many blocks to fill
    return "█" * filled + "░" * (length - filled)  # concatenate filled + empty blocks


# turns a numerical difficulty score into a word label
def difficulty_label(score: float) -> str:
    if score < 2.0:
        return "Easy"
    elif score < 3.0:
        return "Moderate"
    elif score < 4.0:
        return "Challenging"
    else:
        return "Very Hard"


# main class that handles all the professor-related commands for the discord bot
class ProfessorsCog(commands.Cog):
    # initializes
    def __init__(self, bot: commands.Bot):
        self.bot = bot  # initialize the bot instance

    # set up discord slash command for professor lokup and discord UI response
    @app_commands.command(
        name="professor",
        description="Look up a Virginia Tech professor's Rate My Professor rating."
    )
    @app_commands.describe(name="Professor's name (e.g. 'Godmar Back')")

    #AI USAGE NOTE: Some of the await statements in this function were created with the help of AI
    async def professor(self, interaction: discord.Interaction, name: str):
        await interaction.response.defer(thinking=True)  # await command for discord

        try:
            prof = await search_professor(name)  # professor lookup on RMP
        except Exception as e:
            NOTE: CODE ADDDED (ephemeral=True on RMP unreachable)
            await interaction.followup.send(  # error message if RMP unreachable
                embed=error_embed(f"Could not reach Rate My Professor: {e}"),
                ephemeral=True,
            )
            return

        NOTE: CODE ADDDED (not-found handling)
        if prof is None:  # if no professor found on RMP
            await interaction.followup.send(
                embed=not_found_embed(name),
                ephemeral=True,
            )
            return

        embed = build_professor_embed(prof)  # create embed
        await interaction.followup.send(embed=embed)  # return embed

#AI USAGE NOTE: the logic for this function was created by humans, but some of the syntax and Discord formatting wasdone with the help of AI.
# creates the actual embed with layout and information that the user sees
def build_professor_embed(prof: ProfessorResult) -> discord.Embed:
    rating = prof.rating  # get the rating
    difficulty = prof.difficulty  # get the difficulty
    would_take_again = prof.would_take_again  # get the take again percentage

    if rating is None:
        color = discord.Color.greyple()  # grey if no rating
    elif rating >= 4.0:
        color = 0x57F287   # green for good
    elif rating >= 3.0:
        color = ORANGE  # orange for okay
    else:
        color = 0xED4245   # red for bad

    embed = discord.Embed(  # create the embed
        title=f"Prof. {prof.name}",
        description=f"**{prof.department}** · Virginia Tech",
        color=color,
        url=prof.url,
    )

    #add relevant fields

    if rating is not None:
        embed.add_field(  # add rating field for professor
            name="Overall Rating",
            value=f"`{rating_bar(rating)}` **{rating:.1f} / 5.0**",
            inline=False,
        )
    else:
        embed.add_field(name="Overall Rating", value="No ratings yet", inline=False)  # no rating message

    if difficulty is not None:
        embed.add_field(  # add difficulty field
            name="Difficulty",
            value=f"`{rating_bar(difficulty)}` **{difficulty:.1f} / 5.0**  ({difficulty_label(difficulty)})",
            inline=False,
        )

    if would_take_again is not None and would_take_again >= 0:
        embed.add_field(  # add take again field if available
            name="Would Take Again",
            value=f"**{round(would_take_again)}%** of students",
            inline=True,
        )

    if prof.num_ratings:
        embed.add_field(name="Total Ratings", value=str(prof.num_ratings), inline=True)  # show how many ratings there are

    embed.set_footer(text="Data from ratemyprofessors.com - ratings may vary by semester")  # add a note at the bottom
    return embed  # send back the finished embed


#AI USAGE NOTE: this function was created with the help of AI.
# creates embed for general errors
def error_embed(message: str) -> discord.Embed:
    return discord.Embed(title="Error", description=message, color=discord.Color.red())  # red embed with the error message


NOTE: CODE ADDED
# this makes an embed for when we can't find the professor
def not_found_embed(name: str) -> discord.Embed:
    return discord.Embed(  # create error embed
        title=f"Professor not found: {name}",
        description=(
            "No results on Rate My Professor for this name at Virginia Tech.\n"
            "Try their full name, e.g. `/professor name Godmar Back`."
        ),
        color=discord.Color.red(),
    )


#AI USAGE NOTE: this function was created with the help of AI.
# adds the cog to the bot when the extension is loaded
async def setup(bot: commands.Bot):
    await bot.add_cog(ProfessorsCog(bot))  # register the professor commands
