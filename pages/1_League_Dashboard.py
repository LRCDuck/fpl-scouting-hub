import streamlit as st
import pandas as pd
import requests
import plotly.express as px

# =====================================================
# DEFAULT SETTINGS
# =====================================================

DEFAULT_LEAGUE_ID = "1116047"
DEFAULT_ENTRY_ID = "6074290"

st.set_page_config(
    page_title="League Dashboard",
    layout="wide"
)

# =====================================================
# SIDEBAR
# =====================================================

st.sidebar.header("⚙️ Settings")

league_id = st.sidebar.text_input(
    "League ID",
    value=DEFAULT_LEAGUE_ID
)

entry_id = st.sidebar.text_input(
    "Your Entry ID",
    value=DEFAULT_ENTRY_ID
)

# =====================================================
# HEADER
# =====================================================

st.title("🏆 League Dashboard")

# =====================================================
# REFRESH
# =====================================================

if st.button("🔄 Refresh Data"):
    st.cache_data.clear()
    st.rerun()

# =====================================================
# FUNCTIONS
# =====================================================

@st.cache_data(ttl=300)
def get_league_data(league_id):

    url = (
        f"https://fantasy.premierleague.com/api/"
        f"leagues-classic/{league_id}/standings/"
    )

    data = requests.get(
        url,
        headers={"User-Agent": "Mozilla/5.0"}
    ).json()

    rows = []

    for manager in data["standings"]["results"]:

        movement = 0

        if manager["last_rank"]:
            movement = manager["last_rank"] - manager["rank"]

        rows.append({
            "Entry ID": manager["entry"],
            "Rank": manager["rank"],
            "Manager": manager["player_name"],
            "Team": manager["entry_name"],
            "GW Score": manager["event_total"],
            "Points": manager["total"],
            "Movement": movement
        })

    return data["league"]["name"], pd.DataFrame(rows)

@st.cache_data(ttl=300)
def get_manager_data(entry_id):

    url = (
        f"https://fantasy.premierleague.com/api/"
        f"entry/{entry_id}/"
    )

    return requests.get(
        url,
        headers={"User-Agent": "Mozilla/5.0"}
    ).json()

# =====================================================
# LOAD DATA
# =====================================================

try:

    league_name, df = get_league_data(league_id)

    my_team = df[df["Entry ID"] == int(entry_id)]

    leader = df.iloc[0]

    # =================================================
    # HERO METRICS
    # =================================================

    st.subheader(f"🏆 {league_name}")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "League Leader",
            leader["Manager"]
        )

    with col2:
        st.metric(
            "Leader Points",
            leader["Points"]
        )

    with col3:
        st.metric(
            "League Average",
            round(df["Points"].mean(), 1)
        )

    with col4:
        st.metric(
            "Managers",
            len(df)
        )

    # =================================================
    # PODIUM
    # =================================================

    st.markdown("---")
    st.subheader("🥇 League Podium")

    podium = df.head(3)

    c1, c2, c3 = st.columns(3)

    with c1:
        st.metric(
            "🥇 First",
            podium.iloc[0]["Manager"],
            podium.iloc[0]["Points"]
        )

    with c2:
        if len(podium) > 1:
            st.metric(
                "🥈 Second",
                podium.iloc[1]["Manager"],
                podium.iloc[1]["Points"]
            )

    with c3:
        if len(podium) > 2:
            st.metric(
                "🥉 Third",
                podium.iloc[2]["Manager"],
                podium.iloc[2]["Points"]
            )

    # =================================================
    # PERSONAL DASHBOARD
    # =================================================

    st.markdown("---")
    st.subheader("👤 Your Dashboard")

    if not my_team.empty:

        my_rank = my_team.iloc[0]["Rank"]
        my_points = my_team.iloc[0]["Points"]

        gap = leader["Points"] - my_points

        team_data = get_manager_data(entry_id)

        d1, d2, d3, d4 = st.columns(4)

        with d1:
            st.metric(
                "Your Rank",
                my_rank
            )

        with d2:
            st.metric(
                "Your Points",
                my_points
            )

        with d3:
            st.metric(
                "Gap To Leader",
                gap
            )

        with d4:
            st.metric(
                "Overall Rank",
                f"{team_data['summary_overall_rank']:,}"
            )

    # =================================================
    # ADD GAP COLUMN
    # =================================================

    df["Gap To Leader"] = (
        leader["Points"] - df["Points"]
    )

    # =================================================
    # LEAGUE TABLE
    # =================================================

    st.markdown("---")
    st.subheader("📋 League Standings")

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )

    # =================================================
    # POINTS CHART
    # =================================================

    st.markdown("---")
    st.subheader("📊 League Points Chart")

    fig = px.bar(
        df.sort_values("Points"),
        x="Manager",
        y="Points",
        color="Points",
        text="Points"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    # =================================================
    # BIGGEST MOVERS
    # =================================================

    st.markdown("---")
    st.subheader("🚀 Biggest Movers")

    biggest_riser = df.loc[
        df["Movement"].idxmax()
    ]

    biggest_faller = df.loc[
        df["Movement"].idxmin()
    ]

    c1, c2 = st.columns(2)

    with c1:
        st.success(
            f"🚀 {biggest_riser['Manager']} "
            f"({biggest_riser['Movement']} places)"
        )

    with c2:
        st.error(
            f"📉 {biggest_faller['Manager']} "
            f"({biggest_faller['Movement']} places)"
        )

    # =================================================
    # AI INSIGHTS
    # =================================================

    st.markdown("---")
    st.subheader("🤖 AI League Report")

    report = f"""
🏆 {leader['Manager']} currently leads the league with {leader['Points']} points.

📈 The biggest climber is {biggest_riser['Manager']}.

📉 The biggest faller is {biggest_faller['Manager']}.

🔥 Average league score is {round(df['Points'].mean(),1)}.

🎯 There are currently {len(df)} managers in the league.
"""

    st.info(report)

except Exception as e:

    st.error(
        f"Failed to load league data: {e}"
    )
