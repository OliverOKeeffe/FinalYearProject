import os
import time
import requests
import pandas as pd

from services.constants import CACHE_TTL_SECONDS, PLAYERS_MAX_PAGES

BASE_URL = "https://v3.football.api-sports.io"

# In-memory cache: cache_key -> (timestamp_saved, json_data)
_API_CACHE = {}


def clear_api_cache():
    _API_CACHE.clear()


# I define a helper function to construct the API headers, which includes the API key from environment variables. This function will be used for all API requests to ensure consistent authentication.
def api_headers():
    key = os.getenv("APIFOOTBALL_KEY")
    if not key:
        raise RuntimeError("Missing APIFOOTBALL_KEY environment variable.")
    return {"x-apisports-key": key, "Accept": "application/json"}


# I define a helper function to create a unique cache key based on the API endpoint path and the parameters. This allows me to store and retrieve cached responses for specific API calls.
def _make_cache_key(path: str, params: dict) -> str:
    items = sorted((params or {}).items(), key=lambda x: x[0])
    return f"{path}|{items}"


# I define a function to make GET requests to the API, which includes caching logic. The function checks if a valid cached response exists for the given path and parameters, and returns it if available. If not, it makes the actual API request, handles errors, caches the response, and returns the data.
def api_get(path: str, params: dict) -> dict:
    key = _make_cache_key(path, params)
    now = time.time()

    if key in _API_CACHE:
        saved_ts, saved_data = _API_CACHE[key]
        if (now - saved_ts) < CACHE_TTL_SECONDS:
            return saved_data
        else:
            del _API_CACHE[key]

    url = f"{BASE_URL}{path}"
    r = requests.get(url, headers=api_headers(), params=params, timeout=25)

    try:
        data = r.json()
    except Exception:
        raise RuntimeError(f"API returned non-JSON data. HTTP {r.status_code}")

    if r.status_code != 200:
        raise RuntimeError(f"HTTP {r.status_code}: {data}")

    errors = data.get("errors")
    if isinstance(errors, dict) and len(errors) > 0:
        raise RuntimeError(f"API errors: {errors}")

    _API_CACHE[key] = (now, data)
    return data


# ---------------------------------------------------------
# TEAM TOP SCORERS
# ---------------------------------------------------------


# I define a function to get the top scorers for a specific team in a league and season. This function handles pagination to ensure it retrieves all relevant players, sums their goals, and returns the top 10 scorers as a DataFrame.
def get_team_top_scorers(
    league_id: int, team_id: int, season_year: int
) -> pd.DataFrame:
    all_rows = []

    first = api_get(
        "/players",
        {"league": league_id, "season": season_year, "team": team_id, "page": 1},
    )

    total_pages = int((first.get("paging") or {}).get("total") or 1)
    capped_pages = min(total_pages, int(PLAYERS_MAX_PAGES))

    # I define a helper function to parse the API response and extract player names and their total goals. This function is used for each page of results to build a complete list of players and their goal counts.
    def parse_response(resp):
        rows = []
        for item in resp.get("response", []):
            player = item.get("player", {}) or {}
            stats = (item.get("statistics") or [{}])[0] or {}
            goals = (stats.get("goals") or {}).get("total", 0)

            rows.append(
                {
                    "player": player.get("name", "Unknown"),
                    "goals": int(goals or 0),
                }
            )
        return rows

    # I start by parsing the first page of results, and then loop through any additional pages up to the capped limit, parsing each one and extending the list of all player goal data.
    all_rows.extend(parse_response(first))

    for page in range(2, capped_pages + 1):
        resp = api_get(
            "/players",
            {"league": league_id, "season": season_year, "team": team_id, "page": page},
        )
        all_rows.extend(parse_response(resp))
    # After collecting all player data, I create a DataFrame, filter out players with zero goals, and return the top 10 scorers sorted by goals.
    df = pd.DataFrame(all_rows)
    if df.empty:
        return df

    df = df.groupby("player", as_index=False)["goals"].sum()
    df = df[df["goals"] > 0]
    if df.empty:
        return df
    # Finally, I sort the DataFrame by goals in descending order, take the top 10 rows, and reset the index before returning it.
    return df.sort_values("goals", ascending=False).head(10).reset_index(drop=True)


# ---------------------------------------------------------
# LEAGUE TOP SCORERS (CORRECT ENDPOINT)
# ---------------------------------------------------------


