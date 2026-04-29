# this file creates the charts for grade distributions and shows them as images in discord


import io
import matplotlib.pyplot as plt
import discord


# for the dark theme i got the discord dark theme colors   
BACK_COLOR = "#23262d"
PLOT_BACK = "#2b2f38"
BAR_COLOR = "#4f7df0"
BAR_COLOR_2 = "#f07b59"
TEXT_COLOR = "#f2f4f8"
GRID_COLOR = "#4a4f5a"


# GRADE_ORDER = ["A", "A-", "B+", "B", "B-", "C+", "C", "C-", "D+", "D", "D-", "F", "W"]


GRADE_COLORS = {
   "A": "#7cc16b",
   "A-": "#70b963",
   "B+": "#5ba9e8",
   "B": "#4f9bda",
   "B-": "#448fcd",
   "C+": "#e0bf63",
   "C": "#d5ae4a",
   "C-": "#c99d37",
   "D+": "#d7816a",
   "D": "#ca6f58",
   "D-": "#bd5d47",
   "F": "#ae4b3b",
   "W": "#9ca3af",
}


# creates a bar chart for one course grade distr.
def generate_grade_bar(course_code, grade_data, semester="") -> discord.File:
   # the order of grades to display
   grade_order = ["A", "A-", "B+", "B", "B-", "C+", "C", "C-", "D+", "D", "D-", "F", "W"]


   #labels = [g for g in GRADE_ORDER if g in grade_data]
   labels = []
   values = []
   #values = [grade_data[g] for g in labels]


   # this part makes sure that the grades are in the correct order and only output them if they exist in data
   for g in grade_order:
       if g in grade_data:
           labels.append(g)
           values.append(grade_data[g])
   # creating the blank chart and ax will put in the bars, titles, and labels
   fig, ax = plt.subplots(figsize=(9.5, 4.8))
   fig.patch.set_facecolor(BACK_COLOR)
   ax.set_facecolor(PLOT_BACK)


   # I asked Claude for help with this part and it gave me code to label the bars with percents and the coloring as well
   # I was a bit confused about how to implement it but I now understand how this code works
   colors = [GRADE_COLORS.get(label, BAR_COLOR) for label in labels]
   bars = ax.bar(labels, values, color=colors, width=0.64, zorder=2)


   # this is for labeling the bars with the info. i asked claude for help on the zip in the loop
   for bar, val in zip(bars, values):
        # only label the bar if it is above 2% for cleanliness
        if val >= 2.0:
            ax.text(
                # x-position center of bar
                bar.get_x() + bar.get_width() / 2,
                # y-position just above the bar
                bar.get_height() + 0.5,
                # round the value to 0 decimal places and add a percent sign
                # i used chatgpt to help me understand how to format a string with a value var in it
                f"{val:.0f}%",
                ha="center", va="bottom",
                color=TEXT_COLOR, fontsize=8, fontweight="bold"
            )


   # this part is for the dark theme, i asked claude to help me with this part as well and it guided me through how to write it and then I put in my colors
   ax.tick_params(colors=TEXT_COLOR)
   ax.xaxis.label.set_color(TEXT_COLOR)
   ax.yaxis.label.set_color(TEXT_COLOR)
   ax.title.set_color(TEXT_COLOR)
   ax.yaxis.grid(True, color=GRID_COLOR, linewidth=0.7, alpha=0.5)
   ax.set_axisbelow(True)
   for spine in ax.spines.values():
       spine.set_edgecolor(GRID_COLOR)


   # title with the course code and sem
   title = "Grade Distribution | " + course_code.upper()
   if semester != "":
       title += " (" + semester + ")"


   # axis labels and title
   ax.set_title(title, fontsize=13, fontweight="bold")
   ax.set_xlabel("Grade", fontsize=11)
   ax.set_ylabel("Students (%)", fontsize=11)


   # i asked claude to help me with this because I wanted to make the spacing automatically adjust but didn't know how
   plt.tight_layout(pad=1.2)


   # i also asked claude to help me with this part to save the chart as a png to output to discord because I wasn't sure how to do it
   buf = io.BytesIO()
   fig.savefig(buf, format="png", facecolor=BACK_COLOR)
   plt.close(fig)
   buf.seek(0)
   return discord.File(buf, filename="grades.png")


# creates a side-by-side bar chart comparing grade distributions of two courses.
# AI (Claude) wrote was used in part to this function, it was used for formmating the png. 
def generate_compare_bar(course1, data1, course2, data2, sem1="", sem2="") -> discord.File:
   grade_order = ["A", "A-", "B+", "B", "B-", "C+", "C", "C-", "D+", "D", "D-", "F", "W"]

   labels, vals1, vals2 = [], [], []
   for g in grade_order:
       if g in data1 or g in data2:
           labels.append(g)
           vals1.append(data1.get(g, 0))
           vals2.append(data2.get(g, 0))

   import numpy as np
   x = np.arange(len(labels))
   width = 0.38

   fig, ax = plt.subplots(figsize=(11, 4.8))
   fig.patch.set_facecolor(BACK_COLOR)
   ax.set_facecolor(PLOT_BACK)

   bars1 = ax.bar(x - width / 2, vals1, width, color=BAR_COLOR, zorder=2, label=course1.upper())
   bars2 = ax.bar(x + width / 2, vals2, width, color=BAR_COLOR_2, zorder=2, label=course2.upper())

   for bars, vals in ((bars1, vals1), (bars2, vals2)):
       for bar, val in zip(bars, vals):
           if val >= 2.0:
               ax.text(
                   bar.get_x() + bar.get_width() / 2,
                   bar.get_height() + 0.5,
                   f"{val:.0f}%",
                   ha="center", va="bottom",
                   color=TEXT_COLOR, fontsize=7.5, fontweight="bold"
               )

   ax.set_xticks(x)
   ax.set_xticklabels(labels)
   ax.tick_params(colors=TEXT_COLOR)
   ax.xaxis.label.set_color(TEXT_COLOR)
   ax.yaxis.label.set_color(TEXT_COLOR)
   ax.title.set_color(TEXT_COLOR)
   ax.yaxis.grid(True, color=GRID_COLOR, linewidth=0.7, alpha=0.5)
   ax.set_axisbelow(True)
   for spine in ax.spines.values():
       spine.set_edgecolor(GRID_COLOR)

   ax.legend(facecolor=PLOT_BACK, edgecolor=GRID_COLOR, labelcolor=TEXT_COLOR)

   label1 = course1.upper() + (f" ({sem1})" if sem1 else "")
   label2 = course2.upper() + (f" ({sem2})" if sem2 else "")
   title = f"Grade Comparison | {label1} vs {label2}"
   ax.set_title(title, fontsize=13, fontweight="bold")
   ax.set_xlabel("Grade", fontsize=11)
   ax.set_ylabel("Students (%)", fontsize=11)

   plt.tight_layout(pad=1.2)

   buf = io.BytesIO()
   fig.savefig(buf, format="png", facecolor=BACK_COLOR)
   plt.close(fig)
   buf.seek(0)
   return discord.File(buf, filename="compare.png")