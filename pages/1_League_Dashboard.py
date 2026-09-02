import html
from datetime import datetime, timezone

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
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
                transparent 35%
            ),
            linear-gradient(
                135deg,
                #17212b 0%,
                #202b3b 55%,
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
        min-height: 155px;
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
        margin-top: 2px;
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
        background:
            linear-gradient(
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

    .award-card {
        background: #161b22;
        border: 1px solid #30363d;
        border-radius: 13px;
        padding: 15px;
        min-height: 120px;
        text-align: center;
    }

    .award-icon {
        font-size: 1.75rem;
    }

    .award-title {
        color: #98a3b1;
        font-size: 0.72rem;
        font-weight: 800;
        letter-spacing: 0.06rem;
        margin-top: 5px;
    }

    .award-winner {
        color: #ffffff;
        font-size: 0.95rem;
        font-weight: 850;
        margin-top: 6px;
    }

    .award-detail {
        color: #00ff87;
        font-size: 0.78rem;
        margin-top: 3px;
    }

    .movement-card {
        background: #161b22;
        border: 1px solid #30363d;
        border-radius: 13px;
        padding: 15px;
        min-height: 110px;
    }

    .movement-card h4 {
        margin: 0 0 7px 0;
        color: #ffffff;
    }

    .movement-card p {
        margin: 0;
        color: #aab3bf;
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
            min-height: 140px;
            padding: 15px 7px;
        }

        .podium-manager {
            font-size: 0.85rem;
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
    help="The ID shown in the FPL mini-league URL.",
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
# API HELPERS
# =========================================================

def api_get(endpoint, timeout=20):
    """Get JSON data from an FPL API endpoint."""

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
    """
    Load every standings page.

    This means the dashboard still works if the league
    contains more managers than the first FPL results page.
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


# =========================================================
# FORMATTERS
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


# =========================================================
# DATA PREPARATION
# =========================================================

def prepare_standings_dataframe(results):
    rows = []

    for manager in results:
        current_rank = safe_int(
            manager.get("rank"),
            0,
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


def highlight_personal_row(row):
    if safe_int(row["Entry ID"]) == safe_int(entry_id):
        return [
            (
                "background-color: rgba(0, 255, 135, 0.20); "
                "color: white; font-weight: bold; "
                "border-top: 1px solid #00ff87; "
                "border-bottom: 1px solid #00ff87;"
            )
        ] * len(row)

    return [""] * len(row)


# =========================================================
# PODIUM CARD
# =========================================================

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
# MAIN PAGE
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

    results = league_data.get(
        "results",
        [],
    )

    standings_df = prepare_standings_dataframe(
        results
    )

    if standings_df.empty:
        st.error(
            "No league standings were found. Check the "
            "Mini-League ID and try again."
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
    # LEAGUE SUMMARY
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
        with podium_columnsst.markdown(
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

        manager_above = None
        manager_below = None

        if personal_rank > 1:
            manager_above_rows = standings_df[
                standings_df["Rank"]
                < personal_rank
            ]

            if not manager_above_rows.empty:
                manager_above = (
                    manager_above_rows.iloc[-1]
                )

        manager_below_rows = standings_df[
            standings_df["Rank"]
            > personal_rank
        ]

        if not manager_below_rows.empty:
            manager_below = (
                manager_below_rows.iloc[0]
            )

        gap_to_above = 0

        if manager_above is not None:
            gap_to_above = (
                safe_int(manager_above["Total Points"])
                - personal_points
            )

        lead_over_below = 0

        if manager_below is not None:
            lead_over_below = (
                personal_points
                - safe_int(
                    manager_below["Total Points"]
                )
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

        detail_1, detail_2 = st.columns(2)

        with detail_1:
            st.metric(
                "Overall FPL Rank",
                format_rank(
                    manager_data.get(
                        "summary_overall_rank"
                    )
                ),
            )

        with detail_2:
            squad_value = (
                safe_int(
                    manager_data.get(
                        "last_deadline_value"
                    )
                )
                / 10
            )

            bank = (
                safe_int(
                    manager_data.get(
                        "last_deadline_bank"
                    )
                )
                / 10
            )

            st.metric(
                "Squad Value and Bank",
                f"£{squad_value:.1f}m",
                delta=f"£{bank:.1f}m in bank",
            )

    else:
        st.warning(
            "Your Entry ID was not found in this mini-league. "
            "You can still view all league analysis below."
        )

    # =====================================================
    # LEAGUE STANDINGS
    # =====================================================

    st.markdown("---")
    st.subheader("📋 League Standings")

    control_1, control_2, control_3 = st.columns(
        [2, 1, 1]
    )

    with control_1:
        search_term = st.text_input(
            "Search manager or team",
            placeholder="Enter a name or team...",
        )

    with control_2:
        table_limit = st.selectbox(
            "Managers to display",
            options=[
                "All",
                "Top 5",
                "Top 10",
                "Top 20",
            ],
        )

    with control_3:
        sort_option = st.selectbox(
            "Sort table by",
            options=[
                "League Rank",
                "Gameweek Score",
                "Rank Movement",
            ],
        )

    table_df = standings_df.copy()

    table_df["Gap to Leader"] = (
        safe_int(leader["Total Points"])
        - table_df["Total Points"]
    )

    table_df["Movement Display"] = table_df[
        "Movement"
    ].apply(movement_text)

    if search_term:
        search_mask = (
            table_df["Manager"]
            .str.contains(
                search_term,
                case=False,
                na=False,
            )
            |
            table_df["Team"]
            .str.contains(
                search_term,
                case=False,
                na=False,
            )
        )

        table_df = table_df[search_mask]

    if sort_option == "Gameweek Score":
        table_df = table_df.sort_values(
            ["GW Score", "Total Points"],
            ascending=[False, False],
        )

    elif sort_option == "Rank Movement":
        table_df = table_df.sort_values(
            ["Movement", "Rank"],
            ascending=[False, True],
        )

    else:
        table_df = table_df.sort_values(
            "Rank",
            ascending=True,
        )

    limit_values = {
        "Top 5": 5,
        "Top 10": 10,
        "Top 20": 20,
    }

    if table_limit in limit_values:
        table_df = table_df.head(
            limit_values[table_limit]
        )

    displayed_columns = [
        "Entry ID",
        "Rank",
        "Trend",
        "Manager",
        "Team",
        "GW Score",
        "Total Points",
        "Gap to Leader",
        "Movement Display",
    ]

    styled_table = (
        table_df[displayed_columns]
        .style
        .apply(
            highlight_personal_row,
            axis=1,
        )
        .format(
            {
                "GW Score": "{:.0f}",
                "Total Points": "{:.0f}",
                "Gap to Leader": "{:.0f}",
            }
        )
    )

    st.dataframe(
        styled_table,
        hide_index=True,
        use_container_width=True,
        column_config={
            "Entry ID": None,
            "Rank": st.column_config.NumberColumn(
                "Rank",
                format="%d",
            ),
            "Trend": st.column_config.TextColumn(
                "Trend",
            ),
            "Manager": st.column_config.TextColumn(
                "Manager",
            ),
            "Team": st.column_config.TextColumn(
                "Team",
            ),
            "GW Score": st.column_config.NumberColumn(
                "GW Score",
                format="%d pts",
            ),
            "Total Points": st.column_config.NumberColumn(
                "Total Points",
                format="%d pts",
            ),
            "Gap to Leader": st.column_config.NumberColumn(
                "Gap to Leader",
                format="%d pts",
            ),
            "Movement Display": st.column_config.TextColumn(
                "Rank Movement",
            ),
        },
    )

    # =====================================================
    # CHARTS
    # =====================================================

    st.markdown("---")
    st.subheader("📈 League Charts")

    chart_tab_1, chart_tab_2, chart_tab_3 = st.tabs(
        [
            "Total Points",
            "Gameweek Scores",
            "Gap to Leader",
        ]
    )

    chart_df = standings_df.copy()

    chart_df["Display Name"] = (
        chart_df["Rank"].astype(str)
        + ". "
        + chart_df["Manager"]
    )

    chart_df["Gap to Leader"] = (
        safe_int(leader["Total Points"])
        - chart_df["Total Points"]
    )

    with chart_tab_1:
        total_points_chart = px.bar(
            chart_df.sort_values(
                "Total Points",
                ascending=True,
            ),
            x="Total Points",
            y="Display Name",
            orientation="h",
            color="Total Points",
            color_continuous_scale=[
                "#37003c",
                "#00ff87",
            ],
            text="Total Points",
            hover_data={
                "Team": True,
                "GW Score": True,
                "Display Name": False,
            },
        )

        total_points_chart.update_layout(
            title="Total Points by Manager",
            xaxis_title="Total Points",
            yaxis_title="",
            coloraxis_showscale=False,
            height=max(
                430,
                len(chart_df) * 35,
            ),
            margin=dict(
                l=10,
                r=15,
                t=55,
                b=30,
            ),
        )

        total_points_chart.update_traces(
            textposition="outside",
        )

        st.plotly_chart(
            total_points_chart,
            use_container_width=True,
        )

    with chart_tab_2:
        gw_chart = px.bar(
            chart_df.sort_values(
                "GW Score",
                ascending=True,
            ),
            x="GW Score",
            y="Display Name",
            orientation="h",
            color="GW Score",
            color_continuous_scale=[
                "#37003c",
                "#00ff87",
            ],
            text="GW Score",
            hover_data={
                "Team": True,
                "Total Points": True,
                "Display Name": False,
            },
        )

        gw_chart.update_layout(
            title="Current Gameweek Scores",
            xaxis_title="Gameweek Points",
            yaxis_title="",
            coloraxis_showscale=False,
            height=max(
                430,
                len(chart_df) * 35,
            ),
            margin=dict(
                l=10,
                r=15,
                t=55,
                b=30,
            ),
        )

        gw_chart.update_traces(
            textposition="outside",
        )

        st.plotly_chart(
            gw_chart,
            use_container_width=True,
        )

    with chart_tab_3:
        gap_chart = go.Figure()

        gap_chart.add_trace(
            go.Bar(
                x=chart_df["Display Name"],
                y=chart_df["Gap to Leader"],
                marker_color="#ff6078",
                text=chart_df["Gap to Leader"],
                textposition="outside",
                hovertemplate=(
                    "<b>%{x}</b><br>"
                    "Gap: %{y} points"
                    "<extra></extra>"
                ),
            )
        )

        gap_chart.update_layout(
            title="Points Behind the League Leader",
            xaxis_title="Manager",
            yaxis_title="Points Behind",
            height=480,
            margin=dict(
                l=10,
                r=15,
                t=55,
                b=100,
            ),
        )

        gap_chart.update_xaxes(
            tickangle=-45,
        )

        st.plotly_chart(
            gap_chart,
            use_container_width=True,
        )

    # =====================================================
    # MOVERS AND AWARDS
    # =====================================================

    st.markdown("---")
    st.subheader("🚀 Movers and League Awards")

    positive_movers = standings_df[
        standings_df["Movement"] > 0
    ]

    negative_movers = standings_df[
        standings_df["Movement"] < 0
    ]

    if not positive_movers.empty:
        biggest_riser = positive_movers.loc[
            positive_movers["Movement"].idxmax()
        ]
    else:
        biggest_riser = None

    if not negative_movers.empty:
        biggest_faller = negative_movers.loc[
            negative_movers["Movement"].idxmin()
        ]
    else:
        biggest_faller = None

    movement_column_1, movement_column_2 = (
        st.columns(2)
    )

    with movement_column_1:
        if biggest_riser is not None:
            st.markdown(
                f"""
                <div class="movement-card">
                    <h4>🚀 Biggest Riser</h4>
                    <p>
                        <strong>
                            {html.escape(str(biggest_riser['Manager']))}
                        </strong>
                        climbed
                        {safe_int(biggest_riser['Movement'])}
                        place(s) to
                        {ordinal(biggest_riser['Rank'])}.
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                """
                <div class="movement-card">
                    <h4>🚀 Biggest Riser</h4>
                    <p>No managers moved up this gameweek.</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

    with movement_column_2:
        if biggest_faller is not None:
            st.markdown(
                f"""
                <div class="movement-card">
                    <h4>📉 Biggest Faller</h4>
                    <p>
                        <strong>
                            {html.escape(str(biggest_faller['Manager']))}
                        </strong>
                        dropped
                        {abs(safe_int(biggest_faller['Movement']))}
                        place(s) to
                        {ordinal(biggest_faller['Rank'])}.
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                """
                <div class="movement-card">
                    <h4>📉 Biggest Faller</h4>
                    <p>No managers moved down this gameweek.</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

    highest_gw_manager = standings_df.loc[
        standings_df["GW Score"].idxmax()
    ]

    lowest_gw_manager = standings_df.loc[
        standings_df["GW Score"].idxmin()
    ]

    closest_challenger = (
        standings_df.iloc[1]
        if len(standings_df) > 1
        else leader
    )

    award_1, award_2, award_3, award_4 = (
        st.columns(4)
    )

    with award_1:
        st.markdown(
            f"""
            <div class="award-card">
                <div class="award-icon">👑</div>
                <div class="award-title">
                    LEAGUE BOSS
                </div>
                <div class="award-winner">
                    {html.escape(str(leader['Manager']))}
                </div>
                <div class="award-detail">
                    {safe_int(leader['Total Points'])} points
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with award_2:
        st.markdown(
            f"""
            <div class="award-card">
                <div class="award-icon">🔥</div>
                <div class="award-title">
                    KING OF THE WEEK
                </div>
                <div class="award-winner">
                    {html.escape(str(highest_gw_manager['Manager']))}
                </div>
                <div class="award-detail">
                    {safe_int(highest_gw_manager['GW Score'])} GW points
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with award_3:
        st.markdown(
            f"""
            <div class="award-card">
                <div class="award-icon">⚔️</div>
                <div class="award-title">
                    CLOSEST CHALLENGER
                </div>
                <div class="award-winner">
                    {html.escape(str(closest_challenger['Manager']))}
                </div>
                <div class="award-detail">
                    {safe_int(leader['Total Points']) - safe_int(closest_challenger['Total Points'])}
                    points behind
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with award_4:
        st.markdown(
            f"""
            <div class="award-card">
                <div class="award-icon">🧊</div>
                <div class="award-title">
                    TOUGH GAMEWEEK
                </div>
                <div class="award-winner">
                    {html.escape(str(lowest_gw_manager['Manager']))}
                </div>
                <div class="award-detail">
                    {safe_int(lowest_gw_manager['GW Score'])} GW points
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # =====================================================
    # TOP GAMEWEEK PERFORMERS
    # =====================================================

    st.markdown("---")
    st.subheader("🔥 Gameweek Performance")

    top_gw = (
        standings_df
        .sort_values(
            ["GW Score", "Total Points"],
            ascending=[False, False],
        )
        .head(5)
        .copy()
    )

    top_gw["GW Position"] = range(
        1,
        len(top_gw) + 1,
    )

    st.dataframe(
        top_gw[
            [
                "GW Position",
                "Manager",
                "Team",
                "GW Score",
                "Rank",
            ]
        ],
        hide_index=True,
        use_container_width=True,
        column_config={
            "GW Position": st.column_config.NumberColumn(
                "GW Position",
                format="%d",
            ),
            "GW Score": st.column_config.NumberColumn(
                "GW Score",
                format="%d pts",
            ),
            "Rank": st.column_config.NumberColumn(
                "League Rank",
                format="%d",
            ),
        },
    )

    # =====================================================
    # AUTOMATIC LEAGUE REPORT
    # =====================================================

    st.markdown("---")
    st.subheader("🤖 League Scouting Report")

    leader_advantage = 0

    if len(standings_df) > 1:
        leader_advantage = (
            safe_int(standings_df.iloc[0]["Total Points"])
            - safe_int(
                standings_df.iloc[1]["Total Points"]
            )
        )

    current_gameweek_name = (
        current_event.get("name")
        if current_event
        else "the current gameweek"
    )

    report_lines = [
        (
            f"🏆 **{leader['Manager']}** leads the league "
            f"with **{safe_int(leader['Total Points'])} points**."
        ),
        (
            f"⚔️ The lead over second place is currently "
            f"**{leader_advantage} points**."
        ),
        (
            f"🔥 **{highest_gw_manager['Manager']}** has the "
            f"highest score in {current_gameweek_name} with "
            f"**{safe_int(highest_gw_manager['GW Score'])} points**."
        ),
        (
            f"📊 The league average is **{league_average} total "
            f"points**, while the average current gameweek score "
            f"is **{gameweek_average} points**."
        ),
    ]

    if biggest_riser is not None:
        report_lines.append(
            f"🚀 **{biggest_riser['Manager']}** is the biggest "
            f"climber, gaining **{safe_int(biggest_riser['Movement'])} "
            f"place(s)**."
        )

    if biggest_faller is not None:
        report_lines.append(
            f"📉 **{biggest_faller['Manager']}** experienced the "
            f"largest fall, dropping "
            f"**{abs(safe_int(biggest_faller['Movement']))} place(s)**."
        )

    if personal_row is not None:
        report_lines.append(
            f"🎯 Your team is currently **{ordinal(personal_rank)}**, "
            f"**{gap_to_leader} points** behind the leader."
        )

        if manager_above is not None:
            report_lines.append(
                f"👀 Your next target is "
                f"**{manager_above['Manager']}**, who is "
                f"**{gap_to_above} points** ahead."
            )

    st.info("\n\n".join(report_lines))

    st.caption(
        "Standings and gameweek scores are retrieved from "
        "the Fantasy Premier League data feed."
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
        f"{status_code}. Check the League ID and Entry ID, "
        f"then refresh the page."
    )

except requests.exceptions.Timeout:
    st.error(
        "The FPL service took too long to respond. "
        "Please refresh the page and try again."
    )

except requests.exceptions.ConnectionError:
    st.error(
        "The app could not connect to the FPL service. "
        "Please try again shortly."
    )

except (KeyError, IndexError, TypeError, ValueError) as error:
    st.error(
        "Some league data was missing or had an "
        "unexpected format."
    )

    with st.expander("Technical error details"):
        st.code(str(error))

except Exception as error:
    st.error(
        "An unexpected error occurred while loading "
        "the League Dashboard."
    )

    with st.expander("Technical error details"):
        st.code(str(error))
