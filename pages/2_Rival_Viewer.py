import html
from datetime import datetime

import pandas as pd
import requests
import streamlit as st


# =========================================================
# DEFAULT SETTINGS
# =========================================================

DEFAULT_LEAGUE_ID = "1116047"
DEFAULT_USER_ENTRY_ID = "6074290"

BASE_URL = "https://fantasy.premierleague.com/api"
REQUEST_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json",
}


# =========================================================
# PAGE SETTINGS
# =========================================================

st.set_page_config(
    page_title="Rival Viewer",
    page_icon="🔍",
    layout="wide",
)

st.title("🔍 Rival Viewer")

st.caption(
    "Scout rival squads, captain choices, chip usage and transfer history."
)


# =========================================================
# SIDEBAR SETTINGS
# =========================================================

st.sidebar.header("⚙️ Site Settings")

league_id = st.sidebar.text_input(
    "Mini-League ID",
    value=DEFAULT_LEAGUE_ID,
    help="The ID shown in your FPL mini-league URL.",
)

your_entry_id = st.sidebar.text_input(
    "Your FPL Entry ID",
    value=DEFAULT_USER_ENTRY_ID,
    help="Saved as the default for later squad comparison features.",
)

if st.sidebar.button(
    "🔄 Refresh Rival Data",
    use_container_width=True,
):
    st.cache_data.clear()
    st.rerun()


# =========================================================
# PAGE CSS
# =========================================================

