#Import Discord library, commands related to /s, and cogs.
import discord
from discord import app_commands
from discord.ext import commands

#Gets the data and charts.
from utils import vt_data, charts

#Color codes for the bot.
MAROON = 0x861F41
ORANGE = 0xE5751F

#Makes a module for the bot.
class GradesCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        #Saves the bot reference for sending messages.
        self.bot = bot 

    #Defines the slash command /grades.
    @app_commands.command(
        #Creates the command /grades for users to use.
        name="grades",
        #Text to help the user understand what the /grades command does.
        description="Show grade distribution for a VT CS course (e.g. CS 3114)."
    )

    #Describes the input the user should provide.
    @app_commands.describe(course="Course code, e.g. CS 3114 or ECE 2574")
    async def grades(self, interaction: discord.Interaction, course: str):
        #Used to avoid any timeout errors.
        if not await safe_defer(interaction):
            #Avoids any kind of crashing that occured as a result.
            return

        #Gets the course data from the vt_data module.
        course_data = vt_data.query_course(course)

        #If the course isn't found, it gives a helpful message to guide the user.
        if course_data is None:
            #It gets the first 15 valid course codes.
            available_courses = ", ".join(vt_data.get_course_codes()[:15])
            await safe_followup_send(
                #Sends a repsonse to Discord.
                interaction,
                embed=not_found_embed(
                    course,
                    f"Available courses include: {available_courses} …\nUse `/grades CS 3114` format."
                ),
                #Makes it so only the user can see this.
                ephemeral=True
            )
            #Stops the function because the course doesn't exist.
            return

        #Unpacks the data from vt_data.query_course. grade_data has counts of grades, semester is a string.
        grade_data, semester = course_data
        #Gets extra insights like average GPA and professor information.
        course_insights = vt_data.query_course_insights(course)
        #Makes a chart to show the grade distribution.
        grade_chart_file = charts.generate_grade_bar(course, grade_data, semester)

        #Creates a Discord embed to show the data nicely.
        embed = discord.Embed(
            #This is the title of the embed.
            title=f"{course.upper()} - Grade Snapshot",
            #A little summary of the grade data + insights.
            description=overview_line(grade_data, course_insights),
            #The color of the embed.
            color=ORANGE,
        )
        #Adds a field with a bar chart of the grade breakdown.
        embed.add_field(
            name="Grade Breakdown",
            #Formats the grades.
            value=grade_summary(grade_data),
            #Fully show this field.
            inline=False,
        )

        #If insights exists, show additional key metrics and instructor data.
        if course_insights:
            #AI was used to write this, but it essentially formats GPA, withdrawal rate, and a rate.
            embed.add_field(name="Key Metrics", value=kpi_cards(course_insights), inline=False)
            #AI was used to write this, but it essentially formats the instructor table.    
            embed.add_field(name="By Instructor", value=instructor_table(course_insights), inline=False)

        #Attaches the chart image to the embed.
        embed.set_image(url="attachment://grades.png")
        #Adds footer text to show the source information and semester.
        embed.set_footer(text=f"Source: VT DataCommons | {semester}")
        #AI was used to write this, but it essentially sends the embed and chart to Discord.
        await safe_followup_send(interaction, embed=embed, file=grade_chart_file)
    
    #Autocompletes for /grades command so Discord suggests the course codes.
    @grades.autocomplete("course")
    async def grades_autocomplete(
        self, interaction: discord.Interaction, current: str
    ) -> list[app_commands.Choice[str]]:
        #Gets all of the valid course codes.
        codes = vt_data.get_course_codes()
        #Converts the input to uppercase.
        current_input_upper = current.upper()
        #Finds matches and the max is 25 for Discord.
        matches = [c for c in codes if current_input_upper in c][:25]
        #Returns the choices to Discord.
        return [app_commands.Choice(name=c, value=c) for c in matches]

    #Defines the /compare commandto compare 2 courses.
    @app_commands.command(
        name="compare",
        description="Compare grade distributions of two VT courses side by side."
    )
    @app_commands.describe(
        course1="First course code (e.g. CS 2114)",
        course2="Second course code (e.g. CS 3114)"
    )
    async def compare(
        self,
        interaction: discord.Interaction,
        course1: str,
        course2: str
    ):
        #used to avoid timeout sessions.
        if not await safe_defer(interaction):
            return

        #Gets the data for both of the courses.
        course1_data = vt_data.query_course(course1)
        course2_data = vt_data.query_course(course2)

        #Checks if either of the courses are missing or don't exist.
        missing_courses = []
        if course1_data is None:
            missing_courses.append(course1.upper())
        if course2_data is None:
            missing_courses.append(course2.upper())
        if missing_courses:
            await safe_followup_send(
                interaction,
                embed=not_found_embed(", ".join(missing_courses), "Check the course code and try again."),
                #This is only visible to the user.
                ephemeral=True
            )
            return

        #Unpacks the data.
        data1, sem1 = course1_data
        data2, sem2 = course2_data
        #Makes a side by side chart to be used for comparison.
        grade_chart_file = charts.generate_compare_bar(course1, data1, course2, data2, sem1, sem2)

        #Creates the embed for comparison.
        embed = discord.Embed(
            title=f"Comparison: {course1.upper()} vs {course2.upper()}",
            color=MAROON,
        )
        embed.add_field(
            name=f"{course1.upper()}  ({sem1})",
            value=grade_summary(data1),
            inline=True
        )
        embed.add_field(
            name=f"{course2.upper()}  ({sem2})",
            value=grade_summary(data2),
            inline=True
        )
        #Attaches the chart.
        embed.set_image(url="attachment://compare.png")
        embed.set_footer(text="Source: VT DataCommons | Tip: pair one heavy and one moderate course")
        #Sends the embed and chart to Discord.
        await safe_followup_send(interaction, embed=embed, file=grade_chart_file)

    #Autocomplete for /compare courses by suggesting course codes as the user is typing.
    @compare.autocomplete("course1")
    @compare.autocomplete("course2")
    async def compare_autocomplete(
        self, interaction: discord.Interaction, current: str
    ) -> list[app_commands.Choice[str]]:
        #Gets all of the valid course codes.
        codes = vt_data.get_course_codes()
        #Converts the user input to uppercase.
        current_input_upper = current.upper()
        #Keeps the matches, the max is 25 for Discord.
        matches = [c for c in codes if current_input_upper in c][:25]
        #Returns the results to Discord.
        return [app_commands.Choice(name=c, value=c) for c in matches]

