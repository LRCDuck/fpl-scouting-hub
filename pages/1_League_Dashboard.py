import streamlit as st
import pandas as pd
import requests
import plotly.express as px

st.set_page_config(layout="wide")

st.title("🏆 League Dashboard")

league_id = st.sidebar.text_input(
    "League ID",
    value="1116047"
)

your_name = st.sidebar.text_input(
    "Your Name"
)

@st.cache_data(ttl=3600)
def fetch_league_data(l_id):

    url = f"https://fantasy.premierleague.com/api/leagues-classic/{l_id}/standings/"

    r = requests.get(
        url,
        headers={"User-Agent": "Mozilla/5.0"}
    )

    data = r.json()

    league_name = data["league"]["name"]

    managers = []

    for m in data["standings"]["results"]:

        trend = "➖"

        if m["rank_sort"] < m["last_rank"]:
            trend = "🔺"
        elif m["rank_sort"] > m["last_rank"]:
            trend = "🔻"

        managers.append({
            "Entry ID": m["entry"],
            "Rank": m["rank"],
            "Trend": trend,
            "Manager": m["player_name"],
            "Team": m["entry_name"],
            "GW Score": m["event_total"],
            "Points": m["total"]
        })

    return league_name, pd.DataFrame(managers)

league_name, df = fetch_league_data(league_id)

st.subheader(f"🏆 {league_name}")

leader = df.iloc[0]

avg_points = round(df["Points"].mean(), 1)

col1,col2,col3,col4 = st.columns(4)

with col1:
    st.metric(
        "Leader",
        leader["Manager"]
    )

with col2:
    st.metric(
        "Leader Points",
        leader["Points"]
    )

with col3:
    st.metric(
        "League Avg",
        avg_points
    )

with col4:
    st.metric(
        "Managers",
        len(df)
    )

if your_name:

    your_team = df[
        df["Manager"]
        .str.contains(
            your_name,
            case=False,
            na=False
        )
    ]

    if not your_team.empty:

        your_rank = your_team.iloc[0]["Rank"]
        your_points = your_team.iloc[0]["Points"]

        st.success(
            f"Rank #{your_rank} | {your_points} points | Gap to leader: {leader['Points'] - your_points}"
        )

st.dataframe(
    df,
    use_container_width=True,
    hide_index=True
)

fig = px.bar(
    df,
    x="Manager",
    y="Points",
    color="Points",
    title="League Points"
)

st.plotly_chart(
    fig,
    use_container_width=True
)
