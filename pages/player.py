import dash
import plotly.express as px
import pandas as pd
import plotly.graph_objects as go
from dash import dcc, html, Input, Output, State
from services.api_football import get_league_player_stats
from services.api_football import (
    get_league_teams,
    get_team_players,
    get_player_stats,
    get_league_player_averages,
)

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
                dcc.Link("Comparison", href="/comparison", className="side-link"),
                dcc.Link("Predictions", href="/predictions", className="side-link"),
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
                html.Div(
                    className="full-width-row",
                    children=[
                        html.Div(
                            className="panel",
                            children=[
                                html.Div("Passing Analysis", className="panel-title"),
                                dcc.Graph(
                                    id="player_passing_chart",
                                    figure=px.bar(title=""),
                                    style={"height": "550px"},
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
                                html.Div("Creativity Map", className="panel-title"),
                                dcc.Graph(
                                    id="player_scatter_chart",
                                    figure=px.scatter(title=""),
                                    style={"height": "420px"},
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
                                    "Attacking Contribution", className="panel-title"
                                ),
                                dcc.Graph(
                                    id="player_donut_chart",
                                    figure=px.pie(title=""),
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
    Output("player_passing_chart", "figure"),
    Output("player_scatter_chart", "figure"),
    Output("player_donut_chart", "figure"),
    Input("player_apply", "n_clicks"),
    State("player_league_dd", "value"),
    State("player_season_dd", "value"),
    State("player_team_dd", "value"),
    State("player_player_dd", "value"),
)
def update_player_stats_chart(n_clicks, league_id, season_year, team_id, player_name):
    if not player_name:
        return (
            px.bar(title="Select a player and click Apply"),
            go.Figure(),
            go.Figure(),
            go.Figure(),
            go.Figure(),
        )

    try:
        league_id = int(league_id)
        season_year = int(season_year)
        team_id = int(team_id)
    except Exception:
        return (
            px.bar(title="Invalid league/season/team selection"),
            go.Figure(),
            go.Figure(),
            go.Figure(),
            go.Figure(),
        )

    stats = get_player_stats(league_id, season_year, team_id, player_name)
    if not stats:
        return (
            px.bar(title=f"No stats found for {player_name}"),
            go.Figure(),
            go.Figure(),
            go.Figure(),
            go.Figure(),
        )

    league_avgs = get_league_player_averages(league_id, season_year)

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

    # player stats
    goals = stats.get("goals", 0)
    assists = stats.get("assists", 0)
    shots = stats.get("shots", 0)
    passes = stats.get("passes", 0)
    key_passes = stats.get("key_passes", 0)
    pass_accuracy = stats.get("pass_accuracy", 0)
    tackles = stats.get("tackles", 0)
    saves = stats.get("saves", 0)

    # league averages
    avg_goals = league_avgs.get("goals", 0)
    avg_assists = league_avgs.get("assists", 0)
    avg_shots = league_avgs.get("shots", 0)
    avg_passes = league_avgs.get("passes", 0)
    avg_tackles = league_avgs.get("tackles", 0)
    avg_saves = league_avgs.get("saves", 0)

    categories = [
        "Goals",
        "Assists",
        "Shots",
        "Passes",
        "Tackles",
    ]

    player_values = [
        goals * 5,
        assists * 5,
        shots,
        passes / 10,
        tackles * 2,
    ]

    league_values = [
        avg_goals * 5,
        avg_assists * 5,
        avg_shots,
        avg_passes / 10,
        avg_tackles * 2,
    ]

    if saves > 0 or avg_saves > 0:
        categories.append("Saves")
        player_values.append(saves * 2)
        league_values.append(avg_saves * 2)

    categories_closed = categories + [categories[0]]
    player_values_closed = player_values + [player_values[0]]
    league_values_closed = league_values + [league_values[0]]

    radar_fig = go.Figure()

    radar_fig.add_trace(
        go.Scatterpolar(
            r=player_values_closed,
            theta=categories_closed,
            fill="toself",
            name=player_name,
        )
    )

    radar_fig.add_trace(
        go.Scatterpolar(
            r=league_values_closed,
            theta=categories_closed,
            fill="toself",
            name="League Average",
        )
    )

    radar_fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                showticklabels=True,
            )
        ),
        showlegend=True,
    )

    # PASSING CHART
    passing_df = pd.DataFrame(
        {
            "stat": ["Passes", "Key Passes", "Pass Accuracy"],
            "value": [passes, key_passes, pass_accuracy],
        }
    )

        # PASSING CHART
    passing_df = pd.DataFrame(
        {
            "stat": ["Passes", "Key Passes", "Pass Accuracy"],
            "value": [passes, key_passes, pass_accuracy],
        }
    )

    passing_fig = go.Figure()

    passing_fig.add_trace(
        go.Scatter(
            x=passing_df["value"],
            y=passing_df["stat"],
            mode="markers+text",
            text=passing_df["value"],
            textposition="middle right",
            marker=dict(size=12, color="orange"),
            name="Value",
        )
    )

    for _, row in passing_df.iterrows():
        passing_fig.add_shape(
            type="line",
            x0=0,
            y0=row["stat"],
            x1=row["value"],
            y1=row["stat"],
            line=dict(color="lightgray", width=3),
        )

    passing_fig.update_layout(
        title=f"{player_name} Passing Stats",
        xaxis_title="Value",
        yaxis_title="",
        height=550,
    )

        # SCATTER PLOT
    league_df = get_league_player_stats(league_id, season_year)

    if league_df is None or league_df.empty:
        scatter_fig = px.scatter(title="No league data available")
    else:
        scatter_fig = px.scatter(
            league_df,
            x="passes",
            y="key_passes",
            size="assists",
            hover_name="player",
            title=f"{player_name} vs League (Creativity Map)",
        )

        selected = league_df[league_df["player"] == player_name]

        if selected.empty:
            scatter_fig.add_trace(
                go.Scatter(
                    x=[passes],
                    y=[key_passes],
                    mode="markers+text",
                    text=[player_name],
                    textposition="top center",
                    marker=dict(size=18, color="red"),
                    name=player_name,
                )
            )
        else:
            scatter_fig.add_trace(
                go.Scatter(
                    x=selected["passes"],
                    y=selected["key_passes"],
                    mode="markers+text",
                    text=[player_name],
                    textposition="top center",
                    marker=dict(size=18, color="red"),
                    name=player_name,
                )
            )

        scatter_fig.update_layout(
            xaxis_title="Total Passes",
            yaxis_title="Key Passes",
        )

    non_scoring_shots = max(shots - goals, 0)

    donut_fig = px.pie(
        names=["Goals", "Non-Scoring Shots"],
        values=[goals, non_scoring_shots],
        title=f"{player_name} Attacking Contribution",
        hole=0.4,
    )
    donut_fig.update_traces(marker_colors=["green", "lightgray"])

    return fig, radar_fig, passing_fig, scatter_fig, donut_fig