# I define a function to get the top scorers for an entire league in a given season. This function calls the correct API endpoint for league top scorers, extracts player names and their total goals, and returns the top 10 scorers as a DataFrame.
def get_league_top_scorers(league_id: int, season_year: int) -> pd.DataFrame:
    data = api_get("/players/topscorers", {"league": league_id, "season": season_year})
    # I parse the API response to extract player names and their total goals, handling cases where data might be missing. I then create a DataFrame, sort it by goals in descending order, and return the top 10 scorers.
    rows = []
    for item in data.get("response", []):
        player = item.get("player", {}) or {}
        stats = (item.get("statistics") or [{}])[0] or {}
        goals = (stats.get("goals") or {}).get("total", 0)

        rows.append(
            {
                "player": player.get("name", "Unknown"),
                "goals": int(goals or 0),
            }
        )
    # I create a DataFrame from the collected player goal data, check if it's empty, and if not, sort it by goals in descending order, take the top 10 rows, reset the index, and return it.
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    # I sort the DataFrame by goals in descending order, take the top 10 rows, reset the index, and return it.
    return df.sort_values("goals", ascending=False).head(10).reset_index(drop=True)


# ---------------------------------------------------------
# TEAM TOP ASSISTS
# ---------------------------------------------------------


# I define a function to get the top assist providers for a specific team in a league and season. This function handles pagination to ensure it retrieves all relevant players, sums their assists, and returns the top 10 assist providers as a DataFrame.
def get_team_top_assists(
    league_id: int, team_id: int, season_year: int
) -> pd.DataFrame:
    all_rows = []
    # I start by making the initial API call to get the first page of players for the specified league, season, and team. This allows me to determine how many total pages of results there are, and I set a cap on the number of pages to retrieve to avoid excessive API calls.
    first = api_get(
        "/players",
        {"league": league_id, "season": season_year, "team": team_id, "page": 1},
    )

    total_pages = int((first.get("paging") or {}).get("total") or 1)
    capped_pages = min(total_pages, int(PLAYERS_MAX_PAGES))

    # I define a helper function to parse the API response and extract player names and their total assists. This function is used for each page of results to build a complete list of players and their assist counts.
    def parse_response(resp):
        rows = []
        for item in resp.get("response", []):
            player = item.get("player", {}) or {}
            stats = (item.get("statistics") or [{}])[0] or {}
            goals = stats.get("goals") or {}
            assists = goals.get("assists", 0)

            rows.append(
                {
                    "player": player.get("name", "Unknown"),
                    "assists": int(assists or 0),
                }
            )
        return rows

    # I start by parsing the first page of results, and then loop through any additional pages up to the capped limit, parsing each one and extending the list of all player assist data.
    all_rows.extend(parse_response(first))
    # After collecting all player data, I create a DataFrame, filter out players with zero assists, and return the top 10 assist providers sorted by assists.
    for page in range(2, capped_pages + 1):
        resp = api_get(
            "/players",
            {"league": league_id, "season": season_year, "team": team_id, "page": page},
        )
        all_rows.extend(parse_response(resp))
    # I create a DataFrame from the collected player assist data, check if it's empty, and if not, group by player to sum assists, filter out players with zero assists, sort by assists in descending order, take the top 10 rows, reset the index, and return it.
    df = pd.DataFrame(all_rows)
    if df.empty:
        return df
    # I group the DataFrame by player and sum their assists, then filter out players with zero assists. If the resulting DataFrame is empty, I return it. Otherwise, I sort it by assists in descending order, take the top 10 rows, reset the index, and return it.
    df = df.groupby("player", as_index=False)["assists"].sum()
    df = df[df["assists"] > 0]
    if df.empty:
        return df

    return df.sort_values("assists", ascending=False).head(10).reset_index(drop=True)


# ---------------------------------------------------------
# TEAM FORM (LAST N MATCHES)
# ---------------------------------------------------------


