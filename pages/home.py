import dash
from dash import dcc, html, Input, Output, State, dash_table
import plotly.express as px

from services.constants import LEAGUES, SEASONS, TEAMS_PL
from services.api_football import (
    get_league_top_scorers,
    get_team_form_points,
    get_team_upcoming_fixtures,
    get_league_leader,
    get_league_table,
    get_team_snapshot,
    get_league_teams,
)

dash.register_page(__name__, path="/")

CHART_HEIGHT = 320


# I define a helper function to create KPI cards, which are small panels that display a title and a value
def kpi_card(title, value_id):
    return html.Div(
        className="kpi-card",
        children=[
            html.Div(title, className="kpi-title"),
            html.Div("—", id=value_id, className="kpi-value"),
        ],
    )


# I define a helper function to create a table of upcoming fixtures, which takes a DataFrame as input and returns a Dash DataTable component
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


# I define a helper function to create a league table, which takes a DataFrame and an optional selected team ID as input and returns a Dash DataTable component. The selected team will be highlighted in the table.
def make_league_table(df, selected_team_id: int | None):
    if df is None or df.empty:
        return html.Div("No league table data found.", className="small-note")

    selected_team_id = int(selected_team_id) if selected_team_id is not None else None
    # I set up conditional styling for the league table to highlight the row of the selected team. If a team is selected, its row will have a different background color and bold font.
    style_data_conditional = []
    if selected_team_id is not None:
        style_data_conditional.append(
            {
                "if": {"filter_query": f"{{team_id}} = {selected_team_id}"},
                "backgroundColor": "#fff4b2",
                "fontWeight": "bold",
            }
        )
    # I create a Dash DataTable with the league table data, specifying columns, pagination, sorting, and styling. The team_id column is hidden but used for conditional styling to highlight the selected team.
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
        hidden_columns=["team_id"],
        sort_action="native",
        page_action="native",
        page_size=20,
        style_table={"overflowX": "auto"},
        style_cell={"fontFamily": "Arial", "fontSize": 13, "padding": "10px"},
        style_header={"fontWeight": "bold"},
        style_data_conditional=style_data_conditional,
    )


# I define the layout of the home page, which consists of a sidebar with navigation links and a main content area with filters, KPIs, charts, and tables. The filters allow users to select a league, season, and team, and the main area displays relevant information based on those selections.
layout = html.Div(
    className="shell",
    children=[
        html.Div(
            className="sidebar",
            children=[
                html.Div("Home Page", className="sidebar-title"),
                dcc.Link("Home", href="/", className="side-link active"),
                dcc.Link("League", href="/league", className="side-link"),
                dcc.Link("Team", href="/team", className="side-link"),
                dcc.Link("Players", href="/player", className="side-link"),
                dcc.Link("Comarison", href="/comparison", className="side-link"),
                dcc.Link("Predictions", href="/predictions", className="side-link"),
            ],
        ),
        html.Div(
            className="main",
            children=[
                html.Div("Football Analytics Dashboard", className="header"),
                # I create a row of filters for selecting the league, season, and team, and a button to apply the filters. The options for the dropdowns are populated from the constants defined in services/constants.py and from API calls to get teams based on the selected league and season.
                html.Div(
                    className="filters-row",
                    children=[
                        html.Div(
                            className="filter-box",
                            children=[
                                html.Div("League dropdown", className="filter-label"),
                                dcc.Dropdown(
                                    id="home_league",
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
                                    id="home_season",
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
                                    id="home_team",
                                    options=TEAMS_PL,
                                    value=TEAMS_PL[0]["value"] if TEAMS_PL else 40,
                                    clearable=False,
                                ),
                            ],
                        ),
                        html.Button(
                            "Apply", id="home_apply", n_clicks=1, className="apply-btn"
                        ),
                    ],
                ),
                # I create a row of KPI cards to display key statistics such as matches played, goals scored, current league leader, and league top scorer. The values in these cards will be updated based on the selected filters and API data.
                html.Div(
                    className="kpi-row",
                    children=[
                        kpi_card("Matches Played", "kpi_matches"),
                        kpi_card("Goals Scored", "kpi_goals"),
                        kpi_card("Current League Leader", "kpi_leader"),
                        kpi_card("League Top Scorer", "kpi_top_scorer"),
                    ],
                ),
                # I create a row with two charts: one showing the recent form of the selected team (points from the last 10 matches) and another showing the top scorers in the league. These charts will be updated based on the selected filters and API data.
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
                                    id="form_team_label",
                                    style={"fontWeight": "700", "marginBottom": "6px"},
                                ),
                                dcc.Graph(
                                    id="form_chart",
                                    figure=px.line(title=""),
                                    style={"height": f"{CHART_HEIGHT}px"},
                                ),
                            ],
                        ),
                        html.Div(
                            className="panel",
                            children=[
                                html.Div(
                                    "Top Scorers (Top 10)", className="panel-title"
                                ),
                                dcc.Graph(
                                    id="home_scorers_chart",
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
                        html.Div(id="fixtures_table"),
                        html.Div(id="home_error", className="error-text"),
                    ],
                ),
                html.Div(
                    className="panel",
                    children=[
                        html.Div("League table", className="panel-title"),
                        html.Div(id="league_table"),
                    ],
                ),
            ],
        ),
    ],
)


