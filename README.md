# Football Statistics Website

A comprehensive football analytics dashboard built with Dash and Python that provides live statistics, predictions, team analysis, and player comparisons across multiple leagues.

## Features

- **League Dashboard**: View league standings, top scorers, and season statistics
- **Team Analysis**: Analyze individual team performance, form, and player statistics
- **Player Statistics**: Explore detailed player stats including goals, assists, tackles, and passes
- **Player Comparison**: Compare two players side-by-side with radar charts and insights
- **Match Predictions**: Get AI-powered predictions for upcoming fixtures
- **Real-time Data**: Powered by the API-Football service for live match data

## Prerequisites

Before you get started, make sure you have:

- **Python 3.8+** installed
- **Git** installed
- An **API-Football API key** (get one for free at [api-football.com](https://api-football.com))

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/FootballStatisticsWebsite-Thesis.git
cd FootballStatisticsWebsite-Thesis
```

### 2. Create a Virtual Environment

```bash
# On macOS/Linux
python3 -m venv .venv
source .venv/bin/activate

# On Windows
python -m venv .venv
.venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Set Up Environment Variables

Create a `.env` file in the root directory and add your API key:

```bash
APIFOOTBALL_KEY=your_api_key_here
```

**Note**: Never commit your `.env` file to GitHub. Make sure it's in your `.gitignore`.

## Running the App

```bash
python app.py
```

The app will start on `http://localhost:8050` by default. Open this URL in your browser to access the dashboard.

## Project Structure

```
.
├── app.py                          # Main application entry point
├── requirements.txt                # Python dependencies
├── README.md                       # This file
├── assets/
│   └── style.css                  # Custom styling
├── pages/
│   ├── home.py                    # Home page
│   ├── league.py                  # League statistics page
│   ├── team.py                    # Team analysis page
│   ├── player.py                  # Player statistics page
│   ├── comparison.py              # Player comparison page
│   └── predictions.py             # Match predictions page
└── services/
    ├── api_football.py            # API integration and data fetching
    ├── constants.py               # Configuration constants
    └── constants.py.save          # Backup configuration
```

## Key Pages

### Home
Starting point with navigation to all features.

### League
View league standings, top scorers, top assists, and overall league statistics.

### Team
Analyze individual team performance including form, fixtures, and player stats.

### Players
Search and view detailed statistics for individual players in a league.

### Comparison
Compare two players across different leagues and seasons with visual comparisons.

### Predictions
Get AI-powered predictions for upcoming matches in selected leagues.

## Configuration

Edit `services/constants.py` to customize:

- Available leagues
- Seasons to display
- Default team selections
- API cache TTL (time-to-live)

## Troubleshooting

### API Key Issues
- Ensure `APIFOOTBALL_KEY` is set in your environment
- Check that your API key is valid at [api-football.com](https://api-football.com)
- Verify the key has sufficient API credits

### Dependencies Not Installing
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Port Already in Use
The app runs on port 8050 by default. If it's already in use, modify `app.py` to use a different port.

## Technologies Used

- **Dash**: Interactive web framework
- **Plotly**: Data visualization
- **Pandas**: Data manipulation
- **Requests**: HTTP client for API calls
- **Python 3.8+**: Core language

## License

This project is for educational purposes as part of a final year thesis.

## Support

If you encounter any issues, please open an issue on GitHub or check the troubleshooting section above.

---

**Happy analyzing!** ⚽