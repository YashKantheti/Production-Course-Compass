import base64  # import base 64 so we can change the school ID format
import ssl  # secure connection for the api pull 
import certifi  # pulls only verified certificate files
import aiohttp  # async web requests

VT_SCHOOL_ID = 1349  # Virginia Tech school ID on Rate My Professors
_RMP_GQL_URL = "https://www.ratemyprofessors.com/graphql"  # GraphQL API link

# This query tells the site what professor info to send back 
#in this case its the first + last name, department, and the rating info from rate my professor 
_SEARCH_QUERY = """
query TeacherSearch($text: String!, $schoolID: ID!) {
  search: newSearch {
    teachers(query: {text: $text, schoolID: $schoolID}, first: 10) {
      edges {
        node {
          id
          firstName
          lastName
          department
          avgRating
          avgDifficulty
          wouldTakeAgainPercent
          numRatings
          legacyId
        }
      }
    }
  }
}
"""

# headers to help simulate the request 
_HEADERS_NO_AUTH = {
    "Content-Type": "application/json",  # the request is sending JSON
    "User-Agent": (  # our browser info
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "  # the device type info
        "AppleWebKit/537.36 (KHTML, like Gecko) "  # the browser engine info
        "Chrome/120.0.0.0 Safari/537.36"  # the version of the browser window
    ),
    "Referer": "https://www.ratemyprofessors.com/",  # says exactly where the request came from
}


# this is the class that stores one professor infromation result we get from the request
class ProfessorResult:
    def __init__(self, node: dict):  # api data is turned into an object 
        self.name = f"{node.get('firstName', '')} {node.get('lastName', '')}".strip()  # first + last name of prof
        self.department = node.get("department") or "N/A"  # the department they are in
        self.rating = node.get("avgRating")  # their average rating
        self.difficulty = node.get("avgDifficulty")  # the indicated average difficulty
        self.would_take_again = node.get("wouldTakeAgainPercent")  # percent of students who would take again
        self.num_ratings = node.get("numRatings", 0)  # total number of ratings given by previous students
        legacy_id = node.get("legacyId")  # the profile id 
        self.url = f"https://www.ratemyprofessors.com/professor/{legacy_id}" if legacy_id else "https://www.ratemyprofessors.com"  # link of the profile on rate my professor


# function to search professor name at indicated school 
async def search_professor(name: str, school_id: int = VT_SCHOOL_ID) -> ProfessorResult | None:
    """
    Search RMP for a professor by name at the given school.
    Returns the result with the most ratings, or None if not found.
    """
    # use base64 to convert the school ID into the format the API understands
    school_node_id = base64.b64encode(f"School-{school_id}".encode()).decode()

    # data sent for the request 
    payload = {
        "query": _SEARCH_QUERY,  # add in the search query text 
        "variables": {"text": name, "schoolID": school_node_id},  # add the value for those search query 
    }

    # SSL setup for the request to safely be able to send requests
    ssl_ctx = ssl.create_default_context(cafile=certifi.where())
    connector = aiohttp.TCPConnector(ssl=ssl_ctx)
    
    # create session to send in the request 
    async with aiohttp.ClientSession(headers=_HEADERS_NO_AUTH, connector=connector) as session: #AI WAS USED TO HELP CREATE THIS LINE 
        async with session.post(_RMP_GQL_URL, json=payload) as resp:
            if resp.status != 200:  # checks if the request failed perchance
                raise RuntimeError(f"RMP returned HTTP {resp.status}")  # if it failed, raises an error flag
            data = await resp.json(content_type=None)  # the response is turned into data

    # teacher result is extracted from the request using .get func
    edges = (
        data.get("data", {})  # get the data 
            .get("search", {})  # get the search 
            .get("teachers", {})  # get the teacher
            .get("results", [])  # get the results list
    )

    if not edges:  # if nothing is found, return nothing
        return None

    # picking the professor with the most rating using numratings to be able to compare 
    best = max(edges, key=lambda e: e["node"].get("numRatings", 0))
    return ProfessorResult(best["node"])  # return the best node as the professor with the most amount of ratings 