# I define a function to get the recent form of a team based on their last N matches in a league and season. This function retrieves the relevant fixtures, checks their status to ensure they are completed matches, determines if the team was home or away, calculates points earned from each match, and returns a DataFrame with the date, points, and result (win/draw/loss) for each match.
def get_team_form_points(
    league_id: int, season_year: int, team_id: int, last_n: int = 10
) -> pd.DataFrame:
    data = api_get(
        "/fixtures",
        {"league": league_id, "season": season_year, "team": team_id, "last": last_n},
    )
    # §
    rows = []
    for item in data.get("response", []):
        fx = item.get("fixture", {}) or {}
        status = (fx.get("status", {}) or {}).get("short", "")
        # I only want to consider matches that have been completed, so I check the status of each fixture and skip any that are not finished (e.g., scheduled or in-progress matches).
        if status not in {"FT", "AET", "PEN"}:
            continue
        # I extract the teams involved in the fixture and the goals scored by each team. I determine if the specified team was playing at home or away, calculate the goals for and against, and then determine the points earned from the match (3 for a win, 1 for a draw, 0 for a loss) and the result (W/D/L).
        teams = item.get("teams", {}) or {}
        goals = item.get("goals", {}) or {}

        home = teams.get("home") or {}
        away = teams.get("away") or {}

        home_id = home.get("id")
        hg = goals.get("home")
        ag = goals.get("away")

        if hg is None or ag is None:
            continue

        is_home = home_id == team_id
        gf = hg if is_home else ag
        ga = ag if is_home else hg

        if gf > ga:
            pts, res = 3, "W"
        elif gf == ga:
            pts, res = 1, "D"
        else:
            pts, res = 0, "L"
        # I extract the date of the fixture, format it as needed, and append a row to the list with the date, points earned, and result for each match.
        rows.append(
            {
                "date": (fx.get("date") or "")[:10],
                "points": pts,
                "result": res,
            }
        )
    # After processing all fixtures, I create a DataFrame from the collected data, check if it's empty, and if not, sort it by date in ascending order, reset the index, and return it.
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    # I sort the DataFrame by date in ascending order, reset the index, and return it. I also add a "match" column that labels each match as M1, M2, etc. for easier reference in the UI.
    df = df.sort_values("date").reset_index(drop=True)
    df["match"] = [f"M{i+1}" for i in range(len(df))]
    return df


# ---------------------------------------------------------
# TEAMS IN A LEAGUE
# ---------------------------------------------------------


# I define a function to get a list of teams for a specific league and season. This function calls the API endpoint for teams, extracts the team names and their corresponding IDs, and returns a list of dictionaries with "label" and "value" keys for use in dropdowns or other UI components.
def get_league_teams(league_id: int, season_year: int) -> list[dict]:
    """Return a list of teams for the given league/season.

    Used to populate team dropdowns.
    """

    data = api_get(
        "/teams",
        {"league": league_id, "season": season_year},
    )
    # I parse the API response to extract team names and their IDs, handling cases where data might be missing. I build a list of dictionaries with "label" for the team name and "value" for the team ID, which can be used to populate dropdown menus in the UI.
    teams = []
    for item in data.get("response", []):
        team = item.get("team") or {}
        team_id = team.get("id")
        team_name = team.get("name")
        if team_id and team_name:
            teams.append({"label": team_name, "value": team_id})

    # Sort alphabetically for predictable dropdown order
    teams = sorted(teams, key=lambda x: x["label"])
    return teams


# ---------------------------------------------------------
# TEAM PLAYERS
# ---------------------------------------------------------


def get_team_players(league_id: int, season_year: int, team_id: int) -> list[str]:
    """Return a list of player names for a given league/team/season."""
    all_players = []
    try:
        first = api_get(
            "/players",
            {"league": league_id, "season": season_year, "team": team_id, "page": 1},
        )
    except Exception:
        return []
    # I determine the total number of pages of results for the players endpoint, and set a cap on the number of pages to retrieve to avoid excessive API calls. I then define a helper function to parse the API response and extract player names, which is used for each page of results to build a complete list of players.
    total_pages = int((first.get("paging") or {}).get("total") or 1)
    capped_pages = min(total_pages, int(PLAYERS_MAX_PAGES))

    # I define a helper function to parse the API response and extract player names. This function iterates through the response data, checks for the presence of player information, and appends valid player names to the list.
    def parse_response(resp):
        players = []
        for item in resp.get("response", []):
            player = (item.get("player") or {}).get("name")
            if player:
                players.append(player)
        return players

    all_players.extend(parse_response(first))
    # I loop through any additional pages of results up to the capped limit, making API calls for each page and parsing the responses to extend the list of all player names.
    for page in range(2, capped_pages + 1):
        resp = api_get(
            "/players",
            {"league": league_id, "season": season_year, "team": team_id, "page": page},
        )
        all_players.extend(parse_response(resp))

    all_players = sorted(set(all_players))
    return all_players


