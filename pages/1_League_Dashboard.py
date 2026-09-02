import html
from datetime import datetime, timezone

import pandas as pd
import plotly.express as px
import requests
import streamlit as st

DEFAULT_LEAGUE_ID = "1116047"
DEFAULT_ENTRY_ID = "6074290"

BASE_URL = "https://fantasy.premierleague.com/api"

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json",
}

st.set_page_config(
    page_title="League Dashboard",
    page_icon="🏆",
    layout="wide",
)

# =========================================================
# STYLING
# =========================================================

st.markdown(
    """
<style>
.block-container {
    padding-top: 1.4rem;
    padding-bottom: 3rem;
}

.hero {
    background:
        radial-gradient(
            circle at top right,
            rgba(0, 255, 135, 0.20),
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
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.25);
}

.hero h1 {
    margin: 0;
    color: white;
    font-size: 2rem;
}

.hero p {
    margin: 7px 0 0;
    color: #b7c0cc;
}

.deadline {
    background: linear-gradient(
        135deg,
        #37003c,
        #5a0961
    );
    border: 1px solid #89428f;
    border-radius: 13px;
    padding: 13px 17px;
    color: white;
    margin-bottom: 18px;
}

.deadline strong {
    color: #00ff87;
}

.podium {
    position: relative;
    background: linear-gradient(
        145deg,
        #1c2330,
        #121720
    );
    border: 1px solid #303b4d;
    border-radius: 16px;
    padding: 19px 10px;
    min-height: 158px;
    text-align: center;
    overflow: hidden;
}

.podium::before {
    content: "";
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 6px;
    background: var(--medal);
}

.medal {
    font-size: 2rem;
}

.place {
    font-size: 0.70rem;
    letter-spacing: 0.08rem;
    color: #9ba7b4;
    font-weight: 800;
}

.pmanager {
    color: white;
    font-weight: 850;
    margin-top: 7px;
}

.pteam {
    color: #9ba7b4;
    font-size: 0.78rem;
}

.ppoints {
    display: inline-block;
    margin-top: 10px;
    background: rgba(255, 255, 255, 0.09);
    color: white;
    border-radius: 8px;
    padding: 5px 10px;
    font-weight: 800;
}

.personal {
    background: linear-gradient(
        135deg,
        rgba(0, 255, 135, 0.15),
        rgba(0, 255, 135, 0.04)
    );
    border: 1px solid rgba(0, 255, 135, 0.45);
    border-radius: 14px;
    padding: 15px;
    margin-bottom: 14px;
}

.personal h3 {
    color: white;
    margin: 0 0 4px;
}

.personal p {
    color: #b7c0cc;
    margin: 0;
}

.card {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 13px;
    padding: 14px;
    min-height: 110px;
}

.card h4 {
    margin: 0 0 6px;
    color: white;
}

.card p {
    margin: 0;
    color: #aab3bf;
}

.award {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 13px;
    padding: 14px 7px;
    min-height: 125px;
    text-align: center;
}

.award-icon {
    font-size: 1.65rem;
}

.award-title {
    color: #98a3b1;
    font-size: 0.68rem;
    font-weight: 800;
    letter-spacing: 0.05rem;
}

.award-name {
    color: white;
    font-weight: 850;
    margin-top: 6px;
}

.award-detail {
    color: #00ff87;
    font-size: 0.78rem;
    margin-top: 3px;
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

@media (max-width: 700px) {
    .hero {
        padding: 17px;
    }

    .hero h1 {
        font-size: 1.55rem;
    }

    .podium {
        min-height: 140px;
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
    response = requests.get(
        f"{BASE_URL}/{endpoint.lstrip('/')}",
        headers=HEADERS,
        timeout=timeout,
    )

    response.raise_for_status()

    return response.json()


@st.cache_data(ttl=1800, show_spinner=False)
def get_bootstrap():
    return api_get("bootstrap-static/")


@st.cache_data(ttl=300, show_spinner=False)
def get_manager(selected_entry_id):
    return api_get(
        f"entry/{selected_entry_id}/"
    )


@st.cache_data(ttl=300, show_spinner=False)
def get_league(selected_league_id):
    results = []
    league_info = {}
    page = 1

    while True:
        data = api_get(
            f"leagues-classic/"
            f"{selected_league_id}/standings/"
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


def safe_int(value, fallback=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return fallback


def ordinal(number):
    number = safe_int(number)

    if 10 <= number % 100 <= 20:
        suffix = "th"
    else:
        suffix = {
            1: "st",
            2: "nd",
            3: "rd",
        }.get(
            number % 10,
            "th",
        )

    return f"{number}{suffix}"


def format_rank(value):
    rank = safe_int(value)

    if rank > 0:
        return f"{rank:,}"

    return "Unavailable"


def movement_text(value):
    value = safe_int(value)

    if value > 0:
        return f"Up {value}"

    if value < 0:
        return f"Down {abs(value)}"

    return "No change"


def format_deadline(value):
    try:
        deadline = datetime.fromisoformat(
            value.replace(
                "Z",
                "+00:00",
            )
        )

        return deadline.strftime(
            "%A %d %B at %H:%M"
        )

    except (AttributeError, ValueError):
        return "Deadline unavailable"


def countdown(value):
    try:
        deadline = datetime.fromisoformat(
            value.replace(
                "Z",
                "+00:00",
            )
        )

        remaining = (
            deadline
            - datetime.now(timezone.utc)
        )

        if remaining.total_seconds() <= 0:
            return "Deadline passed"

        minutes = int(
            remaining.total_seconds() // 60
        )

        days, minutes = divmod(
            minutes,
            1440,
        )

        hours, minutes = divmod(
            minutes,
            60,
        )

        return (
            f"{days}d {hours}h "
            f"{minutes}m remaining"
        )

    except (AttributeError, ValueError):
        return "Countdown unavailable"


def make_dataframe(results):
    rows = []

    for manager in results:
        rank = safe_int(
            manager.get("rank")
        )

        last_rank = safe_int(
            manager.get("last_rank"),
            rank,
        )

        movement = last_rank - rank

        if movement > 0:
            trend = "▲"
        elif movement < 0:
            trend = "▼"
        else:
            trend = "•"

        rows.append(
            {
                "Entry ID": safe_int(
                    manager.get("entry")
                ),
                "Rank": rank,
                "Trend": trend,
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

    if not rows:
        return pd.DataFrame()

    return (
        pd.DataFrame(rows)
        .sort_values("Rank")
        .reset_index(drop=True)
    )


def podium_html(row, position):
    styles = {
        1: (
            "🥇",
            "FIRST PLACE",
            "#FFD700",
        ),
        2: (
            "🥈",
            "SECOND PLACE",
            "#C0C0C0",
        ),
        3: (
            "🥉",
            "THIRD PLACE",
            "#CD7F32",
        ),
    }

    medal, label, colour = (
        styles[position]
    )

    return f"""
<div
    class="podium"
    style="--medal:{colour}"
>
    <div class="medal">
        {medal}
    </div>

    <div class="place">
        {label}
    </div>

    <div class="pmanager">
        {html.escape(str(row["Manager"]))}
    </div>

    <div class="pteam">
        {html.escape(str(row["Team"]))}
    </div>

    <div class="ppoints">
        {safe_int(row["Total Points"])} points
    </div>
</div>
"""


# =========================================================
# MAIN DASHBOARD
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
        "Loading league standings..."
    ):
        league_info, raw_results = (
            get_league(
                league_id.strip()
            )
        )

        manager_data = get_manager(
            entry_id.strip()
        )

        bootstrap = get_bootstrap()

    league_df = make_dataframe(
        raw_results
    )

    if league_df.empty:
        st.error(
            "No standings were found. "
            "Check the Mini-League ID."
        )

        st.stop()

    league_name = league_info.get(
        "name",
        "FPL Mini-League",
    )

    leader = league_df.iloc[0]

    my_rows = league_df[
        league_df["Entry ID"]
        == safe_int(entry_id)
    ]

    if my_rows.empty:
        my_row = None
    else:
        my_row = my_rows.iloc[0]

    events = bootstrap.get(
        "events",
        [],
    )

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
        next_event = next(
            (
                event
                for event in events
                if not event.get("finished")
            ),
            None,
        )

    # =====================================================
    # HEADER
    # =====================================================

    st.markdown(
        f"""
<div class="hero">
    <h1>
        🏆 {html.escape(league_name)}
    </h1>

    <p>
        Live standings, rank movement,
        gameweek performance and
        mini-league insights.
    </p>
</div>
""",
        unsafe_allow_html=True,
    )

    if next_event:
        deadline = next_event.get(
            "deadline_time"
        )

        event_name = next_event.get(
            "name",
            "Next Gameweek",
        )

        st.markdown(
            f"""
<div class="deadline">
    ⏰ <strong>
        {html.escape(event_name)} deadline:
    </strong>

    {html.escape(format_deadline(deadline))}
    ·
    {html.escape(countdown(deadline))}
</div>
""",
            unsafe_allow_html=True,
        )

    # =====================================================
    # LEAGUE OVERVIEW
    # =====================================================

    league_average = round(
        league_df[
            "Total Points"
        ].mean(),
        1,
    )

    gw_average = round(
        league_df[
            "GW Score"
        ].mean(),
        1,
    )

    spread = (
        safe_int(
            league_df.iloc[0][
                "Total Points"
            ]
        )
        - safe_int(
            league_df.iloc[-1][
                "Total Points"
            ]
        )
    )

    st.subheader(
        "📊 League Overview"
    )

    overview_1, overview_2, overview_3 = (
        st.columns(3)
    )

    overview_4, overview_5, overview_6 = (
        st.columns(3)
    )

    overview_1.metric(
        "League Leader",
        leader["Manager"],
    )

    overview_2.metric(
        "Leader Points",
        safe_int(
            leader["Total Points"]
        ),
    )

    overview_3.metric(
        "Managers",
        len(league_df),
    )

    overview_4.metric(
        "League Average",
        f"{league_average} pts",
    )

    overview_5.metric(
        "Average GW Score",
        f"{gw_average} pts",
    )

    overview_6.metric(
        "First-to-Last Spread",
        f"{spread} pts",
    )

    # =====================================================
    # PODIUM
    # =====================================================

    st.markdown("---")

    st.subheader(
        "🏅 League Podium"
    )

    podium_columns = st.columns(3)

    for index, (_, podium_manager) in enumerate(
        league_df.head(3).iterrows()
    ):
        with podium_columnsst.markdown(
                podium_html(
                    podium_manager,
                    index + 1,
                ),
                unsafe_allow_html=True,
            )

    # =====================================================
    # PERSONAL DASHBOARD
    # =====================================================

    st.markdown("---")

    st.subheader(
        "👤 Your League Position"
    )

    my_rank = None
    gap_to_leader = None
    manager_above = None
    gap_to_above = None

    if my_row is not None:
        my_rank = safe_int(
            my_row["Rank"]
        )

        my_points = safe_int(
            my_row["Total Points"]
        )

        my_movement = safe_int(
            my_row["Movement"]
        )

        gap_to_leader = (
            safe_int(
                leader[
                    "Total Points"
                ]
            )
            - my_points
        )

        above_rows = league_df[
            league_df["Rank"] < my_rank
        ]

        below_rows = league_df[
            league_df["Rank"] > my_rank
        ]

        if above_rows.empty:
            manager_above = None
        else:
            manager_above = (
                above_rows.iloc[-1]
            )

        if below_rows.empty:
            manager_below = None
        else:
            manager_below = (
                below_rows.iloc[0]
            )

        if manager_above is None:
            gap_to_above = 0
        else:
            gap_to_above = (
                safe_int(
                    manager_above[
                        "Total Points"
                    ]
                )
                - my_points
            )

        if manager_below is None:
            lead_over_below = 0
        else:
            lead_over_below = (
                my_points
                - safe_int(
                    manager_below[
                        "Total Points"
                    ]
                )
            )

        st.markdown(
            f"""
<div class="personal">
    <h3>
        {html.escape(str(my_row["Team"]))}
    </h3>

    <p>
        Managed by
        {html.escape(str(my_row["Manager"]))}
        · Currently {ordinal(my_rank)}
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
            ordinal(my_rank),
            delta=movement_text(
                my_movement
            ),
        )

        personal_2.metric(
            "Total Points",
            my_points,
        )

        personal_3.metric(
            "Current GW Score",
            safe_int(
                my_row["GW Score"]
            ),
        )

        personal_4.metric(
            "Gap to Leader",
            f"{gap_to_leader} pts",
        )

        if manager_above is not None:
            personal_5.metric(
                (
                    "Gap to "
                    f"{manager_above['Manager']}"
                ),
                f"{gap_to_above} pts",
            )
        else:
            personal_5.metric(
                "Position",
                "League leader",
            )

        if manager_below is not None:
            personal_6.metric(
                (
                    "Lead over "
                    f"{manager_below['Manager']}"
                ),
                f"{lead_over_below} pts",
            )
        else:
            personal_6.metric(
                "Manager Below",
                "None",
            )

        detail_1, detail_2, detail_3 = (
            st.columns(3)
        )

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

        detail_2.metric(
            "Squad Value",
            f"£{squad_value:.1f}m",
        )

        detail_3.metric(
            "Money in Bank",
            f"£{bank:.1f}m",
        )

    else:
        st.warning(
            "Your Entry ID was not found "
            "in this mini-league."
        )

    # =====================================================
    # STANDINGS TABLE
    # =====================================================

    st.markdown("---")

    st.subheader(
        "📋 League Standings"
    )

    control_1, control_2, control_3 = (
        st.columns(
            [2, 1, 1]
        )
    )

    with control_1:
        search = st.text_input(
            "Search manager or team",
            placeholder="Enter a name...",
        )

    with control_2:
        table_limit = st.selectbox(
            "Managers to display",
            [
                "All",
                "Top 5",
                "Top 10",
                "Top 20",
            ],
        )

    with control_3:
        sort_by = st.selectbox(
            "Sort by",
            [
                "League Rank",
                "Gameweek Score",
                "Rank Movement",
            ],
        )

    table = league_df.copy()

    table["Gap to Leader"] = (
        safe_int(
            leader["Total Points"]
        )
        - table["Total Points"]
    )

    table["Rank Movement"] = (
        table["Movement"].apply(
            movement_text
        )
    )

    if search:
        search_mask = (
            table["Manager"].str.contains(
                search,
                case=False,
                na=False,
            )
            |
            table["Team"].str.contains(
                search,
                case=False,
                na=False,
            )
        )

        table = table[
            search_mask
        ]

    if sort_by == "Gameweek Score":
        table = table.sort_values(
            [
                "GW Score",
                "Total Points",
            ],
            ascending=[
                False,
                False,
            ],
        )

    elif sort_by == "Rank Movement":
        table = table.sort_values(
            [
                "Movement",
                "Rank",
            ],
            ascending=[
                False,
                True,
            ],
        )

    else:
        table = table.sort_values(
            "Rank"
        )

    table_limits = {
        "Top 5": 5,
        "Top 10": 10,
        "Top 20": 20,
    }

    if table_limit in table_limits:
        table = table.head(
            table_limits[
                table_limit
            ]
        )

    st.dataframe(
        table[
            [
                "Rank",
                "Trend",
                "Manager",
                "Team",
                "GW Score",
                "Total Points",
                "Gap to Leader",
                "Rank Movement",
            ]
        ],
        hide_index=True,
        use_container_width=True,
    )

    # =====================================================
    # CHARTS
    # =====================================================

    st.markdown("---")

    st.subheader(
        "📈 League Charts"
    )

    chart_df = league_df.copy()

    chart_df["Display Name"] = (
        chart_df["Rank"].astype(str)
        + ". "
        + chart_df["Manager"]
    )

    chart_df["Gap to Leader"] = (
        safe_int(
            leader["Total Points"]
        )
        - chart_df["Total Points"]
    )

    chart_tab_1, chart_tab_2, chart_tab_3 = (
        st.tabs(
            [
                "Total Points",
                "Gameweek Scores",
                "Gap to Leader",
            ]
        )
    )

    with chart_tab_1:
        total_chart = px.bar(
            chart_df.sort_values(
                "Total Points"
            ),
            x="Total Points",
            y="Display Name",
            orientation="h",
            color="Total Points",
            text="Total Points",
            color_continuous_scale=[
                "#37003c",
                "#00ff87",
            ],
            hover_data=[
                "Team",
                "GW Score",
            ],
        )

        total_chart.update_layout(
            height=max(
                430,
                len(chart_df) * 35,
            ),
            coloraxis_showscale=False,
            yaxis_title="",
        )

        st.plotly_chart(
            total_chart,
            use_container_width=True,
        )

    with chart_tab_2:
        gameweek_chart = px.bar(
            chart_df.sort_values(
                "GW Score"
            ),
            x="GW Score",
            y="Display Name",
            orientation="h",
            color="GW Score",
            text="GW Score",
            color_continuous_scale=[
                "#37003c",
                "#00ff87",
            ],
            hover_data=[
                "Team",
                "Total Points",
            ],
        )

        gameweek_chart.update_layout(
            height=max(
                430,
                len(chart_df) * 35,
            ),
            coloraxis_showscale=False,
            yaxis_title="",
        )

        st.plotly_chart(
            gameweek_chart,
            use_container_width=True,
        )

    with chart_tab_3:
        gap_chart = px.bar(
            chart_df.sort_values(
                "Gap to Leader",
                ascending=False,
            ),
            x="Gap to Leader",
            y="Display Name",
            orientation="h",
            color="Gap to Leader",
            text="Gap to Leader",
            color_continuous_scale=[
                "#00ff87",
                "#ff6078",
            ],
            hover_data=[
                "Team",
                "Total Points",
            ],
        )

        gap_chart.update_layout(
            height=max(
                430,
                len(chart_df) * 35,
            ),
            coloraxis_showscale=False,
            yaxis_title="",
        )

        st.plotly_chart(
            gap_chart,
            use_container_width=True,
        )

    # =====================================================
    # MOVERS
    # =====================================================

    positive_movers = league_df[
        league_df["Movement"] > 0
    ]

    negative_movers = league_df[
        league_df["Movement"] < 0
    ]

    if positive_movers.empty:
        biggest_riser = None
    else:
        biggest_riser = (
            positive_movers.loc[
                positive_movers[
                    "Movement"
                ].idxmax()
            ]
        )

    if negative_movers.empty:
        biggest_faller = None
    else:
        biggest_faller = (
            negative_movers.loc[
                negative_movers[
                    "Movement"
                ].idxmin()
            ]
        )

    st.markdown("---")

    st.subheader(
        "🚀 Biggest Movers"
    )

    mover_1, mover_2 = st.columns(2)

    with mover_1:
        if biggest_riser is not None:
            riser_text = (
                f"<strong>"
                f"{html.escape(str(biggest_riser['Manager']))}"
                f"</strong> climbed "
                f"{safe_int(biggest_riser['Movement'])} "
                f"place(s)."
            )
        else:
            riser_text = (
                "No managers moved up "
                "this gameweek."
            )

        st.markdown(
            f"""
<div class="card">
    <h4>🚀 Biggest Riser</h4>
    <p>{riser_text}</p>
</div>
""",
            unsafe_allow_html=True,
        )

    with mover_2:
        if biggest_faller is not None:
            faller_text = (
                f"<strong>"
                f"{html.escape(str(biggest_faller['Manager']))}"
                f"</strong> dropped "
                f"{abs(safe_int(biggest_faller['Movement']))} "
                f"place(s)."
            )
        else:
            faller_text = (
                "No managers moved down "
                "this gameweek."
            )

        st.markdown(
            f"""
<div class="card">
    <h4>📉 Biggest Faller</h4>
    <p>{faller_text}</p>
</div>
""",
            unsafe_allow_html=True,
        )

    # =====================================================
    # AWARDS
    # =====================================================

    best_gw = league_df.loc[
        league_df[
            "GW Score"
        ].idxmax()
    ]

    worst_gw = league_df.loc[
        league_df[
            "GW Score"
        ].idxmin()
    ]

    if len(league_df) > 1:
        challenger = league_df.iloc[1]
    else:
        challenger = leader

    second_place_gap = (
        safe_int(
            leader["Total Points"]
        )
        - safe_int(
            challenger["Total Points"]
        )
    )

    st.markdown("---")

    st.subheader(
        "🏅 League Awards"
    )

    awards = [
        (
            "👑",
            "LEAGUE BOSS",
            leader["Manager"],
            (
                f"{safe_int(leader['Total Points'])} "
                f"points"
            ),
        ),
        (
            "🔥",
            "KING OF THE WEEK",
            best_gw["Manager"],
            (
                f"{safe_int(best_gw['GW Score'])} "
                f"GW points"
            ),
        ),
        (
            "⚔️",
            "CLOSEST CHALLENGER",
            challenger["Manager"],
            (
                f"{second_place_gap} "
                f"points behind"
            ),
        ),
        (
            "🧊",
            "TOUGH GAMEWEEK",
            worst_gw["Manager"],
            (
                f"{safe_int(worst_gw['GW Score'])} "
                f"GW points"
            ),
        ),
    ]

    award_columns = st.columns(4)

    for column, award in zip(
        award_columns,
        awards,
    ):
        icon, title, name, detail = award

        with column:
            st.markdown(
                f"""
<div class="award">
    <div class="award-icon">
        {icon}
    </div>

    <div class="award-title">
        {title}
    </div>

    <div class="award-name">
        {html.escape(str(name))}
    </div>

    <div class="award-detail">
        {detail}
    </div>
</div>
""",
                unsafe_allow_html=True,
            )

    # =====================================================
    # SCOUTING REPORT
    # =====================================================

    st.markdown("---")

    st.subheader(
        "🤖 League Scouting Report"
    )

    if current_event:
        gameweek_name = current_event.get(
            "name",
            "the current gameweek",
        )
    else:
        gameweek_name = (
            "the current gameweek"
        )

    report_lines = [
        (
            f"🏆 **{leader['Manager']}** leads "
            f"with **{safe_int(leader['Total Points'])} "
            f"points**."
        ),
        (
            f"⚔️ The lead over second place is "
            f"**{second_place_gap} points**."
        ),
        (
            f"🔥 **{best_gw['Manager']}** has the "
            f"highest score in {gameweek_name} with "
            f"**{safe_int(best_gw['GW Score'])} points**."
        ),
        (
            f"📊 The total-points average is "
            f"**{league_average}**, while the current "
            f"GW average is **{gw_average}**."
        ),
    ]

    if biggest_riser is not None:
        report_lines.append(
            f"🚀 **{biggest_riser['Manager']}** is "
            f"the biggest climber, gaining "
            f"**{safe_int(biggest_riser['Movement'])} "
            f"place(s)**."
        )

    if my_row is not None:
        report_lines.append(
            f"🎯 Your team is **{ordinal(my_rank)}**, "
            f"**{gap_to_leader} points** behind "
            f"the leader."
        )

        if manager_above is not None:
            report_lines.append(
                f"👀 Your next target is "
                f"**{manager_above['Manager']}**, "
                f"**{gap_to_above} points** ahead."
            )

    st.info(
        "\n\n".join(
            report_lines
        )
    )

# =========================================================
# ERROR HANDLING
# =========================================================

except requests.exceptions.HTTPError as error:
    status = getattr(
        error.response,
        "status_code",
        "Unknown",
    )

    st.error(
        f"The FPL service returned status code "
        f"{status}. Check the IDs and refresh."
    )

except requests.exceptions.Timeout:
    st.error(
        "The FPL service took too long to respond. "
        "Refresh and try again."
    )

except requests.exceptions.ConnectionError:
    st.error(
        "The app could not connect to the FPL service. "
        "Try again shortly."
    )

except Exception as error:
    st.error(
        "An unexpected error occurred while loading "
        "the League Dashboard."
    )

    with st.expander(
        "Technical error details"
    ):
        st.code(
            str(error)
        )
