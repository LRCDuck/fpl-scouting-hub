import html
import json
from collections import Counter
from datetime import datetime, timezone

import pandas as pd
import requests
import streamlit as st
from google import genai
from google.genai import types


# =========================================================
# DEFAULT SETTINGS
# =========================================================

DEFAULT_LEAGUE_ID = "1116047"
DEFAULT_ENTRY_ID = "6074290"
DEFAULT_MODEL = "gemini-2.5-flash"

BASE_URL = "https://fantasy.premierleague.com/api"

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json",
}


# =========================================================
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="AI FPL Analyst",
    page_icon="🤖",
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

.notice {
    background: #241f0d;
    border: 1px solid #776c21;
    border-radius: 10px;
    padding: 11px;
    color: #e8dfaa;
    margin-bottom: 12px;
}

.connected {
    background: rgba(0, 255, 135, 0.08);
    border: 1px solid rgba(0, 255, 135, 0.40);
    border-radius: 10px;
    padding: 11px;
    color: #baf7d5;
    margin-bottom: 12px;
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

st.sidebar.header(
    "⚙️ AI Analyst Settings"
)

league_id = st.sidebar.text_input(
    "Mini-League ID",
    value=DEFAULT_LEAGUE_ID,
)

entry_id = st.sidebar.text_input(
    "Your FPL Entry ID",
    value=DEFAULT_ENTRY_ID,
)

analysis_focus = st.sidebar.selectbox(
    "Analysis focus",
    [
        "My Squad",
        "Transfer Suggestions",
        "Captaincy",
        "Mini-League",
        "Selected Rival",
        "Chip Strategy",
    ],
)

risk_level = st.sidebar.selectbox(
    "Risk preference",
    [
        "Safe",
        "Balanced",
        "Aggressive",
    ],
    index=1,
)

time_horizon = st.sidebar.selectbox(
    "Planning horizon",
    [
        "Next gameweek",
        "Next 3 gameweeks",
        "Long term",
    ],
    index=1,
)

max_hit = st.sidebar.selectbox(
    "Maximum points hit",
    [
        0,
        4,
        8,
        12,
    ],
    index=0,
)

number_of_transfers = st.sidebar.selectbox(
    "Transfers to consider",
    [
        1,
        2,
        3,
    ],
    index=0,
)

st.sidebar.markdown("---")

if st.sidebar.button(
    "🧹 Clear Chat",
    width="stretch",
):
    st.session_state.pop(
        "fpl_ai_messages",
        None,
    )

    st.session_state.pop(
        "pending_fpl_question",
        None,
    )

    st.rerun()

if st.sidebar.button(
    "🔄 Refresh FPL Data",
    width="stretch",
):
    st.cache_data.clear()
    st.rerun()


# =========================================================
# API FUNCTIONS
# =========================================================

def api_get(endpoint, timeout=20):
    url = (
        f"{BASE_URL}/"
        f"{endpoint.lstrip('/')}"
    )

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


@st.cache_data(
    ttl=300,
    show_spinner=False,
)
def get_entry(entry):
    return api_get(
        f"entry/{entry}/"
    )


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
def get_picks(entry, gameweek):
    return api_get(
        f"entry/{entry}/event/"
        f"{gameweek}/picks/"
    )


@st.cache_data(
    ttl=300,
    show_spinner=False,
)
def get_fixtures():
    return api_get(
        "fixtures/"
    )


@st.cache_data(
    ttl=300,
    show_spinner=False,
)
def get_league(league):
    results = []
    league_information = {}
    page = 1

    while True:
        data = api_get(
            f"leagues-classic/{league}/"
            f"standings/"
            f"?page_standings={page}"
        )

        if not league_information:
            league_information = data.get(
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

        has_next = standings.get(
            "has_next",
            False,
        )

        if not has_next or page >= 25:
            break

        page += 1

    return league_information, results


# =========================================================
# GENERAL HELPERS
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


def format_rank(value):
    rank = safe_int(value)

    if rank > 0:
        return f"{rank:,}"

    return "Unavailable"


def format_chip_name(value):
    chip_names = {
        "wildcard": "Wildcard",
        "freehit": "Free Hit",
        "bboost": "Bench Boost",
        "3xc": "Triple Captain",
        "manager": "Assistant Manager",
    }

    return chip_names.get(
        value,
        str(value)
        .replace("_", " ")
        .title(),
    )


def get_current_gameweek(events):
    current_event = next(
        (
            event
            for event in events
            if event.get("is_current")
        ),
        None,
    )

    if current_event:
        return safe_int(
            current_event.get("id")
        )

    completed_events = [
        safe_int(event.get("id"))
        for event in events
        if event.get("finished")
    ]

    return max(
        completed_events,
        default=1,
    )


def get_position_name(element_type):
    positions = {
        1: "Goalkeeper",
        2: "Defender",
        3: "Midfielder",
        4: "Forward",
    }

    return positions.get(
        element_type,
        "Unknown",
    )


# =========================================================
# FIXTURE ANALYSIS
# =========================================================

def get_fixture_difficulty(
    player,
    fixtures,
    gameweek,
    horizon,
):
    team_id = player.get("team")

    if horizon == "Next gameweek":
        fixture_count = 1

    elif horizon == "Next 3 gameweeks":
        fixture_count = 3

    else:
        fixture_count = 6

    future_fixtures = [
        fixture
        for fixture in fixtures
        if not fixture.get("finished")
        and safe_int(
            fixture.get("event"),
            999,
        ) >= gameweek
        and (
            fixture.get("team_h")
            == team_id
            or fixture.get("team_a")
            == team_id
        )
    ]

    future_fixtures = sorted(
        future_fixtures,
        key=lambda fixture: safe_int(
            fixture.get("event"),
            999,
        ),
    )[:fixture_count]

    difficulties = []

    for fixture in future_fixtures:
        if fixture.get("team_h") == team_id:
            difficulty = safe_int(
                fixture.get(
                    "team_h_difficulty"
                )
            )
        else:
            difficulty = safe_int(
                fixture.get(
                    "team_a_difficulty"
                )
            )

        difficulties.append(
            difficulty
        )

    if not difficulties:
        return None

    return round(
        sum(difficulties)
        / len(difficulties),
        2,
    )


# =========================================================
# PLAYER DATA
# =========================================================

def build_player_row(
    player,
    teams,
    fixtures,
    gameweek,
    horizon,
    pick=None,
):
    team = teams.get(
        player.get("team"),
        {},
    )

    return {
        "id": player.get("id"),
        "name": player.get(
            "web_name"
        ),
        "club": team.get(
            "name"
        ),
        "position": get_position_name(
            player.get("element_type")
        ),
        "price": (
            safe_int(
                player.get("now_cost")
            )
            / 10
        ),
        "total_points": safe_int(
            player.get("total_points")
        ),
        "event_points": safe_int(
            player.get("event_points")
        ),
        "form": safe_float(
            player.get("form")
        ),
        "ownership_percent": safe_float(
            player.get(
                "selected_by_percent"
            )
        ),
        "points_per_game": safe_float(
            player.get(
                "points_per_game"
            )
        ),
        "minutes": safe_int(
            player.get("minutes")
        ),
        "status": player.get(
            "status"
        ),
        "news": player.get(
            "news",
            "",
        ),
        "fixture_difficulty": (
            get_fixture_difficulty(
                player,
                fixtures,
                gameweek,
                horizon,
            )
        ),
        "squad_position": (
            safe_int(
                pick.get("position")
            )
            if pick
            else None
        ),
        "multiplier": (
            safe_int(
                pick.get("multiplier")
            )
            if pick
            else None
        ),
        "captain": (
            bool(
                pick.get("is_captain")
            )
            if pick
            else False
        ),
        "vice_captain": (
            bool(
                pick.get(
                    "is_vice_captain"
                )
            )
            if pick
            else False
        ),
    }


def build_candidate_pool(
    players,
    teams,
    fixtures,
    gameweek,
    horizon,
    squad_ids,
):
    candidates = []

    for player in players.values():
        player_id = player.get("id")

        if player_id in squad_ids:
            continue

        if safe_int(
            player.get("minutes")
        ) <= 0:
            continue

        if player.get("status") in {
            "u",
            "n",
        }:
            continue

        player_row = build_player_row(
            player,
            teams,
            fixtures,
            gameweek,
            horizon,
        )

        fixture_difficulty = (
            player_row[
                "fixture_difficulty"
            ]
            or 3
        )

        candidate_score = (
            player_row["form"] * 2
            + player_row[
                "points_per_game"
            ]
            + player_row[
                "total_points"
            ] / 20
            - fixture_difficulty
        )

        player_row["candidate_score"] = (
            round(
                candidate_score,
                2,
            )
        )

        candidates.append(
            player_row
        )

    return sorted(
        candidates,
        key=lambda player: player[
            "candidate_score"
        ],
        reverse=True,
    )[:50]


# =========================================================
# AI CONTEXT
# =========================================================

def build_context(
    entry,
    history,
    transfers,
    picks,
    players,
    teams,
    fixtures,
    league_information,
    standings,
    selected_rival_id,
    gameweek,
    horizon,
):
    squad = []

    for pick in picks:
        player = players.get(
            pick.get("element"),
            {},
        )

        squad.append(
            build_player_row(
                player,
                teams,
                fixtures,
                gameweek,
                horizon,
                pick,
            )
        )

    squad_ids = {
        player["id"]
        for player in squad
    }

    candidates = build_candidate_pool(
        players,
        teams,
        fixtures,
        gameweek,
        horizon,
        squad_ids,
    )

    chips = [
        {
            "chip": format_chip_name(
                chip.get("name")
            ),
            "gameweek": chip.get(
                "event"
            ),
        }
        for chip in history.get(
            "chips",
            [],
        )
    ]

    league_row = next(
        (
            manager
            for manager in standings
            if safe_int(
                manager.get("entry")
            ) == safe_int(entry_id)
        ),
        {},
    )

    if standings:
        leader = standings[0]
    else:
        leader = {}

    top_managers = [
        {
            "rank": manager.get(
                "rank"
            ),
            "manager": manager.get(
                "player_name"
            ),
            "team": manager.get(
                "entry_name"
            ),
            "points": manager.get(
                "total"
            ),
            "entry": manager.get(
                "entry"
            ),
        }
        for manager in standings[:10]
    ]

    recent_transfers = []

    sorted_transfers = sorted(
        transfers,
        key=lambda transfer: transfer.get(
            "time",
            "",
        ),
        reverse=True,
    )[:12]

    for transfer in sorted_transfers:
        player_in = players.get(
            transfer.get("element_in"),
            {},
        ).get(
            "web_name"
        )

        player_out = players.get(
            transfer.get("element_out"),
            {},
        ).get(
            "web_name"
        )

        recent_transfers.append(
            {
                "gameweek": transfer.get(
                    "event"
                ),
                "player_in": player_in,
                "player_out": player_out,
            }
        )

    context = {
        "data_timestamp_utc": (
            datetime.now(
                timezone.utc
            ).isoformat()
        ),
        "current_gameweek": gameweek,
        "team": {
            "entry_id": entry_id,
            "name": entry.get("name"),
            "overall_points": entry.get(
                "summary_overall_points"
            ),
            "overall_rank": entry.get(
                "summary_overall_rank"
            ),
            "squad_value": (
                safe_int(
                    entry.get(
                        "last_deadline_value"
                    )
                )
                / 10
            ),
            "bank": (
                safe_int(
                    entry.get(
                        "last_deadline_bank"
                    )
                )
                / 10
            ),
            "event_transfers": entry.get(
                "summary_event_transfers"
            ),
            "event_transfer_cost": entry.get(
                "summary_event_transfers_cost"
            ),
        },
        "league": {
            "name": league_information.get(
                "name"
            ),
            "rank": league_row.get(
                "rank"
            ),
            "points": league_row.get(
                "total"
            ),
            "leader": leader.get(
                "player_name"
            ),
            "leader_points": leader.get(
                "total"
            ),
            "top_10": top_managers,
        },
        "squad": squad,
        "candidate_pool": candidates,
        "chips_used": chips,
        "recent_transfers": (
            recent_transfers
        ),
        "selected_rival_entry": (
            selected_rival_id
        ),
        "preferences": {
            "analysis_focus": (
                analysis_focus
            ),
            "risk_preference": (
                risk_level
            ),
            "planning_horizon": (
                time_horizon
            ),
            "maximum_hit": max_hit,
            "transfers_to_consider": (
                number_of_transfers
            ),
        },
    }

    return context


# =========================================================
# BUILT-IN FALLBACK ANALYSIS
# =========================================================

def rule_based_analysis(context):
    squad = context["squad"]

    candidates = context[
        "candidate_pool"
    ]

    availability_risks = [
        player
        for player in squad
        if player["status"] != "a"
    ]

    weakest_players = sorted(
        squad,
        key=lambda player: (
            player["form"],
            player["points_per_game"],
            player["total_points"],
        ),
    )[:3]

    response_lines = [
        "### Built-in squad analysis"
    ]

    if availability_risks:
        risk_text = ", ".join(
            (
                f"{player['name']} "
                f"({player['news'] or player['status']})"
            )
            for player in availability_risks
        )

        response_lines.append(
            f"**Availability concerns:** "
            f"{risk_text}"
        )

    else:
        response_lines.append(
            "**Availability concerns:** "
            "None currently listed by FPL."
        )

    weakest_text = ", ".join(
        (
            f"{player['name']} "
            f"(form {player['form']}, "
            f"{player['points_per_game']} PPG)"
        )
        for player in weakest_players
    )

    response_lines.append(
        f"**Lowest statistical performers:** "
        f"{weakest_text}"
    )

    club_counts = Counter(
        player["club"]
        for player in squad
    )

    transfer_suggestions = []

    for outgoing in weakest_players:
        estimated_budget = (
            outgoing["price"]
            + context["team"]["bank"]
        )

        suitable_candidates = [
            candidate
            for candidate in candidates
            if candidate["position"]
            == outgoing["position"]
            and candidate["price"]
            <= estimated_budget
            and club_counts[
                candidate["club"]
            ] < 3
        ]

        if suitable_candidates:
            incoming = (
                suitable_candidates[0]
            )

            transfer_suggestions.append(
                f"**{outgoing['name']} to "
                f"{incoming['name']}**: "
                f"£{incoming['price']:.1f}m, "
                f"form {incoming['form']}, "
                f"average fixture difficulty "
                f"{incoming['fixture_difficulty']}."
            )

    if transfer_suggestions:
        response_lines.append(
            "**Possible moves to investigate:**"
            "\n\n- "
            + "\n- ".join(
                transfer_suggestions[
                    :number_of_transfers
                ]
            )
        )

    response_lines.append(
        "These are statistical shortlist ideas, "
        "not guaranteed point predictions. "
        "Check late team news before acting."
    )

    return "\n\n".join(
        response_lines
    )


# =========================================================
# GEMINI SYSTEM INSTRUCTION
# =========================================================

def build_system_instruction(context):
    context_json = json.dumps(
        context,
        ensure_ascii=False,
    )

    return (
        "You are an FPL analyst embedded in a "
        "Streamlit application. Answer using only "
        "the supplied FPL context. Clearly distinguish "
        "facts from judgement. Never invent players, "
        "prices, fixtures, free transfers, injuries or "
        "chip availability. "
        "\n\n"
        "For transfer advice:"
        "\n"
        "1. Check affordability using the displayed "
        "current player price plus money in the bank."
        "\n"
        "2. Match the outgoing and incoming positions."
        "\n"
        "3. Do not create more than three players from "
        "one Premier League club."
        "\n"
        f"4. Respect the maximum requested hit of "
        f"{max_hit} points."
        "\n"
        f"5. Consider no more than "
        f"{number_of_transfers} transfers."
        "\n"
        f"6. Use a {risk_level.lower()} risk approach."
        "\n"
        f"7. Focus on the {time_horizon.lower()}."
        "\n\n"
        "Exact FPL selling prices and free-transfer "
        "balances may not be publicly available. "
        "When they are unavailable, clearly state that "
        "affordability is only an estimate based on "
        "current listed prices. Do not guarantee future "
        "returns. Provide a primary recommendation, "
        "one or two alternatives, risks and assumptions."
        "\n\n"
        "Current FPL context JSON:"
        "\n"
        f"{context_json}"
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

    # =====================================================
    # LOAD GEMINI SETTINGS
    # =====================================================

    try:
        api_key = st.secrets[
            "GEMINI_API_KEY"
        ]

    except (
        KeyError,
        FileNotFoundError,
    ):
        api_key = ""

    try:
        model_name = st.secrets.get(
            "GEMINI_MODEL",
            DEFAULT_MODEL,
        )

    except FileNotFoundError:
        model_name = DEFAULT_MODEL

    # =====================================================
    # LOAD FPL DATA
    # =====================================================

    with st.spinner(
        "Loading your live FPL context..."
    ):
        bootstrap = get_bootstrap()

        entry = get_entry(
            entry_id.strip()
        )

        history = get_history(
            entry_id.strip()
        )

        transfers = get_transfers(
            entry_id.strip()
        )

        fixtures = get_fixtures()

        league_information, standings = (
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

    teams = {
        team["id"]: team
        for team in bootstrap.get(
            "teams",
            [],
        )
    }

    gameweek = get_current_gameweek(
        bootstrap.get(
            "events",
            [],
        )
    )

    picks_data = get_picks(
        entry_id.strip(),
        gameweek,
    )

    picks = picks_data.get(
        "picks",
        [],
    )

    if not picks:
        st.error(
            "Your current public squad could not "
            "be loaded from FPL."
        )

        st.stop()

    # =====================================================
    # RIVAL SELECTOR
    # =====================================================

    rival_options = {
        "No specific rival": None
    }

    for manager in standings:
        manager_entry = safe_int(
            manager.get("entry")
        )

        if manager_entry == safe_int(
            entry_id
        ):
            continue

        label = (
            f"#{manager.get('rank')} | "
            f"{manager.get('player_name')} | "
            f"{manager.get('entry_name')}"
        )

        rival_options[label] = (
            manager.get("entry")
        )

    rival_label = st.sidebar.selectbox(
        "Selected rival",
        list(
            rival_options.keys()
        ),
    )

    rival_id = rival_options[
        rival_label
    ]

    # =====================================================
    # BUILD CONTEXT
    # =====================================================

    context = build_context(
        entry=entry,
        history=history,
        transfers=transfers,
        picks=picks,
        players=players,
        teams=teams,
        fixtures=fixtures,
        league_information=(
            league_information
        ),
        standings=standings,
        selected_rival_id=rival_id,
        gameweek=gameweek,
        horizon=time_horizon,
    )

    # =====================================================
    # HERO
    # =====================================================

    team_name = html.escape(
        str(
            entry.get(
                "name",
                "your squad",
            )
        )
    )

    league_name = html.escape(
        str(
            league_information.get(
                "name",
                "your mini-league",
            )
        )
    )

    hero_html = (
        f'<div class="hero">'
        f'<h1>🤖 AI FPL Analyst</h1>'
        f'<p>'
        f'Ask questions about {team_name}, '
        f'transfers, captaincy and {league_name}.'
        f'</p>'
        f'</div>'
    )

    st.markdown(
        hero_html,
        unsafe_allow_html=True,
    )

    if api_key:
        connected_html = (
            f'<div class="connected">'
            f'✅ Gemini is connected using '
            f'<strong>{html.escape(str(model_name))}</strong>.'
            f'</div>'
        )

        st.markdown(
            connected_html,
            unsafe_allow_html=True,
        )

    else:
        notice_html = (
            '<div class="notice">'
            'Gemini is not connected. Add '
            '<strong>GEMINI_API_KEY</strong> in '
            'Streamlit Secrets. Built-in analysis '
            'remains available.'
            '</div>'
        )

        st.markdown(
            notice_html,
            unsafe_allow_html=True,
        )

    # =====================================================
    # TEAM SNAPSHOT
    # =====================================================

    metric_1, metric_2 = st.columns(2)
    metric_3, metric_4 = st.columns(2)

    metric_1.metric(
        "Gameweek",
        gameweek,
    )

    metric_2.metric(
        "Squad Value",
        (
            f"£{context['team']['squad_value']:.1f}m"
        ),
    )

    metric_3.metric(
        "Money in Bank",
        (
            f"£{context['team']['bank']:.1f}m"
        ),
    )

    metric_4.metric(
        "Mini-League Rank",
        (
            context["league"]["rank"]
            or "Not found"
        ),
    )

    # =====================================================
    # QUICK QUESTIONS
    # =====================================================

    st.subheader(
        "⚡ Quick Analysis"
    )

    quick_questions = [
        (
            "🔄 Suggest transfers",
            "Suggest my best transfer options within budget.",
        ),
        (
            "🚨 Check squad risks",
            "Identify the biggest risks in my squad.",
        ),
        (
            "🧢 Analyse captaincy",
            "Rank my best captain choices.",
        ),
        (
            "💎 Find differentials",
            "Find useful differentials for my team.",
        ),
        (
            "🏆 Analyse league position",
            "Analyse my mini-league position and next target.",
        ),
        (
            "🎲 Review chips",
            "Review my chip usage and future chip strategy.",
        ),
    ]

    quick_columns = st.columns(3)

    for index, quick_item in enumerate(
        quick_questions
    ):
        button_label, question = (
            quick_item
        )

        button_clicked = quick_columns[
            index % 3
        ].button(
            button_label,
            key=f"quick_question_{index}",
            width="stretch",
        )

        if button_clicked:
            st.session_state[
                "pending_fpl_question"
            ] = question

    # =====================================================
    # DATA TRANSPARENCY
    # =====================================================

    with st.expander(
        "📊 View the data supplied to the analyst"
    ):
        squad_dataframe = pd.DataFrame(
            context["squad"]
        )

        st.dataframe(
            squad_dataframe,
            hide_index=True,
            width="stretch",
        )

        st.caption(
            "A shortlist of statistically strong "
            "transfer candidates is also supplied "
            "to Gemini, together with budget, fixtures, "
            "injuries and league information."
        )

        st.caption(
            f"Data context created at "
            f"{context['data_timestamp_utc']}."
        )

    # =====================================================
    # CHAT HISTORY
    # =====================================================

    if "fpl_ai_messages" not in st.session_state:
        st.session_state[
            "fpl_ai_messages"
        ] = [
            {
                "role": "assistant",
                "content": (
                    "Ask me about your squad, transfer "
                    "options, captaincy, rivals or chip "
                    "strategy. I will use the live FPL "
                    "data loaded above."
                ),
            }
        ]

    for message in st.session_state[
        "fpl_ai_messages"
    ]:
        with st.chat_message(
            message["role"]
        ):
            st.markdown(
                message["content"]
            )

    typed_question = st.chat_input(
        "Ask your FPL analyst a question..."
    )

    pending_question = (
        st.session_state.pop(
            "pending_fpl_question",
            None,
        )
    )

    question = (
        typed_question
        or pending_question
    )

    # =====================================================
    # ANSWER QUESTION
    # =====================================================

    if question:
        st.session_state[
            "fpl_ai_messages"
        ].append(
            {
                "role": "user",
                "content": question,
            }
        )

        with st.chat_message("user"):
            st.markdown(
                question
            )

        with st.chat_message(
            "assistant"
        ):
            if not api_key:
                answer = (
                    rule_based_analysis(
                        context
                    )
                )

                st.markdown(
                    answer
                )

            else:
                try:
                    client = genai.Client(
                        api_key=api_key
                    )

                    recent_conversation = (
                        st.session_state[
                            "fpl_ai_messages"
                        ][-8:]
                    )

                    transcript = "\n\n".join(
                        (
                            f"{message['role'].upper()}: "
                            f"{message['content']}"
                        )
                        for message
                        in recent_conversation
                    )

                    with st.spinner(
                        "Analysing your FPL data..."
                    ):
                        response = (
                            client.models.generate_content(
                                model=model_name,
                                contents=transcript,
                                config=(
                                    types.GenerateContentConfig(
                                        system_instruction=(
                                            build_system_instruction(
                                                context
                                            )
                                        ),
                                        temperature=0.25,
                                        max_output_tokens=1400,
                                    )
                                ),
                            )
                        )

                    if response.text:
                        answer = response.text
                    else:
                        answer = (
                            "Gemini returned an empty "
                            "response. Please try "
                            "rephrasing the question."
                        )

                    client.close()

                    st.markdown(
                        answer
                    )

                except Exception as ai_error:
                    answer = (
                        rule_based_analysis(
                            context
                        )
                    )

                    st.warning(
                        "Gemini could not answer this "
                        "request, so the built-in analysis "
                        "is shown instead."
                    )

                    with st.expander(
                        "Gemini technical details"
                    ):
                        st.code(
                            str(ai_error)
                        )

                    st.markdown(
                        answer
                    )

        st.session_state[
            "fpl_ai_messages"
        ].append(
            {
                "role": "assistant",
                "content": answer,
            }
        )

    st.caption(
        "AI recommendations are analytical opinions, "
        "not guaranteed outcomes. Player availability, "
        "prices, fixtures and line-ups can change before "
        "the FPL deadline."
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
        f"Entry ID, then refresh the page."
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
        "Some FPL data was missing or had "
        "an unexpected format."
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
        "loading the AI FPL Analyst."
    )

    with st.expander(
        "Technical error details"
    ):
        st.code(
            str(error)
        )
