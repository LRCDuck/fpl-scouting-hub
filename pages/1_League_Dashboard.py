import html
from datetime import datetime, timezone

import pandas as pd
import plotly.express as px
import requests
import streamlit as st


# =========================================================
# DEFAULT SETTINGS
# =========================================================

DEFAULT_LEAGUE_ID = "1116047"
DEFAULT_ENTRY_ID = "6074290"

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
    page_title="League Dashboard",
    page_icon="🏆",
    layout="wide",
    initial_sidebar_state="expanded",
)


# =========================================================
# PAGE STYLING
# =========================================================

st.markdown(
    """
    <style>
    .block-container {
        padding-top: 1.4rem;
        padding-bottom: 3rem;
    }

    .league-hero {
        background:
            radial-gradient(
                circle at top right,
                rgba(0, 255, 135, 0.20),
                transparent 36%
            ),
            linear-gradient(
                135deg,
                #17212b 0%,
                #202b3b 56%,
                #111820 100%
            );
        border: 1px solid #303b4d;
        border-radius: 20px;
        padding: 25px;
        margin-bottom: 20px;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.25);
    }

    .league-hero-title {
        color: #ffffff;
        font-size: 2rem;
        font-weight: 850;
        margin: 0;
    }

    .league-hero-subtitle {
        color: #b7c0cc;
        font-size: 0.95rem;
        margin: 7px 0 0 0;
    }

    .deadline-banner {
        background: linear-gradient(
            135deg,
            #37003c 0%,
            #5a0961 100%
        );
        border: 1px solid #89428f;
        border-radius: 13px;
        color: #ffffff;
        padding: 13px 17px;
        margin-bottom: 19px;
    }

    .deadline-banner strong {
        color: #00ff87;
    }

    .podium-card {
        position: relative;
        background: linear-gradient(
            145deg,
            #1c2330,
            #121720
        );
        border: 1px solid #303b4d;
        border-radius: 16px;
        padding: 20px 12px;
        text-align: center;
        min-height: 165px;
        box-shadow: 0 5px 15px rgba(0, 0, 0, 0.22);
        overflow: hidden;
    }

    .podium-card::before {
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 6px;
        background: var(--podium-colour);
    }

    .podium-medal {
        font-size: 2rem;
        margin-bottom: 5px;
    }

    .podium-position {
        color: #9ba7b4;
        font-size: 0.72rem;
        font-weight: 800;
        letter-spacing: 0.1rem;
    }

    .podium-manager {
        color: #ffffff;
        font-size: 1.05rem;
        font-weight: 850;
        margin-top: 8px;
    }

    .podium-team {
        color: #9ba7b4;
        font-size: 0.78rem;
        margin-top: 3px;
    }

    .podium-points {
        display: inline-block;
        margin-top: 11px;
        color: #ffffff;
        background: rgba(255, 255, 255, 0.09);
        border-radius: 8px;
        padding: 5px 10px;
        font-weight: 800;
    }

    .personal-banner {
        background: linear-gradient(
            135deg,
            rgba(0, 255, 135, 0.15),
            rgba(0, 255, 135, 0.04)
        );
        border: 1px solid rgba(0, 255, 135, 0.45);
        border-radius: 14px;
        padding: 16px;
        margin: 8px 0 15px 0;
    }

    .personal-banner h3 {
        color: #ffffff;
        margin: 0 0 5px 0;
    }

    .personal-banner p {
        color: #b7c0cc;
        margin: 0;
    }

    .movement-card {
        background: #161b22;
        border: 1px solid #30363d;
        border-radius: 13px;
        padding: 15px;
        min-height: 115px;
    }

    .movement-card h4 {
        color: #ffffff;
        margin: 0 0 7px 0;
    }

    .movement-card p {
        color: #aab3bf;
        margin: 0;
    }

    .award-card {
        background: #161b22;
        border: 1px solid #30363d;
        border-radius: 13px;
        padding: 15px 8px;
        min-height: 135px;
        text-align: center;
    }

    .award-icon {
        font-size: 1.75rem;
    }

    .award-title {
        color: #98a3b1;
        font-size: 0.70rem;
        font-weight: 800;
        letter-spacing: 0.05rem;
        margin-top: 5px;
    }

    .award-winner {
        color: #ffffff;
        font-size: 0.92rem;
        font-weight: 850;
        margin-top: 7px;
    }

    .award-detail {
        color: #00ff87;
        font-size: 0.78rem;
        margin-top: 4px;
    }

    div[data-testid="stMetric"] {
        background: #161b22;
        border: 1px solid #30363d;
        border-radius: 13px;
        padding: 13px;
    }

    div[data-testid="stMetricLabel"] {
        color: #aab3bf;
    }

    div[data-testid="stMetricValue"] {
        color: #ffffff;
    }

    div.stButton > button {
        border-radius: 9px;
        font-weight: 750;
    }

    @media (max-width: 700px) {
        .league-hero {
            padding: 17px;
        }

        .league-hero-title {
            font-size: 1.55rem;
        }

        .podium-card {
            min-height: 145px;
            padding: 15px 7px;
        }

        .podium-manager {
            font-size: 0.85rem;
        }

        .award-card {
            min-height: 120px;
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
    help="The ID shown in your FPL mini-league URL.",
)

entry_id = st.sidebar.text_input(
    "Your FPL Entry ID",
    value=DEFAULT_ENTRY_ID,
    help="Your personal FPL team ID.",
)

st.sidebar.markdown("---")

if st.sidebar.button(
    "🔄 Refresh League Data",
    use_container_width=True,
):
    st.cache_data.clear()
    st.rerun()

st.sidebar.caption(
    "League standings are cached for five minutes."
)


# =========================================================
# API FUNCTIONS
# =========================================================

def api_get(endpoint, timeout=20):
    url = f"{BASE_URL}/{endpoint.lstrip('/')}"

    response = requests.get(
        url,
        headers=REQUEST_HEADERS,
        timeout=timeout,
    )

    response.raise_for_status()

    return response.json()


@st.cache_data(ttl=1800, show_spinner=False)
def get_bootstrap_data():
    return api_get("bootstrap-static/")


@st.cache_data(ttl=300, show_spinner=False)
def get_manager_data(selected_entry_id):
    return api_get(f"entry/{selected_entry_id}/")


@st.cache_data(ttl=300, show_spinner=False)
def get_league_data(selected_league_id):
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


# =========================================================
# HELPER FUNCTIONS
# =========================================================

def safe_int(value, fallback=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return fallback


def format_rank(value):
    rank = safe_int(value)

    if rank <= 0:
        return "Unavailable"

    return f"{rank:,}"


def ordinal(number):
    number = safe_int(number)

    if 10 <= number % 100 <= 20:
        suffix = "th"
    else:
        suffix = {
            1: "st",
            2: "nd",
            3: "rd",
        }.get(number % 10, "th")

    return f"{number}{suffix}"


def format_deadline(deadline_text):
    if not deadline_text:
        return "Deadline unavailable"

    try:
        deadline = datetime.fromisoformat(
            deadline_text.replace("Z", "+00:00")
        )

        return deadline.strftime(
            "%A %d %B at %H:%M"
        )

    except ValueError:
        return deadline_text


def deadline_countdown(deadline_text):
    if not deadline_text:
        return "Countdown unavailable"

    try:
        deadline = datetime.fromisoformat(
            deadline_text.replace("Z", "+00:00")
        )

        difference = deadline - datetime.now(timezone.utc)

        if difference.total_seconds() <= 0:
            return "Deadline passed"

        total_minutes = int(
            difference.total_seconds() // 60
        )

        days, remaining_minutes = divmod(
            total_minutes,
            1440,
        )

        hours, minutes = divmod(
            remaining_minutes,
            60,
        )

        return (
            f"{days}d {hours}h {minutes}m remaining"
        )

    except ValueError:
        return "Countdown unavailable"


def movement_icon(movement):
    if movement > 0:
        return "▲"

    if movement < 0:
        return "▼"

    return "•"


def movement_text(movement):
    if movement > 0:
        return f"Up {movement}"

    if movement < 0:
        return f"Down {abs(movement)}"

    return "No change"


def prepare_standings_dataframe(results):
    rows = []

    for manager in results:
        current_rank = safe_int(
            manager.get("rank")
        )

        last_rank = safe_int(
            manager.get("last_rank"),
            current_rank,
        )

        movement = last_rank - current_rank

        rows.append(
            {
                "Entry ID": safe_int(
                    manager.get("entry")
                ),
                "Rank": current_rank,
                "Trend": movement_icon(movement),
                "Movement": movement,
                "Manager": manager.get(
                    "player_name",
                    "Unknown Manager",
                ),
                "Team": manager.get(
                    "entry_name",
                    "Unknown Team",
                ),
                "GW Score": safe_int(
                    manager.get("event_total")
                ),
                "Total Points": safe_int(
                    manager.get("total")
                ),
            }
        )

    dataframe = pd.DataFrame(rows)

    if not dataframe.empty:
        dataframe = dataframe.sort_values(
            ["Rank", "Total Points"],
            ascending=[True, False],
        ).reset_index(drop=True)

    return dataframe


def podium_card(manager_row, position):
    podium_styles = {
        1: {
            "medal": "🥇",
            "label": "FIRST PLACE",
            "colour": "#FFD700",
        },
        2: {
            "medal": "🥈",
            "label": "SECOND PLACE",
            "colour": "#C0C0C0",
        },
        3: {
            "medal": "🥉",
            "label": "THIRD PLACE",
            "colour": "#CD7F32",
        },
    }

    style = podium_styles[position]

    manager_name = html.escape(
        str(manager_row["Manager"])
    )

    team_name = html.escape(
        str(manager_row["Team"])
    )

    points = safe_int(
        manager_row["Total Points"]
    )

    return f"""
    <div
        class="podium-card"
        style="--podium-colour:{style['colour']};"
    >
        <div class="podium-medal">
            {style['medal']}
        </div>

        <div class="podium-position">
            {style['label']}
        </div>

        <div class="podium-manager">
            {manager_name}
        </div>

        <div class="podium-team">
            {team_name}
        </div>

        <div class="podium-points">
            {points} points
        </div>
    </div>
    """


# =========================================================
# MAIN DASHBOARD
# =========================================================

try:
    if not str(league_id).strip().isdigit():
        st.error(
            "The Mini-League ID must contain numbers only."
        )
        st.stop()

    if not str(entry_id).strip().isdigit():
        st.error(
            "Your FPL Entry ID must contain numbers only."
        )
        st.stop()

    with st.spinner(
        "Loading league standings and FPL data..."
    ):
        league_data = get_league_data(
            str(league_id).strip()
        )

        manager_data = get_manager_data(
            str(entry_id).strip()
        )

        bootstrap_data = get_bootstrap_data()

    league_information = league_data.get(
        "league",
        {},
    )

    league_name = league_information.get(
        "name",
        "FPL Mini-League",
    )

    standings_df = prepare_standings_dataframe(
        league_data.get("results", [])
    )

    if standings_df.empty:
        st.error(
            "No league standings were found. "
            "Check the Mini-League ID and try again."
        )
        st.stop()

    leader = standings_df.iloc[0]

    personal_rows = standings_df[
        standings_df["Entry ID"]
        == safe_int(entry_id)
    ]

    personal_row = None

    if not personal_rows.empty:
        personal_row = personal_rows.iloc[0]

    events = bootstrap_data.get("events", [])

    current_event = next(
        (
            event
            for event in events
            if event.get("is_current")
        ),
        None,
    )

    next_event = next(
        (
            event
            for event in events
            if event.get("is_next")
        ),
        None,
    )

    if next_event is None:
        unfinished_events = [
            event
            for event in events
            if not event.get("finished")
        ]

        if unfinished_events:
            next_event = unfinished_events[0]

    # =====================================================
    # HERO
    # =====================================================

    st.markdown(
        f"""
        <div class="league-hero">
            <p class="league-hero-title">
                🏆 {html.escape(league_name)}
            </p>

            <p class="league-hero-subtitle">
                Live standings, rank movement, gameweek
                performance and mini-league scouting insights.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if next_event:
        deadline_name = next_event.get(
            "name",
            "Next Gameweek",
        )

        deadline_time = next_event.get(
            "deadline_time"
        )

        st.markdown(
            f"""
            <div class="deadline-banner">
                ⏰ <strong>
                    {html.escape(deadline_name)} deadline:
                </strong>
                {html.escape(format_deadline(deadline_time))}
                · {html.escape(deadline_countdown(deadline_time))}
            </div>
            """,
            unsafe_allow_html=True,
        )

    # =====================================================
    # LEAGUE OVERVIEW
    # =====================================================

    st.subheader("📊 League Overview")

    league_average = round(
        standings_df["Total Points"].mean(),
        1,
    )

    gameweek_average = round(
        standings_df["GW Score"].mean(),
        1,
    )

    league_spread = (
        safe_int(standings_df.iloc[0]["Total Points"])
        - safe_int(
            standings_df.iloc[-1]["Total Points"]
        )
    )

    overview_1, overview_2, overview_3 = st.columns(3)
    overview_4, overview_5, overview_6 = st.columns(3)

    overview_1.metric(
        "League Leader",
        leader["Manager"],
    )

    overview_2.metric(
        "Leader Points",
        safe_int(leader["Total Points"]),
    )

    overview_3.metric(
        "Managers",
        len(standings_df),
    )

    overview_4.metric(
        "League Average",
        f"{league_average} pts",
    )

    overview_5.metric(
        "Average GW Score",
        f"{gameweek_average} pts",
    )

    overview_6.metric(
        "First-to-Last Spread",
        f"{league_spread} pts",
    )

    # =====================================================
    # PODIUM
    # =====================================================

    st.markdown("---")
    st.subheader("🏅 League Podium")

    podium = standings_df.head(3)
    podium_columns = st.columns(3)

    for index, (_, podium_manager) in enumerate(
        podium.iterrows()
    ):
        with podium_columns[index]:
            st.markdown(
                podium_card(
                    podium_manager,
                    index + 1,
                ),
                unsafe_allow_html=True,
            )

    # =====================================================
    # PERSONAL DASHBOARD
    # =====================================================

    st.markdown("---")
    st.subheader("👤 Your League Position")

    personal_rank = None
    gap_to_leader = None
    gap_to_above = None
    manager_above = None
    manager_below = None

    if personal_row is not None:
        personal_rank = safe_int(
            personal_row["Rank"]
        )

        personal_points = safe_int(
            personal_row["Total Points"]
        )

        personal_gw_score = safe_int(
            personal_row["GW Score"]
        )

        personal_movement = safe_int(
            personal_row["Movement"]
        )

        gap_to_leader = (
            safe_int(leader["Total Points"])
            - personal_points
        )

        if personal_rank > 1:
            managers_above = standings_df[
                standings_df["Rank"] < personal_rank
            ]

            if not managers_above.empty:
                manager_above = managers_above.iloc[-1]

        managers_below = standings_df[
            standings_df["Rank"] > personal_rank
        ]

        if not managers_below.empty:
            manager_below = managers_below.iloc[0]

        if manager_above is not None:
            gap_to_above = (
                safe_int(manager_above["Total Points"])
                - personal_points
            )

        lead_over_below = None

        if manager_below is not None:
            lead_over_below = (
                personal_points
                - safe_int(manager_below["Total Points"])
            )

        st.markdown(
            f"""
            <div class="personal-banner">
                <h3>
                    {html.escape(str(personal_row['Team']))}
                </h3>

                <p>
                    Managed by
                    {html.escape(str(personal_row['Manager']))}
                    · Currently {ordinal(personal_rank)}
                    in {html.escape(league_name)}
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        personal_1, personal_2, personal_3 = (
            st.columns(3)
        )

        personal_4, personal_5, personal_6 = (
            st.columns(3)
        )

        personal_1.metric(
            "League Rank",
            ordinal(personal_rank),
            delta=movement_text(personal_movement),
        )

        personal_2.metric(
            "Total Points",
            personal_points,
        )

        personal_3.metric(
            "Current GW Score",
            personal_gw_score,
        )

        personal_4.metric(
            "Gap to Leader",
            f"{gap_to_leader} pts",
        )

        if manager_above is not None:
            personal_5.metric(
                f"Gap to {manager_above['Manager']}",
                f"{gap_to_above} pts",
            )
        else:
            personal_5.metric(
                "Position",
                "League leader",
            )

        if manager_below is not None:
            personal_6.metric(
                f"Lead over {manager_below['Manager']}",
                f"{lead_over_below} pts",
            )
        else:
            personal_6.metric(
                "Manager Below",
                "None",
            )

        detail_1, detail_2, detail_3 = st.columns(3)

        detail_1.metric(
            "Overall FPL Rank",
            format_rank(
                manager_data.get(
                    "summary_overall_rank"
                )
            ),
        )

        squad_value = (
            safe_int(
                manager_data.get(
   
