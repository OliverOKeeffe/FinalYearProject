# services/constants.py

# Cache API responses for this many seconds (10 minutes)
CACHE_TTL_SECONDS = 600

# Safety limit so /players pagination doesn't explode requests
PLAYERS_MAX_PAGES = 6

# Seasons (API uses start year)
SEASONS = [
    {"label": "2023/24", "value": 2023},
    {"label": "2024/25", "value": 2024},
    {"label": "2022/23", "value": 2022},
]

# Current season start year (update when you have access to newer seasons)
# With the Ultra plan we can access the 2025/26 season; set current accordingly.
CURRENT_SEASON = 2025

# Include the current season in the SEASONS list if not already present.
if not any(s["value"] == CURRENT_SEASON for s in SEASONS):
    SEASONS.insert(0, {"label": f"{CURRENT_SEASON}/{str(CURRENT_SEASON+1)[-2:]}", "value": CURRENT_SEASON})

# Leagues (starter list)
LEAGUES = [
    {"label": "Premier League", "value": 39},
    {"label": "La Liga", "value": 140},
    {"label": "Serie A", "value": 135},
    {"label": "Bundesliga", "value": 78},
    {"label": "Ligue 1", "value": 61},
]

# Simple starter team list for Premier League (can be replaced with /teams later)
TEAMS_PL = [
    {"label": "Arsenal", "value": 42},
    {"label": "Chelsea", "value": 49},
    {"label": "Liverpool", "value": 40},
    {"label": "Manchester City", "value": 50},
    {"label": "Manchester United", "value": 33},
    {"label": "Tottenham", "value": 47},
]
