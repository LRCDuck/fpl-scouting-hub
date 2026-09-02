import streamlit as st
import requests
import pandas as pd

st.title("🔍 Rival Viewer")

league_id = st.sidebar.text_input(
    "League ID",
    value="1116047"
)

@st.cache_data(ttl=3600)
def get_league(l_id):

    data = requests.get(
        f"https://fantasy.premierleague.com/api/leagues-classic/{l_id}/standings/"
    ).json()

    return data["standings"]["results"]

managers = get_league(league_id)

names = {
    x["player_name"]: x["entry"]
    for x in managers
}

selected = st.selectbox(
    "Select Rival",
    list(names.keys())
)

entry_id = names[selected]

team = requests.get(
    f"https://fantasy.premierleague.com/api/entry/{entry_id}/"
).json()

col1,col2,col3,col4=st.columns(4)

col1.metric(
    "Overall Rank",
    f"{team['summary_overall_rank']:,}"
)

col2.metric(
    "Team Value",
    f"£{team['last_deadline_value']/10:.1f}m"
)

col3.metric(
    "Bank",
    f"£{team['last_deadline_bank']/10:.1f}m"
)

col4.metric(
    "Transfers",
    team["summary_event_transfers"]
)

st.json(team["chips"])
