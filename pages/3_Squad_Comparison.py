import html
from datetime import datetime

import pandas as pd
import requests
import streamlit as st


# =========================================================
# DEFAULT SETTINGS
# =========================================================

DEFAULT_LEAGUE_ID = "1116047"
DEFAULT_ENTRY_ID = "6074290"

BASE_URL = "https://fantasy.premierleague.com/api"

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json",
}


# =========================================================
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="Squad Comparison",
    page_icon="⚔️",
    layout="wide",
)


# =========================================================
# PAGE STYLING
# =========================================================

st.markdown(
    """
<style>
.block-container {
    padding-top: 1.3rem;
    padding-bottom: 3rem;
}

.hero {
    background:
        radial-gradient(
            circle at top right,
            rgba(0, 255, 135, 0.18),
            transparent 35%
        ),
        linear-gradient(
            135deg,
            #17212b,
            #202b3b 55%,
            #111820
        );
    border: 1px solid #303b4d;
    border-radius: 20px;
    padding: 24px;
    margin-bottom: 18px;
}

.hero h1 {
    margin: 0;
    color: #ffffff;
    font-size: 2rem;
}

.hero p {
    margin: 7px 0 0;
    color: #b7c0cc;
}

.team-banner {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 14px;
    padding: 14px;
    margin-bottom: 10px;
}

.team-banner h3 {
    margin: 0;
    color: #ffffff;
}

.team-banner p {
    margin: 4px 0 0;
    color: #9ba7b4;
    font-size: 0.85rem;
}

.pitch {
    position: relative;
    overflow: hidden;
    background:
        repeating-linear-gradient(
            90deg,
            rgba(255, 255, 255, 0.025) 0,
            rgba(255, 255, 255, 0.025) 70px,
            rgba(0, 0, 0, 0.03) 70px,
            rgba(0, 0, 0, 0.03) 140px
        ),
        linear-gradient(
            180deg,
            #0ba74f,
            #078a42
        );
    border: 2px solid rgba(255, 255, 255, 0.8);
    border-radius: 18px;
    padding: 12px 6px;
    min-height: 540px;
}

.pitch::before {
    content: "";
    position: absolute;
    left: 0;
    right: 0;
    top: 50%;
    height: 2px;
    background: rgba(255, 255, 255, 0.28);
}

.pitch-row {
    position: relative;
    z-index: 2;
    margin-bottom: 13px;
}

.position-title {
    text-align: center;
    color: rgba(255, 255, 255, 0.82);
    font-size: 0.58rem;
    font-weight: 800;
    letter-spacing: 0.08rem;
    margin-bottom: 4px;
}

.players {
    display: flex;
    justify-content: center;
    gap: 5px;
    align-items: stretch;
}

.player-card {
    position: relative;
    width: clamp(62px, 7.4vw, 112px);
    min-height: 70px;
    border-radius: 9px;
    padding: 12px 3px 5px;
    text-align: center;
    color: #ffffff;
    box-shadow: 0 3px 7px rgba(0, 0, 0, 0.3);
    overflow: hidden;
}

.player-name {
    font-size: 0.70rem;
    font-weight: 850;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    text-shadow: 0 1px 3px rgba(0, 0, 0, 0.8);
}

.player-stat {
    display: inline-block;
    margin-top: 5px;
    background: rgba(0, 0, 0, 0.38);
    border-radius: 5px;
    padding: 2px 4px;
    font-size: 0.57rem;
}

.club-name {
    font-size: 0.48rem;
    opacity: 0.8;
    margin-top: 3px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.badge {
    position: absolute;
    top: 4px;
    right: 4px;
    border-radius: 50%;
    width: 17px;
    height: 17px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.58rem;
    font-weight: 900;
}

.status {
    position: absolute;
    top: 4px;
    left: 4px;
    font-size: 0.7rem;
}

.bench {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 12px;
    padding: 10px;
    margin-top: 8px;
}

.bench-row {
    display: flex;
    justify-content: center;
    gap: 6px;
    flex-wrap: wrap;
}

div[data-testid="stMetric"] {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 13px;
    padding: 12px;
}

div.stButton > button {
    border-radius: 9px;
    font-weight: 750;
}

@media (max-width: 800px) {
    .hero {
        padding: 17px;
    }

    .hero h1 {
        font-size: 1.5rem;
    }

    .pitch {
        min-height: 470px;
    }

    .players {
        gap: 2px;
    }

    .player-card {
        width: clamp(48px, 14vw, 77px);
        min-height: 64px;
    }

    .player-name {
        font-size: 0.58rem;
    }

    .club-name {
        display: none;
    }
}
</style>
""",
    unsafe_allow_html=True,
)


# =========================================================
# SIDEBAR
# =========================================================

st.sidebar.header("⚙️ Site Settings")

league_id = st.sidebar.text_input(
    "Mini-League ID",
    value=DEFAULT_LEAGUE_ID,
)

entry_id = st.sidebar.text_input(
    "Your FPL Entry ID",
    value=DEFAULT_ENTRY_ID,
)

