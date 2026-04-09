#AI USAGE NOTE: AI helped reformat/create several of the docstrings in this file.
"""
VT grade distribution data loader.

Data source: VT University Data Commons grade distribution CSV.
Since UDC requires VT PID authentication, bundle a pre-exported CSV at data/vt_grades.csv.
To refresh data: log into https://udc.vt.edu/irdata/data/courses/grades and export to CSV.

Expected CSV columns:
    term, subject, course_number, instructor, gpa, A, A-, B+, B, B-, C+, C, C-, D+, D, D-, F, W
"""

import csv
from collections import defaultdict
from pathlib import Path

DATA_PATH = Path(__file__).parent.parent / "data" / "vt_grades.csv"

# column names for all possible grade values in the csv
GRADE_COLS = ["A", "A-", "B+", "B", "B-", "C+", "C", "C-", "D+", "D", "D-", "F", "W"]

#AI USAGE NOTE: The cache structure and logic was done with the help of AI.
# general cache structure being set up - maps course code to term (e.g., "202408") to grade distribution percentages
cache: dict[str, dict[str, dict[str, float]]] | None = None

#AI USAGE NOTE: The cache structure and logic was done with the help of AI.
# cache for pre-computed course insights
insights_cache: dict[str, dict] | None = None

#AI USAGE NOTE: The cache structure and logic was done with the help of AI.
def load() -> dict[str, dict[str, dict[str, float]]]:
    """Load and parse grade distribution CSV, returning cached grade percentages by course and term."""
    global cache
    if cache is not None:
        return cache  # return cached data if already loaded

    data: dict[str, dict[str, dict[str, float]]] = defaultdict(dict)

    # warn if data file doesn't exist and return empty result
    if not DATA_PATH.exists():
        print(f"[vt_data] WARNING: {DATA_PATH} not found. Grade commands will return no data.")
        cache = {}
        return cache

    with open(DATA_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # extract and normalize the course identifier from the row
            subject = row.get("subject", "").strip().upper()
            number = row.get("course_number", "").strip()
            term = row.get("term", "").strip()
            
            # skip incomplete rows
            if not subject or not number or not term:
                continue

            # build unique course identifier from subject and course number
            code = f"{subject} {number}"
            grades = {}  # will store grade percentages for this row
            total = 0.0  # sum of all grade counts for this row
            raw = {}  # temporarily store raw grade counts before converting to percentages
            
            # collect raw grade counts and calculate total enrollments
            for g in GRADE_COLS:
                try:
                    val = float(row.get(g, 0) or 0)
                except ValueError:
                    val = 0.0
                raw[g] = val  # store the raw count
                total += val  # accumulate for later division

            # convert raw counts to percentages
            if total > 0:
                grades = {g: round(raw[g] / total * 100, 2) for g in GRADE_COLS}  # divide each grade by total and multiply by 100
            else:
                grades = {g: 0.0 for g in GRADE_COLS}  # if no students, all grades are 0%

            # aggregate by term (we average across different instructors teaching the same course in the same term)
            if term not in data[code]:
                # initialize term entry with count tracker and zero placeholders for each grade
                data[code][term] = {"_count": 0, **{g: 0.0 for g in GRADE_COLS}}
            entry = data[code][term]
            entry["_count"] += 1  # increment instructor count for this course-term pair
            for g in GRADE_COLS:
                entry[g] += grades[g]  # accumulate grade percentages from this instructor

    # finalize averages by dividing accumulated grade percentages by number of sections
    result: dict[str, dict[str, dict[str, float]]] = {}
    for code, terms in data.items():
        result[code] = {}
        for term, entry in terms.items():
            count = entry["_count"]  # number of instructors for this course in this term
            # average the accumulated percentages by dividing by instructor count
            result[code][term] = {g: round(entry[g] / count, 2) for g in GRADE_COLS}

    cache = result  # store in global cache
    return cache  # return the processed grade distribution data


def get_course_codes() -> list[str]:
    """Return a sorted list of all available course codes (e.g., ['CS 3114', 'CS 3304', ...])."""
    return sorted(load().keys())


def load_insights() -> dict[str, dict]:
    """
    Aggregate course-level metrics and instructor rollups for UI summaries.
    Returns metrics like average GPA, A-rate, W-rate, and a list of instructors sorted by experience.
    """
    global insights_cache
    if insights_cache is not None:
        return insights_cache  # return cached insights if already computed

    # initialize the insights accumulator with nested default dicts for aggregation
    insights: dict[str, dict] = defaultdict(
        lambda: {
            "terms": set(),  # set of unique terms this course was offered
            "sections": 0,  # total number of course sections
            "gpa_sum": 0.0,  # accumulate gpas to compute average
            "gpa_count": 0,  # count of gpas for averaging
            "a_rate_sum": 0.0,  # accumulate a/a- rates
            "w_rate_sum": 0.0,  # accumulate withdrawal rates
            "instructors": defaultdict(  # per-instructor statistics
                lambda: {"sections": 0, "a_rate_sum": 0.0, "gpa_sum": 0.0, "gpa_count": 0}
            ),
        }
    )

    # return empty cache if data file doesn't exist
    if not DATA_PATH.exists():
        insights_cache = {}
        return insights_cache

    with open(DATA_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # normalize course identifiers
            subject = row.get("subject", "").strip().upper()
            number = row.get("course_number", "").strip()
            term = row.get("term", "").strip()
            instructor = row.get("instructor", "").strip() or "Staff"  # default to "staff" if missing
            
            # skip incomplete rows
            if not subject or not number or not term:
                continue

            code = f"{subject} {number}"
            item = insights[code]
            item["terms"].add(term)
            item["sections"] += 1

            # safely extract and accumulate gpa value
            try:
                gpa_val = float(row.get("gpa", 0) or 0)
            except ValueError:
                gpa_val = 0.0

            if gpa_val > 0:  # only accumulate if gpa is valid
                item["gpa_sum"] += gpa_val
                item["gpa_count"] += 1  # track count for averaging later

            # extract a/a- and w (withdrawal) rates
            try:
                a_rate = float(row.get("A", 0) or 0) + float(row.get("A-", 0) or 0)  # combine A and A- percentages
            except ValueError:
                a_rate = 0.0
            try:
                w_rate = float(row.get("W", 0) or 0)  # withdrawal rate
            except ValueError:
                w_rate = 0.0

            # accumulate course-level rates
            item["a_rate_sum"] += a_rate  # accumulate for course average
            item["w_rate_sum"] += w_rate  # accumulate for course average

            # accumulate per-instructor statistics
            instr = item["instructors"][instructor]  # get or create instructor entry
            instr["sections"] += 1  # increment section count for this instructor
            instr["a_rate_sum"] += a_rate  # accumulate for instructor average
            if gpa_val > 0:
                instr["gpa_sum"] += gpa_val  # accumulate instructor gpa
                instr["gpa_count"] += 1  # track count for averaging

    # finalize aggregated metrics and build instructor ranking
    finalized: dict[str, dict] = {}
    for code, raw in insights.items():
        sections = raw["sections"]  # total number of sections this course has
        # compute course-level averages
        avg_gpa = round(raw["gpa_sum"] / raw["gpa_count"], 2) if raw["gpa_count"] else 0.0  # average gpa across all sections
        avg_a_rate = round(raw["a_rate_sum"] / sections, 1) if sections else 0.0  # average a-rate across all sections
        avg_w_rate = round(raw["w_rate_sum"] / sections, 1) if sections else 0.0  # average withdrawal rate

        # build list of instructor rows with computed metrics
        instructor_rows = []
        for name, i in raw["instructors"].items():
            i_sections = i["sections"]  # sections taught by this instructor
            i_a = round(i["a_rate_sum"] / i_sections, 1) if i_sections else 0.0  # average a-rate for this instructor
            i_gpa = round(i["gpa_sum"] / i["gpa_count"], 2) if i["gpa_count"] else 0.0  # average gpa for this instructor
            instructor_rows.append(
                {
                    "name": name,
                    "sections": i_sections,
                    "a_rate": i_a,
                    "gpa": i_gpa,
                }
            )

        # sort instructors by experience (sections) and performance (a-rate), descending
        instructor_rows.sort(key=lambda r: (r["sections"], r["a_rate"]), reverse=True)  # most experienced and highest-rated first

        # store the finalized metrics for this course
        finalized[code] = {
            "terms": len(raw["terms"]),  # number of unique terms course was offered
            "sections": sections,  # total number of sections taught
            "avg_gpa": avg_gpa,  # average course gpa
            "a_rate": avg_a_rate,  # average a/a- percentage
            "w_rate": avg_w_rate,  # average withdrawal percentage
            "instructors": instructor_rows,  # sorted list of instructors with metrics
        }

    insights_cache = finalized  # cache the finalized insights
    return insights_cache  # return the aggregated insights data


def query_course(course_code: str, semester: str | None = None) -> tuple[dict[str, float], str] | None:
    """
    Return (grade_distribution_dict, semester_label) for the given course code.
    If semester is None, returns the most recent semester's data.
    Returns None if the course is not found.
    """
    db = load()  # load the grade distribution cache
    code = course_code.strip().upper()  # normalize the course code

    # return none if course doesn't exist in database
    if code not in db:
        return None

    terms = db[code]  # get all terms available for this course
    if not terms:
        return None

    # return specific semester if requested and available
    if semester and semester in terms:
        return terms[semester], format_term(semester)

    # default to the most recent term if semester not specified
    latest_term = max(terms.keys())  # find lexicographically largest term code
    return terms[latest_term], format_term(latest_term)


def query_course_insights(course_code: str) -> dict | None:
    """
    Return aggregated course metrics and top instructors for dashboard-style embeds.
    Includes average GPA, A-rate, W-rate, and sorted instructor list.
    """
    db = load_insights()  # load the pre-computed insights cache
    code = course_code.strip().upper()  # normalize the course code
    return db.get(code)  # return insights or None if course not found


def format_term(term: str) -> str:
    """
    Convert term code (like '202408') into a human-readable semester label (like 'Fall 2024').
    Falls back to the raw term string if format doesn't match.
    """
    if len(term) == 6:
        year = term[:4]  # extract first 4 digits as year
        month = term[4:]  # extract last 2 digits as month code
        # map month codes to season names
        seasons = {"01": "Spring", "06": "Summer", "08": "Fall", "12": "Winter"}
        season = seasons.get(month, month)  # look up season or use month code as fallback
        return f"{season} {year}"
    return term  # return unchanged if not 6 digits
