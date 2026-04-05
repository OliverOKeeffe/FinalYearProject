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


def api_headers():
    key = os.getenv("APIFOOTBALL_KEY")
    if not key:
        raise RuntimeError("Missing APIFOOTBALL_KEY environment variable.")
    return {"x-apisports-key": key, "Accept": "application/json"}


def _make_cache_key(path: str, params: dict) -> str:
    items = sorted((params or {}).items(), key=lambda x: x[0])
    return f"{path}|{items}"


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

    all_rows.extend(parse_response(first))

    for page in range(2, capped_pages + 1):
        resp = api_get(
            "/players",
            {"league": league_id, "season": season_year, "team": team_id, "page": page},
        )
        all_rows.extend(parse_response(resp))

    df = pd.DataFrame(all_rows)
    if df.empty:
        return df

    df = df.groupby("player", as_index=False)["goals"].sum()
    df = df[df["goals"] > 0]
    if df.empty:
        return df

    return df.sort_values("goals", ascending=False).head(10).reset_index(drop=True)


# ---------------------------------------------------------
# LEAGUE TOP SCORERS (CORRECT ENDPOINT)
# ---------------------------------------------------------


def get_league_top_scorers(league_id: int, season_year: int) -> pd.DataFrame:
    data = api_get("/players/topscorers", {"league": league_id, "season": season_year})

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

    df = pd.DataFrame(rows)
    if df.empty:
        return df

    return df.sort_values("goals", ascending=False).head(10).reset_index(drop=True)


# ---------------------------------------------------------
# TEAM TOP ASSISTS
# ---------------------------------------------------------


def get_team_top_assists(
    league_id: int, team_id: int, season_year: int
) -> pd.DataFrame:
    all_rows = []

    first = api_get(
        "/players",
        {"league": league_id, "season": season_year, "team": team_id, "page": 1},
    )

    total_pages = int((first.get("paging") or {}).get("total") or 1)
    capped_pages = min(total_pages, int(PLAYERS_MAX_PAGES))

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

    all_rows.extend(parse_response(first))

    for page in range(2, capped_pages + 1):
        resp = api_get(
            "/players",
            {"league": league_id, "season": season_year, "team": team_id, "page": page},
        )
        all_rows.extend(parse_response(resp))

    df = pd.DataFrame(all_rows)
    if df.empty:
        return df

    df = df.groupby("player", as_index=False)["assists"].sum()
    df = df[df["assists"] > 0]
    if df.empty:
        return df

    return df.sort_values("assists", ascending=False).head(10).reset_index(drop=True)


# ---------------------------------------------------------
# TEAM FORM (LAST N MATCHES)
# ---------------------------------------------------------


def get_team_form_points(
    league_id: int, season_year: int, team_id: int, last_n: int = 10
) -> pd.DataFrame:
    data = api_get(
        "/fixtures",
        {"league": league_id, "season": season_year, "team": team_id, "last": last_n},
    )

    rows = []
    for item in data.get("response", []):
        fx = item.get("fixture", {}) or {}
        status = (fx.get("status", {}) or {}).get("short", "")

        if status not in {"FT", "AET", "PEN"}:
            continue

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

        rows.append(
            {
                "date": (fx.get("date") or "")[:10],
                "points": pts,
                "result": res,
            }
        )

    df = pd.DataFrame(rows)
    if df.empty:
        return df

    df = df.sort_values("date").reset_index(drop=True)
    df["match"] = [f"M{i+1}" for i in range(len(df))]
    return df


# ---------------------------------------------------------
# TEAMS IN A LEAGUE
# ---------------------------------------------------------


def get_league_teams(league_id: int, season_year: int) -> list[dict]:
    """Return a list of teams for the given league/season.

    Used to populate team dropdowns.
    """

    data = api_get(
        "/teams",
        {"league": league_id, "season": season_year},
    )

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

    total_pages = int((first.get("paging") or {}).get("total") or 1)
    capped_pages = min(total_pages, int(PLAYERS_MAX_PAGES))

    def parse_response(resp):
        players = []
        for item in resp.get("response", []):
            player = (item.get("player") or {}).get("name")
            if player:
                players.append(player)
        return players

    all_players.extend(parse_response(first))

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

        for item in resp.get("response", []):
            player = (item.get("player") or {}).get("name")
            if player != player_name:
                continue

            stats = (item.get("statistics") or [{}])[0] or {}
            goals = (stats.get("goals") or {}).get("total", 0)
            assists = (stats.get("goals") or {}).get("assists", 0)
            shots = (stats.get("shots") or {}).get("total", 0)
            passes = (stats.get("passes") or {}).get("total", 0)
            key_passes = (stats.get("passes") or {}).get("key", 0)
            pass_accuracy = (stats.get("passes") or {}).get("accuracy", 0)
            tackles = (stats.get("tackles") or {}).get("total", 0)
            saves = (stats.get("goals") or {}).get("saves", 0)

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

        paging = resp.get("paging", {})
        total_pages = int(paging.get("total", 1))
        if page >= total_pages:
            break
        page += 1

    return collected


# ---------------------------------------------------------
# TEAM UPCOMING FIXTURES
# ---------------------------------------------------------