if st.sidebar.button(
    "🔄 Refresh Comparison Data",
    width="stretch",
):
    st.cache_data.clear()
    st.rerun()

st.sidebar.caption(
    "Comparison data is cached for five minutes."
)


# =========================================================
# API FUNCTIONS
# =========================================================

def api_get(endpoint, timeout=20):
    url = f"{BASE_URL}/{endpoint.lstrip('/')}"

    response = requests.get(
        url,
        headers=HEADERS,
        timeout=timeout,
    )

    response.raise_for_status()

    return response.json()


@st.cache_data(
    ttl=21600,
    show_spinner=False,
)
def get_bootstrap():
    return api_get(
        "bootstrap-static/"
    )


@st.cache_data(
    ttl=300,
    show_spinner=False,
)
def get_entry(entry):
    return api_get(
        f"entry/{entry}/"
    )


@st.cache_data(
    ttl=300,
    show_spinner=False,
)
def get_history(entry):
    return api_get(
        f"entry/{entry}/history/"
    )


@st.cache_data(
    ttl=300,
    show_spinner=False,
)
def get_transfers(entry):
    return api_get(
        f"entry/{entry}/transfers/"
    )


@st.cache_data(
    ttl=300,
    show_spinner=False,
)
def get_picks(entry, gameweek):
    return api_get(
        f"entry/{entry}/event/{gameweek}/picks/"
    )


@st.cache_data(
    ttl=300,
    show_spinner=False,
)
def get_live(gameweek):
    return api_get(
        f"event/{gameweek}/live/"
    )


@st.cache_data(
    ttl=300,
    show_spinner=False,
)
def get_league(league):
    results = []
    league_info = {}
    page = 1

    while True:
        data = api_get(
            f"leagues-classic/{league}/standings/"
            f"?page_standings={page}"
        )

        if not league_info:
            league_info = data.get(
                "league",
                {},
            )

        standings = data.get(
            "standings",
            {},
        )

        results.extend(
            standings.get(
                "results",
                [],
            )
        )

        if (
            not standings.get("has_next", False)
            or page >= 25
        ):
            break

        page += 1

    return league_info, results


# =========================================================
# HELPER FUNCTIONS
# =========================================================

def safe_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def format_rank(value):
    rank = safe_int(value)

    if rank > 0:
        return f"{rank:,}"

    return "Unavailable"


def chip_name(value):
    chip_names = {
        "wildcard": "Wildcard",
        "freehit": "Free Hit",
        "bboost": "Bench Boost",
        "3xc": "Triple Captain",
        "manager": "Assistant Manager",
    }

    return chip_names.get(
        value,
        str(value).replace(
            "_",
            " ",
        ).title(),
    )


def status_details(player):
    status = player.get(
        "status",
        "a",
    )

    details = {
        "a": (
            "",
            "Available",
        ),
        "d": (
            "⚠️",
            "Doubtful",
        ),
        "i": (
            "🚨",
            "Injured",
        ),
        "s": (
            "🟥",
            "Suspended",
        ),
        "u": (
            "⛔",
            "Unavailable",
        ),
        "n": (
            "🚫",
            "Not available",
        ),
    }

    icon, status_text = details.get(
        status,
        (
            "⚠️",
            "Availability concern",
        ),
    )

    chance = player.get(
        "chance_of_playing_next_round"
    )

    if (
        chance is not None
        and status != "a"
    ):
        status_text = (
            f"{status_text}, "
            f"{chance}% chance of playing"
        )

    return icon, status_text


def club_colours(team_name):
    colours = {
        "Arsenal": (
            "#EF0107",
            "#FFFFFF",
        ),
        "Aston Villa": (
            "#670E36",
            "#95BFE5",
        ),
        "Bournemouth": (
            "#DA291C",
            "#000000",
        ),
        "Brentford": (
            "#E30613",
            "#FFFFFF",
        ),
        "Brighton": (
            "#0057B8",
            "#FFFFFF",
        ),
        "Burnley": (
            "#6C1D45",
            "#99D6EA",
        ),
        "Chelsea": (
            "#034694",
            "#FFFFFF",
        ),
        "Crystal Palace": (
            "#1B458F",
            "#C4122E",
        ),
        "Everton": (
            "#003399",
            "#FFFFFF",
        ),
        "Fulham": (
            "#FFFFFF",
            "#000000",
        ),
        "Leeds": (
            "#FFFFFF",
            "#1D428A",
        ),
        "Liverpool": (
            "#C8102E",
            "#FFFFFF",
        ),
        "Man City": (
            "#6CABDD",
            "#1C2C5B",
        ),
        "Man Utd": (
            "#DA291C",
            "#FBE122",
        ),
        "Newcastle": (
            "#241F20",
            "#FFFFFF",
        ),
        "Nott'm Forest": (
            "#DD0000",
            "#FFFFFF",
        ),
        "Southampton": (
            "#D71920",
            "#FFFFFF",
        ),
        "Sunderland": (
            "#EB172B",
            "#FFFFFF",
        ),
        "Spurs": (
            "#132257",
            "#FFFFFF",
        ),
        "West Ham": (
            "#7A263A",
            "#1BB1E7",
        ),
        "Wolves": (
            "#FDB913",
            "#231F20",
        ),
    }

    return colours.get(
        team_name,
        (
            "#36454F",
            "#FFFFFF",
        ),
    )


