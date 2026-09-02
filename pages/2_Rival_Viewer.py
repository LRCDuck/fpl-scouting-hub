import streamlit as st
import requests
import pandas as pd

# =====================================================
# SETTINGS
# =====================================================

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

# =====================================================
# CSS
# =====================================================

st.markdown("""
<style>

.pitch{
    background: linear-gradient(
        180deg,
        #00a64f 0%,
        #00b050 100%
    );
    border-radius:20px;
    padding:20px;
    margin-top:20px;
}

.player-card{
    background:white;
    color:black;
    font-weight:bold;
    text-align:center;
    border-radius:10px;
    padding:10px;
    margin:4px;
    box-shadow:0 2px 6px rgba(0,0,0,0.25);
}

.bench-player{
    background:#ececec;
    color:black;
    border-radius:8px;
    text-align:center;
    padding:8px;
    margin:4px;
}

.row-space{
    margin-bottom:25px;
}

</style>
""", unsafe_allow_html=True)

# =====================================================
# API FUNCTIONS
# =====================================================

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
def manager_data(entry):

    return requests.get(
        f"https://fantasy.premierleague.com/api/entry/{entry}/"
    ).json()

@st.cache_data(ttl=300)
def manager_history(entry):

    return requests.get(
        f"https://fantasy.premierleague.com/api/entry/{entry}/history/"
    ).json()

@st.cache_data(ttl=300)
def manager_transfers(entry):

    return requests.get(
        f"https://fantasy.premierleague.com/api/entry/{entry}/transfers/"
    ).json()

@st.cache_data(ttl=300)
def picks(entry, gw):

    return requests.get(
        f"https://fantasy.premierleague.com/api/entry/{entry}/event/{gw}/picks/"
    ).json()


# =====================================================
# LOAD DATA
# =====================================================