#Helper function to build summary as the bar chart,
def grade_summary(grade_data: dict) -> str:
    """Build compact fixed-width summary for primary grade buckets."""
    #A and A- combined.
    a_pct = grade_data.get("A", 0) + grade_data.get("A-", 0)
    #B grades combined.
    b_pct = grade_data.get("B+", 0) + grade_data.get("B", 0) + grade_data.get("B-", 0)
    #C grades combined.
    c_pct = grade_data.get("C+", 0) + grade_data.get("C", 0) + grade_data.get("C-", 0)
    #D and F grades combined.
    d_f_pct = (
        grade_data.get("D+", 0) + grade_data.get("D", 0) +
        grade_data.get("D-", 0) + grade_data.get("F", 0)
    )
    #Withdrawals.
    w_pct = grade_data.get("W", 0)
    lines = [
        bar_line("A", a_pct),
        bar_line("B", b_pct),
        bar_line("C", c_pct),
        bar_line("D/F", d_f_pct),
        bar_line("W", w_pct),
    ]
    #Used for formatting.
    return "```\n" + "\n".join(lines) + "\n```"

#Helper function for 1 line of the bar chart.
def bar_line(label: str, pct: float) -> str:
    #Converts percent to 0-20 scale for the number of bars.
    units = max(0, min(20, int(round(pct / 5))))
    #Creates the bar.
    return f"{label:<3} | {'#' * units}{'-' * (20 - units)} | {pct:>5.1f}%"