# ---------------------------------------------------------
# Player Stats (NEW FUNCTION)
# ---------------------------------------------------------


def get_player_stats(
    league_id: int, season_year: int, team_id: int, player_name: str
) -> dict:
    """Return key stats for a single player on a team in a league/season."""
    page = 1
    collected = {}

    while True:
        resp = api_get(
            "/players",
            {
                "league": league_id,
                "season": season_year,
                "team": team_id,
                "page": page,
            },
        )
        # I loop through the paginated results to find the specific player by name, and if found, I extract their key statistics such as goals, assists, shots, passes, tackles, and saves. If the player is not found after checking all pages, I return an empty dictionary.
        for item in resp.get("response", []):
            player = (item.get("player") or {}).get("name")
            if player != player_name:
                continue
            # If the player is found, I extract their statistics, handling cases where data might be missing, and return a dictionary with the collected stats.
            stats = (item.get("statistics") or [{}])[0] or {}
            goals = (stats.get("goals") or {}).get("total", 0)
            assists = (stats.get("goals") or {}).get("assists", 0)
            shots = (stats.get("shots") or {}).get("total", 0)
            passes = (stats.get("passes") or {}).get("total", 0)
            key_passes = (stats.get("passes") or {}).get("key", 0)
            pass_accuracy = (stats.get("passes") or {}).get("accuracy", 0)
            tackles = (stats.get("tackles") or {}).get("total", 0)
            saves = (stats.get("goals") or {}).get("saves", 0)
            # I convert all stats to integers (defaulting to 0 if missing) and return them in a dictionary. This allows the UI to display the player's key statistics in a consistent format.
            collected = {
                "goals": int(goals or 0),
                "assists": int(assists or 0),
                "shots": int(shots or 0),
                "passes": int(passes or 0),
                "key_passes": int(key_passes or 0),
                "pass_accuracy": int(pass_accuracy or 0),
                "tackles": int(tackles or 0),
                "saves": int(saves or 0),
            }
            return collected
        # If the player is not found on the current page, I check if there are more pages to retrieve. If there are no more pages, I break the loop and return an empty dictionary.
        paging = resp.get("paging", {})
        total_pages = int(paging.get("total", 1))
        if page >= total_pages:
            break
        page += 1

    return collected


# ---------------------------------------------------------
# TEAM UPCOMING FIXTURES
# ---------------------------------------------------------


# I define a function to get the upcoming fixtures for a specific team in a league and season. This function retrieves the next scheduled fixtures, extracts relevant information such as date, time, home team, and away team, and returns a DataFrame sorted by date and time.
def get_team_upcoming_fixtures(
    league_id: int, season_year: int, team_id: int, next_n: int = 5
) -> pd.DataFrame:
    # "next" already returns the next scheduled fixtures, so no need to filter status
    data = api_get(
        "/fixtures",
        {"league": league_id, "season": season_year, "team": team_id, "next": next_n},
    )
    # I parse the API response to extract fixture details, handling cases where data might be missing. I build a list of dictionaries with the date, time, home team, and away team for each upcoming fixture, create a DataFrame from this list, sort it by date and time, and return it.
    rows = []
    for item in data.get("response", []):
        fx = item.get("fixture", {}) or {}
        teams = item.get("teams", {}) or {}

        home = teams.get("home") or {}
        away = teams.get("away") or {}

        dt = fx.get("date") or ""
        date_str = dt[:10]
        time_str = dt[11:16]
        # I append a row to the list with the date, time, home team name, and away team name for each upcoming fixture. I handle cases where team information might be missing by providing default values.
        rows.append(
            {
                "Date": date_str,
                "Time": time_str,
                "Home": home.get("name", "Unknown"),
                "Away": away.get("name", "Unknown"),
            }
        )
    # After processing all fixtures, I create a DataFrame from the collected data, check if it's empty, and if not, sort it by date and time in ascending order, reset the index, and return it.
    df = pd.DataFrame(rows)
    if not df.empty:
        df = df.sort_values(["Date", "Time"]).reset_index(drop=True)
    return df


