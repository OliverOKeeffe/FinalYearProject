import dash
from dash import dcc, html, Input, Output, State, dash_table
import plotly.express as px

from services.constants import LEAGUES, SEASONS, TEAMS_PL
from services.api_football import (
    get_team_top_scorers,
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


layout = html.Div(
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
                                html.Div("League dropdown", className="filter-label"),
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
                                html.Div("Season dropdown", className="filter-label"),
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
                        html.Button("Apply", id="team_apply", n_clicks=1, className="apply-btn"),
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
                                html.Div("Team Form trend (last 10 matches)", className="panel-title"),
                                html.Div(id="team_form_label", style={"fontWeight": "700", "marginBottom": "6px"}),
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
                                html.Div("Team Top Scorers", className="panel-title"),
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
    Output("team_scorers_chart", "figure"),
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
        team_name = next((t["label"] for t in teams if int(t["value"]) == team_id), str(team_id))

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
            top_scorer = f"{scorers_df.iloc[0]['player']} ({scorers_df.iloc[0]['goals']})"

        scorers_fig.update_layout(height=CHART_HEIGHT, margin=dict(l=30, r=10, t=40, b=30))

        # Form
        form_df = get_team_form_points(league_id, season_year, team_id, last_n=10)
        form_label = f"Form for: {team_name}"

        if form_df is None or form_df.empty:
            form_fig = px.line(title="No finished matches returned for this team/season yet.")
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

        # Upcoming fixtures
        fixtures_df = get_team_upcoming_fixtures(league_id, season_year, team_id, next_n=5)
        fixtures_table = make_fixtures_table(fixtures_df)

        return (
            matches,
            goals,
            position,
            top_scorer,
            form_label,
            form_fig,
            scorers_fig,
            fixtures_table,
            "",
        )

    except Exception as e:
        empty_form = px.line(title="API error")
        empty_form.update_layout(height=CHART_HEIGHT)
        empty_scorers = px.bar(title="API error")
        empty_scorers.update_layout(height=CHART_HEIGHT)

        return "—", "—", "—", "—", "", empty_form, empty_scorers, html.Div(), str(e)