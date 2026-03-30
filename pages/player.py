import dash
import plotly.express as px
import pandas as pd
import plotly.graph_objects as go
from dash import dcc, html, Input, Output, State
from services.api_football import get_league_teams, get_team_players, get_player_stats

from services.constants import LEAGUES, SEASONS, TEAMS_PL

dash.register_page(__name__, path="/player")


layout = html.Div(
    className="shell",
    children=[
        html.Div(
            className="sidebar",
            children=[
                html.Div("Player Page", className="sidebar-title"),
                dcc.Link("Home", href="/", className="side-link"),
                dcc.Link("League", href="/league", className="side-link"),
                dcc.Link("Team", href="/team", className="side-link"),
                dcc.Link("Players", href="/player", className="side-link active"),
            ],
        ),
        html.Div(
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
                html.Div(
                    className="full-width-row",
                    children=[
                        html.Div(
                            className="panel",
                            children=[
                                html.Div("Player key stats", className="panel-title"),
                                dcc.Graph(
                                    id="player_stats_chart",
                                    figure=px.bar(title=""),
                                    style={"height": "520px"},
                                ),
                            ],
                        ),
                    ],
                ),
                html.Div(
                    className="full-width-row",
                    children=[
                        html.Div(
                            className="panel",
                            children=[
                                html.Div(
                                    "Player Radar Profile", className="panel-title"
                                ),
                                dcc.Graph(
                                    id="player_radar_chart",
                                    figure=go.Figure(),
                                    style={"height": "420px"},
                                ),
                            ],
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
    new_value = (
        current_team_id
        if current_team_id in values
        else (teams[0]["value"] if teams else None)
    )
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


@dash.callback(
    Output("player_stats_chart", "figure"),
    Output("player_radar_chart", "figure"),
    Input("player_apply", "n_clicks"),
    State("player_league_dd", "value"),
    State("player_season_dd", "value"),
    State("player_team_dd", "value"),
    State("player_player_dd", "value"),
)
def update_player_stats_chart(n_clicks, league_id, season_year, team_id, player_name):
    if not player_name:
        return px.bar(title="Select a player and click Apply"), go.Figure()

    try:
        league_id = int(league_id)
        season_year = int(season_year)
        team_id = int(team_id)
    except Exception:
        return px.bar(title="Invalid league/season/team selection"), go.Figure()

    stats = get_player_stats(league_id, season_year, team_id, player_name)
    if not stats:
        return px.bar(title=f"No stats found for {player_name}"), go.Figure()

    df = pd.DataFrame([{"stat": k.capitalize(), "value": v} for k, v in stats.items()])

    fig = px.bar(
        df,
        x="stat",
        y="value",
        title=f"{player_name} Key Stats ({season_year})",
        text="value",
    )
    fig.update_traces(marker_color="steelblue", textposition="outside")
    fig.update_layout(yaxis_title="Value", xaxis_title="")

    goals = stats.get("goals", 0)
    assists = stats.get("assists", 0)
    shots = stats.get("shots", 0)
    passes = stats.get("passes", 0)
    tackles = stats.get("tackles", 0)
    saves = stats.get("saves", 0)

    categories = [
        "Goals",
        "Assists",
        "Shots",
        "Passes",
        "Tackles",
    ]

    values = [
        goals * 5,
        assists * 5,
        shots,
        passes / 10,
        tackles * 2,
    ]

    if saves > 0:
        categories.append("Saves")
        values.append(saves * 2)

    categories_closed = categories + [categories[0]]
    values_closed = values + [values[0]]

    radar_fig = go.Figure()

    radar_fig.add_trace(
        go.Scatterpolar(
            r=values_closed,
            theta=categories_closed,
            fill="toself",
            name=player_name,
        )
    )

    radar_fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                showticklabels=True,
            )
        ),
        showlegend=False,
    )

    return fig, radar_fig