# ---------------------------------------------------------
# LEAGUE LEADER (FIXED PARSING)
# ---------------------------------------------------------


# I define a function to get the current league leader for a specific league and season. This function retrieves the league standings, extracts the team name and points of the top-ranked team, and returns a formatted string with this information. If any data is missing or the response is empty, it returns a placeholder string.
def get_league_leader(league_id: int, season_year: int) -> str:
    data = api_get("/standings", {"league": league_id, "season": season_year})
    # I parse the API response to extract the league standings, handling cases where data might be missing. I check if the response contains valid standings data, and if so, I extract the team name and points of the top-ranked team. I return a formatted string with the team name and points, or just the team name if points are not available. If any required data is missing, I return a placeholder string "—".
    resp = data.get("response", [])
    if not resp:
        return "—"

    league = (resp[0] or {}).get("league") or {}
    standings_lists = league.get("standings") or []
    if not standings_lists or not standings_lists[0]:
        return "—"
    # I extract the first row of the standings, which should correspond to the league leader, and then extract the team name and points from that row. I handle cases where this data might be missing to ensure the function returns a meaningful string even if the API response is incomplete.
    first_row = standings_lists[0][0]
    team = first_row.get("team") or {}
    team_name = team.get("name") or "—"
    points = first_row.get("points")

    return f"{team_name} ({points} pts)" if points is not None else team_name


def get_league_table(league_id: int, season_year: int) -> pd.DataFrame:
    """Return a league standings table for the given league/season.

    The returned DataFrame includes a hidden `team_id` column so that
    Dash can highlight the selected team row without exposing the ID in the UI.
    """
    # I define a function to get the league standings table for a specific league and season. This function retrieves the standings data from the API, extracts relevant information for each team such as rank, team name, matches played, wins, draws, losses, goals for, goals against, goal difference, and points. It returns a DataFrame sorted by rank with this information.
    data = api_get("/standings", {"league": league_id, "season": season_year})
    resp = data.get("response", [])
    if not resp:
        return pd.DataFrame()

    league = (resp[0] or {}).get("league") or {}
    standings_lists = league.get("standings") or []
    if not standings_lists or not standings_lists[0]:
        return pd.DataFrame()
    # I loop through the standings data for the league, extracting the relevant information for each team and appending it to a list of rows. I handle cases where certain data might be missing to ensure the function can still return a meaningful DataFrame even if the API response is incomplete.
    rows = []
    for row in standings_lists[0]:
        team = row.get("team") or {}
        all_stats = row.get("all") or {}
        goals = all_stats.get("goals") or {}
        # I append a dictionary to the list of rows with the extracted information for each team, including rank, team name, team ID, matches played, wins, draws, losses, goals for, goals against, goal difference, and points. This structured data will be used to create the league standings table in the UI.
        rows.append(
            {
                "rank": row.get("rank"),
                "team": team.get("name"),
                "team_id": team.get("id"),
                "played": all_stats.get("played"),
                "win": all_stats.get("win"),
                "draw": all_stats.get("draw"),
                "lose": all_stats.get("lose"),
                "goals_for": goals.get("for"),
                "goals_against": goals.get("against"),
                "goal_diff": row.get("goalsDiff"),
                "points": row.get("points"),
            }
        )
    # After processing all teams, I create a DataFrame from the collected data, check if it's empty, and if not, sort it by rank in ascending order, reset the index, and return it. The DataFrame includes a hidden `team_id` column for use in the UI without exposing it directly to users.
    df = pd.DataFrame(rows)
    if df.empty:
        return df

    return df.sort_values("rank").reset_index(drop=True)


# ---------------------------------------------------------
# TEAM SNAPSHOT (FIXED GOALS TOTALS)
# ---------------------------------------------------------


