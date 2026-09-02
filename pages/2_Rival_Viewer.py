import streamlit as st
import requests
import pandas as pd

DEFAULT_LEAGUE_ID = "1116047"

st.set_page_config(
    page_title="Rival Viewer",
    layout="wide"
)

st.title("🔍 Rival Viewer")

league_id = st.sidebar.text_input(
    "League ID",
    value=DEFAULT_LEAGUE_ID
)

# ==========================================================
# CSS
# ==========================================================

st.markdown("""
<style>

.pitch{
    background: linear-gradient(
        180deg,
        #0f9d58 0%,
        #0ca54a 100%
    );
    border-radius:25px;
    padding:30px;
    border:4px solid white;
}

.player-card{
    border-radius:12px;
    padding:12px;
    text-align:center;
    font-weight:bold;
    color:white;
    min-height:100px;
    margin-bottom:10px;
    box-shadow:0px 4px 8px rgba(0,0,0,0.3);
}

.captain{
    border:4px solid gold;
}

.vice{
    border:4px solid #1e90ff;
}

.injured{
    border:4px solid red;
}

.bench-card{
    border-radius:10px;
    padding:10px;
    text-align:center;
    font-weight:bold;
    color:white;
    min-height:80px;
}

</style>
""", unsafe_allow_html=True)

# ==========================================================
# TEAM COLOURS
# ==========================================================

TEAM_COLOURS = {
    1:"#EF0107",
    2:"#95BFE5",
    3:"#DA291C",
    4:"#E30613",
    5:"#0057B8",
    6:"#034694",
    7:"#1B458F",
    8:"#003399",
    9:"#000000",
    10:"#C8102E",
    11:"#6CABDD",
    12:"#DA291C",
    13:"#241F20",
    14:"#DD0000",
    15:"#132257",
    16:"#7A263A",
    17:"#FDB913",
    18:"#0057B8",
    19:"#6CABDD",
    20:"#C8102E"
}

# ==========================================================
# API
# ==========================================================

@st.cache_data(ttl=86400)
def bootstrap():
    return requests.get(
        "https://fantasy.premierleague.com/api/bootstrap-static/"
    ).json()


@st.cache_data(ttl=300)
def league_data(league_id):
    return requests.get(
        f"https://fantasy.premierleague.com/api/leagues-classic/{league_id}/standings/"
    ).json()


@st.cache_data(ttl=300)
def manager_data(entry_id):
    return requests.get(
        f"https://fantasy.premierleague.com/api/entry/{entry_id}/"
    ).json()


@st.cache_data(ttl=300)
def manager_history(entry_id):
    return requests.get(
        f"https://fantasy.premierleague.com/api/entry/{entry_id}/history/"
    ).json()


@st.cache_data(ttl=300)
def manager_transfers(entry_id):
    return requests.get(
        f"https://fantasy.premierleague.com/api/entry/{entry_id}/transfers/"
    ).json()


@st.cache_data(ttl=300)
def team_picks(entry_id, gw):
    return requests.get(
        f"https://fantasy.premierleague.com/api/entry/{entry_id}/event/{gw}/picks/"
    ).json()


# ==========================================================
# HELPERS
# ==========================================================

def render_card(player, pdata, display_mode):

    css_class = "player-card"

    if player["is_captain"]:
        css_class += " captain"

    elif player["is_vice_captain"]:
        css_class += " vice"

    elif pdata["status"] != "a":
        css_class += " injured"

    team_colour = TEAM_COLOURS.get(
        pdata["team"],
        "#444444"
    )

    badges = ""

    if pdata["status"] != "a":
        badges += "🚨 "

    if player["is_captain"]:
        badges += "👑 "

    if player["is_vice_captain"]:
        badges += "🛡 "

    if display_mode == "Points":
        value = f"{pdata['total_points']} pts"
    else:
        value = f"£{pdata['now_cost']/10:.1f}m"

    return f"""
    <div class="{css_class}"
         style="background:{team_colour};">

        <div>{badges}</div>

        <div>
            {pdata['web_name']}
        </div>

        <div style="margin-top:8px;font-size:14px;">
            {value}
        </div>

    </div>
    """


# ==========================================================
# LOAD
# ==========================================================