def get_team_upcoming_fixtures(
    league_id: int, season_year: int, team_id: int, next_n: int = 5
) -> pd.DataFrame:
    # "next" already returns the next scheduled fixtures, so no need to filter status
    data = api_get(
        "/fixtures",
        {"league": league_id, "season": season_year, "team": team_id, "next": next_n},
    )

    rows = []
    for item in data.get("response", []):
        fx = item.get("fixture", {}) or {}
        teams = item.get("teams", {}) or {}

        home = teams.get("home") or {}
        away = teams.get("away") or {}

        dt = fx.get("date") or ""
        date_str = dt[:10]
        time_str = dt[11:16]

        rows.append(
            {
                "Date": date_str,
                "Time": time_str,
                "Home": home.get("name", "Unknown"),
                "Away": away.get("name", "Unknown"),
            }
        )

    df = pd.DataFrame(rows)
    if not df.empty:
        df = df.sort_values(["Date", "Time"]).reset_index(drop=True)
    return df


# ---------------------------------------------------------
# LEAGUE LEADER (FIXED PARSING)
# ---------------------------------------------------------


def get_league_leader(league_id: int, season_year: int) -> str:
    data = api_get("/standings", {"league": league_id, "season": season_year})

    resp = data.get("response", [])
    if not resp:
        return "—"

    league = (resp[0] or {}).get("league") or {}
    standings_lists = league.get("standings") or []
    if not standings_lists or not standings_lists[0]:
        return "—"

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

    data = api_get("/standings", {"league": league_id, "season": season_year})
    resp = data.get("response", [])
    if not resp:
        return pd.DataFrame()

    league = (resp[0] or {}).get("league") or {}
    standings_lists = league.get("standings") or []
    if not standings_lists or not standings_lists[0]:
        return pd.DataFrame()

    rows = []
    for row in standings_lists[0]:
        team = row.get("team") or {}
        all_stats = row.get("all") or {}
        goals = all_stats.get("goals") or {}

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

    df = pd.DataFrame(rows)
    if df.empty:
        return df

    return df.sort_values("rank").reset_index(drop=True)


# ---------------------------------------------------------
# TEAM SNAPSHOT (FIXED GOALS TOTALS)
# ---------------------------------------------------------


def get_team_snapshot(league_id: int, season_year: int, team_id: int) -> dict:
    data = api_get(
        "/teams/statistics",
        {"league": league_id, "season": season_year, "team": team_id},
    )

    response = data.get("response", {}) or {}
    if not response:
        return {}

    fixtures = response.get("fixtures", {}) or {}
    goals = response.get("goals", {}) or {}

    # Matches played is usually an int here
    matches_played = (fixtures.get("played") or {}).get("total", 0)

    # goals["for"]["total"] is often a dict: {"home": X, "away": Y, "total": Z}
    goals_for_total = (goals.get("for") or {}).get("total", 0)

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


def get_league_player_averages(league_id, season_year):
    try:
        data = api_get(
            "/players",
            {"league": league_id, "season": season_year, "page": 1},
        )

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

        def process(resp):
            nonlocal player_count

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

        if player_count == 0:
            return {}

        return {k: v / player_count for k, v in totals.items()}

    except Exception as e:
        print("League average error:", e)
        return {}

# ---------------------------------------------------------
#  Get player stats for scatter plot (NEW FUNCTION)
# ---------------------------------------------------------
def get_league_player_stats(league_id: int, season_year: int) -> pd.DataFrame:
    rows = []

    try:
        data = api_get(
            "/players",
            {"league": league_id, "season": season_year, "page": 1},
        )
    except Exception:
        return pd.DataFrame()

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

            temp.append({
                "player": player.get("name", "Unknown"),
                "passes": int(passes or 0),
                "key_passes": int(key_passes or 0),
                "assists": int(assists or 0),
            })
        return temp

    rows.extend(parse(data))

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
def get_fixture_by_teams(league_id: int, season_year: int, home_team_id: int, away_team_id: int) -> dict:
    data = api_get(
        "/fixtures",
        {
            "league": league_id,
            "season": season_year,
            "team": home_team_id,
            "next": 20,
        },
    )

    for item in data.get("response", []):
        teams = item.get("teams", {}) or {}
        home = teams.get("home", {}) or {}
        away = teams.get("away", {}) or {}

        if home.get("id") == home_team_id and away.get("id") == away_team_id:
            return item

    return {}

def get_match_prediction(fixture_id: int) -> dict:
    data = api_get("/predictions", {"fixture": fixture_id})

    response = data.get("response", [])
    if not response:
        return {}

    return response[0]

# ---------------------------------------------------------
# LEAGUE UPCOMING FIXTURES
# ---------------------------------------------------------
def get_league_upcoming_fixtures(league_id: int, season_year: int, next_n: int = 10) -> list[dict]:
    data = api_get(
        "/fixtures",
        {"league": league_id, "season": season_year, "next": next_n},
    )

    rows = []
    for item in data.get("response", []):
        fixture = item.get("fixture", {}) or {}
        teams = item.get("teams", {}) or {}

        home = teams.get("home", {}) or {}
        away = teams.get("away", {}) or {}

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