# I set up a callback to update the options and selected value of the team dropdown based on the selected league and season. When the league or season changes, it fetches the teams for that league and season from the API and updates the dropdown options. If the previously selected team is still valid, it remains selected; otherwise, it defaults to the first team in the new list.
@dash.callback(
    Output("home_team", "options"),
    Output("home_team", "value"),
    Input("home_league", "value"),
    Input("home_season", "value"),
    State("home_team", "value"),
)
# This function takes the selected league ID, season year, and current team ID as inputs, fetches the teams for the selected league and season, and returns the new options and selected value for the team dropdown. If there is an error during data fetching, it returns a default list of teams and keeps the current selection if possible.
def update_home_team_options(league_id, season_year, current_team_id):
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


# I define a callback function that updates the KPIs, charts, fixtures table, and league table on the home page when the "Apply" button is clicked. The function takes the selected league ID, season year, and team ID as inputs, fetches the relevant data from the API, and updates the components accordingly. If there is an error during data fetching or processing, it returns default values and displays the error message.
@dash.callback(
    Output("kpi_matches", "children"),
    Output("kpi_goals", "children"),
    Output("kpi_leader", "children"),
    Output("kpi_top_scorer", "children"),
    Output("form_team_label", "children"),
    Output("form_chart", "figure"),
    Output("home_scorers_chart", "figure"),
    Output("fixtures_table", "children"),
    Output("league_table", "children"),
    Output("home_error", "children"),
    Input("home_apply", "n_clicks"),
    State("home_league", "value"),
    State("home_season", "value"),
    State("home_team", "value"),
)
# This function takes the number of clicks on the "Apply" button, the selected league ID, season year, and team ID as inputs. It fetches various pieces of data from the API, including the league leader, team snapshot, top scorers, team form points, upcoming fixtures, and league table. It then updates the KPIs, charts, fixtures table, and league table on the home page with this data. If any errors occur during this process, it returns default values and displays the error message in the designated error box.
def update_home(n, league_id, season_year, team_id):
    try:
        league_id = int(league_id)
        season_year = int(season_year)
        team_id = int(team_id)

        leader = get_league_leader(league_id, season_year)
        # I fetch the team snapshot to get the number of matches played and goals scored for the selected team in the selected league and season. If no snapshot is returned, I use default values of "—" for both metrics.
        snap = get_team_snapshot(league_id, season_year, team_id) or {}
        matches = snap.get("matches_played", "—")
        goals = snap.get("goals_scored", "—")
        # I fetch the top scorers for the league and season, and create a bar chart to display the top 10 scorers. If no data is returned, I display a message indicating that no scorer data is available.
        scorers_df = get_league_top_scorers(league_id, season_year)
        if scorers_df is None or scorers_df.empty:
            scorers_fig = px.bar(title="No scorer data returned for this selection.")
            top_scorer = "—"
        else:
            scorers_fig = px.bar(scorers_df, x="player", y="goals", title="")
            top_scorer = (
                f"{scorers_df.iloc[0]['player']} ({scorers_df.iloc[0]['goals']})"
            )

        scorers_fig.update_layout(
            height=CHART_HEIGHT, margin=dict(l=30, r=10, t=40, b=30)
        )
        # I fetch the recent form points for the selected team, league, and season, and create a line chart to display the form trend over the last 10 matches. If no data is returned, I display a message indicating that no form data is available.
        form_df = get_team_form_points(league_id, season_year, team_id, last_n=10)
        teams = get_league_teams(league_id, season_year)
        team_name = next(
            (t["label"] for t in teams if int(t["value"]) == team_id), str(team_id)
        )
        form_label = f"Form for: {team_name}"
        # I create a line chart to show the form trend, with points on the y-axis and match identifiers on the x-axis. If there is no form data, I display a message indicating that no finished matches have been returned for this team and season yet.
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
        # I fetch the upcoming fixtures for the selected league, season, and team, and create a table to display these fixtures. If no fixtures are found, I display a message indicating that no upcoming fixtures were found.
        fixtures_df = get_team_upcoming_fixtures(
            league_id, season_year, team_id, next_n=5
        )
        fixtures_table = make_fixtures_table(fixtures_df)

        league_table_df = get_league_table(league_id, season_year)
        league_table = make_league_table(league_table_df, team_id)

        return (
            matches,
            goals,
            leader,
            top_scorer,
            form_label,
            form_fig,
            scorers_fig,
            fixtures_table,
            league_table,
            "",
        )
    # If any exceptions occur during the data fetching or processing, I catch the exception and return default values for all components, along with the error message to be displayed in the error box on the home page.
    except Exception as e:
        empty_form = px.line(title="API error")
        empty_form.update_layout(height=CHART_HEIGHT)
        empty_scorers = px.bar(title="API error")
        empty_scorers.update_layout(height=CHART_HEIGHT)
        # In case of an error, I return default values for all KPIs and charts, an empty table for fixtures and league table, and the error message to be displayed in the designated error box on the home page.
        return (
            "—",
            "—",
            "—",
            "—",
            "",
            empty_form,
            empty_scorers,
            html.Div(),
            html.Div(),
            str(e),
        )