try:

    data = bootstrap()

    players_lookup = {
        p["id"]: p
        for p in data["elements"]
    }

    standings = league_data(league_id)

    managers = {
        x["player_name"]: x["entry"]
        for x in standings["standings"]["results"]
    }

    manager_name = st.selectbox(
        "Select Manager",
        sorted(managers.keys())
    )

    entry_id = managers[manager_name]

    manager = manager_data(entry_id)

    history = manager_history(entry_id)

    transfers = manager_transfers(entry_id)

    current_gw = history["current"][-1]["event"]

    picks = team_picks(
        entry_id,
        current_gw
    )

    display_mode = st.selectbox(
        "Display on cards",
        [
            "Points",
            "Price"
        ]
    )

    # ======================================================
    # OVERVIEW
    # ======================================================

    st.subheader("📊 Team Overview")

    c1,c2,c3,c4,c5 = st.columns(5)

    c1.metric(
        "Overall Rank",
        f"{manager['summary_overall_rank']:,}"
    )

    c2.metric(
        "Total Points",
        manager["summary_overall_points"]
    )

    c3.metric(
        "Team Value",
        f"£{manager['last_deadline_value']/10:.1f}m"
    )

    c4.metric(
        "Bank",
        f"£{manager['last_deadline_bank']/10:.1f}m"
    )

    c5.metric(
        "Transfers",
        len(transfers)
    )

    starters = [
        p for p in picks["picks"]
        if p["multiplier"] > 0
    ]

    bench = [
        p for p in picks["picks"]
        if p["multiplier"] == 0
    ]

    gk = [
        p for p in starters
        if players_lookup[p["element"]]["element_type"] == 1
    ]

    defs = [
        p for p in starters
        if players_lookup[p["element"]]["element_type"] == 2
    ]

    mids = [
        p for p in starters
        if players_lookup[p["element"]]["element_type"] == 3
    ]

    fwds = [
        p for p in starters
        if players_lookup[p["element"]]["element_type"] == 4
    ]

    formation = f"{len(defs)}-{len(mids)}-{len(fwds)}"

    st.success(f"📋 Formation: {formation}")

    tab1, tab2, tab3 = st.tabs(
        [
            "⚽ Pitch",
            "🔄 Transfers",
            "🎲 Chips"
        ]
    )

    # ======================================================
    # PITCH
    # ======================================================

    with tab1:

        st.markdown(
            "<div class='pitch'>",
            unsafe_allow_html=True
        )

        st.markdown("### 🥅 Goalkeeper")

        cols = st.columns(max(1, len(gk)))

        for i, player in enumerate(gk):

            pdata = players_lookup[player["element"]]

            cols[i].markdown(
                render_card(
                    player,
                    pdata,
                    display_mode
                ),
                unsafe_allow_html=True
            )

        st.markdown("### 🛡 Defence")

        cols = st.columns(len(defs))

        for i, player in enumerate(defs):

            pdata = players_lookup[player["element"]]

            cols[i].markdown(
                render_card(
                    player,
                    pdata,
                    display_mode
                ),
                unsafe_allow_html=True
            )

        st.markdown("### 🎯 Midfield")

        cols = st.columns(len(mids))

        for i, player in enumerate(mids):

            pdata = players_lookup[player["element"]]

            cols[i].markdown(
                render_card(
                    player,
                    pdata,
                    display_mode
                ),
                unsafe_allow_html=True
            )

        st.markdown("### ⚽ Attack")

        cols = st.columns(len(fwds))

        for i, player in enumerate(fwds):

            pdata = players_lookup[player["element"]]

            cols[i].markdown(
                render_card(
                    player,
                    pdata,
                    display_mode
                ),
                unsafe_allow_html=True
            )

        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("---")

        st.subheader("🪑 Bench")

        cols = st.columns(4)

        for i, player in enumerate(bench):

            pdata = players_lookup[player["element"]]

            cols[i].markdown(
                render_card(
                    player,
                    pdata,
                    display_mode
                ),
                unsafe_allow_html=True
            )

    # ======================================================
    # TRANSFERS
    # ======================================================

    with tab2:

        st.subheader("🔄 Latest Transfers")

        if transfers:

            rows = []

            for t in transfers[-20:]:

                rows.append({
                    "GW": t["event"],
                    "IN": players_lookup.get(
                        t["element_in"],
                        {}
                    ).get(
                        "web_name",
                        "Unknown"
                    ),
                    "OUT": players_lookup.get(
                        t["element_out"],
                        {}
                    ).get(
                        "web_name",
                        "Unknown"
                    ),
                    "Date": t["time"][:10]
                })

            st.dataframe(
                pd.DataFrame(rows)
                .sort_values("GW",
                             ascending=False),
                hide_index=True,
                use_container_width=True
            )

        else:

            st.info(
                "No transfers found."
            )

    # ======================================================
    # CHIPS
    # ======================================================

    with tab3:

        chips = manager.get(
            "chips",
            []
        )

        if chips:

            chip_rows = []

            for chip in chips:

                chip_rows.append({
                    "Chip": chip["name"],
                    "GW": chip["event"]
                })

            st.dataframe(
                pd.DataFrame(
                    chip_rows
                ),
                hide_index=True,
                use_container_width=True
            )

        else:

            st.info(
                "No chips used."
            )

    st.markdown("---")

    st.subheader("🤖 Scout Report")

    st.info(
        f"""
🏆 {manager_name}

📈 Overall Rank: {manager['summary_overall_rank']:,}

💰 Team Value: £{manager['last_deadline_value']/10:.1f}m

🎲 Chips Used: {len(manager.get('chips', []))}

🔄 Transfers Made: {len(transfers)}

📋 Current Formation: {formation}
"""
    )

except Exception as e:

    st.error(
        f"Error loading rival data: {e}"
    )
