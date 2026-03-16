from dotenv import load_dotenv
load_dotenv()  # loads APIFOOTBALL_KEY from .env into environment variables

from dash import Dash, html, dcc
import dash

app = Dash(__name__, use_pages=True, suppress_callback_exceptions=True)
app.title = "Thesis Football Dashboard"

app.layout = html.Div(
    children=[
        html.Div(
            style={"padding": "12px 20px", "borderBottom": "1px solid #ddd", "fontFamily": "Arial"},
            children=[
                dcc.Link("Home", href="/", style={"marginRight": "12px"}),
            ],
        ),
        dash.page_container,
    ]
)

if __name__ == "__main__":
    app.run(debug=True)
