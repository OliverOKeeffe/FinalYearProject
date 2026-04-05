import dash
import pandas as pd
import plotly.graph_objects as go
from dash import dcc, html, Input, Output, State, dash_table
from services.api_football import get_league_teams, get_team_players, get_player_stats
from services.constants import LEAGUES, SEASONS, TEAMS_PL

dash.register_page(__name__, path="/comparison")


def kpi_card(title, value_id):
    return html.Div(
        className="kpi-card",
        children=[
            html.Div(title, className="kpi-title"),
            html.Div("—", id=value_id, className="kpi-value"),
        ],
    )


layout = html.Div(
    className="shell",
    children=[
        html.Div(
            className="sidebar",
            children=[
                html.Div("Comparison Page", className="sidebar-title"),
                dcc.Link("Home", href="/", className="side-link"),
                dcc.Link("League", href="/league", className="side-link"),
                dcc.Link("Team", href="/team", className="side-link"),
                dcc.Link("Players", href="/player", className="side-link"),
                dcc.Link("Comparison", href="/comparison", className="side-link active"),
                dcc.Link("Predictions", href="/predictions", className="side-link"),
            ],
        ),
        html.Div(
            className="main",
            children=[
                html.Div("Player Comparison Dashboard", className="header"),
                html.Div(
                    className="filters-row",
                    children=[
                        html.Div(
                            className="filter-box",
                            children=[
                                html.Div("League A", className="filter-label"),
                                dcc.Dropdown(
                                    id="compA_league_dd",
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
                                html.Div("Season A", className="filter-label"),
                                dcc.Dropdown(
                                    id="compA_season_dd",
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
                                html.Div("Team A", className="filter-label"),
                                dcc.Dropdown(
                                    id="compA_team_dd",
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
                                html.Div("Player A", className="filter-label"),
                                dcc.Dropdown(
                                    id="compA_player_dd",
                                    options=[],
                                    value=None,
                                    placeholder="Select player A",
                                    clearable=False,
                                    searchable=False,
                                ),
                            ],
                        ),
                    ],
                ),
                html.Div(
                    className="filters-row",
                    children=[
                        html.Div(
                            className="filter-box",
                            children=[
                                html.Div("League B", className="filter-label"),
                                dcc.Dropdown(
                                    id="compB_league_dd",
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
                                html.Div("Season B", className="filter-label"),
                                dcc.Dropdown(
                                    id="compB_season_dd",
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
                                html.Div("Team B", className="filter-label"),
                                dcc.Dropdown(
                                    id="compB_team_dd",
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
                                html.Div("Player B", className="filter-label"),
                                dcc.Dropdown(
                                    id="compB_player_dd",
                                    options=[],
                                    value=None,
                                    placeholder="Select player B",
                                    clearable=False,
                                    searchable=False,
                                ),
                            ],
                        ),
                        html.Div(
                            className="apply-container",
                            children=[
                                html.Button(
                                    "Compare",
                                    id="comparison_apply",
                                    n_clicks=0,
                                    className="apply-btn",
                                ),
                            ],
                        ),
                    ],
                ),
                html.Div(
                    className="kpi-row",
                    children=[
                        kpi_card("Goals Leader", "comp_kpi_goals"),
                        kpi_card("Assists Leader", "comp_kpi_assists"),
                        kpi_card("Tackles Leader", "comp_kpi_tackles"),
                        kpi_card("Passes Leader", "comp_kpi_passes"),
                    ],
                ),
                html.Div(
                    className="full-width-row",
                    children=[
                        html.Div(
                            className="panel",
                            children=[
                                html.Div(
                                    "Player Comparison Radar", className="panel-title"
                                ),
                                dcc.Graph(
                                    id="comparison_radar_chart",
                                    figure=go.Figure(),
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
                                    "Comparison Stats Table", className="panel-title"
                                ),
                                html.Div(id="comparison_stats_table"),
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
                                    "Comparison Insights", className="panel-title"
                                ),
                                html.Div(id="comparison_insights"),
                            ],
                        ),
                    ],
                ),
            ],
        ),
    ],
)


@dash.callback(
    Output("compA_team_dd", "options"),
    Output("compA_team_dd", "value"),
    Input("compA_league_dd", "value"),
    Input("compA_season_dd", "value"),
    State("compA_team_dd", "value"),
)
def update_compA_team_options(league_id, season_year, current_team_id):
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
    Output("compB_team_dd", "options"),
    Output("compB_team_dd", "value"),
    Input("compB_league_dd", "value"),
    Input("compB_season_dd", "value"),
    State("compB_team_dd", "value"),
)
def update_compB_team_options(league_id, season_year, current_team_id):
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
    Output("compA_player_dd", "options"),
    Output("compA_player_dd", "value"),
    Input("compA_league_dd", "value"),
    Input("compA_season_dd", "value"),
    Input("compA_team_dd", "value"),
)
def update_compA_player_options(league_id, season_year, team_id):
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
    Output("compB_player_dd", "options"),
    Output("compB_player_dd", "value"),
    Input("compB_league_dd", "value"),
    Input("compB_season_dd", "value"),
    Input("compB_team_dd", "value"),
)
def update_compB_player_options(league_id, season_year, team_id):
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
    Output("comp_kpi_goals", "children"),
    Output("comp_kpi_assists", "children"),
    Output("comp_kpi_tackles", "children"),
    Output("comp_kpi_passes", "children"),
    Output("comparison_radar_chart", "figure"),
    Output("comparison_stats_table", "children"),
    Output("comparison_insights", "children"),
    Input("comparison_apply", "n_clicks"),
    State("compA_league_dd", "value"),
    State("compA_season_dd", "value"),
    State("compA_team_dd", "value"),
    State("compA_player_dd", "value"),
    State("compB_league_dd", "value"),
    State("compB_season_dd", "value"),
    State("compB_team_dd", "value"),
    State("compB_player_dd", "value"),
)
def update_comparison_radar(
    n_clicks,
    leagueA,
    seasonA,
    teamA,
    playerA,
    leagueB,
    seasonB,
    teamB,
    playerB,
):
    if not playerA or not playerB:
        fig = go.Figure()
        fig.update_layout(title="Select two players and click Compare")
        return "—", "—", "—", "—", fig, html.Div(), html.Div()

    try:
        leagueA = int(leagueA)
        seasonA = int(seasonA)
        teamA = int(teamA)

        leagueB = int(leagueB)
        seasonB = int(seasonB)
        teamB = int(teamB)

    except Exception:
        fig = go.Figure()
        fig.update_layout(title="Invalid selection")
        return "—", "—", "—", "—", fig, html.Div(), html.Div()

    statsA = get_player_stats(leagueA, seasonA, teamA, playerA)
    statsB = get_player_stats(leagueB, seasonB, teamB, playerB)

    if not statsA or not statsB:
        fig = go.Figure()
        fig.update_layout(title="Could not load comparison data")
        return "—", "—", "—", "—",fig, html.Div(), html.Div()

    goalsA = statsA.get("goals", 0)
    assistsA = statsA.get("assists", 0)
    shotsA = statsA.get("shots", 0)
    passesA = statsA.get("passes", 0)
    tacklesA = statsA.get("tackles", 0)
    savesA = statsA.get("saves", 0)

    goalsB = statsB.get("goals", 0)
    assistsB = statsB.get("assists", 0)
    shotsB = statsB.get("shots", 0)
    passesB = statsB.get("passes", 0)
    tacklesB = statsB.get("tackles", 0)
    savesB = statsB.get("saves", 0)

    if goalsA > goalsB:
        goals_kpi = playerA
    elif goalsB > goalsA:
        goals_kpi = playerB
    else:
        goals_kpi = "Draw"

    if assistsA > assistsB:
        assists_kpi = playerA
    elif assistsB > assistsA:
        assists_kpi = playerB
    else:
        assists_kpi = "Draw"

    if tacklesA > tacklesB:
        tackles_kpi = playerA
    elif tacklesB > tacklesA:
        tackles_kpi = playerB
    else:
        tackles_kpi = "Draw"

    if passesA > passesB:
        passes_kpi = playerA
    elif passesB > passesA:
        passes_kpi = playerB
    else:
        passes_kpi = "Draw"

    categories = [
        "Goals",
        "Assists",
        "Shots",
        "Passes",
        "Tackles",
    ]

    valuesA = [
        goalsA * 5,
        assistsA * 5,
        shotsA,
        passesA / 10,
        tacklesA * 2,
    ]

    valuesB = [
        goalsB * 5,
        assistsB * 5,
        shotsB,
        passesB / 10,
        tacklesB * 2,
    ]

    if savesA > 0 or savesB > 0:
        categories.append("Saves")
        valuesA.append(savesA * 2)
        valuesB.append(savesB * 2)

    categories_closed = categories + [categories[0]]
    valuesA_closed = valuesA + [valuesA[0]]
    valuesB_closed = valuesB + [valuesB[0]]

    fig = go.Figure()

    fig.add_trace(
        go.Scatterpolar(
            r=valuesA_closed,
            theta=categories_closed,
            fill="toself",
            name=f"{playerA} ({seasonA} - {leagueA})",
        )
    )

    fig.add_trace(
        go.Scatterpolar(
            r=valuesB_closed,
            theta=categories_closed,
            fill="toself",
            name=f"{playerB} ({seasonB} - {leagueB})",
        )
    )

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                showticklabels=True,
            )
        ),
        showlegend=True,
    )

    table_data = pd.DataFrame(
        [
            {"Stat": "Goals", "Player A": goalsA, "Player B": goalsB},
            {"Stat": "Assists", "Player A": assistsA, "Player B": assistsB},
            {"Stat": "Shots", "Player A": shotsA, "Player B": shotsB},
            {"Stat": "Passes", "Player A": passesA, "Player B": passesB},
            {"Stat": "Tackles", "Player A": tacklesA, "Player B": tacklesB},
            {"Stat": "Saves", "Player A": savesA, "Player B": savesB},
        ]
    )

    stats_table = dash_table.DataTable(
        columns=[{"name": c, "id": c} for c in table_data.columns],
        data=table_data.to_dict("records"),
        style_table={"overflowX": "auto"},
        style_cell={"fontFamily": "Arial", "fontSize": 13, "padding": "10px"},
        style_header={"fontWeight": "bold"},
    )

    insights = []

    if goalsA > goalsB:
        insights.append(html.Div(f"{playerA} has scored more goals than {playerB}."))
    elif goalsB > goalsA:
        insights.append(html.Div(f"{playerB} has scored more goals than {playerA}."))
    else:
        insights.append(
            html.Div(f"{playerA} and {playerB} have scored the same number of goals.")
        )

    if assistsA > assistsB:
        insights.append(html.Div(f"{playerA} has more assists than {playerB}."))
    elif assistsB > assistsA:
        insights.append(html.Div(f"{playerB} has more assists than {playerA}."))
    else:
        insights.append(
            html.Div(f"{playerA} and {playerB} have the same number of assists.")
        )

    if shotsA > shotsB:
        insights.append(html.Div(f"{playerA} has taken more shots than {playerB}."))
    elif shotsB > shotsA:
        insights.append(html.Div(f"{playerB} has taken more shots than {playerA}."))
    else:
        insights.append(
            html.Div(f"{playerA} and {playerB} have taken the same number of shots.")
        )

    if passesA > passesB:
        insights.append(html.Div(f"{playerA} attempts more passes than {playerB}."))
    elif passesB > passesA:
        insights.append(html.Div(f"{playerB} attempts more passes than {playerA}."))
    else:
        insights.append(
            html.Div(f"{playerA} and {playerB} attempt the same number of passes.")
        )

    if tacklesA > tacklesB:
        insights.append(html.Div(f"{playerA} makes more tackles than {playerB}."))
    elif tacklesB > tacklesA:
        insights.append(html.Div(f"{playerB} makes more tackles than {playerA}."))
    else:
        insights.append(
            html.Div(f"{playerA} and {playerB} make the same number of tackles.")
        )

    return goals_kpi, assists_kpi, tackles_kpi, passes_kpi, fig, stats_table, insights