#Helper function for the overview line.
def overview_line(grade_data: dict, course_insights: dict | None) -> str:
    #A rate.
    a_rate = grade_data.get("A", 0) + grade_data.get("A-", 0)
    #Withdrawals.
    w_rate = grade_data.get("W", 0)
    #AI was used to write this, but it essentially calculates the GPA from grades.
    est_gpa = estimate_gpa(grade_data)

    if not course_insights:
        return f"All sections summary | Est GPA `{est_gpa:.2f}` | A-rate `{a_rate:.1f}%` | Withdraw `{w_rate:.1f}%`"

    #If there are insights, show the average GPA and # of sections.
    return (
        f"Across `{course_insights['terms']}` terms and `{course_insights['sections']}` sections | "
        f"Avg GPA `{course_insights['avg_gpa']:.2f}` | A-rate `{a_rate:.1f}%` | Withdraw `{w_rate:.1f}%`"
    )

#Helper function to show the key metrics.
def kpi_cards(course_insights: dict) -> str:
    #AI was used to write this, but it essentially shows the GPA, Withdrawal rate, and A rate.
    return "```\n" + (
        f"AVG GPA   {course_insights['avg_gpa']:.2f}\n"
        f"A RATE    {course_insights['a_rate']:.1f}%\n"
        f"WITHDRAW  {course_insights['w_rate']:.1f}%"
    ) + "\n```"

#Helper function to show information about the instructor.
def instructor_table(course_insights: dict) -> str:
    #Uses the top 4 instructors.
    rows = course_insights.get("instructors", [])[:4]
    if not rows:
        return "No instructor-level rows available."

    header = f"{'Instructor':<16} {'Sec':>3} {'A%':>5} {'GPA':>5}"
    body = [header, "-" * len(header)]
    for r in rows:
        #Limits the name to 16 characters, deafults it to Staff.
        name = (r["name"] or "Staff")[:16]
        body.append(f"{name:<16} {r['sections']:>3} {r['a_rate']:>5.1f} {r['gpa']:>5.2f}")
    return "```\n" + "\n".join(body) + "\n```"

#Helper function to estimate the GPA from grade percentages. 
def estimate_gpa(grade_data: dict) -> float:
    #Grades to GPA.
    weights = {
        "A": 4.0,
        "A-": 3.7,
        "B+": 3.3,
        "B": 3.0,
        "B-": 2.7,
        "C+": 2.3,
        "C": 2.0,
        "C-": 1.7,
        "D+": 1.3,
        "D": 1.0,
        "D-": 0.7,
        "F": 0.0,
    }
    total = 0.0
    for grade, weight in weights.items():
        #Converts percentage to fraction and multiplies it by the GPA.
        total += (grade_data.get(grade, 0) / 100.0) * weight
    return total

#Embed for the course not found.
def not_found_embed(course: str, hint: str = "") -> discord.Embed:
    embed = discord.Embed(
        title=f"Course not found: {course.upper()}",
        description=hint or "Make sure the course code is correct.",
        color=discord.Color.red()
    )
    return embed

#AI was used to write this, but it essentially helps ensure that there will be no Discord timeouts.
async def safe_defer(interaction: discord.Interaction) -> bool:
    """Defer safely; return False if the interaction is already invalid/expired."""
    try:
        await interaction.response.defer(thinking=True)
        return True
    except discord.NotFound:
        #The interaction expired.
        return False
    except discord.InteractionResponded:
        #It already responded and it's safe to continue.
        return True

#AI helped me write this, but it essentially sends a follow up message.
async def safe_followup_send(interaction: discord.Interaction, **kwargs) -> bool:
    """Send follow-up safely; return False if the interaction token is no longer valid."""
    try:
        await interaction.followup.send(**kwargs)
        return True
    except discord.NotFound:
        #The interaction token was invalid, so the message wasn't sent.
        return False

#Function to add cog to the bot.
async def setup(bot: commands.Bot):
    await bot.add_cog(GradesCog(bot))
