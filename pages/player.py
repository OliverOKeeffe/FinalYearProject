import dash
from dash import dcc, html, Input, Output, State
from services.api import get_league_teams, get_team_players

from services.constants import LEAGUES, SEASONS, TEAMS_PL

dash.register_page(__name__, path="/player")


layout = html.Div(
    className="main",
    children=[
        html.Div("Player Analytics Dashboard", className="header"),

        html.Div(
            className="filters-row",
            children=[
                html.Div(
                    className="filter-box",
                    children=[
                        html.Div("League dropdown", className="filter-label"),
                        dcc.Dropdown(
                            id="player_league_dd",
                            options=LEAGUES,
                            value=39,
                            clearable=False,
                            searchable=False,
                        ),
                    ],
                ),
                html.Div(
                    className="filter-box",
                    children=[
                        html.Div("Season dropdown", className="filter-label"),
                        dcc.Dropdown(
                            id="player_season_dd",
                            options=SEASONS,
                            value=SEASONS[0]["value"] if SEASONS else 2024,
                            clearable=False,
                            searchable=False,
                        ),
                    ],
                ),
                html.Div(
                    className="filter-box",
                    children=[
                        html.Div("Team dropdown", className="filter-label"),
                        dcc.Dropdown(
                            id="player_team_dd",
                            options=TEAMS_PL,
                            value=TEAMS_PL[0]["value"] if TEAMS_PL else 40,
                            clearable=False,
                            searchable=False,
                        ),
                    ],
                ),
                html.Div(
                    className="filter-box",
                    children=[
                        html.Div("Player dropdown", className="filter-label"),
                        dcc.Dropdown(
                            id="player_player_dd",
                            options=[],
                            value=None,
                            placeholder="Select a player",
                            clearable=False,
                            searchable=False,
                        ),
                    ],
                ),
                html.Div(
                    className="apply-container",
                    children=[
                        html.Button(
                            "Apply",
                            id="player_apply",
                            n_clicks=0,
                            className="apply-btn",
                        ),
                    ],
                ),
            ],
        ),
    ],
)


@dash.callback(
    Output("player_team_dd", "options"),
    Output("player_team_dd", "value"),
    Input("player_league_dd", "value"),
    Input("player_season_dd", "value"),
    State("player_team_dd", "value"),
)
def update_player_team_options(league_id, season_year, current_team_id):
    try:
        league_id = int(league_id)
        season_year = int(season_year)
    except Exception:
        return TEAMS_PL, current_team_id

    teams = get_league_teams(league_id, season_year)
    if not teams:
        return TEAMS_PL, current_team_id

    try:
        current_team_id = int(current_team_id) if current_team_id is not None else None
    except Exception:
        current_team_id = None

    values = [t["value"] for t in teams]
    new_value = current_team_id if current_team_id in values else (teams[0]["value"] if teams else None)
    return teams, new_value


@dash.callback(
    Output("player_player_dd", "options"),
    Output("player_player_dd", "value"),
    Input("player_league_dd", "value"),
    Input("player_season_dd", "value"),
    Input("player_team_dd", "value"),
)
def update_player_player_options(league_id, season_year, team_id):
    try:
        league_id = int(league_id)
        season_year = int(season_year)
        team_id = int(team_id)
    except Exception:
        return [], None

    player_names = get_team_players(league_id, season_year, team_id)
    options = [{"label": p, "value": p} for p in player_names]
    value = options[0]["value"] if options else None
    return options, value