# I imported the nessecary libraries and modules
import dash
import pandas as pd
import plotly.graph_objects as go
from dash import dcc, html, Input, Output, State, dash_table
from services.api_football import get_league_teams, get_team_players, get_player_stats
from services.constants import LEAGUES, SEASONS, TEAMS_PL

dash.register_page(__name__, path="/comparison")


# I defined a helper function to create KPI cards for displaying the leaders in various statistics. This function takes a title and an ID for the value element, and returns a styled div containing the title and a placeholder for the value that will be updated dynamically.
def kpi_card(title, value_id):
    return html.Div(
        className="kpi-card",
        children=[
            html.Div(title, className="kpi-title"),
            html.Div("—", id=value_id, className="kpi-value"),
        ],
    )


# I defined the layout of the comparison page, which includes a sidebar for navigation and a main area for content. The main area contains filters for selecting two players to compare, KPI cards to show the leaders in various statistics, a radar chart to visualize the comparison, a table to show the raw stats, and a section for insights based on the comparison.
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
                dcc.Link(
                    "Comparison", href="/comparison", className="side-link active"
                ),
                dcc.Link("Predictions", href="/predictions", className="side-link"),
            ],
        ),
        # I created the main content area, which includes a header, two rows of filters for selecting the league, season, team, and player for both players being compared, KPI cards to show the leaders in goals, assists, tackles, and passes, a radar chart to visualize the comparison of stats between the two players, a table to show the raw statistics side by side, and a section to display insights based on the comparison.
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
                # I created a second row of filters for the second player being compared, allowing the user to select the league, season, team, and player for the second player. I also included a button to trigger the comparison after the selections are made.
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
                        # I included a button to trigger the comparison after the user has made their selections for both players. When clicked, this button will execute a callback function that retrieves the selected players' stats, updates the KPI cards, radar chart, stats table, and insights section based on the comparison of the two players.
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
                # I created a row of KPI cards to display the leaders in goals, assists, tackles, and passes based on the comparison of the two selected players. These cards will be updated dynamically based on the stats of the players being compared.
                html.Div(
                    className="kpi-row",
                    children=[
                        kpi_card("Goals Leader", "comp_kpi_goals"),
                        kpi_card("Assists Leader", "comp_kpi_assists"),
                        kpi_card("Tackles Leader", "comp_kpi_tackles"),
                        kpi_card("Passes Leader", "comp_kpi_passes"),
                    ],
                ),
                # I created a section to display a radar chart that visualizes the comparison of stats between the two selected players. This chart will be updated dynamically based on the stats retrieved for each player after the "Compare" button is clicked.
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
                # I created a section to display a table that shows the raw statistics for both players side by side. This table will be updated dynamically based on the stats retrieved for each player after the "Compare" button is clicked.
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
                # I created a section to display insights based on the comparison of the two players. This section will be updated dynamically with text insights that highlight key differences or similarities between the players based on their stats.
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


# I defined a callback function that updates the team options in the dropdowns for both players based on the selected league and season. This function retrieves the teams for the selected league and season, updates the options in the team dropdowns, and ensures that the currently selected team remains selected if it is still valid.
@dash.callback(
    Output("compA_team_dd", "options"),
    Output("compA_team_dd", "value"),
    Input("compA_league_dd", "value"),
    Input("compA_season_dd", "value"),
    State("compA_team_dd", "value"),
)
# This function takes the selected league ID and season year for player A, retrieves the teams for that league and season, and updates the team dropdown options and value accordingly. If the current team selection is still valid, it remains selected; otherwise, it defaults to the first team in the list.
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


# I defined a similar callback function for player B to update the team options based on the selected league and season for player B. This ensures that both players' team dropdowns are dynamically updated based on the user's selections for league and season.
@dash.callback(
    Output("compB_team_dd", "options"),
    Output("compB_team_dd", "value"),
    Input("compB_league_dd", "value"),
    Input("compB_season_dd", "value"),
    State("compB_team_dd", "value"),
)
# This function takes the selected league ID and season year for player B, retrieves the teams for that league and season, and updates the team dropdown options and value accordingly. If the current team selection is still valid, it remains selected; otherwise, it defaults to the first team in the list.
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


