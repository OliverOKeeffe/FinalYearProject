import dash
from dash import dcc, html, Input, Output, State, dash_table
import plotly.express as px
import plotly.graph_objects as go

from services.constants import LEAGUES, SEASONS, TEAMS_PL
from services.api_football import (
    get_team_top_scorers,
    get_team_top_assists,
    get_team_form_points,
    get_team_upcoming_fixtures,
    get_team_snapshot,
    get_league_teams,
    get_league_table,
)

dash.register_page(__name__, path="/team")

CHART_HEIGHT = 320


def kpi_card(title, value_id):
    return html.Div(
        className="kpi-card",
        children=[
            html.Div(title, className="kpi-title"),
            html.Div("—", id=value_id, className="kpi-value"),
        ],
    )


def make_fixtures_table(df):
    if df is None or df.empty:
        return html.Div("No upcoming fixtures found.", className="small-note")

    return dash_table.DataTable(
        columns=[{"name": c, "id": c} for c in df.columns],
        data=df.to_dict("records"),
        page_size=5,
        style_table={"overflowX": "auto"},
        style_cell={"fontFamily": "Arial", "fontSize": 13, "padding": "10px"},
        style_header={"fontWeight": "bold"},
    )


layout = (
    html.Div(
        className="shell",
        children=[
            html.Div(
                className="sidebar",
                children=[
                    html.Div("Team Page", className="sidebar-title"),
                    dcc.Link("Home", href="/", className="side-link"),
                    dcc.Link("League", href="/league", className="side-link"),
                    dcc.Link("Team", href="/team", className="side-link active"),
                    dcc.Link("Players", href="/player", className="side-link"),
                    dcc.Link("Comparison", href="/comparison", className="side-link"),
                    dcc.Link("Predictions", href="/predictions", className="side-link"),
                ],
            ),
            html.Div(
                className="main",
                children=[
                    html.Div("Team Analytics Dashboard", className="header"),
                    html.Div(
                        className="filters-row",
                        children=[
                            html.Div(
                                className="filter-box",
                                children=[
                                    html.Div(
                                        "League dropdown", className="filter-label"
                                    ),
                                    dcc.Dropdown(
                                        id="team_league_dd",
                                        options=LEAGUES,
                                        value=39,
                                        clearable=False,
                                    ),
                                ],
                            ),
                            html.Div(
                                className="filter-box",
                                children=[
                                    html.Div(
                                        "Season dropdown", className="filter-label"
                                    ),
                                    dcc.Dropdown(
                                        id="team_season_dd",
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
                                        id="team_team_dd",
                                        options=TEAMS_PL,
                                        value=TEAMS_PL[0]["value"] if TEAMS_PL else 40,
                                        clearable=False,
                                    ),
                                ],
                            ),
                            html.Button(
                                "Apply",
                                id="team_apply",
                                n_clicks=1,
                                className="apply-btn",
                            ),
                        ],
                    ),
                    html.Div(
                        className="kpi-row",
                        children=[
                            kpi_card("Matches played", "team_kpi_matches"),
                            kpi_card("Goals scored", "team_kpi_goals"),
                            kpi_card("League position", "team_kpi_position"),
                            kpi_card("Top scorer", "team_kpi_top_scorer"),
                        ],
                    ),
                    html.Div(
                        className="charts-row",
                        children=[
                            html.Div(
                                className="panel",
                                children=[
                                    html.Div(
                                        "Team Form trend (last 10 matches)",
                                        className="panel-title",
                                    ),
                                    html.Div(
                                        id="team_form_label",
                                        style={
                                            "fontWeight": "700",
                                            "marginBottom": "6px",
                                        },
                                    ),
                                    dcc.Graph(
                                        id="team_form_chart",
                                        figure=px.line(title=""),
                                        style={"height": f"{CHART_HEIGHT}px"},
                                    ),
                                ],
                            ),
                            html.Div(
                                className="panel",
                                children=[
                                    html.Div(
                                        "Team Top Scorers", className="panel-title"
                                    ),
                                    dcc.Graph(
                                        id="team_scorers_chart",
                                        figure=px.bar(title=""),
                                        style={"height": f"{CHART_HEIGHT}px"},
                                    ),
                                ],
                            ),
                        ],
                    ),
                    html.Div(
                        className="charts-row",
                        children=[
                            html.Div(
                                className="panel",
                                children=[
                                    html.Div(
                                        "Results Breakdown (last 10 matches)",
                                        className="panel-title",
                                    ),
                                    dcc.Graph(
                                        id="team_results_chart",
                                        figure=px.pie(title=""),
                                        style={"height": f"{CHART_HEIGHT}px"},
                                    ),
                                ],
                            ),
                            html.Div(
                                className="panel",
                                children=[
                                    html.Div(
                                        "Team Top Assists", className="panel-title"
                                    ),
                                    dcc.Graph(
                                        id="team_assists_chart",
                                        figure=px.bar(title=""),
                                        style={"height": f"{CHART_HEIGHT}px"},
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
                                        "Cumulative points (last 10 matches)",
                                        className="panel-title",
                                    ),
                                    dcc.Graph(
                                        id="team_cumulative_points_chart",
                                        figure=px.line(title=""),
                                        style={"height": f"{CHART_HEIGHT}px"},
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
                                        "Team vs League Average Profile",
                                        className="panel-title",
                                    ),
                                    dcc.Graph(
                                        id="team_radar_chart",
                                        figure=go.Figure(),
                                        style={"height": f"{CHART_HEIGHT + 80}px"},
                                    ),
                                ],
                            ),
                        ],
                    ),
                    html.Div(
                        className="panel fixtures-panel",
                        children=[
                            html.Div("Upcoming fixtures", className="fixtures-title"),
                            html.Div(id="team_fixtures_table"),
                            html.Div(id="team_error_box", className="error-text"),
                        ],
                    ),
                ],
            ),
        ],
    ),
)


