import dash
from dash import dcc, html, Input, Output, State, dash_table

from services.constants import LEAGUES, SEASONS
from services.api_football import (
    get_league_upcoming_fixtures,
    get_match_prediction,
)

dash.register_page(__name__, path="/predictions")


layout = html.Div(
    className="shell",
    children=[
        html.Div(
            className="sidebar",
            children=[
                html.Div("Prediction Page", className="sidebar-title"),
                dcc.Link("Home", href="/", className="side-link"),
                dcc.Link("League", href="/league", className="side-link"),
                dcc.Link("Team", href="/team", className="side-link"),
                dcc.Link("Players", href="/player", className="side-link"),
                dcc.Link("Comparison", href="/comparison", className="side-link"),
                dcc.Link("Predictions", href="/predictions", className="side-link"),
            ],
        ),
        html.Div(
            className="main",
            children=[
                html.Div("Match Prediction Dashboard", className="header"),
                html.Div(
                    className="filters-row",
                    children=[
                        html.Div(
                            className="filter-box",
                            children=[
                                html.Div("League dropdown", className="filter-label"),
                                dcc.Dropdown(
                                    id="pred_league_dd",
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
                                    id="pred_season_dd",
                                    options=SEASONS,
                                    value=SEASONS[0]["value"] if SEASONS else 2024,
                                    clearable=False,
                                ),
                            ],
                        ),
                        html.Div(
                            className="apply-container",
                            children=[
                                html.Button(
                                    "Predict",
                                    id="pred_apply",
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
                                html.Div(
                                    "Upcoming Fixture Predictions",
                                    className="panel-title",
                                ),
                                html.Div(id="predictions_table"),
                                html.Div(id="pred_error_box", className="error-text"),
                            ],
                        ),
                    ],
                ),
            ],
        ),
    ],
)


@dash.callback(
    Output("predictions_table", "children"),
    Output("pred_error_box", "children"),
    Input("pred_apply", "n_clicks"),
    State("pred_league_dd", "value"),
    State("pred_season_dd", "value"),
)
def update_prediction_page(n, league_id, season_year):
    try:
        # I convert inputs to integers to ensure correct API usage
        league_id = int(league_id)
        season_year = int(season_year)

        # I fetch the next 10 upcoming fixtures for the selected league/season
        fixtures = get_league_upcoming_fixtures(league_id, season_year, next_n=10)
        # If no fixtures are found, I return a message
        if not fixtures:
            return html.Div("No upcoming fixtures found."), ""

        rows = []
         # For each fixture, I request prediction data from the API and build a row for the table
        for fx in fixtures:
            fixture_id = fx.get("fixture_id")
             # I call the prediction endpoint using the fixture ID 
            pred = get_match_prediction(fixture_id) if fixture_id else {}
            # I extract the relevant prediction details, handling cases where data might be missing
            predictions = pred.get("predictions", {}) if pred else {}
            winner = (predictions.get("winner") or {}).get("name", "No prediction")
            advice = predictions.get("advice", "No advice")
            percent = predictions.get("percent", {}) if pred else {}
            # I build each row of the table
            rows.append(
                {
                    "Date": fx.get("date", ""),
                    "Time": fx.get("time", ""),
                    "Home": fx.get("home_team", ""),
                    "Away": fx.get("away_team", ""),
                    "Winner": winner,
                    "Home %": percent.get("home", "—"),
                    "Draw %": percent.get("draw", "—"),
                    "Away %": percent.get("away", "—"),
                    "Advice": advice,
                }
            )
        # I convert the rows into a Dash DataTable for display
        table = dash_table.DataTable(
            columns=[{"name": c, "id": c} for c in rows[0].keys()],
            data=rows,
            page_size=10,
            style_table={"overflowX": "auto"},
            style_cell={"fontFamily": "Arial", "fontSize": 13, "padding": "10px"},
            style_header={"fontWeight": "bold"},
        )

        return table, ""

    except Exception as e:
        return html.Div(), str(e)