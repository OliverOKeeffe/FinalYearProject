import dash
from dash import dcc, html

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
                        ),
                    ],
                ),
                html.Button(
                    "Apply",
                    id="player_apply",
                    n_clicks=0,
                    className="apply-btn",
                ),
            ],
        ),
    ],
)