@dash.callback(
    Output("team_team_dd", "options"),
    Output("team_team_dd", "value"),
    Input("team_league_dd", "value"),
    Input("team_season_dd", "value"),
    State("team_team_dd", "value"),
)
def update_team_dropdown_options(league_id, season_year, current_team_id):
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
    if current_team_id in values:
        value = current_team_id
    else:
        value = teams[0]["value"] if teams else None

    return teams, value


@dash.callback(
    Output("team_kpi_matches", "children"),
    Output("team_kpi_goals", "children"),
    Output("team_kpi_position", "children"),
    Output("team_kpi_top_scorer", "children"),
    Output("team_form_label", "children"),
    Output("team_form_chart", "figure"),
    Output("team_cumulative_points_chart", "figure"),
    Output("team_radar_chart", "figure"),
    Output("team_scorers_chart", "figure"),
    Output("team_results_chart", "figure"),
    Output("team_assists_chart", "figure"),
    Output("team_fixtures_table", "children"),
    Output("team_error_box", "children"),
    Input("team_apply", "n_clicks"),
    State("team_league_dd", "value"),
    State("team_season_dd", "value"),
    State("team_team_dd", "value"),
)
def update_team_page(n, league_id, season_year, team_id):
    try:
        league_id = int(league_id)
        season_year = int(season_year)
        team_id = int(team_id)

        teams = get_league_teams(league_id, season_year)
        team_name = next(
            (t["label"] for t in teams if int(t["value"]) == team_id), str(team_id)
        )

        # Team KPIs
        snap = get_team_snapshot(league_id, season_year, team_id) or {}
        matches = snap.get("matches_played", "—")
        goals = snap.get("goals_scored", "—")

        # League position
        table_df = get_league_table(league_id, season_year)
        if table_df is None or table_df.empty:
            position = "—"
        else:
            row = table_df[table_df["team_id"] == team_id]
            position = str(row.iloc[0]["rank"]) if not row.empty else "—"

        # Top scorers
        scorers_df = get_team_top_scorers(league_id, team_id, season_year)
        if scorers_df is None or scorers_df.empty:
            scorers_fig = px.bar(title="No scorer data returned for this team.")
            top_scorer = "—"
        else:
            scorers_fig = px.bar(scorers_df, x="player", y="goals", title="")
            top_scorer = (
                f"{scorers_df.iloc[0]['player']} ({scorers_df.iloc[0]['goals']})"
            )

        scorers_fig.update_layout(
            height=CHART_HEIGHT, margin=dict(l=30, r=10, t=40, b=30)
        )

        # Form
        form_df = get_team_form_points(league_id, season_year, team_id, last_n=10)
        form_label = f"Form for: {team_name}"

        if form_df is None or form_df.empty:
            form_fig = px.line(
                title="No finished matches returned for this team/season yet."
            )
        else:
            form_fig = px.line(
                form_df,
                x="match",
                y="points",
                markers=True,
                title="",
                hover_data=["date", "result", "points"],
            )
            form_fig.update_yaxes(tickmode="array", tickvals=[0, 1, 3])

        form_fig.update_layout(height=CHART_HEIGHT, margin=dict(l=30, r=10, t=40, b=30))

        # Cumulative points
        if form_df is None or form_df.empty:
            cumulative_fig = px.line(
                title="No finished matches returned for this team/season yet."
            )
        else:
            cum_df = form_df.copy()
            cum_df["cumulative_points"] = cum_df["points"].cumsum()
            cumulative_fig = px.line(
                cum_df,
                x="match",
                y="cumulative_points",
                markers=True,
                title="",
                hover_data=["date", "result", "points", "cumulative_points"],
            )
            cumulative_fig.update_yaxes(tick0=0)

        cumulative_fig.update_layout(
            height=CHART_HEIGHT, margin=dict(l=30, r=10, t=40, b=30)
        )

        # Top assists
        assists_df = get_team_top_assists(league_id, team_id, season_year)

        if assists_df is None or assists_df.empty:
            assists_fig = px.bar(title="No assists data returned for this team.")
        else:
            assists_fig = px.bar(
                assists_df,
                x="player",
                y="assists",
                title="",
            )

        assists_fig.update_layout(
            height=CHART_HEIGHT, margin=dict(l=30, r=10, t=40, b=30)
        )

        # Upcoming fixtures
        fixtures_df = get_team_upcoming_fixtures(
            league_id, season_year, team_id, next_n=5
        )
        fixtures_table = make_fixtures_table(fixtures_df)

        # Radar chart: selected team vs league average
        if table_df is None or table_df.empty:
            radar_fig = go.Figure()
            radar_fig.update_layout(
                title="No league table data available.",
                height=CHART_HEIGHT + 80,
                margin=dict(l=30, r=30, t=40, b=30),
            )
        else:
            team_row = table_df[table_df["team_id"] == team_id]

            if team_row.empty:
                radar_fig = go.Figure()
                radar_fig.update_layout(
                    title="No team radar data available.",
                    height=CHART_HEIGHT + 80,
                    margin=dict(l=30, r=30, t=40, b=30),
                )
            else:
                row = team_row.iloc[0]

                # team values
                team_played = row["played"] if row["played"] else 1
                team_goals_per_match = row["goals_for"] / team_played
                team_goals_against_per_match = row["goals_against"] / team_played
                team_win_rate = row["win"] / team_played
                team_draw_rate = row["draw"] / team_played
                team_loss_rate = row["lose"] / team_played
                team_points_per_match = row["points"] / team_played

                # league average values
                avg_played = table_df["played"].replace(0, 1)

                league_goals_per_match = (table_df["goals_for"] / avg_played).mean()
                league_goals_against_per_match = (table_df["goals_against"] / avg_played).mean()
                league_win_rate = (table_df["win"] / avg_played).mean()
                league_draw_rate = (table_df["draw"] / avg_played).mean()
                league_loss_rate = (table_df["lose"] / avg_played).mean()
                league_points_per_match = (table_df["points"] / avg_played).mean()

                categories = [
                    "Goals / Match",
                    "Goals Against / Match",
                    "Win Rate",
                    "Draw Rate",
                    "Loss Rate",
                    "Points / Match",
                ]

                team_values = [
                    team_goals_per_match,
                    team_goals_against_per_match,
                    team_win_rate,
                    team_draw_rate,
                    team_loss_rate,
                    team_points_per_match,
                ]

                league_values = [
                    league_goals_per_match,
                    league_goals_against_per_match,
                    league_win_rate,
                    league_draw_rate,
                    league_loss_rate,
                    league_points_per_match,
                ]

                # close the shape
                categories_closed = categories + [categories[0]]
                team_values_closed = team_values + [team_values[0]]
                league_values_closed = league_values + [league_values[0]]

                radar_fig = go.Figure()

                radar_fig.add_trace(
                    go.Scatterpolar(
                        r=team_values_closed,
                        theta=categories_closed,
                        fill="toself",
                        name=team_name,
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
                    height=CHART_HEIGHT + 80,
                    margin=dict(l=30, r=30, t=40, b=30),
                    showlegend=True,
                )

        # Results breakdown (W/D/L) from the last N matches
        results_fig = px.pie(
            names=["W", "D", "L"],
            values=[
                (
                    int((form_df[form_df["result"] == "W"].shape[0]))
                    if form_df is not None
                    else 0
                ),
                (
                    int((form_df[form_df["result"] == "D"].shape[0]))
                    if form_df is not None
                    else 0
                ),
                (
                    int((form_df[form_df["result"] == "L"].shape[0]))
                    if form_df is not None
                    else 0
                ),
            ],
            title="",
        )
        results_fig.update_layout(
            height=CHART_HEIGHT, margin=dict(l=30, r=10, t=40, b=30)
        )

        return (
            matches,
            goals,
            position,
            top_scorer,
            form_label,
            form_fig,
            cumulative_fig,
            radar_fig,
            scorers_fig,
            results_fig,
            assists_fig,
            fixtures_table,
            "",
        )

    except Exception as e:
        empty_form = px.line(title="API error")
        empty_form.update_layout(height=CHART_HEIGHT)
        empty_cumulative = px.line(title="API error")
        empty_cumulative.update_layout(height=CHART_HEIGHT)
        empty_radar = go.Figure()
        empty_radar.update_layout(title="API error", height=CHART_HEIGHT + 80)
        empty_scorers = px.bar(title="API error")
        empty_scorers.update_layout(height=CHART_HEIGHT)
        empty_results = px.pie(title="API error")
        empty_results.update_layout(height=CHART_HEIGHT)
        empty_assists = px.bar(title="API error")
        empty_assists.update_layout(height=CHART_HEIGHT)
        

        return (
            "—",
            "—",
            "—",
            "—",
            "",
            empty_form,
            empty_cumulative,
            empty_radar,
            empty_scorers,
            empty_results,
            empty_assists,
            html.Div(),
            str(e),
        )