try:

    boot = bootstrap()

    players_lookup = {
        p["id"]: p
        for p in boot["elements"]
    }

    league = league_data(league_id)

    names = {
        m["player_name"]: m["entry"]
        for m in league["standings"]["results"]
    }

    manager_name = st.selectbox(
        "Select Manager",
        sorted(names.keys())
    )

    entry_id = names[manager_name]

    manager = manager_data(entry_id)

    history = manager_history(entry_id)

    transfers = manager_transfers(entry_id)

    current_gw = history["current"][-1]["event"]

    current_picks = picks(
        entry_id,
        current_gw
    )

    # =================================================
    # OVERVIEW
    # =================================================

    st.subheader("📊 Team Overview")

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.metric(
            "Overall Rank",
            f"{manager['summary_overall_rank']:,}"
        )

    with c2:
        st.metric(
            "Total Points",
            manager["summary_overall_points"]
        )

    with c3:
        st.metric(
            "Team Value",
            f"£{manager['last_deadline_value']/10:.1f}m"
        )

    with c4:
        st.metric(
            "Bank",
            f"£{manager['last_deadline_bank']/10:.1f}m"
        )

    # =================================================
    # BUILD SQUAD
    # =================================================

    squad = []

    for player in current_picks["picks"]:

        pdata = players_lookup[player["element"]]

        squad.append({
            "web_name": pdata["web_name"],
            "position": pdata["element_type"],
            "multiplier": player["multiplier"],
            "captain": player["is_captain"],
            "vice": player["is_vice_captain"]
        })

    starters = [
        p for p in squad
        if p["multiplier"] > 0
    ]

    bench = [
        p for p in squad
        if p["multiplier"] == 0
    ]

    gk = [x for x in starters if x["position"] == 1]
    defs = [x for x in starters if x["position"] == 2]
    mids = [x for x in starters if x["position"] == 3]
    fwds = [x for x in starters if x["position"] == 4]

    formation = f"{len(defs)}-{len(mids)}-{len(fwds)}"

    st.success(f"📋 Formation: {formation}")

    # =================================================
    # TABS
    # =================================================

    tab1, tab2, tab3 = st.tabs(
        [
            "⚽ Pitch View",
            "🔄 Transfers",
            "🎲 Chips"
        ]
    )

    # =================================================
    # PITCH TAB
    # =================================================

    with tab1:

        st.markdown(
            "<div class='pitch'>",
            unsafe_allow_html=True
        )

        st.markdown(
            "<h3 style='text-align:center;'>Goalkeeper</h3>",
            unsafe_allow_html=True
        )

        cols = st.columns(max(1, len(gk)))

        for i, p in enumerate(gk):

            label = p["web_name"]

            if p["captain"]:
                label += " (C)"

            if p["vice"]:
                label += " (V)"

            cols[i].markdown(
                f"<div class='player-card'>{label}</div>",
                unsafe_allow_html=True
            )

        st.markdown(
            "<h3 style='text-align:center;'>Defence</h3>",
            unsafe_allow_html=True
        )

        cols = st.columns(len(defs))

        for i, p in enumerate(defs):

            cols[i].markdown(
                f"<div class='player-card'>{p['web_name']}</div>",
                unsafe_allow_html=True
            )

        st.markdown(
            "<h3 style='text-align:center;'>Midfield</h3>",
            unsafe_allow_html=True
        )

        cols = st.columns(len(mids))

        for i, p in enumerate(mids):

            cols[i].markdown(
                f"<div class='player-card'>{p['web_name']}</div>",
                unsafe_allow_html=True
            )

        st.markdown(
            "<h3 style='text-align:center;'>Attack</h3>",
            unsafe_allow_html=True
        )

        cols = st.columns(len(fwds))

        for i, p in enumerate(fwds):

            cols[i].markdown(
                f"<div class='player-card'>{p['web_name']}</div>",
                unsafe_allow_html=True
            )

        st.markdown("---")

        st.subheader("🪑 Bench")

        bench_cols = st.columns(4)

        for i, p in enumerate(bench):

            bench_cols[i].markdown(
                f"<div class='bench-player'>{p['web_name']}</div>",
                unsafe_allow_html=True
            )

        st.markdown(
            "</div>",
            unsafe_allow_html=True
        )

    # =================================================
    # TRANSFERS TAB
    # =================================================

    with tab2:

        st.subheader("🔄 Latest Transfers")

        if transfers:

            rows = []

            for t in transfers[-20:]:

                player_in = players_lookup.get(
                    t["element_in"],
                    {}
                ).get("web_name", "Unknown")

                player_out = players_lookup.get(
                    t["element_out"],
                    {}
                ).get("web_name", "Unknown")

                rows.append({
                    "GW": t["event"],
                    "IN": player_in,
                    "OUT": player_out,
                    "Date": t["time"][:10]
                })

            transfer_df = pd.DataFrame(rows)

            transfer_df = transfer_df.sort_values(
                "GW",
                ascending=False
            )

            st.dataframe(
                transfer_df,
                use_container_width=True,
                hide_index=True
            )

        else:

            st.info("No transfer history found.")

    # =================================================
    # CHIPS TAB
    # =================================================

    with tab3:

        st.subheader("🎲 Chips Used")

        chips = manager.get("chips", [])

        if chips:

            chip_rows = []

            for chip in chips:

                chip_rows.append({
                    "Chip": chip["name"],
                    "GW": chip["event"]
                })

            st.dataframe(
                pd.DataFrame(chip_rows),
                hide_index=True,
                use_container_width=True
            )

        else:

            st.info(
                "No chips used yet."
            )

    # =================================================
    # AI SCOUT REPORT
    # =================================================

    st.markdown("---")

    st.subheader("🤖 Scout Report")

    st.info(
        f"""
🏆 {manager_name} currently has {manager['summary_overall_points']} points.

📈 Overall rank: {manager['summary_overall_rank']:,}

💰 Squad value: £{manager['last_deadline_value']/10:.1f}m

🎲 Chips used: {len(manager.get('chips', []))}

🔄 Transfers made: {len(transfers)}

⚔️ Use the formation view above to scout captain choices, team structure and potential differentials.
"""
    )

except Exception as e:

    st.error(
        f"Failed to load rival data: {e}"
    )