# I define a function to get a snapshot of key statistics for a specific team in a league and season. This function retrieves the team's statistics from the API, extracts the total matches played and total goals scored, and returns this information in a dictionary. I handle cases where the goals data might be structured differently (e.g., as a dict with home/away/total) to ensure accurate extraction of the total goals scored.
def get_team_snapshot(league_id: int, season_year: int, team_id: int) -> dict:
    data = api_get(
        "/teams/statistics",
        {"league": league_id, "season": season_year, "team": team_id},
    )

    response = data.get("response", {}) or {}
    if not response:
        return {}
    # I extract the fixtures and goals data from the API response, handling cases where these might be missing. I then extract the total matches played from the fixtures data, and handle the goals data to ensure I get the total goals scored, accounting for cases where it might be structured as a dict with home/away/total.
    fixtures = response.get("fixtures", {}) or {}
    goals = response.get("goals", {}) or {}

    # Matches played is usually an int here
    matches_played = (fixtures.get("played") or {}).get("total", 0)

    # goals["for"]["total"] is often a dict: {"home": X, "away": Y, "total": Z}
    goals_for_total = (goals.get("for") or {}).get("total", 0)
    # I check if the goals_for_total is a dict, and if so, I extract the "total" value. If it's not a dict, I assume it's already the total number of goals scored. This ensures that I correctly handle different data structures returned by the API for goals.
    if isinstance(goals_for_total, dict):
        goals_scored = goals_for_total.get("total", 0)
    else:
        goals_scored = goals_for_total

    return {
        "matches_played": matches_played,
        "goals_scored": goals_scored,
    }


# ---------------------------------------------------------
#  LEAGUE PLAYER AVERAGES (NEW FUNCTION) testing data
# ---------------------------------------------------------


# I define a function to calculate the average statistics for players in a specific league and season. This function retrieves player data from the API, handles pagination to ensure it processes multiple pages of results, sums up key statistics such as goals, assists, shots, passes, tackles, and saves for all players, counts the number of players processed, and returns a dictionary with the average values for each statistic.
def get_league_player_averages(league_id, season_year):
    try:
        data = api_get(
            "/players",
            {"league": league_id, "season": season_year, "page": 1},
        )
        # I determine the total number of pages of results for the players endpoint, and set a cap on the number of pages to retrieve to avoid excessive API calls. I then define a helper function to process the API response and extract player statistics, which is used for each page of results to build up the totals for all players.
        total_pages = int((data.get("paging") or {}).get("total") or 1)

        totals = {
            "goals": 0,
            "assists": 0,
            "shots": 0,
            "passes": 0,
            "tackles": 0,
            "saves": 0,
        }

        player_count = 0

        # I define a helper function to process the API response for a page of player data. This function iterates through the players in the response, extracts their statistics, and updates the totals for each statistic while counting the number of players processed.
        def process(resp):
            nonlocal player_count
            # I loop through the players in the API response, extract their statistics, and update the totals for each statistic. I also increment the player count for each player processed to later calculate the averages.
            for item in resp.get("response", []):
                stats = (item.get("statistics") or [{}])[0] or {}

                goals = (stats.get("goals") or {}).get("total", 0)
                assists = (stats.get("goals") or {}).get("assists", 0)
                shots = (stats.get("shots") or {}).get("total", 0)
                passes = (stats.get("passes") or {}).get("total", 0)
                tackles = (stats.get("tackles") or {}).get("total", 0)
                saves = (stats.get("goals") or {}).get("saves", 0)

                totals["goals"] += goals or 0
                totals["assists"] += assists or 0
                totals["shots"] += shots or 0
                totals["passes"] += passes or 0
                totals["tackles"] += tackles or 0
                totals["saves"] += saves or 0

                player_count += 1

        # first page
        process(data)

        # remaining pages (limit to avoid API overload)
        for page in range(2, min(total_pages, 5) + 1):
            resp = api_get(
                "/players",
                {"league": league_id, "season": season_year, "page": page},
            )
            process(resp)
        # After processing all pages of player data, I check if any players were counted to avoid division by zero. If there are players, I calculate the average for each statistic by dividing the totals by the player count and return the averages in a dictionary.
        if player_count == 0:
            return {}

        return {k: v / player_count for k, v in totals.items()}

    except Exception as e:
        print("League average error:", e)
        return {}


