import dash
from dash import html

dash.register_page(__name__, path="/player")


layout = html.Div(
    children=[
        html.H2("Player Page"),
    ]
)