st.markdown(
    """
    <style>
    div[data-testid="stMetric"] {
        background: #161b22;
        border: 1px solid #30363d;
        border-radius: 12px;
        padding: 12px;
    }

    div[data-testid="stMetricLabel"] {
        color: #aab3bf;
    }

    div[data-testid="stMetricValue"] {
        color: #ffffff;
    }

    .rival-heading {
        background: linear-gradient(135deg, #161b22, #202938);
        border: 1px solid #30363d;
        border-radius: 14px;
        padding: 16px 20px;
        margin: 10px 0 18px 0;
    }

    .rival-heading h3 {
        margin: 0;
        color: #ffffff;
    }

    .rival-heading p {
        margin: 5px 0 0 0;
        color: #aab3bf;
    }

    .legend-wrap {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        margin: 10px 0 16px 0;
    }

    .legend-item {
        background: #161b22;
        border: 1px solid #30363d;
        border-radius: 8px;
        padding: 6px 10px;
        font-size: 0.82rem;
        color: #e6edf3;
    }

    @media (max-width: 700px) {
        .rival-heading {
            padding: 12px;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# CLUB COLOURS
# The fallback colour is used for any promoted or renamed
# club not yet listed here.
# =========================================================

CLUB_COLOURS = {
    "Arsenal": ("#EF0107", "#FFFFFF"),
    "Aston Villa": ("#670E36", "#95BFE5"),
    "Bournemouth": ("#DA291C", "#000000"),
    "Brentford": ("#E30613", "#FFFFFF"),
    "Brighton": ("#0057B8", "#FFFFFF"),
    "Burnley": ("#6C1D45", "#99D6EA"),
    "Chelsea": ("#034694", "#FFFFFF"),
    "Crystal Palace": ("#1B458F", "#C4122E"),
    "Everton": ("#003399", "#FFFFFF"),
    "Fulham": ("#FFFFFF", "#000000"),
    "Leeds": ("#FFFFFF", "#1D428A"),
    "Leicester": ("#003090", "#FDBE11"),
    "Liverpool": ("#C8102E", "#FFFFFF"),
    "Luton": ("#F78F1E", "#002D62"),
    "Man City": ("#6CABDD", "#1C2C5B"),
    "Man Utd": ("#DA291C", "#FBE122"),
    "Newcastle": ("#241F20", "#FFFFFF"),
    "Nott'm Forest": ("#DD0000", "#FFFFFF"),
    "Norwich": ("#FFF200", "#00A650"),
    "Sheffield Utd": ("#EE2737", "#000000"),
    "Southampton": ("#D71920", "#FFFFFF"),
    "Sunderland": ("#EB172B", "#FFFFFF"),
    "Spurs": ("#132257", "#FFFFFF"),
    "Tottenham": ("#132257", "#FFFFFF"),
    "West Ham": ("#7A263A", "#1BB1E7"),
    "Wolves": ("#FDB913", "#231F20"),
    "Ipswich": ("#0044AA", "#FFFFFF"),
}


# =========================================================
# API HELPERS
# =========================================================

def api_get(endpoint, timeout=20):
    """Return JSON from an FPL API endpoint."""

    url = f"{BASE_URL}/{endpoint.lstrip('/')}"

    response = requests.get(
        url,
        headers=REQUEST_HEADERS,
        timeout=timeout,
    )

    response.raise_for_status()

    return response.json()


@st.cache_data(ttl=21600, show_spinner=False)
def get_bootstrap_data():
    return api_get("bootstrap-static/")


@st.cache_data(ttl=300, show_spinner=False)
def get_league_data(selected_league_id):
    """
    Retrieve all available standings pages.

    FPL normally returns a limited number of managers per page,
    so this continues until there is no next page.
    """

    all_results = []
    league_information = {}
    page_number = 1

    while True:
        data = api_get(
            f"leagues-classic/{selected_league_id}/standings/"
            f"?page_standings={page_number}"
        )

        if not league_information:
            league_information = data.get("league", {})

        standings = data.get("standings", {})
        results = standings.get("results", [])

        all_results.extend(results)

        if not standings.get("has_next", False):
            break

        page_number += 1

        if page_number > 25:
            break

    return {
        "league": league_information,
        "results": all_results,
    }


@st.cache_data(ttl=300, show_spinner=False)
def get_manager_data(entry_id):
    return api_get(f"entry/{entry_id}/")


@st.cache_data(ttl=300, show_spinner=False)
def get_manager_history(entry_id):
    return api_get(f"entry/{entry_id}/history/")


@st.cache_data(ttl=300, show_spinner=False)
def get_manager_transfers(entry_id):
    return api_get(f"entry/{entry_id}/transfers/")


@st.cache_data(ttl=300, show_spinner=False)
def get_manager_picks(entry_id, gameweek):
    return api_get(f"entry/{entry_id}/event/{gameweek}/picks/")


# =========================================================
# FORMATTERS
# =========================================================

def safe_number(value, fallback=0):
    if value is None:
        return fallback

    try:
        return int(value)
    except (TypeError, ValueError):
        return fallback


def format_rank(value):
    value = safe_number(value, 0)

    if value <= 0:
        return "Unavailable"

    return f"{value:,}"


def format_chip_name(chip_name):
    chip_names = {
        "wildcard": "Wildcard",
        "freehit": "Free Hit",
        "bboost": "Bench Boost",
        "3xc": "Triple Captain",
        "manager": "Assistant Manager",
    }

    return chip_names.get(
        chip_name,
        str(chip_name).replace("_", " ").title(),
    )


def get_status_information(player_data):
    """
    Return an icon and description for the player's availability.
    """

    status = player_data.get("status", "a")
    chance_next_round = player_data.get("chance_of_playing_next_round")
    news = player_data.get("news", "")

    status_details = {
        "a": ("", "Available"),
        "d": ("⚠️", "Doubtful"),
        "i": ("🚨", "Injured"),
        "s": ("🟥", "Suspended"),
        "u": ("⛔", "Unavailable"),
        "n": ("🚫", "Not available"),
    }

    icon, description = status_details.get(
        status,
        ("⚠️", "Availability concern"),
    )

    if chance_next_round is not None and status != "a":
        description = (
            f"{description}, {chance_next_round}% chance of playing"
        )

    if news:
        description = f"{description}: {news}"

    return icon, description


def get_club_style(team_name):
    primary, secondary = CLUB_COLOURS.get(
        team_name,
        ("#36454F", "#FFFFFF"),
    )

    return primary, secondary


def build_manager_options(standings_results):
    """
    Build unique dropdown labels so managers with the same name
    can still be selected separately.
    """

    options = {}

    sorted_results = sorted(
        standings_results,
        key=lambda row: safe_number(row.get("rank"), 999999),
    )

    for manager_row in sorted_results:
        manager_name = manager_row.get(
            "player_name",
            "Unknown Manager",
        )

        team_name = manager_row.get(
            "entry_name",
            "Unknown Team",
        )

        rank = manager_row.get("rank", "?")
        entry = manager_row.get("entry")

        label = (
            f"#{rank} | {manager_name} | "
            f"{team_name}"
        )

        options[label] = entry

    return options


# =========================================================
# PLAYER CARD HTML
# =========================================================

def build_player_card(
    pick,
    player_data,
    team_data,
    display_mode,
    is_bench=False,
):
    """
    Build one compact player card.

    All HTML is returned on one continuous structure so Streamlit
    does not display HTML tags as text.
    """

    player_name = html.escape(
        str(player_data.get("web_name", "Unknown"))
    )

    team_name = html.escape(
        str(team_data.get("name", "Unknown Club"))
    )

    primary_colour, secondary_colour = get_club_style(
        team_data.get("name", "")
    )

    status_icon, status_description = get_status_information(
        player_data
    )

    escaped_status = html.escape(status_description)

    is_captain = bool(pick.get("is_captain", False))
    is_vice = bool(pick.get("is_vice_captain", False))

    multiplier = safe_number(pick.get("multiplier"), 0)

    if display_mode == "Gameweek Points":
        gameweek_points = safe_number(
            player_data.get("event_points"),
            0,
        )

        displayed_points = gameweek_points * max(multiplier, 1)

        if is_captain and multiplier > 1:
            stat_text = (
                f"{gameweek_points} × {multiplier} "
                f"= {displayed_points} pts"
            )
        else:
            stat_text = f"{gameweek_points} pts"

    elif display_mode == "Price":
        player_price = (
            safe_number(player_data.get("now_cost"), 0) / 10
        )

        stat_text = f"£{player_price:.1f}m"

    elif display_mode == "Ownership":
        ownership = player_data.get(
            "selected_by_percent",
            "0",
        )

        stat_text = f"{ownership}% owned"

    else:
        season_points = safe_number(
            player_data.get("total_points"),
            0,
        )

        stat_text = f"{season_points} total pts"

    if is_captain:
        border_colour = "#FFD700"
        border_width = "4px"
        captain_badge = "C"
        badge_background = "#FFD700"
        badge_text_colour = "#111111"

    elif is_vice:
        border_colour = "#27A9FF"
        border_width = "4px"
        captain_badge = "V"
        badge_background = "#27A9FF"
        badge_text_colour = "#FFFFFF"

    elif player_data.get("status", "a") != "a":
        border_colour = "#FF4B4B"
        border_width = "3px"
        captain_badge = ""
        badge_background = "transparent"
        badge_text_colour = "#FFFFFF"

    else:
        border_colour = secondary_colour
        border_width = "2px"
        captain_badge = ""
        badge_background = "transparent"
        badge_text_colour = "#FFFFFF"

    bench_text = "BENCH" if is_bench else ""

    badge_html = ""

    if captain_badge:
        badge_html = (
            f'<span class="captain-badge" '
            f'style="background:{badge_background};'
            f'color:{badge_text_colour};">'
            f'{captain_badge}</span>'
        )

    injury_html = ""

    if status_icon:
        injury_html = (
            f'<span class="status-badge" '
            f'title="{escaped_status}">'
            f'{status_icon}</span>'
        )

    bench_html = ""

    if bench_text:
        bench_html = (
            '<div class="bench-label">BENCH</div>'
        )

    return (
        f'<div class="fpl-player-card" '
        f'style="background:linear-gradient(145deg,'
        f'{primary_colour} 0%,{primary_colour} 70%,'
        f'{secondary_colour} 170%);'
        f'border:{border_width} solid {border_colour};">'
        f'{bench_html}'
        f'<div class="card-badges">'
        f'{injury_html}{badge_html}'
        f'</div>'
        f'<div class="club-strip" '
        f'style="background:{secondary_colour};"></div>'
        f'<div class="player-name">{player_name}</div>'
        f'<div class="player-stat">{html.escape(stat_text)}</div>'
        f'<div class="club-name">{team_name}</div>'
        f'</div>'
    )


def build_pitch_row(
    position_title,
    players_in_position,
    players_lookup,
    teams_lookup,
    display_mode,
):
    cards = []

    for pick in players_in_position:
        player_data = players_lookup.get(
            pick.get("element"),
            {},
        )

        team_data = teams_lookup.get(
            player_data.get("team"),
            {},
        )

        cards.append(
            build_player_card(
                pick=pick,
                player_data=player_data,
                team_data=team_data,
                display_mode=display_mode,
                is_bench=False,
            )
        )

    cards_html = "".join(cards)

    return (
        '<div class="pitch-position-row">'
        f'<div class="position-label">{position_title}</div>'
        '<div class="player-row">'
        f'{cards_html}'
        '</div>'
        '</div>'
    )


def build_pitch_html(
    goalkeepers,
    defenders,
    midfielders,
    forwards,
    players_lookup,
    teams_lookup,
    display_mode,
):
    """
    Render the complete pitch in a single HTML block.

    This is the key fix. The green pitch remains behind the cards
    because Streamlit is not asked to place st.columns inside a
    separate HTML container.
    """

    goalkeeper_row = build_pitch_row(
        "GOALKEEPER",
        goalkeepers,
        players_lookup,
        teams_lookup,
        display_mode,
    )

    defender_row = build_pitch_row(
        "DEFENCE",
        defenders,
        players_lookup,
        teams_lookup,
        display_mode,
    )

    midfielder_row = build_pitch_row(
        "MIDFIELD",
        midfielders,
        players_lookup,
        teams_lookup,
        display_mode,
    )

    forward_row = build_pitch_row(
        "FORWARDS",
        forwards,
        players_lookup,
        teams_lookup,
        display_mode,
    )

    return f"""
    <style>
    .fpl-pitch {{
        position: relative;
        overflow: hidden;
        background:
            repeating-linear-gradient(
                90deg,
                rgba(255,255,255,0.03) 0px,
                rgba(255,255,255,0.03) 90px,
                rgba(0,0,0,0.035) 90px,
                rgba(0,0,0,0.035) 180px
            ),
            linear-gradient(180deg, #0ba74f 0%, #078a42 100%);
        border: 3px solid rgba(255,255,255,0.92);
        border-radius: 22px;
        padding: 18px 14px;
        box-shadow: inset 0 0 28px rgba(0,0,0,0.20);
    }}

    .fpl-pitch::before {{
        content: "";
        position: absolute;
        left: 50%;
        top: 0;
        bottom: 0;
        width: 2px;
        background: rgba(255,255,255,0.35);
        transform: translateX(-50%);
        pointer-events: none;
    }}

    .fpl-pitch::after {{
        content: "";
        position: absolute;
        left: 50%;
        top: 50%;
        width: 120px;
        height: 120px;
        border: 2px solid rgba(255,255,255,0.35);
        border-radius: 50%;
        transform: translate(-50%, -50%);
        pointer-events: none;
    }}

    .pitch-position-row {{
        position: relative;
        z-index: 2;
        margin-bottom: 13px;
    }}

    .pitch-position-row:last-child {{
        margin-bottom: 0;
    }}

    .position-label {{
        text-align: center;
        color: rgba(255,255,255,0.88);
        font-size: 0.68rem;
        font-weight: 800;
        letter-spacing: 0.12rem;
        margin-bottom: 5px;
        text-shadow: 0 1px 3px rgba(0,0,0,0.45);
    }}

    .player-row {{
        display: flex;
        justify-content: center;
        align-items: stretch;
        gap: 10px;
        width: 100%;
    }}

    .fpl-player-card {{
        position: relative;
        box-sizing: border-box;
        width: clamp(105px, 15vw, 155px);
        min-height: 80px;
        border-radius: 11px;
        padding: 13px 6px 7px 6px;
        text-align: center;
        color: #ffffff;
        box-shadow: 0 4px 9px rgba(0,0,0,0.32);
        overflow: hidden;
    }}

    .club-strip {{
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 7px;
        opacity: 0.95;
    }}

    .card-badges {{
        position: absolute;
        top: 8px;
        right: 5px;
        display: flex;
        gap: 3px;
        align-items: center;
    }}

    .captain-badge {{
        display: inline-flex;
        width: 19px;
        height: 19px;
        border-radius: 50%;
        align-items: center;
        justify-content: center;
        font-size: 0.68rem;
        font-weight: 900;
        box-shadow: 0 1px 4px rgba(0,0,0,0.35);
    }}

    .status-badge {{
        font-size: 0.82rem;
        line-height: 1;
        cursor: help;
    }}

    .player-name {{
        margin-top: 4px;
        font-size: 0.88rem;
        line-height: 1.1;
        font-weight: 850;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        text-shadow: 0 1px 3px rgba(0,0,0,0.75);
    }}

    .player-stat {{
        display: inline-block;
        margin-top: 6px;
        background: rgba(0,0,0,0.36);
        border-radius: 7px;
        padding: 3px 7px;
        font-size: 0.72rem;
        font-weight: 750;
    }}

    .club-name {{
        margin-top: 4px;
        font-size: 0.58rem;
        opacity: 0.87;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }}

    .bench-label {{
        position: absolute;
        top: 7px;
        left: 5px;
        background: rgba(0,0,0,0.50);
        border-radius: 4px;
        padding: 2px 4px;
        font-size: 0.48rem;
        font-weight: 800;
        letter-spacing: 0.04rem;
    }}

    @media (max-width: 800px) {{
        .fpl-pitch {{
            padding: 13px 5px;
        }}

        .player-row {{
            gap: 4px;
        }}

        .fpl-player-card {{
            width: clamp(60px, 18vw, 105px);
            min-height: 72px;
            padding: 12px 3px 5px 3px;
            border-radius: 8px;
        }}

        .player-name {{
            font-size: 0.68rem;
        }}

        .player-stat {{
            font-size: 0.58rem;
            padding: 2px 4px;
        }}

        .club-name {{
            display: none;
        }}

        .captain-badge {{
            width: 16px;
            height: 16px;
            font-size: 0.56rem;
        }}

        .position-label {{
            font-size: 0.55rem;
            margin-bottom: 3px;
        }}
    }}
    </style>

    <div class="fpl-pitch">
        {goalkeeper_row}
        {defender_row}
        {midfielder_row}
        {forward_row}
    </div>
    """


def build_bench_html(
    bench,
    players_lookup,
    teams_lookup,
    display_mode,
):
    cards = []

    for pick in bench:
        player_data = players_lookup.get(
            pick.get("element"),
            {},
        )

        team_data = teams_lookup.get(
            player_data.get("team"),
            {},
        )

        cards.append(
            build_player_card(
                pick=pick,
                player_data=player_data,
                team_data=team_data,
                display_mode=display_mode,
                is_bench=True,
            )
        )

    cards_html = "".join(cards)

    return f"""
    <style>
    .bench-area {{
        background: linear-gradient(135deg, #202733, #12171f);
        border: 1px solid #394150;
        border-radius: 16px;
        padding: 15px 10px;
        margin-top: 10px;
    }}

    .bench-row {{
        display: flex;
        justify-content: center;
        gap: 12px;
        flex-wrap: wrap;
    }}

    @media (max-width: 700px) {{
        .bench-row {{
            gap: 6px;
        }}
    }}
    </style>

    <div class="bench-area">
        <div class="bench-row">
            {cards_html}
        </div>
    </div>
    """


# =========================================================
# MAIN PAGE
# =========================================================

try:
    if not str(league_id).strip().isdigit():
        st.error("The League ID must contain numbers only.")
        st.stop()

    if not str(your_entry_id).strip().isdigit():
        st.warning(
            "Your Entry ID should contain numbers only. "
            "This does not prevent rival viewing."
        )

    with st.spinner("Loading FPL league and player data..."):
        bootstrap_data = get_bootstrap_data()
        league = get_league_data(str(league_id).strip())

    players_lookup = {
        player["id"]: player
        for player in bootstrap_data.get("elements", [])
    }

    teams_lookup = {
        team["id"]: team
        for team in bootstrap_data.get("teams", [])
    }

    events = bootstrap_data.get("events", [])
    standings_results = league.get("results", [])

    if not standings_results:
        st.error(
            "No managers were found. Check that the mini-league "
            "ID is correct and that the league is publicly accessible."
        )
        st.stop()

    league_name = league.get(
        "league",
        {},
    ).get(
        "name",
        "FPL Mini-League",
    )

    manager_options = build_manager_options(
        standings_results
    )

    selected_label = st.selectbox(
        "Select a rival manager",
        options=list(manager_options.keys()),
    )

    selected_entry_id = manager_options[selected_label]

    selected_standing = next(
        (
            row
            for row in standings_results
            if row.get("entry") == selected_entry_id
        ),
        {},
    )

    with st.spinner("Loading the selected manager..."):
        manager = get_manager_data(selected_entry_id)
        history = get_manager_history(selected_entry_id)
        transfers = get_manager_transfers(selected_entry_id)

    manager_history_rows = history.get("current", [])

    if not manager_history_rows:
        st.warning(
            "No completed gameweeks are available for this manager."
        )
        st.stop()

    available_gameweeks = [
        safe_number(row.get("event"))
        for row in manager_history_rows
        if safe_number(row.get("event")) > 0
    ]

    latest_available_gameweek = max(available_gameweeks)

    header_left, header_right = st.columns([3, 1])

    with header_left:
        st.markdown(
            f"""
            <div class="rival-heading">
                <h3>{html.escape(manager.get("name", "Unknown Team"))}</h3>
                <p>
                    {html.escape(selected_standing.get("player_name", "Unknown Manager"))}
                    · {html.escape(league_name)}
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with header_right:
        selected_gameweek = st.selectbox(
            "Gameweek",
            options=sorted(
                available_gameweeks,
                reverse=True,
            ),
            index=0,
            format_func=lambda value: f"Gameweek {value}",
        )

    selected_history = next(
        (
            row
            for row in manager_history_rows
            if safe_number(row.get("event")) == selected_gameweek
        ),
        manager_history_rows[-1],
    )

    with st.spinner(
        f"Loading Gameweek {selected_gameweek} squad..."
    ):
        squad_data = get_manager_picks(
            selected_entry_id,
            selected_gameweek,
        )

    picks = squad_data.get("picks", [])

    if not picks:
        st.warning(
            f"No public squad is available for Gameweek "
            f"{selected_gameweek}."
        )
        st.stop()

    display_mode = st.radio(
        "Player card display",
        options=[
            "Gameweek Points",
            "Price",
            "Ownership",
            "Season Points",
        ],
        horizontal=True,
    )

    gameweek_points = safe_number(
        selected_history.get("points"),
        0,
    )

    gameweek_rank = safe_number(
        selected_history.get("rank"),
        0,
    )

    overall_points = safe_number(
        selected_history.get("total_points"),
        manager.get("summary_overall_points", 0),
    )

    overall_rank = safe_number(
        selected_history.get("overall_rank"),
        manager.get("summary_overall_rank", 0),
    )

    team_value = (
        safe_number(
            selected_history.get(
                "value",
                manager.get("last_deadline_value", 0),
            ),
            0,
        )
        / 10
    )

    bank = (
        safe_number(
            selected_history.get(
                "bank",
                manager.get("last_deadline_bank", 0),
            ),
            0,
        )
        / 10
    )

    transfers_this_week = safe_number(
        selected_history.get("event_transfers"),
        0,
    )

    transfer_cost = safe_number(
        selected_history.get("event_transfers_cost"),
        0,
    )

    metric_1, metric_2, metric_3 = st.columns(3)
    metric_4, metric_5, metric_6 = st.columns(3)

    metric_1.metric(
        f"GW{selected_gameweek} Points",
        gameweek_points,
    )

    metric_2.metric(
        "Total Points",
        overall_points,
    )

    metric_3.metric(
        "Overall Rank",
        format_rank(overall_rank),
    )

    metric_4.metric(
        "Squad Value",
        f"£{team_value:.1f}m",
    )

    metric_5.metric(
        "Money in Bank",
        f"£{bank:.1f}m",
    )

    metric_6.metric(
        "GW Transfers",
        transfers_this_week,
        delta=(
            f"-{transfer_cost} points"
            if transfer_cost > 0
            else "No hit"
        ),
        delta_color=(
            "inverse"
            if transfer_cost > 0
            else "normal"
        ),
    )

    starters = [
        pick
        for pick in picks
        if safe_number(pick.get("position")) <= 11
    ]

    bench = [
        pick
        for pick in picks
        if safe_number(pick.get("position")) > 11
    ]

    goalkeepers = [
        pick
        for pick in starters
        if players_lookup.get(
            pick.get("element"),
            {},
        ).get("element_type") == 1
    ]

    defenders = [
        pick
        for pick in starters
        if players_lookup.get(
            pick.get("element"),
            {},
        ).get("element_type") == 2
    ]

    midfielders = [
        pick
        for pick in starters
        if players_lookup.get(
            pick.get("element"),
            {},
        ).get("element_type") == 3
    ]

    forwards = [
        pick
        for pick in starters
        if players_lookup.get(
            pick.get("element"),
            {},
        ).get("element_type") == 4
    ]

    formation = (
        f"{len(defenders)}-"
        f"{len(midfielders)}-"
        f"{len(forwards)}"
    )

    st.markdown(
        f"""
        <div class="legend-wrap">
            <div class="legend-item">
                📋 Formation: <strong>{formation}</strong>
            </div>
            <div class="legend-item">
                🟡 Gold border: Captain
            </div>
            <div class="legend-item">
                🔵 Blue border: Vice-captain
            </div>
            <div class="legend-item">
                🚨 Availability concern
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    pitch_tab, transfers_tab, chips_tab, report_tab = st.tabs(
        [
            "⚽ Pitch",
            "🔄 Transfers",
            "🎲 Chips",
            "🤖 Scout Report",
        ]
    )

    # =====================================================
    # PITCH TAB
    # =====================================================

    with pitch_tab:
        pitch_html = build_pitch_html(
            goalkeepers=goalkeepers,
            defenders=defenders,
            midfielders=midfielders,
            forwards=forwards,
            players_lookup=players_lookup,
            teams_lookup=teams_lookup,
            display_mode=display_mode,
        )

        st.markdown(
            pitch_html,
            unsafe_allow_html=True,
        )

        st.subheader("🪑 Bench")

        bench_html = build_bench_html(
            bench=bench,
            players_lookup=players_lookup,
            teams_lookup=teams_lookup,
            display_mode=display_mode,
        )

        st.markdown(
            bench_html,
            unsafe_allow_html=True,
        )

        unavailable_players = []

        for pick in picks:
            player_data = players_lookup.get(
                pick.get("element"),
                {},
            )

            if player_data.get("status", "a") != "a":
                status_icon, status_description = (
                    get_status_information(player_data)
                )

                unavailable_players.append(
                    {
                        "Player": player_data.get(
                            "web_name",
                            "Unknown",
                        ),
                        "Status": (
                            f"{status_icon} "
                            f"{status_description}"
                        ),
                    }
                )

        if unavailable_players:
            with st.expander(
                "🚨 View player availability concerns"
            ):
                st.dataframe(
                    pd.DataFrame(unavailable_players),
                    hide_index=True,
                    use_container_width=True,
                )

    # =====================================================
    # TRANSFERS TAB
    # =====================================================

    with transfers_tab:
        st.subheader("🔄 Transfer History")

        if transfers:
            transfer_rows = []

            sorted_transfers = sorted(
                transfers,
                key=lambda record: record.get("time", ""),
                reverse=True,
            )

            for transfer in sorted_transfers:
                player_in = players_lookup.get(
                    transfer.get("element_in"),
                    {},
                )

                player_out = players_lookup.get(
                    transfer.get("element_out"),
                    {},
                )

                time_text = transfer.get("time", "")

                try:
                    formatted_time = datetime.fromisoformat(
                        time_text.replace("Z", "+00:00")
                    ).strftime("%d %b %Y, %H:%M")
                except (TypeError, ValueError):
                    formatted_time = time_text

                transfer_rows.append(
                    {
                        "GW": transfer.get("event"),
                        "Player In": player_in.get(
                            "web_name",
                            "Unknown",
                        ),
                        "In Price": (
                            f"£{safe_number(transfer.get('element_in_cost')) / 10:.1f}m"
                        ),
                        "Player Out": player_out.get(
                            "web_name",
                            "Unknown",
                        ),
                        "Out Price": (
                            f"£{safe_number(transfer.get('element_out_cost')) / 10:.1f}m"
                        ),
                        "Date": formatted_time,
                    }
                )

            transfer_dataframe = pd.DataFrame(
                transfer_rows
            )

            current_gameweek_transfers = transfer_dataframe[
                transfer_dataframe["GW"] == selected_gameweek
            ]

            transfer_metric_1, transfer_metric_2 = st.columns(2)

            transfer_metric_1.metric(
                f"GW{selected_gameweek} Transfers",
                len(current_gameweek_transfers),
            )

            transfer_metric_2.metric(
                "Season Transfers Recorded",
                len(transfer_dataframe),
            )

            gameweek_only = st.toggle(
                f"Show only Gameweek {selected_gameweek}",
                value=False,
            )

            if gameweek_only:
                displayed_transfers = current_gameweek_transfers
            else:
                displayed_transfers = transfer_dataframe

            if displayed_transfers.empty:
                st.info(
                    f"No transfers were recorded for "
                    f"Gameweek {selected_gameweek}."
                )
            else:
                st.dataframe(
                    displayed_transfers,
                    hide_index=True,
                    use_container_width=True,
                )

        else:
            st.info(
                "No transfer history is currently available "
                "for this manager."
            )

    # =====================================================
    # CHIPS TAB
    # =====================================================

    with chips_tab:
        st.subheader("🎲 Chip Usage")

        chips = history.get("chips", [])

        if chips:
            chip_rows = []

            for chip in sorted(
                chips,
                key=lambda record: safe_number(
                    record.get("event")
                ),
            ):
                chip_rows.append(
                    {
                        "Chip": format_chip_name(
                            chip.get("name", "")
                        ),
                        "Gameweek": chip.get("event"),
                    }
                )

            st.dataframe(
                pd.DataFrame(chip_rows),
                hide_index=True,
                use_container_width=True,
            )

            st.metric(
                "Chips Used",
                len(chip_rows),
            )

        else:
            st.info(
                "This manager has no recorded chip usage yet."
            )

        st.caption(
            "Only chips already made public by FPL are shown."
        )

    # =====================================================
    # SCOUT REPORT TAB
    # =====================================================

    with report_tab:
        captain_pick = next(
            (
                pick
                for pick in picks
                if pick.get("is_captain")
            ),
            None,
        )

        vice_pick = next(
            (
                pick
                for pick in picks
                if pick.get("is_vice_captain")
            ),
            None,
        )

        captain_name = "Unknown"

        if captain_pick:
            captain_name = players_lookup.get(
                captain_pick.get("element"),
                {},
            ).get(
                "web_name",
                "Unknown",
            )

        vice_name = "Unknown"

        if vice_pick:
            vice_name = players_lookup.get(
                vice_pick.get("element"),
                {},
            ).get(
                "web_name",
                "Unknown",
            )

        chip_used_this_week = next(
            (
                format_chip_name(chip.get("name"))
                for chip in history.get("chips", [])
                if safe_number(chip.get("event"))
                == selected_gameweek
            ),
            "No chip",
        )

        report_manager = selected_standing.get(
            "player_name",
            "The selected manager",
        )

        st.info(
            f"""
**{report_manager} scouting summary**

🏆 **Gameweek score:** {gameweek_points} points

📊 **Gameweek rank:** {format_rank(gameweek_rank)}

🌍 **Overall rank:** {format_rank(overall_rank)}

🧢 **Captain:** {captain_name}

🔵 **Vice-captain:** {vice_name}

📋 **Formation:** {formation}

🔄 **Transfers this gameweek:** {transfers_this_week}

💥 **Transfer cost:** {transfer_cost} points

🎲 **Chip:** {chip_used_this_week}

💰 **Squad value:** £{team_value:.1f}m with £{bank:.1f}m in the bank
"""
        )

except requests.exceptions.HTTPError as error:
    status_code = getattr(
        error.response,
        "status_code",
        "Unknown",
    )

    st.error(
        f"The FPL API returned an error "
        f"(status code {status_code}). "
        f"Check the league ID or try refreshing later."
    )

except requests.exceptions.Timeout:
    st.error(
        "The FPL API took too long to respond. "
        "Please use the refresh button and try again."
    )

except requests.exceptions.ConnectionError:
    st.error(
        "The app could not connect to the FPL API. "
        "Please check the Streamlit logs or try again later."
    )

except (KeyError, IndexError, TypeError, ValueError) as error:
    st.error(
        "Some FPL data was missing or had an unexpected format."
    )

    with st.expander("Technical error details"):
        st.code(str(error))

except Exception as error:
    st.error(
        "An unexpected error occurred while loading "
        "the Rival Viewer."
    )

    with st.expander("Technical error details"):
        st.code(str(error))
