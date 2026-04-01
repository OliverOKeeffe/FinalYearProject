import dash
from dash import dcc, html, Input, Output, State, dash_table
import plotly.express as px

from services.constants import LEAGUES, SEASONS
from services.api_football import (
    get_league_top_scorers,
    get_league_leader,
    get_league_table,
)

dash.register_page(__name__, path="/league")

CHART_HEIGHT = 320


def kpi_card(title, value_id):
    return html.Div(
        className="kpi-card",
        children=[
            html.Div(title, className="kpi-title"),
            html.Div("—", id=value_id, className="kpi-value"),
        ],
    )


def make_league_table(df):
    if df is None or df.empty:
        return html.Div("No league table data found.", className="small-note")

    return dash_table.DataTable(
        columns=[
            {"name": "#", "id": "rank"},
            {"name": "Team", "id": "team"},
            {"name": "P", "id": "played"},
            {"name": "W", "id": "win"},
            {"name": "D", "id": "draw"},
            {"name": "L", "id": "lose"},
            {"name": "GF", "id": "goals_for"},
            {"name": "GA", "id": "goals_against"},
            {"name": "GD", "id": "goal_diff"},
            {"name": "Pts", "id": "points"},
        ],
        data=df.to_dict("records"),
        sort_action="native",
        page_action="native",
        page_size=20,
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
                html.Div("League Page", className="sidebar-title"),
                dcc.Link("Home", href="/", className="side-link"),
                dcc.Link("League", href="/league", className="side-link active"),
                dcc.Link("Team", href="/team", className="side-link"),
                dcc.Link("Players", href="/player", className="side-link"),
                dcc.Link("Comparison", href="/comparison", className="side-link"),
            ],
        ),
        html.Div(
            className="main",
            children=[
                html.Div("League Analytics Dashboard", className="header"),
                html.Div(
                    className="filters-row",
                    children=[
                        html.Div(
                            className="filter-box",
                            children=[
                                html.Div("League dropdown", className="filter-label"),
                                dcc.Dropdown(
                                    id="league_league_dd",
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
                                    id="league_season_dd",
                                    options=SEASONS,
                                    value=SEASONS[0]["value"] if SEASONS else 2024,
                                    clearable=False,
                                ),
                            ],
                        ),
                        html.Button(
                            "Apply",
                            id="league_apply",
                            n_clicks=1,
                            className="apply-btn",
                        ),
                    ],
                ),
                html.Div(
                    className="kpi-row",
                    children=[
                        kpi_card("League Leader", "league_kpi_leader"),
                        kpi_card("Top Scorer", "league_kpi_top_scorer"),
                        kpi_card("Teams in League", "league_kpi_teams"),
                        kpi_card("Highest Points", "league_kpi_points"),
                    ],
                ),
                html.Div(
                    className="charts-row",
                    children=[
                        html.Div(
                            className="panel",
                            children=[
                                html.Div("Top Scorers", className="panel-title"),
                                dcc.Graph(
                                    id="league_scorers_chart",
                                    figure=px.bar(title=""),
                                    style={"height": f"{CHART_HEIGHT}px"},
                                ),
                            ],
                        ),
                        html.Div(
                            className="panel",
                            children=[
                                html.Div("Goals vs Points", className="panel-title"),
                                dcc.Graph(
                                    id="league_bubble_chart",
                                    figure=px.scatter(title=""),
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
                                html.Div("Goals Scored Treemap", className="panel-title"),
                                dcc.Graph(
                                    id="league_treemap_chart",
                                    figure=px.treemap(title=""),
                                    style={"height": f"{CHART_HEIGHT}px"},
                                ),
                            ],
                        ),
                    ],
                ),
                html.Div(
                    className="panel",
                    children=[
                        html.Div("League Table", className="panel-title"),
                        html.Div(id="league_table_box"),
                        html.Div(id="league_error_box", className="error-text"),
                    ],
                ),
            ],
        ),
    ],
)


@dash.callback(
    Output("league_kpi_leader", "children"),
    Output("league_kpi_top_scorer", "children"),
    Output("league_kpi_teams", "children"),
    Output("league_kpi_points", "children"),
    Output("league_scorers_chart", "figure"),
    Output("league_bubble_chart", "figure"),
    Output("league_treemap_chart", "figure"),
    Output("league_table_box", "children"),
    Output("league_error_box", "children"),
    Input("league_apply", "n_clicks"),
    State("league_league_dd", "value"),
    State("league_season_dd", "value"),
)
def update_league_page(n, league_id, season_year):
    try:
        league_id = int(league_id)
        season_year = int(season_year)

        leader = get_league_leader(league_id, season_year)
        table_df = get_league_table(league_id, season_year)
        scorers_df = get_league_top_scorers(league_id, season_year)

        if table_df is None or table_df.empty:
            bubble_fig = px.scatter(title="No league table data found.")
            treemap_fig = px.treemap(title="No league table data found.")
            league_table = make_league_table(table_df)
            team_count = "—"
            highest_points = "—"
        else:
            bubble_fig = px.scatter(
                table_df,
                x="goals_for",
                y="points",
                size="goals_against",
                hover_name="team",
                title="",
            )

            treemap_fig = px.treemap(
                table_df,
                path=["team"],
                values="goals_for",
                title="",
            )

            team_count = str(len(table_df))
            highest_points = str(table_df["points"].max())
            league_table = make_league_table(table_df)

        bubble_fig.update_layout(
            height=CHART_HEIGHT, margin=dict(l=30, r=10, t=40, b=30)
        )
        treemap_fig.update_layout(
            height=CHART_HEIGHT, margin=dict(l=30, r=10, t=40, b=30)
        )

        if scorers_df is None or scorers_df.empty:
            scorers_fig = px.bar(title="No scorer data returned for this selection.")
            top_scorer = "—"
        else:
            scorers_fig = px.bar(
                scorers_df,
                x="player",
                y="goals",
                title="",
            )
            top_scorer = f"{scorers_df.iloc[0]['player']} ({scorers_df.iloc[0]['goals']})"

        scorers_fig.update_layout(
            height=CHART_HEIGHT, margin=dict(l=30, r=10, t=40, b=30)
        )

        return (
            leader,
            top_scorer,
            team_count,
            highest_points,
            scorers_fig,
            bubble_fig,
            treemap_fig,
            league_table,
            "",
        )

    except Exception as e:
        empty_scorers = px.bar(title="API error")
        empty_scorers.update_layout(height=CHART_HEIGHT)

        empty_bubble = px.scatter(title="API error")
        empty_bubble.update_layout(height=CHART_HEIGHT)

        empty_treemap = px.treemap(title="API error")
        empty_treemap.update_layout(height=CHART_HEIGHT)

        return (
            "—",
            "—",
            "—",
            "—",
            empty_scorers,
            empty_bubble,
            empty_treemap,
            html.Div(),
            str(e),
        )