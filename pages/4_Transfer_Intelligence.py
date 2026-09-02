import html
from collections import Counter
from datetime import datetime

import pandas as pd
import plotly.graph_objects as go
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
    page_title="Transfer Intelligence",
    page_icon="🔄",
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

.insight-card {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 13px;
    padding: 14px;
    min-height: 112px;
}

.insight-card h4 {
    margin: 0 0 7px;
    color: #ffffff;
}

.insight-card p {
    margin: 0;
    color: #aab3bf;
}

.award {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 13px;
    padding: 14px 8px;
    min-height: 128px;
    text-align: center;
}

.award-icon {
    font-size: 1.7rem;
}

.award-title {
    color: #98a3b1;
    font-size: 0.68rem;
    font-weight: 800;
    letter-spacing: 0.05rem;
}

.award-name {
    color: #ffffff;
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
        font-size: 1.5rem;
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
    "🔄 Refresh Transfer Data",
    width="stretch",
):
    st.cache_data.clear()
    st.rerun()

st.sidebar.caption(
    "Public transfer data is cached for five minutes."
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
def get_live(gameweek):
    return api_get(
        f"event/{gameweek}/live/"
    )


# =========================================================
# HELPER FUNCTIONS
# =========================================================

def safe_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def format_time(value):
    try:
        transfer_time = datetime.fromisoformat(
            value.replace(
                "Z",
                "+00:00",
            )
        )

        return transfer_time.strftime(
            "%d %b %Y, %H:%M"
        )

    except (AttributeError, ValueError):
        return str(
            value or "Unknown"
        )


def make_history_map(history):
    return {
        safe_int(row.get("event")): row
        for row in history.get(
            "current",
            [],
        )
    }


def player_points(
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


def create_transfer_dataframe(records):
    columns = [
        "Manager",
        "Team",
        "GW",
        "Player In",
        "Player Out",
        "In Price",
        "Out Price",
        "Time",
        "Incoming Points",
        "Outgoing Points",
        "Hit Cost",
        "Net Impact",
        "Result",
    ]

    if not records:
        return pd.DataFrame(
            columns=columns
        )

    return pd.DataFrame(
        records,
        columns=columns,
    )


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
        "Loading league transfer activity..."
    ):
        bootstrap = get_bootstrap()

        league_info, managers = (
            get_league(
                league_id.strip()
            )
        )

    players = {
        player["id"]: player
        for player in bootstrap.get(
            "elements",
            [],
        )
    }

    events = bootstrap.get(
        "events",
        [],
    )

    # =====================================================
    # HERO
    # =====================================================

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
        f'<h1>🔄 Transfer Intelligence</h1>'
        f'<p>'
        f'League-wide transfer trends, '
        f'hit analysis and market behaviour '
        f'for {league_name}.'
        f'</p>'
        f'</div>'
    )

    st.markdown(
        hero_html,
        unsafe_allow_html=True,
    )

    # =====================================================
    # LOAD MANAGER HISTORIES
    # =====================================================

    manager_payload = []

    progress = st.progress(
        0,
        text=(
            "Collecting public histories "
            "and transfers..."
        ),
    )

    total_managers = max(
        len(managers),
        1,
    )

    for index, manager in enumerate(
        managers,
        start=1,
    ):
        manager_entry = str(
            manager.get("entry")
        )

        try:
            transfers = get_transfers(
                manager_entry
            )

            history = get_history(
                manager_entry
            )

        except requests.RequestException:
            transfers = []

            history = {
                "current": [],
            }

        manager_payload.append(
            {
                "entry": safe_int(
                    manager.get("entry")
                ),
                "manager": manager.get(
                    "player_name",
                    "Unknown Manager",
                ),
                "team": manager.get(
                    "entry_name",
                    "Unknown Team",
                ),
                "rank": safe_int(
                    manager.get("rank")
                ),
                "transfers": transfers,
                "history": history,
                "history_map": make_history_map(
                    history
                ),
            }
        )

        progress.progress(
            index / total_managers,
            text=(
                f"Loaded {index} of "
                f"{total_managers} managers"
            ),
        )

    progress.empty()

    available_gameweeks = sorted(
        {
            gameweek
            for item in manager_payload
            for gameweek in item[
                "history_map"
            ].keys()
        },
        reverse=True,
    )

    if not available_gameweeks:
        st.error(
            "No gameweek history is available "
            "for this league."
        )

        st.stop()

    # =====================================================
    # PAGE CONTROLS
    # =====================================================

    control_1, control_2 = (
        st.columns(2)
    )

    with control_1:
        selected_gameweek = st.selectbox(
            "Gameweek",
            available_gameweeks,
            index=0,
            format_func=lambda value: (
                f"Gameweek {value}"
            ),
        )

    with control_2:
        analysis_period = st.selectbox(
            "Analysis period",
            [
                "Selected gameweek",
                "Last 5 gameweeks",
                "Full season",
            ],
        )

    if analysis_period == "Selected gameweek":
        period_gameweeks = {
            selected_gameweek
        }

    elif analysis_period == "Last 5 gameweeks":
        period_gameweeks = set(
            [
                gameweek
                for gameweek in available_gameweeks
                if gameweek <= selected_gameweek
            ][:5]
        )

    else:
        period_gameweeks = {
            gameweek
            for gameweek in available_gameweeks
            if gameweek <= selected_gameweek
        }

    # =====================================================
    # LOAD LIVE GAMEWEEK POINTS
    # =====================================================

    live_by_gameweek = {}

    with st.spinner(
        "Calculating transfer impact..."
    ):
        for gameweek in period_gameweeks:
            try:
                live_data = get_live(
                    gameweek
                )

                live_by_gameweek[
                    gameweek
                ] = {
                    item["id"]: item
                    for item in live_data.get(
                        "elements",
                        [],
                    )
                }

            except requests.RequestException:
                live_by_gameweek[
                    gameweek
                ] = {}

    # =====================================================
    # BUILD TRANSFER ANALYSIS
    # =====================================================

    transfer_records = []
    activity_rows = []
    inactive_selected_gameweek = []

    for manager in manager_payload:
        relevant_transfers = [
            transfer
            for transfer in manager[
                "transfers"
            ]
            if safe_int(
                transfer.get("event")
            ) in period_gameweeks
        ]

        selected_transfers = [
            transfer
            for transfer in manager[
                "transfers"
            ]
            if safe_int(
                transfer.get("event")
            ) == selected_gameweek
        ]

        if not selected_transfers:
            inactive_selected_gameweek.append(
                manager["manager"]
            )

        period_hit_cost = sum(
            safe_int(
                manager["history_map"]
                .get(
                    gameweek,
                    {},
                )
                .get(
                    "event_transfers_cost"
                )
            )
            for gameweek in period_gameweeks
        )

        active_gameweeks = len(
            {
                safe_int(
                    transfer.get("event")
                )
                for transfer in relevant_transfers
            }
        )

        activity_rows.append(
            {
                "Manager": manager[
                    "manager"
                ],
                "Team": manager[
                    "team"
                ],
                "League Rank": manager[
                    "rank"
                ],
                "Transfers": len(
                    relevant_transfers
                ),
                "Active GWs": active_gameweeks,
                "No-Transfer GWs": max(
                    len(period_gameweeks)
                    - active_gameweeks,
                    0,
                ),
                "Hit Cost": period_hit_cost,
            }
        )

        transfers_by_gameweek = {}

        for transfer in relevant_transfers:
            transfer_gameweek = safe_int(
                transfer.get("event")
            )

            transfers_by_gameweek.setdefault(
                transfer_gameweek,
                [],
            ).append(
                transfer
            )

        for (
            transfer_gameweek,
            gameweek_transfers,
        ) in transfers_by_gameweek.items():
            total_gameweek_hit = safe_int(
                manager["history_map"]
                .get(
                    transfer_gameweek,
                    {},
                )
                .get(
                    "event_transfers_cost"
                )
            )

            if gameweek_transfers:
                allocated_hit = (
                    total_gameweek_hit
                    / len(gameweek_transfers)
                )
            else:
                allocated_hit = 0

            live_lookup = (
                live_by_gameweek.get(
                    transfer_gameweek,
                    {},
                )
            )

            for transfer in gameweek_transfers:
                incoming_id = transfer.get(
                    "element_in"
                )

                outgoing_id = transfer.get(
                    "element_out"
                )

                incoming_points = (
                    player_points(
                        incoming_id,
                        live_lookup,
                    )
                )

                outgoing_points = (
                    player_points(
                        outgoing_id,
                        live_lookup,
                    )
                )

                net_impact = (
                    incoming_points
                    - outgoing_points
                    - allocated_hit
                )

                if net_impact > 0:
                    result = "Paid off"

                elif net_impact < 0:
                    result = "Failed"

                else:
                    result = "Break-even"

                transfer_records.append(
                    {
                        "Manager": manager[
                            "manager"
                        ],
                        "Team": manager[
                            "team"
                        ],
                        "GW": transfer_gameweek,
                        "Player In": players.get(
                            incoming_id,
                            {},
                        ).get(
                            "web_name",
                            "Unknown",
                        ),
                        "Player Out": players.get(
                            outgoing_id,
                            {},
                        ).get(
                            "web_name",
                            "Unknown",
                        ),
                        "In Price": (
                            f"£{safe_int(transfer.get('element_in_cost')) / 10:.1f}m"
                        ),
                        "Out Price": (
                            f"£{safe_int(transfer.get('element_out_cost')) / 10:.1f}m"
                        ),
                        "Time": format_time(
                            transfer.get("time")
                        ),
                        "Incoming Points": (
                            incoming_points
                        ),
                        "Outgoing Points": (
                            outgoing_points
                        ),
                        "Hit Cost": round(
                            allocated_hit,
                            1,
                        ),
                        "Net Impact": round(
                            net_impact,
                            1,
                        ),
                        "Result": result,
                    }
                )

    transfers_df = (
        create_transfer_dataframe(
            transfer_records
        )
    )

    activity_df = pd.DataFrame(
        activity_rows
    )

    if transfers_df.empty:
        selected_gameweek_df = (
            transfers_df.copy()
        )
    else:
        selected_gameweek_df = (
            transfers_df[
                transfers_df["GW"]
                == selected_gameweek
            ].copy()
        )

    total_transfers = len(
        transfers_df
    )

    if activity_df.empty:
        active_managers = 0
        total_hits = 0
    else:
        active_managers = int(
            activity_df[
                "Transfers"
            ].gt(0).sum()
        )

        total_hits = int(
            activity_df[
                "Hit Cost"
            ].sum()
        )

    if transfers_df.empty:
        total_net_impact = 0.0
    else:
        total_net_impact = float(
            transfers_df[
                "Net Impact"
            ].sum()
        )

    # =====================================================
    # TRANSFER WINDOW OVERVIEW
    # =====================================================

    st.subheader(
        "📊 Transfer Window Overview"
    )

    metric_1, metric_2 = st.columns(2)
    metric_3, metric_4 = st.columns(2)

    metric_1.metric(
        "Transfers",
        total_transfers,
    )

    metric_2.metric(
        "Active Managers",
        (
            f"{active_managers}/"
            f"{len(manager_payload)}"
        ),
    )

    metric_3.metric(
        "Points Spent on Hits",
        total_hits,
    )

    metric_4.metric(
        "Immediate Net Impact",
        f"{total_net_impact:+.1f} pts",
    )

    st.caption(
        "Immediate impact compares incoming and outgoing "
        "player points in the transfer gameweek. Hit costs "
        "are shared across a manager's transfers for the estimate."
    )

    # =====================================================
    # LEAGUE TRANSFER FEED
    # =====================================================

    st.markdown("---")

    st.subheader(
        "🛰️ League Transfer Feed"
    )

    if analysis_period == "Selected gameweek":
        feed_source = (
            selected_gameweek_df
        )
    else:
        feed_source = transfers_df

    if feed_source.empty:
        st.info(
            "No public transfers were recorded "
            "for this period."
        )

    else:
        transfer_feed = (
            feed_source
            .sort_values(
                [
                    "GW",
                    "Time",
                ],
                ascending=[
                    False,
                    False,
                ],
            )
        )

        st.dataframe(
            transfer_feed[
                [
                    "Manager",
                    "Team",
                    "GW",
                    "Player Out",
                    "Player In",
                    "Out Price",
                    "In Price",
                    "Time",
                    "Net Impact",
                    "Result",
                ]
            ],
            hide_index=True,
            width="stretch",
        )

    # =====================================================
    # MOST BOUGHT AND SOLD
    # =====================================================

    st.markdown("---")

    st.subheader(
        "📈 Most Bought and Sold"
    )

    if transfers_df.empty:
        bought_counter = Counter()
        sold_counter = Counter()

    else:
        bought_counter = Counter(
            transfers_df["Player In"]
        )

        sold_counter = Counter(
            transfers_df["Player Out"]
        )

    bought_df = pd.DataFrame(
        bought_counter.most_common(10),
        columns=[
            "Player",
            "Times Bought",
        ],
    )

    sold_df = pd.DataFrame(
        sold_counter.most_common(10),
        columns=[
            "Player",
            "Times Sold",
        ],
    )

    bought_column, sold_column = (
        st.columns(2)
    )

    with bought_column:
        st.markdown(
            "#### 🟢 Most Bought"
        )

        if bought_df.empty:
            st.info(
                "No purchases were found."
            )
        else:
            st.dataframe(
                bought_df,
                hide_index=True,
                width="stretch",
            )

    with sold_column:
        st.markdown(
            "#### 🔴 Most Sold"
        )

        if sold_df.empty:
            st.info(
                "No sales were found."
            )
        else:
            st.dataframe(
                sold_df,
                hide_index=True,
                width="stretch",
            )

    # =====================================================
    # ACTIVITY LEADERBOARD
    # =====================================================

    st.markdown("---")

    st.subheader(
        "🏃 Transfer Activity Leaderboard"
    )

    if activity_df.empty:
        st.info(
            "No manager activity is available."
        )

    else:
        activity_df[
            "Average per Active GW"
        ] = activity_df.apply(
            lambda row: round(
                row["Transfers"]
                / row["Active GWs"],
                2,
            )
            if row["Active GWs"]
            else 0,
            axis=1,
        )

        activity_leaderboard = (
            activity_df
            .sort_values(
                [
                    "Transfers",
                    "Hit Cost",
                ],
                ascending=[
                    False,
                    False,
                ],
            )
        )

        st.dataframe(
            activity_leaderboard,
            hide_index=True,
            width="stretch",
        )

    # =====================================================
    # POINTS-HIT TRACKER
    # =====================================================

    st.markdown("---")

    st.subheader(
        "💥 Points-Hit Tracker"
    )

    selected_hit_tab, recent_hit_tab, season_hit_tab = (
        st.tabs(
            [
                "Selected GW",
                "Last 5 GWs",
                "Full Season",
            ]
        )
    )

    selected_hit_gameweeks = {
        selected_gameweek
    }

    recent_hit_gameweeks = set(
        [
            gameweek
            for gameweek in available_gameweeks
            if gameweek <= selected_gameweek
        ][:5]
    )

    season_hit_gameweeks = {
        gameweek
        for gameweek in available_gameweeks
        if gameweek <= selected_gameweek
    }

    hit_tabs = [
        (
            selected_hit_tab,
            selected_hit_gameweeks,
        ),
        (
            recent_hit_tab,
            recent_hit_gameweeks,
        ),
        (
            season_hit_tab,
            season_hit_gameweeks,
        ),
    ]

    for hit_tab, hit_gameweeks in hit_tabs:
        with hit_tab:
            hit_rows = []

            for manager in manager_payload:
                hit_cost = sum(
                    safe_int(
                        manager[
                            "history_map"
                        ]
                        .get(
                            gameweek,
                            {},
                        )
                        .get(
                            "event_transfers_cost"
                        )
                    )
                    for gameweek in hit_gameweeks
                )

                hit_weeks = sum(
                    1
                    for gameweek in hit_gameweeks
                    if safe_int(
                        manager[
                            "history_map"
                        ]
                        .get(
                            gameweek,
                            {},
                        )
                        .get(
                            "event_transfers_cost"
                        )
                    ) > 0
                )

                hit_rows.append(
                    {
                        "Manager": manager[
                            "manager"
                        ],
                        "Team": manager[
                            "team"
                        ],
                        "Hit Cost": hit_cost,
                        "Hit Gameweeks": (
                            hit_weeks
                        ),
                    }
                )

            hits_df = pd.DataFrame(
                hit_rows
            ).sort_values(
                "Hit Cost",
                ascending=False,
            )

            st.dataframe(
                hits_df,
                hide_index=True,
                width="stretch",
            )

    # =====================================================
    # TRANSFER SUCCESS LEADERBOARD
    # =====================================================

    st.markdown("---")

    st.subheader(
        "🎯 Did the Transfers Pay Off?"
    )

    if transfers_df.empty:
        st.info(
            "No transfers are available "
            "to evaluate."
        )

    else:
        success_summary = (
            transfers_df
            .groupby(
                [
                    "Manager",
                    "Team",
                ],
                as_index=False,
            )
            .agg(
                Transfers=(
                    "Result",
                    "size",
                ),
                Successful=(
                    "Result",
                    lambda values: int(
                        (
                            values
                            == "Paid off"
                        ).sum()
                    ),
                ),
                Failed=(
                    "Result",
                    lambda values: int(
                        (
                            values
                            == "Failed"
                        ).sum()
                    ),
                ),
                Net_Transfer_Impact=(
                    "Net Impact",
                    "sum",
                ),
            )
        )

        success_summary[
            "Success Rate"
        ] = (
            (
                success_summary[
                    "Successful"
                ]
                / success_summary[
                    "Transfers"
                ]
                * 100
            )
            .round(1)
            .astype(str)
            + "%"
        )

        success_summary = (
            success_summary.rename(
                columns={
                    "Net_Transfer_Impact": (
                        "Net Transfer Impact"
                    )
                }
            )
        )

        success_summary = (
            success_summary.sort_values(
                "Net Transfer Impact",
                ascending=False,
            )
        )

        st.dataframe(
            success_summary,
            hide_index=True,
            width="stretch",
        )

    # =====================================================
    # TRANSFER AWARDS
    # =====================================================

    st.markdown("---")

    st.subheader(
        "🏆 Best Moves and Seller's Regret"
    )

    if transfers_df.empty:
        st.info(
            "No moves are available to review."
        )

    else:
        best_move = transfers_df.loc[
            transfers_df[
                "Net Impact"
            ].idxmax()
        ]

        worst_move = transfers_df.loc[
            transfers_df[
                "Net Impact"
            ].idxmin()
        ]

        regret_scores = (
            transfers_df[
                "Outgoing Points"
            ]
            - transfers_df[
                "Incoming Points"
            ]
        )

        regret_move = transfers_df.loc[
            regret_scores.idxmax()
        ]

        instant_impact = transfers_df.loc[
            transfers_df[
                "Incoming Points"
            ].idxmax()
        ]

        award_data = [
            (
                "🏆",
                "BEST TRANSFER",
                best_move["Manager"],
                (
                    f"{best_move['Player Out']} to "
                    f"{best_move['Player In']} · "
                    f"{best_move['Net Impact']:+.1f} pts"
                ),
            ),
            (
                "🗑️",
                "WORST TRANSFER",
                worst_move["Manager"],
                (
                    f"{worst_move['Player Out']} to "
                    f"{worst_move['Player In']} · "
                    f"{worst_move['Net Impact']:+.1f} pts"
                ),
            ),
            (
                "😬",
                "SELLER'S REGRET",
                regret_move["Manager"],
                (
                    f"Sold {regret_move['Player Out']} "
                    f"before {regret_move['Outgoing Points']} pts"
                ),
            ),
            (
                "🔥",
                "INSTANT IMPACT",
                instant_impact["Manager"],
                (
                    f"Bought {instant_impact['Player In']} · "
                    f"{instant_impact['Incoming Points']} pts"
                ),
            ),
        ]

        award_columns = st.columns(4)

        for column, award in zip(
            award_columns,
            award_data,
        ):
            (
                award_icon,
                award_title,
                award_manager,
                award_detail,
            ) = award

            card_html = (
                f'<div class="award">'
                f'<div class="award-icon">'
                f'{award_icon}'
                f'</div>'
                f'<div class="award-title">'
                f'{award_title}'
                f'</div>'
                f'<div class="award-name">'
                f'{html.escape(str(award_manager).title())}'
                f'</div>'
                f'<div class="award-detail">'
                f'{html.escape(str(award_detail))}'
                f'</div>'
                f'</div>'
            )

            column.markdown(
                card_html,
                unsafe_allow_html=True,
            )

    # =====================================================
    # TRANSFER TIMING
    # =====================================================

    st.markdown("---")

    st.subheader(
        "🕐 Transfer Timing Analysis"
    )

    timing_rows = []

    for manager in manager_payload:
        relevant_transfers = [
            transfer
            for transfer in manager[
                "transfers"
            ]
            if safe_int(
                transfer.get("event")
            ) in period_gameweeks
        ]

        transfer_hours = []

        for transfer in relevant_transfers:
            try:
                transfer_time = (
                    datetime.fromisoformat(
                        transfer.get(
                            "time",
                            "",
                        ).replace(
                            "Z",
                            "+00:00",
                        )
                    )
                )

                transfer_hours.append(
                    transfer_time.hour
                )

            except (
                AttributeError,
                ValueError,
            ):
                pass

        if transfer_hours:
            average_hour = round(
                sum(transfer_hours)
                / len(transfer_hours),
                1,
            )
        else:
            average_hour = None

        if not relevant_transfers:
            timing_style = (
                "No transfers"
            )

        elif (
            average_hour is not None
            and average_hour < 12
        ):
            timing_style = (
                "Early-day mover"
            )

        else:
            timing_style = (
                "Later-day mover"
            )

        timing_rows.append(
            {
                "Manager": manager[
                    "manager"
                ],
                "Transfers": len(
                    relevant_transfers
                ),
                "Average UTC Hour": (
                    average_hour
                ),
                "Timing Style": (
                    timing_style
                ),
            }
        )

    timing_df = (
        pd.DataFrame(
            timing_rows
        )
        .sort_values(
            "Transfers",
            ascending=False,
        )
    )

    st.dataframe(
        timing_df,
        hide_index=True,
        width="stretch",
    )

    st.caption(
        "Timing style is a time-of-day label. "
        "It does not measure how close a transfer "
        "was to the FPL deadline."
    )

    # =====================================================
    # TRANSFER FLOW SANKEY
    # =====================================================

    st.markdown("---")

    st.subheader(
        "🌊 Transfer Flow"
    )

    if transfers_df.empty:
        st.info(
            "No transfer flow is available "
            "for this period."
        )

    else:
        flow_counts = (
            transfers_df
            .groupby(
                [
                    "Player Out",
                    "Player In",
                ]
            )
            .size()
            .reset_index(
                name="Count"
            )
            .sort_values(
                "Count",
                ascending=False,
            )
            .head(20)
        )

        labels = list(
            dict.fromkeys(
                flow_counts[
                    "Player Out"
                ].tolist()
                + flow_counts[
                    "Player In"
                ].tolist()
            )
        )

        label_index = {
            label: index
            for index, label in enumerate(
                labels
            )
        }

        sankey_figure = go.Figure(
            data=[
                go.Sankey(
                    node={
                        "pad": 15,
                        "thickness": 18,
                        "label": labels,
                        "color": "#30363d",
                    },
                    link={
                        "source": [
                            label_index[value]
                            for value in flow_counts[
                                "Player Out"
                            ]
                        ],
                        "target": [
                            label_index[value]
                            for value in flow_counts[
                                "Player In"
                            ]
                        ],
                        "value": (
                            flow_counts[
                                "Count"
                            ].tolist()
                        ),
                        "color": (
                            "rgba(0,255,135,0.35)"
                        ),
                    },
                )
            ]
        )

        sankey_figure.update_layout(
            title=(
                "Most Common Player-to-Player "
                "Transfer Flows"
            ),
            height=520,
            margin={
                "l": 10,
                "r": 10,
                "t": 50,
                "b": 10,
            },
        )

        st.plotly_chart(
            sankey_figure,
            width="stretch",
        )

    # =====================================================
    # PRICE MOVEMENT
    # =====================================================

    st.markdown("---")

    st.subheader(
        "💷 Price Movement Since Transfer"
    )

    if transfers_df.empty:
        st.info(
            "No purchases are available "
            "for price analysis."
        )

    else:
        player_name_lookup = {
            player.get("web_name"): player
            for player in players.values()
        }

        price_rows = []

        for _, transfer in transfers_df.iterrows():
            player = player_name_lookup.get(
                transfer["Player In"],
                {},
            )

            purchase_price = float(
                str(
                    transfer["In Price"]
                )
                .replace(
                    "£",
                    "",
                )
                .replace(
                    "m",
                    "",
                )
            )

            current_price = (
                safe_int(
                    player.get(
                        "now_cost"
                    )
                )
                / 10
            )

            price_movement = round(
                current_price
                - purchase_price,
                1,
            )

            price_rows.append(
                {
                    "Manager": transfer[
                        "Manager"
                    ],
                    "Player": transfer[
                        "Player In"
                    ],
                    "Bought At": transfer[
                        "In Price"
                    ],
                    "Current Price": (
                        f"£{current_price:.1f}m"
                    ),
                    "Price Movement": (
                        f"{price_movement:+.1f}m"
                    ),
                    "Movement Value": (
                        price_movement
                    ),
                }
            )

        price_df = pd.DataFrame(
            price_rows
        ).sort_values(
            "Movement Value",
            ascending=False,
        )

        st.dataframe(
            price_df[
                [
                    "Manager",
                    "Player",
                    "Bought At",
                    "Current Price",
                    "Price Movement",
                ]
            ],
            hide_index=True,
            width="stretch",
        )

        st.caption(
            "Price movement compares purchase price with "
            "the current listed price. Actual FPL selling "
            "value may differ because of profit rules."
        )

    # =====================================================
    # NO-TRANSFER CLUB
    # =====================================================

    st.markdown("---")

    st.subheader(
        "🛌 No-Transfer Club"
    )

    if inactive_selected_gameweek:
        no_transfer_text = ", ".join(
            sorted(
                inactive_selected_gameweek
            )
        )

        st.write(
            no_transfer_text
        )

        st.caption(
            f"No public transfer was recorded for "
            f"these managers in Gameweek "
            f"{selected_gameweek}."
        )

    else:
        st.success(
            f"Every manager made at least one "
            f"public transfer in Gameweek "
            f"{selected_gameweek}."
        )

    # =====================================================
    # AUTOMATED TRANSFER REPORT
    # =====================================================

    st.markdown("---")

    st.subheader(
        "🤖 Transfer Intelligence Report"
    )

    if bought_df.empty:
        most_bought = None
    else:
        most_bought = bought_df.iloc[0]

    if sold_df.empty:
        most_sold = None
    else:
        most_sold = sold_df.iloc[0]

    if activity_df.empty:
        most_active = None
    else:
        most_active = (
            activity_df
            .sort_values(
                "Transfers",
                ascending=False,
            )
            .iloc[0]
        )

    report_lines = [
        (
            f"🔄 The league made "
            f"**{total_transfers} transfers** across "
            f"**{active_managers} active managers** "
            f"during the selected period."
        ),
        (
            f"💥 Managers spent a combined "
            f"**{total_hits} points** on additional "
            f"transfers."
        ),
        (
            f"📊 The estimated immediate transfer "
            f"impact was **{total_net_impact:+.1f} points** "
            f"after allocated hit costs."
        ),
    ]

    if most_bought is not None:
        report_lines.append(
            f"🟢 **{most_bought['Player']}** was the "
            f"most-bought player with "
            f"**{most_bought['Times Bought']} purchases**."
        )

    if most_sold is not None:
        report_lines.append(
            f"🔴 **{most_sold['Player']}** was the "
            f"most-sold player with "
            f"**{most_sold['Times Sold']} sales**."
        )

    if most_active is not None:
        report_lines.append(
            f"🏃 **{most_active['Manager']}** was the "
            f"most active manager with "
            f"**{most_active['Transfers']} transfers**."
        )

    if inactive_selected_gameweek:
        report_lines.append(
            f"🛌 **{len(inactive_selected_gameweek)} "
            f"managers** recorded no transfer in "
            f"Gameweek {selected_gameweek}."
        )

    st.info(
        "\n\n".join(
            report_lines
        )
    )

    st.caption(
        "Transfer histories, gameweek scores and hit costs "
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
        "Some transfer data was missing or "
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
        "loading Transfer Intelligence."
    )

    with st.expander(
        "Technical error details"
    ):
        st.code(
            str(error)
        )