# ---------------------------------------------------------
#  Get player stats for scatter plot (NEW FUNCTION)
# ---------------------------------------------------------
# I define a function to get player statistics for all players in a specific league and season, which can be used for creating scatter plots or other visualizations. This function retrieves player data from the API, handles pagination to ensure it processes multiple pages of results, extracts key statistics such as passes, key passes, and assists for each player, and returns this information in a DataFrame.
def get_league_player_stats(league_id: int, season_year: int) -> pd.DataFrame:
    rows = []

    try:
        data = api_get(
            "/players",
            {"league": league_id, "season": season_year, "page": 1},
        )
    except Exception:
        return pd.DataFrame()
    # I determine the total number of pages of results for the players endpoint, and set a cap on the number of pages to retrieve to avoid excessive API calls. I then define a helper function to parse the API response and extract player statistics, which is used for each page of results to build up a list of player stats for all players.
    total_pages = int((data.get("paging") or {}).get("total") or 1)
    capped_pages = min(total_pages, 5)  # keep it fast

    def parse(resp):
        temp = []
        for item in resp.get("response", []):
            player = item.get("player", {}) or {}
            stats = (item.get("statistics") or [{}])[0] or {}

            passes = (stats.get("passes") or {}).get("total", 0)
            key_passes = (stats.get("passes") or {}).get("key", 0)
            assists = (stats.get("goals") or {}).get("assists", 0)

            temp.append(
                {
                    "player": player.get("name", "Unknown"),
                    "passes": int(passes or 0),
                    "key_passes": int(key_passes or 0),
                    "assists": int(assists or 0),
                }
            )
        return temp

    rows.extend(parse(data))
    # I loop through any additional pages of results up to the capped limit, making API calls for each page and parsing the responses to extend the list of player statistics.
    for page in range(2, capped_pages + 1):
        resp = api_get(
            "/players",
            {"league": league_id, "season": season_year, "page": page},
        )
        rows.extend(parse(resp))

    df = pd.DataFrame(rows)

    if df.empty:
        return df

    return df


# ---------------------------------------------------------
#  Get fixture details for a specific matchup (NEW FUNCTION)
# ---------------------------------------------------------


# I define a function to get the fixture details for a specific matchup between two teams in a league and season. This function retrieves the upcoming fixtures for the home team, checks if any of them match the specified away team, and if so, returns the fixture details. If no matching fixture is found, it returns an empty dictionary.
def get_fixture_by_teams(
    league_id: int, season_year: int, home_team_id: int, away_team_id: int
) -> dict:
    data = api_get(
        "/fixtures",
        {
            "league": league_id,
            "season": season_year,
            "team": home_team_id,
            "next": 20,
        },
    )
    # I loop through the upcoming fixtures for the home team, checking if any of them involve the specified away team. If a matching fixture is found, I return the details of that fixture. If no match is found after checking all upcoming fixtures, I return an empty dictionary.
    for item in data.get("response", []):
        teams = item.get("teams", {}) or {}
        home = teams.get("home", {}) or {}
        away = teams.get("away", {}) or {}

        if home.get("id") == home_team_id and away.get("id") == away_team_id:
            return item

    return {}


# I define a function to get the match prediction for a specific fixture. This function calls the API endpoint for predictions, extracts the response, and returns the prediction details for the fixture. If no prediction is available, it returns an empty dictionary.
def get_match_prediction(fixture_id: int) -> dict:
    data = api_get("/predictions", {"fixture": fixture_id})

    response = data.get("response", [])
    if not response:
        return {}

    return response[0]


# ---------------------------------------------------------
# LEAGUE UPCOMING FIXTURES
# ---------------------------------------------------------


# I define a function to get the upcoming fixtures for an entire league in a given season. This function retrieves the next scheduled fixtures for the league, extracts relevant information such as date, time, home team, and away team for each fixture, and returns a list of dictionaries with this information.
def get_league_upcoming_fixtures(
    league_id: int, season_year: int, next_n: int = 10
) -> list[dict]:
    data = api_get(
        "/fixtures",
        {"league": league_id, "season": season_year, "next": next_n},
    )
    # I parse the API response to extract fixture details, handling cases where data might be missing. I build a list of dictionaries with the fixture ID, date, time, home team name, and away team name for each upcoming fixture in the league.
    rows = []
    for item in data.get("response", []):
        fixture = item.get("fixture", {}) or {}
        teams = item.get("teams", {}) or {}

        home = teams.get("home", {}) or {}
        away = teams.get("away", {}) or {}
        # I append a dictionary to the list of rows with the fixture ID, date, time, home team name, and away team name for each upcoming fixture. I handle cases where certain data might be missing by providing default values.
        rows.append(
            {
                "fixture_id": fixture.get("id"),
                "date": (fixture.get("date") or "")[:10],
                "time": (fixture.get("date") or "")[11:16],
                "home_team": home.get("name", "Unknown"),
                "away_team": away.get("name", "Unknown"),
            }
        )

    return rows
