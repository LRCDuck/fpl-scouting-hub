import html
from datetime import datetime, timezone

import pandas as pd
import plotly.express as px
import requests
import streamlit as st


# =========================================================
# SETTINGS
# =========================================================

BASE_URL = "https://fantasy.premierleague.com/api"

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json",
}


# =========================================================
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="FPL Player Market",
    page_icon="📈",
    layout="wide",
)


# =========================================================
# STYLING
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

.market-card {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 13px;
    padding: 15px;
    min-height: 122px;
    text-align: center;
}

.market-icon {
    font-size: 1.65rem;
}

.market-title {
    color: #98a3b1;
    font-size: 0.70rem;
    font-weight: 800;
    letter-spacing: 0.05rem;
}

.market-player {
    color: #ffffff;
    font-size: 0.98rem;
    font-weight: 850;
    margin-top: 7px;
}

.market-detail {
    color: #00ff87;
    font-size: 0.78rem;
    margin-top: 4px;
}

.warning-detail {
    color: #ff6078;
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

    .market-card {
        min-height: 110px;
    }
}
</style>
""",
    unsafe_allow_html=True,
)


# =========================================================
# API
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
    ttl=1800,
    show_spinner=False,
)
def get_bootstrap():
    return api_get(
        "bootstrap-static/"
    )


# =========================================================
# HELPERS
# =========================================================

def safe_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def safe_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def position_name(position_id):
    positions = {
        1: "Goalkeeper",
        2: "Defender",
        3: "Midfielder",
        4: "Forward",
    }

    return positions.get(
        position_id,
        "Unknown",
    )


def availability_text(status):
    statuses = {
        "a": "Available",
        "d": "Doubtful",
        "i": "Injured",
        "s": "Suspended",
        "u": "Unavailable",
        "n": "Not available",
    }

    return statuses.get(
        status,
        "Availability concern",
    )


def status_icon(status):
    icons = {
        "a": "✅",
        "d": "⚠️",
        "i": "🚨",
        "s": "🟥",
        "u": "⛔",
        "n": "🚫",
    }

    return icons.get(
        status,
        "⚠️",
    )


def price_change_text(change):
    if change > 0:
        return f"+£{change:.1f}m"

    if change < 0:
        return f"-£{abs(change):.1f}m"

    return "No change"


def build_player_dataframe(
    bootstrap_data,
):
    team_lookup = {
        team["id"]: team["name"]
        for team in bootstrap_data.get(
            "teams",
            [],
        )
    }

    rows = []

    for player in bootstrap_data.get(
        "elements",
        [],
    ):
        price = (
            safe_int(
                player.get("now_cost")
            )
            / 10
        )

        price_change_gameweek = (
            safe_int(
                player.get(
                    "cost_change_event"
                )
            )
            / 10
        )

        price_change_season = (
            safe_int(
                player.get(
                    "cost_change_start"
                )
            )
            / 10
        )

        transfers_in = safe_int(
            player.get(
                "transfers_in_event"
            )
        )

        transfers_out = safe_int(
            player.get(
                "transfers_out_event"
            )
        )

        net_transfers = (
            transfers_in
            - transfers_out
        )

        total_points = safe_int(
            player.get("total_points")
        )

        if price > 0:
            value_score = round(
                total_points / price,
                2,
            )
        else:
            value_score = 0

        expected_goals = safe_float(
            player.get(
                "expected_goals"
            )
        )

        expected_assists = safe_float(
            player.get(
                "expected_assists"
            )
        )

        expected_involvement = (
            expected_goals
            + expected_assists
        )

        rows.append(
            {
                "Player ID": player.get(
                    "id"
                ),
                "Player": player.get(
                    "web_name",
                    "Unknown",
                ),
                "Club": team_lookup.get(
                    player.get("team"),
                    "Unknown",
                ),
                "Position": position_name(
                    player.get(
                        "element_type"
                    )
                ),
                "Price": price,
                "Price Display": (
                    f"£{price:.1f}m"
                ),
                "GW Price Change": (
                    price_change_gameweek
                ),
                "GW Price Movement": (
                    price_change_text(
                        price_change_gameweek
                    )
                ),
                "Season Price Change": (
                    price_change_season
                ),
                "Transfers In": (
                    transfers_in
                ),
                "Transfers Out": (
                    transfers_out
                ),
                "Net Transfers": (
                    net_transfers
                ),
                "Ownership %": safe_float(
                    player.get(
                        "selected_by_percent"
                    )
                ),
                "Form": safe_float(
                    player.get("form")
                ),
                "Points Per Game": (
                    safe_float(
                        player.get(
                            "points_per_game"
                        )
                    )
                ),
                "GW Points": safe_int(
                    player.get(
                        "event_points"
                    )
                ),
                "Total Points": (
                    total_points
                ),
                "Value Score": (
                    value_score
                ),
                "Minutes": safe_int(
                    player.get("minutes")
                ),
                "Starts": safe_int(
                    player.get("starts")
                ),
                "Goals": safe_int(
                    player.get(
                        "goals_scored"
                    )
                ),
                "Assists": safe_int(
                    player.get("assists")
                ),
                "Clean Sheets": safe_int(
                    player.get(
                        "clean_sheets"
                    )
                ),
                "Bonus": safe_int(
                    player.get("bonus")
                ),
                "Expected Goals": (
                    expected_goals
                ),
                "Expected Assists": (
                    expected_assists
                ),
                "Expected Involvement": (
                    round(
                        expected_involvement,
                        2,
                    )
                ),
                "ICT Index": safe_float(
                    player.get(
                        "ict_index"
                    )
                ),
                "Influence": safe_float(
                    player.get("influence")
                ),
                "Creativity": safe_float(
                    player.get("creativity")
                ),
                "Threat": safe_float(
                    player.get("threat")
                ),
                "Status Code": player.get(
                    "status",
                    "a",
                ),
                "Status": availability_text(
                    player.get(
                        "status",
                        "a",
                    )
                ),
                "Status Icon": status_icon(
                    player.get(
                        "status",
                        "a",
                    )
                ),
                "News": player.get(
                    "news",
                    "",
                ),
                "Chance of Playing": (
                    player.get(
                        "chance_of_playing_next_round"
                    )
                ),
            }
        )

    return pd.DataFrame(
        rows
    )


def market_card(
    icon,
    title,
    player,
    detail,
    warning=False,
):
    detail_class = (
        "market-detail warning-detail"
        if warning
        else "market-detail"
    )

    return (
        f'<div class="market-card">'
        f'<div class="market-icon">'
        f'{icon}'
        f'</div>'
        f'<div class="market-title">'
        f'{html.escape(str(title))}'
        f'</div>'
        f'<div class="market-player">'
        f'{html.escape(str(player))}'
        f'</div>'
        f'<div class="{detail_class}">'
        f'{html.escape(str(detail))}'
        f'</div>'
        f'</div>'
    )


# =========================================================
# SIDEBAR
# =========================================================

st.sidebar.header(
    "⚙️ Market Filters"
)

if st.sidebar.button(
    "🔄 Refresh Market Data",
    width="stretch",
):
    st.cache_data.clear()
    st.rerun()


# =========================================================
# MAIN PAGE
# =========================================================

try:
    with st.spinner(
        "Loading the complete FPL player market..."
    ):
        bootstrap = get_bootstrap()

    players_df = build_player_dataframe(
        bootstrap
    )

    if players_df.empty:
        st.error(
            "No FPL player information "
            "could be loaded."
        )

        st.stop()

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

    if current_event:
        current_gameweek = current_event.get(
            "name",
            "Current Gameweek",
        )
    else:
        current_gameweek = (
            "Between Gameweeks"
        )

    hero_html = (
        f'<div class="hero">'
        f'<h1>📈 FPL Player Market</h1>'
        f'<p>'
        f'Whole-game price movements, transfer trends, '
        f'form, ownership, value and availability. '
        f'Current period: '
        f'{html.escape(str(current_gameweek))}.'
        f'</p>'
        f'</div>'
    )

    st.markdown(
        hero_html,
        unsafe_allow_html=True,
    )

    # =====================================================
    # FILTERS
    # =====================================================

    clubs = sorted(
        players_df[
            "Club"
        ].dropna().unique()
    )

    positions = [
        "Goalkeeper",
        "Defender",
        "Midfielder",
        "Forward",
    ]

    selected_positions = (
        st.sidebar.multiselect(
            "Positions",
            positions,
            default=positions,
        )
    )

    selected_clubs = (
        st.sidebar.multiselect(
            "Clubs",
            clubs,
            default=clubs,
        )
    )

    minimum_price = float(
        players_df["Price"].min()
    )

    maximum_price = float(
        players_df["Price"].max()
    )

    selected_price_range = (
        st.sidebar.slider(
            "Price range",
            min_value=minimum_price,
            max_value=maximum_price,
            value=(
                minimum_price,
                maximum_price,
            ),
            step=0.1,
            format="£%.1fm",
        )
    )

    maximum_ownership = (
        st.sidebar.slider(
            "Maximum ownership percentage",
            min_value=0.0,
            max_value=100.0,
            value=100.0,
            step=1.0,
        )
    )

    available_only = (
        st.sidebar.toggle(
            "Available players only",
            value=False,
        )
    )

    minimum_minutes = (
        st.sidebar.number_input(
            "Minimum minutes",
            min_value=0,
            value=0,
            step=90,
        )
    )

    search_term = (
        st.sidebar.text_input(
            "Search player",
            placeholder="Enter player name...",
        )
    )

    filtered_df = players_df[
        players_df[
            "Position"
        ].isin(
            selected_positions
        )
    ].copy()

    filtered_df = filtered_df[
        filtered_df[
            "Club"
        ].isin(
            selected_clubs
        )
    ]

    filtered_df = filtered_df[
        filtered_df[
            "Price"
        ].between(
            selected_price_range[0],
            selected_price_range[1],
        )
    ]

    filtered_df = filtered_df[
        filtered_df[
            "Ownership %"
        ] <= maximum_ownership
    ]

    filtered_df = filtered_df[
        filtered_df[
            "Minutes"
        ] >= minimum_minutes
    ]

    if available_only:
        filtered_df = filtered_df[
            filtered_df[
                "Status Code"
            ] == "a"
        ]

    if search_term:
        filtered_df = filtered_df[
            filtered_df[
                "Player"
            ].str.contains(
                search_term,
                case=False,
                na=False,
            )
        ]

    # =====================================================
    # MARKET OVERVIEW
    # =====================================================

    st.subheader(
        "📊 Market Overview"
    )

    price_risers = players_df[
        players_df[
            "GW Price Change"
        ] > 0
    ]

    price_fallers = players_df[
        players_df[
            "GW Price Change"
        ] < 0
    ]

    total_transfers_in = int(
        players_df[
            "Transfers In"
        ].sum()
    )

    total_transfers_out = int(
        players_df[
            "Transfers Out"
        ].sum()
    )

    overview_1, overview_2 = st.columns(2)
    overview_3, overview_4 = st.columns(2)

    overview_1.metric(
        "Players in FPL",
        len(players_df),
    )

    overview_2.metric(
        "Price Risers This GW",
        len(price_risers),
    )

    overview_3.metric(
        "Price Fallers This GW",
        len(price_fallers),
    )

    overview_4.metric(
        "Players Matching Filters",
        len(filtered_df),
    )

    # =====================================================
    # MARKET HEADLINES
    # =====================================================

    most_bought = players_df.loc[
        players_df[
            "Transfers In"
        ].idxmax()
    ]

    most_sold = players_df.loc[
        players_df[
            "Transfers Out"
        ].idxmax()
    ]

    highest_net_demand = players_df.loc[
        players_df[
            "Net Transfers"
        ].idxmax()
    ]

    strongest_form = players_df.loc[
        players_df[
            "Form"
        ].idxmax()
    ]

    st.markdown("---")

    st.subheader(
        "🔥 Market Headlines"
    )

    headline_columns = st.columns(4)

    headline_columns[0].markdown(
        market_card(
            "🟢",
            "MOST BOUGHT",
            most_bought["Player"],
            (
                f"{most_bought['Transfers In']:,} "
                f"transfers in"
            ),
        ),
        unsafe_allow_html=True,
    )

    headline_columns[1].markdown(
        market_card(
            "🔴",
            "MOST SOLD",
            most_sold["Player"],
            (
                f"{most_sold['Transfers Out']:,} "
                f"transfers out"
            ),
            warning=True,
        ),
        unsafe_allow_html=True,
    )

    headline_columns[2].markdown(
        market_card(
            "📈",
            "HIGHEST NET DEMAND",
            highest_net_demand["Player"],
            (
                f"{highest_net_demand['Net Transfers']:+,} "
                f"net transfers"
            ),
        ),
        unsafe_allow_html=True,
    )

    headline_columns[3].markdown(
        market_card(
            "🔥",
            "STRONGEST FORM",
            strongest_form["Player"],
            (
                f"Form rating "
                f"{strongest_form['Form']:.1f}"
            ),
        ),
        unsafe_allow_html=True,
    )

    # =====================================================
    # PRICE CHANGES
    # =====================================================

    st.markdown("---")

    st.subheader(
        "💷 Price Changes"
    )

    risers_tab, fallers_tab, season_tab = (
        st.tabs(
            [
                "This GW Risers",
                "This GW Fallers",
                "Season Movement",
            ]
        )
    )

    with risers_tab:
        riser_table = (
            price_risers
            .sort_values(
                [
                    "GW Price Change",
                    "Transfers In",
                ],
                ascending=[
                    False,
                    False,
                ],
            )
        )

        if riser_table.empty:
            st.info(
                "No gameweek price rises are "
                "currently recorded."
            )

        else:
            st.dataframe(
                riser_table[
                    [
                        "Player",
                        "Club",
                        "Position",
                        "Price Display",
                        "GW Price Movement",
                        "Transfers In",
                        "Net Transfers",
                        "Ownership %",
                        "Form",
                    ]
                ],
                hide_index=True,
                width="stretch",
            )

    with fallers_tab:
        faller_table = (
            price_fallers
            .sort_values(
                [
                    "GW Price Change",
                    "Transfers Out",
                ],
                ascending=[
                    True,
                    False,
                ],
            )
        )

        if faller_table.empty:
            st.info(
                "No gameweek price falls are "
                "currently recorded."
            )

        else:
            st.dataframe(
                faller_table[
                    [
                        "Player",
                        "Club",
                        "Position",
                        "Price Display",
                        "GW Price Movement",
                        "Transfers Out",
                        "Net Transfers",
                        "Ownership %",
                        "Form",
                    ]
                ],
                hide_index=True,
                width="stretch",
            )

    with season_tab:
        season_price_table = (
            filtered_df
            .sort_values(
                "Season Price Change",
                ascending=False,
            )
        )

        st.dataframe(
            season_price_table[
                [
                    "Player",
                    "Club",
                    "Position",
                    "Price Display",
                    "Season Price Change",
                    "Ownership %",
                    "Total Points",
                    "Form",
                ]
            ],
            hide_index=True,
            width="stretch",
        )

    # =====================================================
    # TRANSFER MARKET
    # =====================================================

    st.markdown("---")

    st.subheader(
        "🔄 Global Transfer Market"
    )

    transfer_in_tab, transfer_out_tab, pressure_tab = (
        st.tabs(
            [
                "Most Transferred In",
                "Most Transferred Out",
                "Net Transfer Pressure",
            ]
        )
    )

    with transfer_in_tab:
        transfers_in_table = (
            filtered_df
            .sort_values(
                "Transfers In",
                ascending=False,
            )
            .head(30)
        )

        st.dataframe(
            transfers_in_table[
                [
                    "Player",
                    "Club",
                    "Position",
                    "Price Display",
                    "Transfers In",
                    "Ownership %",
                    "Form",
                    "GW Points",
                    "Status",
                ]
            ],
            hide_index=True,
            width="stretch",
        )

    with transfer_out_tab:
        transfers_out_table = (
            filtered_df
            .sort_values(
                "Transfers Out",
                ascending=False,
            )
            .head(30)
        )

        st.dataframe(
            transfers_out_table[
                [
                    "Player",
                    "Club",
                    "Position",
                    "Price Display",
                    "Transfers Out",
                    "Ownership %",
                    "Form",
                    "GW Points",
                    "Status",
                    "News",
                ]
            ],
            hide_index=True,
            width="stretch",
        )

    with pressure_tab:
        transfer_pressure_table = (
            filtered_df
            .sort_values(
                "Net Transfers",
                ascending=False,
            )
            .head(40)
        )

        st.dataframe(
            transfer_pressure_table[
                [
                    "Player",
                    "Club",
                    "Position",
                    "Price Display",
                    "Transfers In",
                    "Transfers Out",
                    "Net Transfers",
                    "GW Price Movement",
                    "Ownership %",
                ]
            ],
            hide_index=True,
            width="stretch",
        )

        st.caption(
            "Net transfer pressure is the difference "
            "between gameweek transfers in and out. "
            "It is not an official price-change prediction."
        )

    # =====================================================
    # PERFORMANCE LEADERS
    # =====================================================

    st.markdown("---")

    st.subheader(
        "🏆 Performance Leaders"
    )

    form_tab, points_tab, value_tab, underlying_tab = (
        st.tabs(
            [
                "Form",
                "Total Points",
                "Value",
                "Underlying Numbers",
            ]
        )
    )

    with form_tab:
        form_table = (
            filtered_df
            .sort_values(
                [
                    "Form",
                    "Points Per Game",
                ],
                ascending=[
                    False,
                    False,
                ],
            )
            .head(30)
        )

        st.dataframe(
            form_table[
                [
                    "Player",
                    "Club",
                    "Position",
                    "Price Display",
                    "Form",
                    "Points Per Game",
                    "GW Points",
                    "Total Points",
                    "Ownership %",
                    "Status",
                ]
            ],
            hide_index=True,
            width="stretch",
        )

    with points_tab:
        total_points_table = (
            filtered_df
            .sort_values(
                "Total Points",
                ascending=False,
            )
            .head(30)
        )

        st.dataframe(
            total_points_table[
                [
                    "Player",
                    "Club",
                    "Position",
                    "Price Display",
                    "Total Points",
                    "Points Per Game",
                    "Minutes",
                    "Ownership %",
                    "Form",
                ]
            ],
            hide_index=True,
            width="stretch",
        )

    with value_tab:
        value_table = filtered_df[
            filtered_df[
                "Minutes"
            ] > 0
        ].sort_values(
            "Value Score",
            ascending=False,
        ).head(30)

        st.dataframe(
            value_table[
                [
                    "Player",
                    "Club",
                    "Position",
                    "Price Display",
                    "Total Points",
                    "Value Score",
                    "Points Per Game",
                    "Ownership %",
                    "Minutes",
                ]
            ],
            hide_index=True,
            width="stretch",
        )

        st.caption(
            "Value Score is total FPL points divided "
            "by current player price."
        )

    with underlying_tab:
        underlying_table = (
            filtered_df
            .sort_values(
                "Expected Involvement",
                ascending=False,
            )
            .head(30)
        )

        st.dataframe(
            underlying_table[
                [
                    "Player",
                    "Club",
                    "Position",
                    "Price Display",
                    "Expected Goals",
                    "Expected Assists",
                    "Expected Involvement",
                    "Threat",
                    "Creativity",
                    "ICT Index",
                    "Minutes",
                ]
            ],
            hide_index=True,
            width="stretch",
        )

    # =====================================================
    # DIFFERENTIAL FINDER
    # =====================================================

    st.markdown("---")

    st.subheader(
        "💎 Differential Finder"
    )

    differential_limit = st.slider(
        "Maximum ownership for differentials",
        min_value=0.5,
        max_value=20.0,
        value=10.0,
        step=0.5,
    )

    differential_table = filtered_df[
        (
            filtered_df["Ownership %"]
            <= differential_limit
        )
        & (
            filtered_df["Status Code"]
            == "a"
        )
        & (
            filtered_df["Minutes"]
            > 0
        )
    ].sort_values(
        [
            "Form",
            "Points Per Game",
            "Expected Involvement",
        ],
        ascending=[
            False,
            False,
            False,
        ],
    ).head(30)

    st.dataframe(
        differential_table[
            [
                "Player",
                "Club",
                "Position",
                "Price Display",
                "Ownership %",
                "Form",
                "Points Per Game",
                "Total Points",
                "Expected Involvement",
                "Net Transfers",
            ]
        ],
        hide_index=True,
        width="stretch",
    )

    # =====================================================
    # AVAILABILITY
    # =====================================================

    st.markdown("---")

    st.subheader(
        "🚨 Player Availability"
    )

    unavailable_players = filtered_df[
        filtered_df[
            "Status Code"
        ] != "a"
    ].copy()

    unavailable_players[
        "Availability"
    ] = (
        unavailable_players[
            "Status Icon"
        ]
        + " "
        + unavailable_players[
            "Status"
        ]
    )

    if unavailable_players.empty:
        st.success(
            "No availability concerns were found "
            "within the current filters."
        )

    else:
        st.dataframe(
            unavailable_players[
                [
                    "Player",
                    "Club",
                    "Position",
                    "Price Display",
                    "Availability",
                    "Chance of Playing",
                    "News",
                    "Transfers Out",
                    "Ownership %",
                ]
            ].sort_values(
                "Transfers Out",
                ascending=False,
            ),
            hide_index=True,
            width="stretch",
        )

    # =====================================================
    # MARKET CHARTS
    # =====================================================

    st.markdown("---")

    st.subheader(
        "📊 Market Visualisations"
    )

    chart_1, chart_2, chart_3 = st.tabs(
        [
            "Net Transfers",
            "Form vs Price",
            "Value vs Ownership",
        ]
    )

    with chart_1:
        net_chart_data = (
            filtered_df
            .sort_values(
                "Net Transfers",
                ascending=False,
            )
            .head(25)
        )

        net_chart = px.bar(
            net_chart_data,
            x="Player",
            y="Net Transfers",
            color="Net Transfers",
            color_continuous_scale=[
                "#ff6078",
                "#00ff87",
            ],
            hover_data=[
                "Club",
                "Position",
                "Price Display",
                "Transfers In",
                "Transfers Out",
            ],
        )

        net_chart.update_layout(
            coloraxis_showscale=False,
            xaxis_title="Player",
            yaxis_title="Net Transfers",
            height=500,
        )

        st.plotly_chart(
            net_chart,
            width="stretch",
        )

    with chart_2:
        form_chart_data = filtered_df[
            filtered_df["Minutes"] > 0
        ].copy()

        form_chart = px.scatter(
            form_chart_data,
            x="Price",
            y="Form",
            color="Position",
            size="Total Points",
            hover_name="Player",
            hover_data=[
                "Club",
                "Ownership %",
                "Points Per Game",
                "Status",
            ],
        )

        form_chart.update_layout(
            xaxis_title="Price (£m)",
            yaxis_title="Form",
            height=550,
        )

        st.plotly_chart(
            form_chart,
            width="stretch",
        )

    with chart_3:
        value_chart_data = filtered_df[
            filtered_df["Minutes"] > 0
        ].copy()

        value_chart = px.scatter(
            value_chart_data,
            x="Ownership %",
            y="Value Score",
            color="Position",
            size="Total Points",
            hover_name="Player",
            hover_data=[
                "Club",
                "Price Display",
                "Form",
                "Points Per Game",
            ],
        )

        value_chart.update_layout(
            xaxis_title="Global FPL Ownership %",
            yaxis_title="Value Score",
            height=550,
        )

        st.plotly_chart(
            value_chart,
            width="stretch",
        )

    # =====================================================
    # PLAYER COMPARISON
    # =====================================================

    st.markdown("---")

    st.subheader(
        "⚔️ Player Comparison"
    )

    player_names = sorted(
        players_df["Player"].tolist()
    )

    comparison_1, comparison_2 = (
        st.columns(2)
    )

    with comparison_1:
        first_player_name = st.selectbox(
            "First player",
            player_names,
            index=0,
        )

    with comparison_2:
        second_default = (
            1
            if len(player_names) > 1
            else 0
        )

        second_player_name = st.selectbox(
            "Second player",
            player_names,
            index=second_default,
        )

    first_player = players_df[
        players_df["Player"]
        == first_player_name
    ].iloc[0]

    second_player = players_df[
        players_df["Player"]
        == second_player_name
    ].iloc[0]

    comparison_rows = [
        {
            "Metric": "Club",
            first_player_name: first_player[
                "Club"
            ],
            second_player_name: second_player[
                "Club"
            ],
        },
        {
            "Metric": "Position",
            first_player_name: first_player[
                "Position"
            ],
            second_player_name: second_player[
                "Position"
            ],
        },
        {
            "Metric": "Price",
            first_player_name: first_player[
                "Price Display"
            ],
            second_player_name: second_player[
                "Price Display"
            ],
        },
        {
            "Metric": "Total Points",
            first_player_name: first_player[
                "Total Points"
            ],
            second_player_name: second_player[
                "Total Points"
            ],
        },
        {
            "Metric": "Form",
            first_player_name: first_player[
                "Form"
            ],
            second_player_name: second_player[
                "Form"
            ],
        },
        {
            "Metric": "Points Per Game",
            first_player_name: first_player[
                "Points Per Game"
            ],
            second_player_name: second_player[
                "Points Per Game"
            ],
        },
        {
            "Metric": "Ownership %",
            first_player_name: first_player[
                "Ownership %"
            ],
            second_player_name: second_player[
                "Ownership %"
            ],
        },
        {
            "Metric": "Net Transfers",
            first_player_name: first_player[
                "Net Transfers"
            ],
            second_player_name: second_player[
                "Net Transfers"
            ],
        },
        {
            "Metric": "Expected Goals",
            first_player_name: first_player[
                "Expected Goals"
            ],
            second_player_name: second_player[
                "Expected Goals"
            ],
        },
        {
            "Metric": "Expected Assists",
            first_player_name: first_player[
                "Expected Assists"
            ],
            second_player_name: second_player[
                "Expected Assists"
            ],
        },
        {
            "Metric": "Availability",
            first_player_name: first_player[
                "Status"
            ],
            second_player_name: second_player[
                "Status"
            ],
        },
    ]

    st.dataframe(
        pd.DataFrame(
            comparison_rows
        ),
        hide_index=True,
        width="stretch",
    )

    # =====================================================
    # COMPLETE PLAYER TABLE
    # =====================================================

    st.markdown("---")

    st.subheader(
        "🔎 Complete Filtered Player Database"
    )

    sort_field = st.selectbox(
        "Sort players by",
        [
            "Total Points",
            "Form",
            "Points Per Game",
            "Transfers In",
            "Net Transfers",
            "Ownership %",
            "Value Score",
            "Expected Involvement",
            "Price",
        ],
    )

    final_table = filtered_df.sort_values(
        sort_field,
        ascending=False,
    )

    st.dataframe(
        final_table[
            [
                "Player",
                "Club",
                "Position",
                "Price Display",
                "GW Price Movement",
                "Transfers In",
                "Transfers Out",
                "Net Transfers",
                "Ownership %",
                "Form",
                "Points Per Game",
                "GW Points",
                "Total Points",
                "Value Score",
                "Expected Goals",
                "Expected Assists",
                "Status",
                "News",
            ]
        ],
        hide_index=True,
        width="stretch",
    )

    # =====================================================
    # DOWNLOAD
    # =====================================================

    csv_data = final_table.to_csv(
        index=False
    ).encode(
        "utf-8"
    )

    st.download_button(
        label="⬇️ Download Filtered Player Data",
        data=csv_data,
        file_name=(
            "fpl_player_market.csv"
        ),
        mime="text/csv",
        width="stretch",
    )

    # =====================================================
    # MARKET REPORT
    # =====================================================

    st.markdown("---")

    st.subheader(
        "🤖 Automated Market Report"
    )

    report_lines = [
        (
            f"🟢 **{most_bought['Player']}** is the "
            f"most-purchased player this gameweek, "
            f"with **{most_bought['Transfers In']:,} "
            f"transfers in**."
        ),
        (
            f"🔴 **{most_sold['Player']}** is the "
            f"most-sold player, with "
            f"**{most_sold['Transfers Out']:,} "
            f"transfers out**."
        ),
        (
            f"📈 **{highest_net_demand['Player']}** "
            f"has the strongest net demand at "
            f"**{highest_net_demand['Net Transfers']:+,} "
            f"net transfers**."
        ),
        (
            f"🔥 **{strongest_form['Player']}** has "
            f"the highest current FPL form rating "
            f"at **{strongest_form['Form']:.1f}**."
        ),
        (
            f"💷 FPL currently records "
            f"**{len(price_risers)} price risers** "
            f"and **{len(price_fallers)} price fallers** "
            f"for the gameweek."
        ),
        (
            f"🔎 Your active filters currently return "
            f"**{len(filtered_df)} players**."
        ),
    ]

    if next_event:
        deadline_time = next_event.get(
            "deadline_time"
        )

        if deadline_time:
            try:
                deadline = datetime.fromisoformat(
                    deadline_time.replace(
                        "Z",
                        "+00:00",
                    )
                )

                remaining = (
                    deadline
                    - datetime.now(
                        timezone.utc
                    )
                )

                if remaining.total_seconds() > 0:
                    total_hours = int(
                        remaining.total_seconds()
                        // 3600
                    )

                    days, hours = divmod(
                        total_hours,
                        24,
                    )

                    report_lines.append(
                        f"⏰ The next deadline is in "
                        f"approximately **{days} days "
                        f"and {hours} hours**."
                    )

            except ValueError:
                pass

    st.info(
        "\n\n".join(
            report_lines
        )
    )

    st.caption(
        "Price movement fields are official recorded "
        "changes, while net transfer pressure is analytical "
        "and should not be treated as a guaranteed price forecast."
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
        f"{status_code}. Please refresh and try again."
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

except (
    KeyError,
    IndexError,
    TypeError,
    ValueError,
) as error:
    st.error(
        "Some player-market data was missing or "
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
        "loading the FPL Player Market."
    )

    with st.expander(
        "Technical error details"
    ):
        st.code(
            str(error)
        )