# I defined callback functions to update the player options in the dropdowns for both players based on the selected league, season, and team. These functions retrieve the players for the selected team and update the player dropdown options and values accordingly.
@dash.callback(
    Output("compA_player_dd", "options"),
    Output("compA_player_dd", "value"),
    Input("compA_league_dd", "value"),
    Input("compA_season_dd", "value"),
    Input("compA_team_dd", "value"),
)
# This function takes the selected league ID, season year, and team ID for player A, retrieves the players for that team, and updates the player dropdown options and value accordingly. If there are no players found, it returns an empty list of options and a None value.
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
# This function takes the selected league ID, season year, and team ID for player B, retrieves the players for that team, and updates the player dropdown options and value accordingly. If there are no players found, it returns an empty list of options and a None value.
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


# I defined a callback function that updates the comparison radar chart, stats table, KPI cards, and insights based on the selected players and their stats. This function retrieves the stats for both players, determines the leaders in various categories, creates a radar chart to visualize the comparison, builds a table to show the raw stats, and generates insights based on the comparison of the two players.
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
# This function takes the number of clicks on the "Compare" button, the selected league ID, season year, team ID, and player name for both players being compared. It retrieves the stats for both players, determines the leaders in goals, assists, tackles, and passes, creates a radar chart to visualize the comparison of stats between the two players, builds a table to show the raw stats side by side, and generates insights based on the comparison of the two players.
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
    #
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
        return "—", "—", "—", "—", fig, html.Div(), html.Div()
    # I create labels for both players that include their name and the season they are being compared for. I also extract the relevant stats for both players, providing default values of 0 if any stats are missing. I determine the leaders in goals, assists, tackles, and passes based on the stats of both players, and prepare the data for the radar chart and stats table.
    playerA_label = f"{playerA} ({seasonA}/{str(seasonA + 1)[-2:]})"
    playerB_label = f"{playerB} ({seasonB}/{str(seasonB + 1)[-2:]})"

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
    # I determine the leaders in each category by comparing the stats of both players. If one player has a higher stat in a category, that player is the leader; if both players have the same stat, it is considered a draw. I then prepare the data for the radar chart and stats table to visualize the comparison between the two players.
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
    # I prepare the values for the radar chart by applying a scaling factor to each stat to ensure that they are visually comparable on the chart. I also prepare the raw values for display in the stats table and for use in the hover tooltips on the radar chart.
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
    # I include saves as a category in the radar chart if either player has made saves, applying a scaling factor to ensure it fits well on the chart. I also prepare the raw values for saves for display in the stats table and hover tooltips.
    if savesA > 0 or savesB > 0:
        categories.append("Saves")
        valuesA.append(savesA * 2)
        valuesB.append(savesB * 2)

    categories_closed = categories + [categories[0]]
    valuesA_closed = valuesA + [valuesA[0]]
    valuesB_closed = valuesB + [valuesB[0]]

    raw_valuesA = [
        goalsA,
        assistsA,
        shotsA,
        passesA,
        tacklesA,
    ]

    raw_valuesB = [
        goalsB,
        assistsB,
        shotsB,
        passesB,
        tacklesB,
    ]
    # I include saves in the raw values if either player has made saves, ensuring that the raw values for both players are aligned with the categories used in the radar chart and stats table.
    if savesA > 0 or savesB > 0:
        raw_valuesA.append(savesA)
        raw_valuesB.append(savesB)

    raw_valuesA_closed = raw_valuesA + [raw_valuesA[0]]
    raw_valuesB_closed = raw_valuesB + [raw_valuesB[0]]
    # I create the radar chart using Plotly, adding traces for both players with the prepared values and categories. I also set up custom hover templates to display the raw values when hovering over the chart. Finally, I update the layout of the chart to ensure it is visually appealing and easy to interpret.
    fig = go.Figure()

    fig.add_trace(
        go.Scatterpolar(
            r=valuesA_closed,
            theta=categories_closed,
            fill="toself",
            name=playerA_label,
            customdata=raw_valuesA_closed,
            hovertemplate="%{theta}: %{customdata}<extra></extra>",
        )
    )

    fig.add_trace(
        go.Scatterpolar(
            r=valuesB_closed,
            theta=categories_closed,
            fill="toself",
            name=playerB_label,
            customdata=raw_valuesB_closed,
            hovertemplate="%{theta}: %{customdata}<extra></extra>",
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
    # I build a table to show the raw stats for both players side by side, and prepare insights based on the comparison of the two players' stats. The insights highlight key differences or similarities between the players based on their performance in various categories.
    table_data = pd.DataFrame(
        [
            {"Stat": "Goals", playerA_label: goalsA, playerB_label: goalsB},
            {"Stat": "Assists", playerA_label: assistsA, playerB_label: assistsB},
            {"Stat": "Shots", playerA_label: shotsA, playerB_label: shotsB},
            {"Stat": "Passes", playerA_label: passesA, playerB_label: passesB},
            {"Stat": "Tackles", playerA_label: tacklesA, playerB_label: tacklesB},
            {"Stat": "Saves", playerA_label: savesA, playerB_label: savesB},
        ]
    )
    # I create a Dash DataTable to display the raw stats in a tabular format, and prepare insights based on the comparison of the two players' stats. The insights highlight key differences or similarities between the players based on their performance in various categories.
    stats_table = dash_table.DataTable(
        columns=[{"name": c, "id": c} for c in table_data.columns],
        data=table_data.to_dict("records"),
        style_table={"overflowX": "auto"},
        style_cell={"fontFamily": "Arial", "fontSize": 13, "padding": "10px"},
        style_header={"fontWeight": "bold"},
    )

    insights = []
    # I generate insights based on the comparison of the two players' stats, highlighting key differences or similarities in their performance across various categories. These insights are displayed as text below the radar chart and stats table to provide context and analysis of the comparison.
    if goalsA > goalsB:
        insights.append(
            html.Div(f"{playerA_label} has scored more goals than {playerB_label}.")
        )
    elif goalsB > goalsA:
        insights.append(
            html.Div(f"{playerB_label} has scored more goals than {playerA_label}.")
        )
    else:
        insights.append(
            html.Div(
                f"{playerA_label} and {playerB_label} have scored the same number of goals."
            )
        )

    if assistsA > assistsB:
        insights.append(
            html.Div(f"{playerA_label} has more assists than {playerB_label}.")
        )
    elif assistsB > assistsA:
        insights.append(
            html.Div(f"{playerB_label} has more assists than {playerA_label}.")
        )
    else:
        insights.append(
            html.Div(
                f"{playerA_label} and {playerB_label} have the same number of assists."
            )
        )

    if shotsA > shotsB:
        insights.append(
            html.Div(f"{playerA_label} has taken more shots than {playerB_label }.")
        )
    elif shotsB > shotsA:
        insights.append(
            html.Div(f"{playerB_label} has taken more shots than {playerA_label}.")
        )
    else:
        insights.append(
            html.Div(
                f"{playerA_label} and {playerB_label} have taken the same number of shots."
            )
        )

    if passesA > passesB:
        insights.append(
            html.Div(f"{playerA_label} attempts more passes than {playerB_label}.")
        )
    elif passesB > passesA:
        insights.append(
            html.Div(f"{playerB_label} attempts more passes than {playerA_label}.")
        )
    else:
        insights.append(
            html.Div(
                f"{playerA_label} and {playerB_label} attempt the same number of passes."
            )
        )

    if tacklesA > tacklesB:
        insights.append(
            html.Div(f"{playerA_label} makes more tackles than {playerB_label}.")
        )
    elif tacklesB > tacklesA:
        insights.append(
            html.Div(f"{playerB_label} makes more tackles than {playerA_label}.")
        )
    else:
        insights.append(
            html.Div(
                f"{playerA_label} and {playerB_label} make the same number of tackles."
            )
        )

    return goals_kpi, assists_kpi, tackles_kpi, passes_kpi, fig, stats_table, insights