def get_history_row(history, gameweek):
    return next(
        (
            row
            for row in history.get(
                "current",
                [],
            )
            if safe_int(
                row.get("event")
            ) == gameweek
        ),
        {},
    )


def selected_chip(history, gameweek):
    chip = next(
        (
            item
            for item in history.get(
                "chips",
                [],
            )
            if safe_int(
                item.get("event")
            ) == gameweek
        ),
        None,
    )

    if chip:
        return chip_name(
            chip.get("name")
        )

    return "No chip"


def pick_points(pick, live_lookup):
    player_live_data = live_lookup.get(
        pick.get("element"),
        {},
    )

    player_stats = player_live_data.get(
        "stats",
        {},
    )

    raw_points = safe_int(
        player_stats.get(
            "total_points"
        )
    )

    multiplier = safe_int(
        pick.get("multiplier")
    )

    return raw_points * multiplier


def raw_player_points(
    player_id,
    live_lookup,
):
    player_live_data = live_lookup.get(
        player_id,
        {},
    )

    player_stats = player_live_data.get(
        "stats",
        {},
    )

    return safe_int(
        player_stats.get(
            "total_points"
        )
    )


def player_stat(
    player,
    pick,
    display_mode,
    live_lookup,
):
    if display_mode == "GW Points":
        raw_points = raw_player_points(
            pick.get("element"),
            live_lookup,
        )

        multiplier = safe_int(
            pick.get("multiplier")
        )

        effective_points = (
            raw_points * multiplier
        )

        if multiplier > 1:
            return (
                f"{raw_points} x {multiplier} "
                f"= {effective_points}"
            )

        return f"{raw_points} pts"

    if display_mode == "Price":
        price = (
            safe_int(
                player.get("now_cost")
            )
            / 10
        )

        return f"£{price:.1f}m"

    if display_mode == "Ownership":
        ownership = player.get(
            "selected_by_percent",
            "0",
        )

        return f"{ownership}%"

    season_points = safe_int(
        player.get("total_points")
    )

    return f"{season_points} total"


def player_card(
    pick,
    players,
    teams,
    display_mode,
    live_lookup,
    comparison,
    is_bench=False,
):
    player = players.get(
        pick.get("element"),
        {},
    )

    team = teams.get(
        player.get("team"),
        {},
    )

    team_name = team.get(
        "name",
        "Unknown",
    )

    primary_colour, secondary_colour = (
        club_colours(team_name)
    )

    status_icon, status_text = (
        status_details(player)
    )

    player_id = pick.get("element")

    ownership_type = comparison.get(
        player_id,
        "shared",
    )

    if pick.get("is_captain"):
        border_colour = "#FFD700"
        badge = "C"
        badge_background = "#FFD700"
        badge_colour = "#111111"

    elif pick.get("is_vice_captain"):
        border_colour = "#27A9FF"
        badge = "V"
        badge_background = "#27A9FF"
        badge_colour = "#FFFFFF"

    elif ownership_type == "mine":
        border_colour = "#00FF87"
        badge = "Y"
        badge_background = "#00FF87"
        badge_colour = "#111111"

    elif ownership_type == "rival":
        border_colour = "#FF6078"
        badge = "R"
        badge_background = "#FF6078"
        badge_colour = "#FFFFFF"

    else:
        border_colour = secondary_colour
        badge = ""
        badge_background = "transparent"
        badge_colour = "#FFFFFF"

    if badge:
        badge_html = (
            f'<span class="badge" '
            f'style="background:{badge_background};'
            f'color:{badge_colour};">'
            f'{badge}'
            f'</span>'
        )
    else:
        badge_html = ""

    if status_icon:
        status_html = (
            f'<span class="status" '
            f'title="{html.escape(status_text)}">'
            f'{status_icon}'
            f'</span>'
        )
    else:
        status_html = ""

    if is_bench:
        bench_html = (
            '<span style="'
            'position:absolute;'
            'bottom:3px;'
            'left:4px;'
            'font-size:0.43rem;'
            'opacity:0.75;'
            '">BENCH</span>'
        )
    else:
        bench_html = ""

    player_name = html.escape(
        str(
            player.get(
                "web_name",
                "Unknown",
            )
        )
    )

    escaped_team_name = html.escape(
        str(team_name)
    )

    displayed_stat = html.escape(
        player_stat(
            player,
            pick,
            display_mode,
            live_lookup,
        )
    )

    return (
        f'<div class="player-card" '
        f'style="'
        f'background:linear-gradient('
        f'145deg,'
        f'{primary_colour} 0%,'
        f'{primary_colour} 70%,'
        f'{secondary_colour} 170%'
        f');'
        f'border:3px solid {border_colour};'
        f'">'
        f'{status_html}'
        f'{badge_html}'
        f'<div class="player-name">'
        f'{player_name}'
        f'</div>'
        f'<div class="player-stat">'
        f'{displayed_stat}'
        f'</div>'
        f'<div class="club-name">'
        f'{escaped_team_name}'
        f'</div>'
        f'{bench_html}'
        f'</div>'
    )


