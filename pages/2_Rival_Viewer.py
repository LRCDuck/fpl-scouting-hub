import streamlit as st
import pandas as pd
import requests

# =====================================================
# DEFAULT SETTINGS
# =====================================================

DEFAULT_LEAGUE_ID = "1116047"

st.set_page_config(
    page_title="Rival Viewer",
    layout="wide"
)

st.title("🔍 Rival Viewer")

# =====================================================
# SIDEBAR
# =====================================================

league_id = st.sidebar.text_input(
    "League ID",
    value=DEFAULT_LEAGUE_ID
)

# =====================================================
# FUNCTIONS
# =====================================================

@st.cache_data(ttl=86400)
def get_bootstrap():

    return requests.get(
        "https://fantasy.premierleague.com/api/bootstrap-static/"
    ).json()

@st.cache_data(ttl=300)
def get_league(league_id):

    return requests.get(
        f"https://fantasy.premierleague.com/api/leagues-classic/{league_id}/standings/"
    ).json()

@st.cache_data(ttl=300)
def get_manager(entry_id):

    return requests.get(
        f"https://fantasy.premierleague.com/api/entry/{entry_id}/"
    ).json()

@st.cache_data(ttl=300)
def get_history(entry_id):

    return requests.get(
        f"https://fantasy.premierleague.com/api/entry/{entry_id}/history/"
    ).json()

@st.cache_data(ttl=300)
def get_transfers(entry_id):

    return requests.get(
        f"https://fantasy.premierleague.com/api/entry/{entry_id}/transfers/"
    ).json()

@st.cache_data(ttl=300)
def get_current_picks(entry_id, gw):

    return requests.get(
        f"https://fantasy.premierleague.com/api/entry/{entry_id}/event/{gw}/picks/"
    ).json()

# =====================================================
# LOAD DATA
# =====================================================

try:

    bootstrap = get_bootstrap()

    players = {
        p["id"]: p
        for p in bootstrap["elements"]
    }

    teams = get_league(league_id)

    managers = teams["standings"]["results"]

    manager_lookup = {
        x["player_name"]: x["entry"]
        for x in managers
    }

    selected_manager = st.selectbox(
        "Select Rival",
        sorted(manager_lookup.keys())
    )

    entry_id = manager_lookup[selected_manager]

    manager = get_manager(entry_id)

    history = get_history(entry_id)

    transfers = get_transfers(entry_id)

    current_gw = history["current"][-1]["event"]

    picks = get_current_picks(
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
    # CHIPS
    # =================================================

    st.markdown("---")
    st.subheader("🎲 Chips Used")

    chips = manager.get("chips", [])

    if chips:

        chip_rows = []

        for chip in chips:

            chip_rows.append({
                "Chip": chip["name"],
                "Gameweek": chip["event"]
            })

        st.dataframe(
            pd.DataFrame(chip_rows),
            use_container_width=True,
            hide_index=True
        )

    else:
        st.info("No chips used.")

    # =================================================
    # CAPTAIN / VC
    # =================================================

    st.markdown("---")
    st.subheader("🧢 Captaincy")

    captain = None
    vice = None

    for player in picks["picks"]:

        if player["is_captain"]:
            captain = players[player["element"]]["web_name"]

        if player["is_vice_captain"]:
            vice = players[player["element"]]["web_name"]

    col1, col2 = st.columns(2)

    with col1:
        st.success(f"Captain: {captain}")

    with col2:
        st.info(f"Vice Captain: {vice}")

    # =================================================
    # CURRENT SQUAD
    # =================================================

    st.markdown("---")
    st.subheader("⚽ Current Squad")

    squad = []

    for player in picks["picks"]:

        p = players[player["element"]]

        squad.append({
            "Player": p["web_name"],
            "Position": p["element_type"],
            "Price": f"£{p['now_cost']/10:.1f}m",
            "Captain": "✅" if player["is_captain"] else "",
            "Vice": "✅" if player["is_vice_captain"] else ""
        })

    squad_df = pd.DataFrame(squad)

    st.dataframe(
        squad_df,
        use_container_width=True,
        hide_index=True
    )

    # =================================================
    # TRANSFERS
    # =================================================

    st.markdown("---")
    st.subheader("🔄 Latest Transfers")

    if len(transfers):

        transfer_rows = []

        for transfer in transfers[-20:]:

            transfer_rows.append({
                "GW": transfer["event"],
                "IN": players.get(
                    transfer["element_in"],
                    {}
                ).get("web_name", "Unknown"),
                "OUT": players.get(
                    transfer["element_out"],
                    {}
                ).get("web_name", "Unknown"),
                "Time": transfer["time"]
            })

        transfer_df = pd.DataFrame(
            transfer_rows
        ).sort_values(
            "GW",
            ascending=False
        )

        st.dataframe(
            transfer_df,
            use_container_width=True,
            hide_index=True
        )

    else:

        st.info(
            "No transfer history available."
        )

    # =================================================
    # AI SCOUTING REPORT
    # =================================================

    st.markdown("---")
    st.subheader("🤖 Scout Report")

    chip_count = len(chips)

    total_transfers = len(transfers)

    report = f"""
🏆 {selected_manager} currently has {manager['summary_overall_points']} points.

💰 Team value stands at £{manager['last_deadline_value']/10:.1f}m.

🎲 Chips used so far: {chip_count}.

🔄 Recorded transfers: {total_transfers}.

🧢 Current captain: {captain}.

⚠️ Review their transfer history and captain selections carefully before making your own moves.
"""

    st.info(report)

except Exception as e:

    st.error(
        f"Unable to load rival data: {e}"
    )
