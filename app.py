import os
from dotenv import load_dotenv
from dash import Dash, html, dcc
import dash

load_dotenv()  # loads APIFOOTBALL_KEY from .env into environment variables

app = Dash(__name__, use_pages=True, suppress_callback_exceptions=True)
server = app.server

app.title = "Thesis Football Dashboard"

app.layout = html.Div(
    children=[
        dash.page_container,
    ]
)

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 8050)),
        debug=False,
    )