def pitch_html(
    picks,
    players,
    teams,
    display_mode,
    live_lookup,
    comparison,
):
    starters = [
        pick
        for pick in picks
        if safe_int(
            pick.get("position")
        ) <= 11
    ]

    bench = [
        pick
        for pick in picks
        if safe_int(
            pick.get("position")
        ) > 11
    ]

    groups = [
        (
            "GOALKEEPER",
            1,
        ),
        (
            "DEFENCE",
            2,
        ),
        (
            "MIDFIELD",
            3,
        ),
        (
            "FORWARDS",
            4,
        ),
    ]

    pitch_rows = []
    formation_parts = []

    for title, element_type in groups:
        group = [
            pick
            for pick in starters
            if players.get(
                pick.get("element"),
                {},
            ).get(
                "element_type"
            ) == element_type
        ]

        if element_type > 1:
            formation_parts.append(
                str(len(group))
            )

        cards = "".join(
            player_card(
                pick,
                players,
                teams,
                display_mode,
                live_lookup,
                comparison,
            )
            for pick in group
        )

        row_html = (
            f'<div class="pitch-row">'
            f'<div class="position-title">'
            f'{title}'
            f'</div>'
            f'<div class="players">'
            f'{cards}'
            f'</div>'
            f'</div>'
        )

        pitch_rows.append(
            row_html
        )

    bench_cards = "".join(
        player_card(
            pick,
            players,
            teams,
            display_mode,
            live_lookup,
            comparison,
            is_bench=True,
        )
        for pick in bench
    )

    complete_html = (
        f'<div class="pitch">'
        f'{"".join(pitch_rows)}'
        f'</div>'
        f'<div class="bench">'
        f'<div class="position-title">'
        f'BENCH'
        f'</div>'
        f'<div class="bench-row">'
        f'{bench_cards}'
        f'</div>'
        f'</div>'
    )

    formation = "-".join(
        formation_parts
    )

    return complete_html, formation


def transfer_rows(
    transfers,
    gameweek,
    players,
):
    rows = []

    for transfer in transfers:
        if safe_int(
            transfer.get("event")
        ) != gameweek:
            continue

        player_in = players.get(
            transfer.get("element_in"),
            {},
        ).get(
            "web_name",
            "Unknown",
        )

        player_out = players.get(
            transfer.get("element_out"),
            {},
        ).get(
            "web_name",
            "Unknown",
        )

        time_value = transfer.get(
            "time",
            "",
        )

        try:
            time_value = (
                datetime.fromisoformat(
                    time_value.replace(
                        "Z",
                        "+00:00",
                    )
                ).strftime(
                    "%d %b %Y, %H:%M"
                )
            )

        except (
            AttributeError,
            ValueError,
        ):
            pass

        rows.append(
            {
                "Player In": player_in,
                "Player Out": player_out,
                "In Price": (
                    f"£{safe_int(transfer.get('element_in_cost')) / 10:.1f}m"
                ),
                "Out Price": (
                    f"£{safe_int(transfer.get('element_out_cost')) / 10:.1f}m"
                ),
                "Date": time_value,
            }
        )

    return rows


# =========================================================
# MAIN PAGE
# =========================================================

