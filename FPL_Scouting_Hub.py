from datetime import datetime, timezone
import html

import pandas as pd
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
    page_title="FPL Scouting Hub",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded",
)


# =========================================================
# CUSTOM CSS
# =========================================================

st.markdown(
    """
    <style>
    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 3rem;
    }

    .hero-card {
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
        padding: 26px;
        margin-bottom: 20px;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.25);
    }

    .hero-title {
        color: #ffffff;
        font-size: 2.25rem;
        font-weight: 850;
        margin: 0;
    }

    .hero-subtitle {
        color: #b7c0cc;
        font-size: 1rem;
        margin-top: 8px;
        margin-bottom: 0;
    }

    .section-card {
        background: #161b22;
        border: 1px solid #30363d;
        border-radius: 14px;
        padding: 17px;
        margin-bottom: 12px;
        min-height: 135px;
    }

    .section-card h3 {
        color: #ffffff;
        font-size: 1.05rem;
        margin-top: 0;
        margin-bottom: 7px;
    }

    .section-card p {
        color: #aab3bf;
        font-size: 0.88rem;
        margin-bottom: 0;
    }

    .deadline-card {
        background: linear-gradient(
            135deg,
            #37003c 0%,
            #5c0b63 100%
        );
        border: 1px solid #8d4194;
        border-radius: 14px;
        padding: 18px;
        margin-bottom: 18px;
        color: #ffffff;
    }

    .deadline-card h3 {
        margin: 0 0 6px 0;
        color: #ffffff;
    }

    .deadline-card p {
        margin: 0;
        color: #e9d8ec;
    }

    .news-item {
        background: #161b22;
        border: 1px solid #30363d;
        border-left: 4px solid #ff4b4b;
        border-radius: 10px;
        padding: 11px 13px;
        margin-bottom: 8px;
    }

    .news-player {
        font-weight: 800;
        color: #ffffff;
    }

    .news-team {
        color: #87909d;
        font-size: 0.78rem;
    }

    .news-text {
        color: #c9d1d9;
        font-size: 0.86rem;
        margin-top: 4px;
    }

    .trend-up {
        color: #00ff87;
        font-weight: 800;
    }

    .trend-down {
        color: #ff6078;
        font-weight: 800;
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

    div.stButton > button,
    div[data-testid="stLinkButton"] > a {
        border-radius: 9px;
        font-weight: 750;
    }

    @media (max-width: 700px) {
        .hero-card {
            padding: 18px;
        }

        .hero-title {
            font-size: 1.65rem;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# API HELPERS
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
def get_entry_data(entry_id):
    return api_get(f"entry/{entry_id}/")


@st.cache_data(ttl=300, show_spinner=False)
def get_league_data(league_id):
    return api_get(
        f"leagues-classic/{league_id}/standings/"
    )


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
            return "Deadline has passed"

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
            f"{days} days, {hours} hours "
            f"and {minutes} minutes remaining"
        )

    except ValueError:
        return "Countdown unavailable"


def get_current_and_next_events(events):
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

    return current_event, next_event


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
    "🔄 Refresh Homepage",
    use_container_width=True,
):
    st.cache_data.clear()
    st.rerun()

st.sidebar.markdown("---")

st.sidebar.caption(
    "Default settings apply across your FPL Scouting Hub."
)


# =========================================================
# HERO
# =========================================================

st.markdown(
    """
    <div class="hero-card">
        <p class="hero-title">
            ⚽ FPL Scouting Hub
        </p>
        <p class="hero-subtitle">
            Your mini-league mission control for rival scouting,
            transfers, player news and gameweek planning.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# MAIN CONTENT
# =========================================================

try:
    if not str(entry_id).strip().isdigit():
        st.error(
            "Your Entry ID must contain numbers only."
        )
        st.stop()

    if not str(league_id).strip().isdigit():
        st.error(
            "Your League ID must contain numbers only."
        )
        st.stop()

    with st.spinner("Loading the latest FPL information..."):
        bootstrap = get_bootstrap_data()
        entry = get_entry_data(entry_id)
        league = get_league_data(league_id)

    players = bootstrap.get("elements", [])
    teams = bootstrap.get("teams", [])
    events = bootstrap.get("events", [])

    team_lookup = {
        team["id"]: team["name"]
        for team in teams
    }

    current_event, next_event = (
        get_current_and_next_events(events)
    )

    league_name = league.get(
        "league",
        {},
    ).get(
        "name",
        "Your Mini-League",
    )

    standings = league.get(
        "standings",
        {},
    ).get(
        "results",
        [],
    )

    your_league_row = next(
        (
            manager
            for manager in standings
            if safe_int(manager.get("entry"))
            == safe_int(entry_id)
        ),
        None,
    )

    # =====================================================
    # DEADLINE
    # =====================================================

    if next_event:
        deadline_name = next_event.get(
            "name",
            "Next Gameweek",
        )

        deadline_text = next_event.get(
            "deadline_time",
        )

        st.markdown(
            f"""
            <div class="deadline-card">
                <h3>
                    ⏰ {html.escape(deadline_name)} Deadline
                </h3>
                <p>
                    {html.escape(format_deadline(deadline_text))}
                    · {html.escape(deadline_countdown(deadline_text))}
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # =====================================================
    # YOUR TEAM METRICS
    # =====================================================

    st.subheader("👤 Your FPL Snapshot")

    metric_1, metric_2, metric_3 = st.columns(3)
    metric_4, metric_5, metric_6 = st.columns(3)

    metric_1.metric(
        "Team",
        entry.get("name", "Unknown"),
    )

    metric_2.metric(
        "Total Points",
        safe_int(
            entry.get("summary_overall_points")
        ),
    )

    metric_3.metric(
        "Overall Rank",
        format_rank(
            entry.get("summary_overall_rank")
        ),
    )

    if your_league_row:
        metric_4.metric(
            f"Rank in {league_name}",
            f"#{your_league_row.get('rank', '?')}",
        )

        league_leader_points = safe_int(
            standings[0].get("total")
        )

        your_points = safe_int(
            your_league_row.get("total")
        )

        gap_to_leader = (
            league_leader_points - your_points
        )

        metric_5.metric(
            "Gap to League Leader",
            f"{gap_to_leader} pts",
        )

    else:
        metric_4.metric(
            "Mini-League Rank",
            "Not found",
        )

        metric_5.metric(
            "Gap to Leader",
            "Unavailable",
        )

    team_value = (
        safe_int(
            entry.get("last_deadline_value")
        )
        / 10
    )

    metric_6.metric(
        "Squad Value",
        f"£{team_value:.1f}m",
    )

    st.markdown("---")

    # =====================================================
    # NAVIGATION CARDS
    # =====================================================

    st.subheader("🧭 Scouting Tools")

    nav_1, nav_2, nav_3 = st.columns(3)

    with nav_1:
        st.markdown(
            """
            <div class="section-card">
                <h3>🏆 League Dashboard</h3>
                <p>
                    View league standings, podium positions,
                    rank movement and gaps to the leader.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.page_link(
            "pages/1_League_Dashboard.py",
            label="Open League Dashboard",
            icon="🏆",
            use_container_width=True,
        )

    with nav_2:
        st.markdown(
            """
            <div class="section-card">
                <h3>🔍 Rival Viewer</h3>
                <p>
                    Inspect rival squads, captain choices,
                    transfers, chips and player availability.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.page_link(
            "pages/2_Rival_Viewer.py",
            label="Open Rival Viewer",
            icon="🔍",
            use_container_width=True,
        )

    with nav_3:
        st.markdown(
            """
            <div class="section-card">
                <h3>⚔️ Squad Comparison</h3>
                <p>
                    Compare shared players, differentials,
                    captains, values and chip strategies.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.page_link(
            "pages/3_Squad_Comparison.py",
            label="Open Squad Comparison",
            icon="⚔️",
            use_container_width=True,
        )

    nav_4, nav_5 = st.columns(2)

    with nav_4:
        st.markdown(
            """
            <div class="section-card">
                <h3>🔄 Transfer Intelligence</h3>
                <p>
                    Review transfer histories, points hits,
                    activity levels and popular moves.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.page_link(
            "pages/4_Transfer_Intelligence.py",
            label="Open Transfer Intelligence",
            icon="🔄",
            use_container_width=True,
        )

    with nav_5:
        st.markdown(
            """
            <div class="section-card">
                <h3>🤖 AI Insights</h3>
                <p>
                    Read automated summaries of league form,
                    captaincy, transfers and rival threats.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.page_link(
            "pages/7_AI_Insights.py",
            label="Open AI Insights",
            icon="🤖",
            use_container_width=True,
        )

    st.markdown("---")

    # =====================================================
    # LIVE FPL UPDATES
    # =====================================================

    update_column, trends_column = st.columns(
        [1.15, 1]
    )

    with update_column:
        st.subheader("🚨 Latest Player Updates")

        player_updates = [
            player
            for player in players
            if player.get("news")
        ]

        player_updates = sorted(
            player_updates,
            key=lambda player: (
                safe_int(
                    player.get(
                        "chance_of_playing_next_round"
                    ),
                    101,
                ),
                -safe_int(
                    player.get("transfers_in_event")
                ),
            ),
        )[:8]

        if player_updates:
            for player in player_updates:
                player_name = html.escape(
                    str(
                        player.get(
                            "web_name",
                            "Unknown",
                        )
                    )
                )

                club_name = html.escape(
                    team_lookup.get(
                        player.get("team"),
                        "Unknown Club",
                    )
                )

                news = html.escape(
                    str(player.get("news", ""))
                )

                chance = player.get(
                    "chance_of_playing_next_round"
                )

                chance_text = ""

                if chance is not None:
                    chance_text = (
                        f" · {chance}% chance of playing"
                    )

                st.markdown(
                    f"""
                    <div class="news-item">
                        <div class="news-player">
                            🚨 {player_name}
                        </div>
                        <div class="news-team">
                            {club_name}{chance_text}
                        </div>
                        <div class="news-text">
                            {news}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        else:
            st.success(
                "No major player availability updates "
                "are currently listed."
            )

    with trends_column:
        st.subheader("🔥 Transfer Market")

        transfer_tab, price_tab = st.tabs(
            [
                "Popular Transfers",
                "Price Changes",
            ]
        )

        with transfer_tab:
            popular_transfers = sorted(
                players,
                key=lambda player: safe_int(
                    player.get("transfers_in_event")
                ),
                reverse=True,
            )[:8]

            transfer_rows = []

            for player in popular_transfers:
                transfer_rows.append(
                    {
                        "Player": player.get(
                            "web_name",
                            "Unknown",
                        ),
                        "Club": team_lookup.get(
                            player.get("team"),
                            "Unknown",
                        ),
                        "Transfers In": safe_int(
                            player.get(
                                "transfers_in_event"
                            )
                        ),
                        "Price": (
                            f"£{safe_int(player.get('now_cost')) / 10:.1f}m"
                        ),
                    }
                )

            st.dataframe(
                pd.DataFrame(transfer_rows),
                hide_index=True,
                use_container_width=True,
            )

        with price_tab:
            price_risers = sorted(
                [
                    player
                    for player in players
                    if safe_int(
                        player.get("cost_change_event")
                    ) > 0
                ],
                key=lambda player: safe_int(
                    player.get("cost_change_event")
                ),
                reverse=True,
            )[:6]

            price_fallers = sorted(
                [
                    player
                    for player in players
                    if safe_int(
                        player.get("cost_change_event")
                    ) < 0
                ],
                key=lambda player: safe_int(
                    player.get("cost_change_event")
                ),
            )[:6]

            if price_risers:
                st.markdown(
                    "<div class='trend-up'>📈 Price Risers</div>",
                    unsafe_allow_html=True,
                )

                for player in price_risers:
                    change = (
                        safe_int(
                            player.get(
                                "cost_change_event"
                            )
                        )
                        / 10
                    )

                    st.write(
                        f"**{player.get('web_name')}** "
                        f"to £{safe_int(player.get('now_cost')) / 10:.1f}m "
                        f"(+£{change:.1f}m)"
                    )

            if price_fallers:
                st.markdown(
                    "<div class='trend-down'>📉 Price Fallers</div>",
                    unsafe_allow_html=True,
                )

                for player in price_fallers:
                    change = abs(
                        safe_int(
                            player.get(
                                "cost_change_event"
                            )
                        )
                        / 10
                    )

                    st.write(
                        f"**{player.get('web_name')}** "
                        f"to £{safe_int(player.get('now_cost')) / 10:.1f}m "
                        f"(-£{change:.1f}m)"
                    )

            if not price_risers and not price_fallers:
                st.info(
                    "No price changes are currently recorded "
                    "for this gameweek."
                )

    st.markdown("---")

    # =====================================================
    # GAMEWEEK HEADLINES
    # =====================================================

    st.subheader("📊 Gameweek Headlines")

    headline_1, headline_2, headline_3 = st.columns(3)

    if current_event:
        headline_1.metric(
            "Current Gameweek",
            current_event.get(
                "name",
                "Unavailable",
            ),
        )

        headline_2.metric(
            "Average Score",
            safe_int(
                current_event.get(
                    "average_entry_score"
                )
            ),
        )

        headline_3.metric(
            "Highest Score",
            safe_int(
                current_event.get(
                    "highest_score"
                )
            ),
        )

    else:
        headline_1.metric(
            "Current Gameweek",
            "Between gameweeks",
        )

        headline_2.metric(
            "Average Score",
            "Unavailable",
        )

        headline_3.metric(
            "Highest Score",
            "Unavailable",
        )

    st.markdown("---")

    # =====================================================
    # OFFICIAL FPL LINKS
    # =====================================================

    st.subheader("📰 Official FPL News")

    st.write(
        "Open the official FPL Scout for articles, "
        "captaincy analysis, injury updates and transfer advice."
    )

    link_1, link_2, link_3 = st.columns(3)

    with link_1:
        st.link_button(
            "📰 Latest FPL Scout News",
            "https://www.premierleague.com/en/fantasy",
            use_container_width=True,
        )

    with link_2:
        st.link_button(
            "🚨 Official Injury Updates",
            "https://www.premierleague.com/en/fantasy/injuries",
            use_container_width=True,
        )

    with link_3:
        st.link_button(
            "⚽ Open Fantasy Premier League",
            "https://fantasy.premierleague.com/",
            use_container_width=True,
        )

    st.caption(
        "Player updates, prices and transfer statistics "
        "are retrieved from the official FPL data feed."
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
        f"{status_code}. Check your League ID and "
        f"Entry ID, then try refreshing."
    )

except requests.exceptions.Timeout:
    st.error(
        "The FPL service took too long to respond. "
        "Please refresh the homepage and try again."
    )

except requests.exceptions.ConnectionError:
    st.error(
        "The app could not connect to the FPL service. "
        "Please try again shortly."
    )

except Exception as error:
    st.error(
        "An unexpected error occurred while loading "
        "the homepage."
    )

    with st.expander("Technical error details"):
        st.code(str(error))