try:
    if (
        not league_id.strip().isdigit()
        or not entry_id.strip().isdigit()
    ):
        st.error(
            "The League ID and Entry ID "
            "must contain numbers only."
        )

        st.stop()

    with st.spinner(
        "Loading league and player data..."
    ):
        bootstrap = get_bootstrap()

        league_info, league_results = (
            get_league(
                league_id.strip()
            )
        )

        my_entry = get_entry(
            entry_id.strip()
        )

        my_history = get_history(
            entry_id.strip()
        )

    players = {
        player["id"]: player
        for player in bootstrap.get(
            "elements",
            [],
        )
    }

    teams = {
        team["id"]: team
        for team in bootstrap.get(
            "teams",
            [],
        )
    }

    manager_options = {}

    sorted_managers = sorted(
        league_results,
        key=lambda item: safe_int(
            item.get("rank"),
            999999,
        ),
    )

    for manager in sorted_managers:
        manager_entry = safe_int(
            manager.get("entry")
        )

        if manager_entry == safe_int(
            entry_id
        ):
            continue

        option_label = (
            f"#{manager.get('rank', '?')} | "
            f"{manager.get('player_name', 'Unknown')} | "
            f"{manager.get('entry_name', 'Unknown Team')}"
        )

        manager_options[
            option_label
        ] = str(
            manager.get("entry")
        )

    if not manager_options:
        st.error(
            "No rival managers were found "
            "in this league."
        )

        st.stop()

    your_team_name = html.escape(
        str(
            my_entry.get(
                "name",
                "Your Team",
            )
        )
    )

    league_name = html.escape(
        str(
            league_info.get(
                "name",
                "your mini-league",
            )
        )
    )

    hero_html = (
        f'<div class="hero">'
        f'<h1>⚔️ Squad Comparison</h1>'
        f'<p>'
        f'{your_team_name} versus a selected rival '
        f'from {league_name}.'
        f'</p>'
        f'</div>'
    )

    st.markdown(
        hero_html,
        unsafe_allow_html=True,
    )

    rival_label = st.selectbox(
        "Select rival",
        list(
            manager_options.keys()
        ),
    )

    rival_id = manager_options[
        rival_label
    ]

    with st.spinner(
        "Loading rival data..."
    ):
        rival_entry = get_entry(
            rival_id
        )

        rival_history = get_history(
            rival_id
        )

        my_transfers = get_transfers(
            entry_id.strip()
        )

        rival_transfers = get_transfers(
            rival_id
        )

    my_gameweeks = {
        safe_int(
            row.get("event")
        )
        for row in my_history.get(
            "current",
            [],
        )
    }

    rival_gameweeks = {
        safe_int(
            row.get("event")
        )
        for row in rival_history.get(
            "current",
            [],
        )
    }

    available_gameweeks = sorted(
        my_gameweeks & rival_gameweeks,
        reverse=True,
    )

    if not available_gameweeks:
        st.error(
            "No completed or active gameweeks "
            "are available for both teams."
        )

        st.stop()

    control_1, control_2 = (
        st.columns(2)
    )

    with control_1:
        gameweek = st.selectbox(
            "Gameweek",
            available_gameweeks,
            format_func=lambda value: (
                f"Gameweek {value}"
            ),
        )

    with control_2:
        display_mode = st.selectbox(
            "Player card display",
            [
                "GW Points",
                "Price",
                "Ownership",
                "Season Points",
            ],
        )

    with st.spinner(
        f"Loading Gameweek {gameweek} squads..."
    ):
        my_picks_data = get_picks(
            entry_id.strip(),
            gameweek,
        )

        rival_picks_data = get_picks(
            rival_id,
            gameweek,
        )

        live_data = get_live(
            gameweek
        )

    my_picks = my_picks_data.get(
        "picks",
        [],
    )

    rival_picks = rival_picks_data.get(
        "picks",
        [],
    )

    if not my_picks or not rival_picks:
        st.error(
            "One of the selected squads "
            "could not be loaded."
        )

        st.stop()

    live_lookup = {
        item["id"]: item
        for item in live_data.get(
            "elements",
            [],
        )
    }

    my_week = get_history_row(
        my_history,
        gameweek,
    )

    rival_week = get_history_row(
        rival_history,
        gameweek,
    )

    my_player_ids = {
        pick.get("element")
        for pick in my_picks
    }

    rival_player_ids = {
        pick.get("element")
        for pick in rival_picks
    }

    shared_ids = (
        my_player_ids
        & rival_player_ids
    )

    my_only_ids = (
        my_player_ids
        - rival_player_ids
    )

    rival_only_ids = (
        rival_player_ids
        - my_player_ids
    )

    comparison = {
        player_id: "shared"
        for player_id in shared_ids
    }

    comparison.update(
        {
            player_id: "mine"
            for player_id in my_only_ids
        }
    )

    comparison.update(
        {
            player_id: "rival"
            for player_id in rival_only_ids
        }
    )

    my_captain = next(
        (
            pick
            for pick in my_picks
            if pick.get("is_captain")
        ),
        {},
    )

    rival_captain = next(
        (
            pick
            for pick in rival_picks
            if pick.get("is_captain")
        ),
        {},
    )

    my_vice = next(
        (
            pick
            for pick in my_picks
            if pick.get("is_vice_captain")
        ),
        {},
    )

    rival_vice = next(
        (
            pick
            for pick in rival_picks
            if pick.get("is_vice_captain")
        ),
        {},
    )

    my_name = my_entry.get(
        "name",
        "Your Team",
    )

    rival_name = rival_entry.get(
        "name",
        "Rival Team",
    )

    my_manager_name = (
        f"{my_entry.get('player_first_name', '')} "
        f"{my_entry.get('player_last_name', '')}"
    ).strip()

    rival_manager_name = (
        f"{rival_entry.get('player_first_name', '')} "
        f"{rival_entry.get('player_last_name', '')}"
    ).strip()

    team_left, team_right = (
        st.columns(2)
    )

    with team_left:
        my_banner = (
            f'<div class="team-banner">'
            f'<h3>🟢 {html.escape(str(my_name))}</h3>'
            f'<p>{html.escape(my_manager_name)}</p>'
            f'</div>'
        )

        st.markdown(
            my_banner,
            unsafe_allow_html=True,
        )

    with team_right:
        rival_banner = (
            f'<div class="team-banner">'
            f'<h3>🔴 {html.escape(str(rival_name))}</h3>'
            f'<p>{html.escape(rival_manager_name)}</p>'
            f'</div>'
        )

        st.markdown(
            rival_banner,
            unsafe_allow_html=True,
        )

    # =====================================================
    # HEAD-TO-HEAD OVERVIEW
    # =====================================================

    st.subheader(
        "📊 Head-to-Head Overview"
    )

    comparison_metrics = [
        (
            "GW Points",
            safe_int(
                my_week.get("points")
            ),
            safe_int(
                rival_week.get("points")
            ),
        ),
        (
            "Total Points",
            safe_int(
                my_week.get("total_points")
            ),
            safe_int(
                rival_week.get("total_points")
            ),
        ),
        (
            "Overall Rank",
            format_rank(
                my_week.get("overall_rank")
            ),
            format_rank(
                rival_week.get("overall_rank")
            ),
        ),
        (
            "Squad Value",
            (
                f"£{safe_int(my_week.get('value')) / 10:.1f}m"
            ),
            (
                f"£{safe_int(rival_week.get('value')) / 10:.1f}m"
            ),
        ),
        (
            "Bank",
            (
                f"£{safe_int(my_week.get('bank')) / 10:.1f}m"
            ),
            (
                f"£{safe_int(rival_week.get('bank')) / 10:.1f}m"
            ),
        ),
        (
            "Transfer Cost",
            (
                f"{safe_int(my_week.get('event_transfers_cost'))} pts"
            ),
            (
                f"{safe_int(rival_week.get('event_transfers_cost'))} pts"
            ),
        ),
    ]

    for metric_name, my_value, rival_value in comparison_metrics:
        metric_left, metric_middle, metric_right = (
            st.columns(
                [
                    1,
                    1.2,
                    1,
                ]
            )
        )

        metric_left.metric(
            f"Your {metric_name}",
            my_value,
        )

        versus_html = (
            f'<div style="'
            f'text-align:center;'
            f'padding-top:20px;'
            f'color:#9ba7b4;'
            f'font-weight:800;'
            f'">'
            f'VS · {html.escape(metric_name)}'
            f'</div>'
        )

        metric_middle.markdown(
            versus_html,
            unsafe_allow_html=True,
        )

        metric_right.metric(
            f"Rival {metric_name}",
            rival_value,
        )

    # =====================================================
    # CAPTAINCY
    # =====================================================

    my_captain_name = players.get(
        my_captain.get("element"),
        {},
    ).get(
        "web_name",
        "Unknown",
    )

    rival_captain_name = players.get(
        rival_captain.get("element"),
        {},
    ).get(
        "web_name",
        "Unknown",
    )

    my_vice_name = players.get(
        my_vice.get("element"),
        {},
    ).get(
        "web_name",
        "Unknown",
    )

    rival_vice_name = players.get(
        rival_vice.get("element"),
        {},
    ).get(
        "web_name",
        "Unknown",
    )

    my_captain_points = pick_points(
        my_captain,
        live_lookup,
    )

    rival_captain_points = pick_points(
        rival_captain,
        live_lookup,
    )

    captain_advantage = (
        my_captain_points
        - rival_captain_points
    )

    st.markdown("---")

    st.subheader(
        "🧢 Captaincy Battle"
    )

    captain_1, captain_2, captain_3 = (
        st.columns(3)
    )

    captain_1.metric(
        "Your Captain",
        my_captain_name,
        (
            f"{my_captain_points} "
            f"effective pts"
        ),
    )

    captain_2.metric(
        "Captaincy Advantage",
        f"{captain_advantage:+d} pts",
    )

    captain_3.metric(
        "Rival Captain",
        rival_captain_name,
        (
            f"{rival_captain_points} "
            f"effective pts"
        ),
    )

    st.caption(
        f"Vice-captains: {my_vice_name} "
        f"versus {rival_vice_name}"
    )

    # =====================================================
    # DIFFERENTIAL TABLES
    # =====================================================

    def differential_rows(
        player_ids,
        team_picks,
    ):
        pick_lookup = {
            pick.get("element"): pick
            for pick in team_picks
        }

        rows = []

        for player_id in player_ids:
            player = players.get(
                player_id,
                {},
            )

            team = teams.get(
                player.get("team"),
                {},
            )

            pick = pick_lookup.get(
                player_id,
                {},
            )

            status_icon, status_text = (
                status_details(player)
            )

            rows.append(
                {
                    "Player": player.get(
                        "web_name",
                        "Unknown",
                    ),
                    "Club": team.get(
                        "name",
                        "Unknown",
                    ),
                    "GW Points": pick_points(
                        pick,
                        live_lookup,
                    ),
                    "Price": (
                        f"£{safe_int(player.get('now_cost')) / 10:.1f}m"
                    ),
                    "Ownership": (
                        f"{player.get('selected_by_percent', '0')}%"
                    ),
                    "Status": (
                        f"{status_icon} {status_text}"
                    ).strip(),
                }
            )

        if not rows:
            return pd.DataFrame(
                columns=[
                    "Player",
                    "Club",
                    "GW Points",
                    "Price",
                    "Ownership",
                    "Status",
                ]
            )

        return (
            pd.DataFrame(rows)
            .sort_values(
                "GW Points",
                ascending=False,
            )
        )

    shared_df = differential_rows(
        shared_ids,
        my_picks,
    )

    my_differentials_df = differential_rows(
        my_only_ids,
        my_picks,
    )

    rival_differentials_df = differential_rows(
        rival_only_ids,
        rival_picks,
    )

    my_differential_points = int(
        my_differentials_df[
            "GW Points"
        ].sum()
    )

    rival_differential_points = int(
        rival_differentials_df[
            "GW Points"
        ].sum()
    )

    differential_advantage = (
        my_differential_points
        - rival_differential_points
    )

    st.markdown("---")

    st.subheader(
        "💎 Shared Players and Differentials"
    )

    differential_1, differential_2 = (
        st.columns(2)
    )

    differential_3, differential_4 = (
        st.columns(2)
    )

    differential_1.metric(
        "Shared Players",
        len(shared_ids),
    )

    differential_2.metric(
        "Your Differentials",
        len(my_only_ids),
        (
            f"{my_differential_points} pts"
        ),
    )

    differential_3.metric(
        "Rival Differentials",
        len(rival_only_ids),
        (
            f"{rival_differential_points} pts"
        ),
    )

    differential_4.metric(
        "Differential Advantage",
        f"{differential_advantage:+d} pts",
    )

    shared_tab, yours_tab, rival_tab = (
        st.tabs(
            [
                "Shared Players",
                "Your Differentials",
                "Rival Differentials",
            ]
        )
    )

    with shared_tab:
        st.dataframe(
            shared_df,
            hide_index=True,
            width="stretch",
        )

    with yours_tab:
        st.dataframe(
            my_differentials_df,
            hide_index=True,
            width="stretch",
        )

    with rival_tab:
        st.dataframe(
            rival_differentials_df,
            hide_index=True,
            width="stretch",
        )

    # =====================================================
    # FPL PITCHES
    # =====================================================

    my_pitch_html, my_formation = (
        pitch_html(
            my_picks,
            players,
            teams,
            display_mode,
            live_lookup,
            comparison,
        )
    )

    rival_pitch_html, rival_formation = (
        pitch_html(
            rival_picks,
            players,
            teams,
            display_mode,
            live_lookup,
            comparison,
        )
    )

    st.markdown("---")

    st.subheader(
        "⚽ Squad Pitches"
    )

    st.caption(
        "Gold border = captain. "
        "Blue border = vice-captain. "
        "Green Y = your differential. "
        "Red R = rival differential."
    )

    pitch_left, pitch_right = (
        st.columns(2)
    )

    with pitch_left:
        st.markdown(
            f"#### 🟢 Your Team · "
            f"{my_formation}"
        )

        st.markdown(
            my_pitch_html,
            unsafe_allow_html=True,
        )

    with pitch_right:
        st.markdown(
            f"#### 🔴 Rival Team · "
            f"{rival_formation}"
        )

        st.markdown(
            rival_pitch_html,
            unsafe_allow_html=True,
        )

    # =====================================================
    # BENCH AND CHIP COMPARISON
    # =====================================================

    my_bench = [
        pick
        for pick in my_picks
        if safe_int(
            pick.get("position")
        ) > 11
    ]

    rival_bench = [
        pick
        for pick in rival_picks
        if safe_int(
            pick.get("position")
        ) > 11
    ]

    my_bench_points = sum(
        raw_player_points(
            pick.get("element"),
            live_lookup,
        )
        for pick in my_bench
    )

    rival_bench_points = sum(
        raw_player_points(
            pick.get("element"),
            live_lookup,
        )
        for pick in rival_bench
    )

    st.markdown("---")

    st.subheader(
        "🪑 Bench and Chip Comparison"
    )

    bench_1, bench_2 = st.columns(2)
    bench_3, bench_4 = st.columns(2)

    bench_1.metric(
        "Your Bench Points",
        my_bench_points,
    )

    bench_2.metric(
        "Rival Bench Points",
        rival_bench_points,
    )

    bench_3.metric(
        "Your GW Chip",
        selected_chip(
            my_history,
            gameweek,
        ),
    )

    bench_4.metric(
        "Rival GW Chip",
        selected_chip(
            rival_history,
            gameweek,
        ),
    )

    # =====================================================
    # TRANSFERS AND CHIPS
    # =====================================================

    st.markdown("---")

    transfers_tab, chips_tab = st.tabs(
        [
            "🔄 Gameweek Transfers",
            "🎲 Full Chip History",
        ]
    )

    with transfers_tab:
        transfer_left, transfer_right = (
            st.columns(2)
        )

        with transfer_left:
            st.markdown(
                "#### Your Transfers"
            )

            my_transfer_rows = transfer_rows(
                my_transfers,
                gameweek,
                players,
            )

            if my_transfer_rows:
                st.dataframe(
                    pd.DataFrame(
                        my_transfer_rows
                    ),
                    hide_index=True,
                    width="stretch",
                )
            else:
                st.info(
                    "No transfers were recorded "
                    "for this gameweek."
                )

        with transfer_right:
            st.markdown(
                "#### Rival Transfers"
            )

            rival_transfer_rows = transfer_rows(
                rival_transfers,
                gameweek,
                players,
            )

            if rival_transfer_rows:
                st.dataframe(
                    pd.DataFrame(
                        rival_transfer_rows
                    ),
                    hide_index=True,
                    width="stretch",
                )
            else:
                st.info(
                    "No transfers were recorded "
                    "for this gameweek."
                )

    with chips_tab:
        chip_left, chip_right = (
            st.columns(2)
        )

        with chip_left:
            st.markdown(
                "#### Your Chips"
            )

            my_chips = [
                {
                    "Chip": chip_name(
                        item.get("name")
                    ),
                    "Gameweek": item.get(
                        "event"
                    ),
                }
                for item in my_history.get(
                    "chips",
                    [],
                )
            ]

            if my_chips:
                st.dataframe(
                    pd.DataFrame(
                        my_chips
                    ),
                    hide_index=True,
                    width="stretch",
                )
            else:
                st.info(
                    "No chips used."
                )

        with chip_right:
            st.markdown(
                "#### Rival Chips"
            )

            rival_chips = [
                {
                    "Chip": chip_name(
                        item.get("name")
                    ),
                    "Gameweek": item.get(
                        "event"
                    ),
                }
                for item in rival_history.get(
                    "chips",
                    [],
                )
            ]

            if rival_chips:
                st.dataframe(
                    pd.DataFrame(
                        rival_chips
                    ),
                    hide_index=True,
                    width="stretch",
                )
            else:
                st.info(
                    "No chips used."
                )

    # =====================================================
    # SCOUTING REPORT
    # =====================================================

    st.markdown("---")

    st.subheader(
        "🤖 Head-to-Head Scouting Report"
    )

    my_gameweek_score = safe_int(
        my_week.get("points")
    )

    rival_gameweek_score = safe_int(
        rival_week.get("points")
    )

    gameweek_difference = (
        my_gameweek_score
        - rival_gameweek_score
    )

    report_lines = [
        (
            f"⚔️ **{my_name}** scored "
            f"**{my_gameweek_score} points**, "
            f"compared with "
            f"**{rival_gameweek_score} points** "
            f"for **{rival_name}** in "
            f"Gameweek {gameweek}."
        ),
        (
            f"💎 Your differentials contributed "
            f"**{my_differential_points} points**, "
            f"while the rival differentials "
            f"contributed "
            f"**{rival_differential_points} points**."
        ),
        (
            f"🧢 Your captain "
            f"**{my_captain_name}** produced "
            f"**{my_captain_points} effective points**, "
            f"compared with "
            f"**{rival_captain_points} points** "
            f"from **{rival_captain_name}**."
        ),
        (
            f"🪑 Your bench contains "
            f"**{my_bench_points} points**, "
            f"compared with "
            f"**{rival_bench_points} points** "
            f"on the rival bench."
        ),
        (
            f"🎲 Chip comparison for the selected "
            f"gameweek: "
            f"**{selected_chip(my_history, gameweek)}** "
            f"versus "
            f"**{selected_chip(rival_history, gameweek)}**."
        ),
    ]

    if gameweek_difference > 0:
        report_lines.append(
            f"📊 Overall, your team is "
            f"**{gameweek_difference} points ahead** "
            f"of the selected rival this gameweek."
        )

    elif gameweek_difference < 0:
        report_lines.append(
            f"📊 Overall, your team is "
            f"**{abs(gameweek_difference)} points behind** "
            f"the selected rival this gameweek."
        )

    else:
        report_lines.append(
            "📊 Both teams are currently level "
            "on gameweek points."
        )

    st.info(
        "\n\n".join(
            report_lines
        )
    )

    st.caption(
        "Squads, points, transfers and chip information "
        "are retrieved from the Fantasy Premier League data feed."
    )


# =========================================================
# ERROR HANDLING
# =========================================================

except requests.exceptions.HTTPError as error:
    status_code = getattr(
        error.response,
        "status_code",
        "Unknown",
    )

    st.error(
        f"The FPL service returned status code "
        f"{status_code}. Check the League ID and "
        f"Entry ID, then try again."
    )

except requests.exceptions.Timeout:
    st.error(
        "The FPL service took too long to respond. "
        "Refresh the page and try again."
    )

except requests.exceptions.ConnectionError:
    st.error(
        "The app could not connect to the FPL service. "
        "Please try again shortly."
    )

except (
    KeyError,
    IndexError,
    TypeError,
    ValueError,
) as error:
    st.error(
        "Some comparison data was missing or "
        "had an unexpected format."
    )

    with st.expander(
        "Technical error details"
    ):
        st.code(
            str(error)
        )

except Exception as error:
    st.error(
        "An unexpected error occurred while "
        "loading Squad Comparison."
    )

    with st.expander(
        "Technical error details"
    ):
        st.code(
            str(error)
        )
