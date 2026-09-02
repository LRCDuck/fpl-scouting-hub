import hashlib
import html
import re
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

import feedparser
import pandas as pd
import requests
import streamlit as st


# =========================================================
# SETTINGS
# =========================================================

BASE_URL = "https://fantasy.premierleague.com/api"
DEFAULT_ENTRY_ID = "6074290"

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": (
        "application/json, "
        "application/rss+xml, "
        "application/xml, "
        "text/xml"
    ),
}


# =========================================================
# NEWS SOURCES
# =========================================================

FEEDS = {
    "BBC Premier League": (
        "https://feeds.bbci.co.uk/"
        "sport/football/premier-league/rss.xml"
    ),
    "BBC Football": (
        "https://feeds.bbci.co.uk/"
        "sport/football/rss.xml"
    ),
    "Sky Sports Football": (
        "https://www.skysports.com/rss/11095"
    ),
    "The Guardian Football": (
        "https://www.theguardian.com/football/rss"
    ),
    "90min Football": (
        "https://www.90min.com/posts.rss"
    ),
}


# =========================================================
# OFFICIAL RESEARCH LINKS
# =========================================================

OFFICIAL_LINKS = {
    "Official FPL Player News": (
        "https://fantasy.premierleague.com/"
        "en/the-scout/player-news"
    ),
    "Premier League Injuries": (
        "https://www.premierleague.com/"
        "en/latest-player-injuries"
    ),
    "Premier League News": (
        "https://www.premierleague.com/en/news"
    ),
    "Premier League Club Sites": (
        "https://www.premierleague.com/en/clubs"
    ),
}


# =========================================================
# CLASSIFICATION TERMS
# =========================================================

PRESS_CONFERENCE_TERMS = (
    "press conference",
    "presser",
    "team news",
    "injury update",
    "fitness update",
    "availability",
    "match preview",
    "manager preview",
    "squad update",
    "what the manager said",
    "pre-match",
    "prematch",
)

INJURY_TERMS = (
    "injury",
    "injured",
    "fitness",
    "doubt",
    "doubtful",
    "ruled out",
    "return",
    "available",
    "unavailable",
    "hamstring",
    "ankle",
    "knee",
    "muscle",
    "suspension",
    "suspended",
    "illness",
    "knock",
)

TRANSFER_TERMS = (
    "transfer",
    "signs",
    "signed",
    "signing",
    "deal",
    "loan",
    "joins",
    "leaves",
    "departure",
    "permanent move",
)

FIXTURE_TERMS = (
    "fixture",
    "postponed",
    "rescheduled",
    "kick-off",
    "kickoff",
    "schedule",
    "match date",
)

FPL_TERMS = (
    "fantasy premier league",
    "fpl",
    "captain",
    "wildcard",
    "free hit",
    "bench boost",
    "triple captain",
    "price rise",
    "price fall",
    "gameweek",
    "differential",
)


# =========================================================
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="FPL News Centre",
    page_icon="📰",
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

.news-card {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 13px;
    padding: 14px;
    margin-bottom: 10px;
}

.news-card h4 {
    margin: 0 0 5px;
    color: #ffffff;
}

.news-card p {
    margin: 5px 0;
    color: #aab3bf;
    font-size: 0.88rem;
}

.news-card a {
    color: #00ff87;
    font-weight: 750;
    text-decoration: none;
}

.news-card a:hover {
    text-decoration: underline;
}

.news-meta {
    color: #7f8a98;
    font-size: 0.76rem;
}

.news-tag {
    display: inline-block;
    border: 1px solid #46505d;
    border-radius: 999px;
    padding: 2px 7px;
    margin-right: 5px;
    margin-top: 5px;
    font-size: 0.68rem;
    color: #d5dbe3;
}

.priority-story {
    border-left: 4px solid #ff6078;
}

.new-story {
    border-top: 1px solid #00ff87;
    border-right: 1px solid #00ff87;
}

.source-box {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 12px;
    padding: 13px;
    margin-bottom: 10px;
}

.source-box h4 {
    color: #ffffff;
    margin: 0 0 5px;
}

.source-box p {
    color: #aab3bf;
    margin: 0;
    font-size: 0.84rem;
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
    "⚙️ News Settings"
)

entry_id = st.sidebar.text_input(
    "Your FPL Entry ID",
    value=DEFAULT_ENTRY_ID,
)

refresh_seconds = st.sidebar.selectbox(
    "Automatic refresh",
    [
        60,
        120,
        300,
        600,
    ],
    index=2,
    format_func=lambda value: (
        f"Every {value // 60} minute(s)"
    ),
)

maximum_articles = st.sidebar.slider(
    "Maximum articles",
    min_value=20,
    max_value=150,
    value=80,
    step=10,
)

if st.sidebar.button(
    "🔄 Refresh Now",
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
def get_picks(entry, gameweek):
    return api_get(
        f"entry/{entry}/event/"
        f"{gameweek}/picks/"
    )


# =========================================================
# NEWS FEED FUNCTIONS
# =========================================================

@st.cache_data(
    ttl=60,
    show_spinner=False,
)
def read_news_feeds():
    articles = []
    failures = []

    for source_name, feed_url in FEEDS.items():
        try:
            response = requests.get(
                feed_url,
                headers=HEADERS,
                timeout=15,
            )

            response.raise_for_status()

            parsed_feed = feedparser.parse(
                response.content
            )

            if (
                parsed_feed.bozo
                and not parsed_feed.entries
            ):
                raise ValueError(
                    str(
                        parsed_feed.bozo_exception
                    )
                )

            for feed_entry in parsed_feed.entries[:40]:
                title = re.sub(
                    r"\s+",
                    " ",
                    feed_entry.get(
                        "title",
                        "",
                    ),
                ).strip()

                link = feed_entry.get(
                    "link",
                    "",
                )

                raw_summary = feed_entry.get(
                    "summary",
                    feed_entry.get(
                        "description",
                        "",
                    ),
                )

                summary = re.sub(
                    r"<[^>]+>",
                    " ",
                    raw_summary,
                )

                summary = re.sub(
                    r"\s+",
                    " ",
                    summary,
                ).strip()[:450]

                published_text = feed_entry.get(
                    "published",
                    feed_entry.get(
                        "updated",
                        "",
                    ),
                )

                published_time = None

                if published_text:
                    try:
                        published_time = (
                            parsedate_to_datetime(
                                published_text
                            )
                        )

                        if (
                            published_time.tzinfo
                            is None
                        ):
                            published_time = (
                                published_time.replace(
                                    tzinfo=timezone.utc
                                )
                            )

                    except (
                        TypeError,
                        ValueError,
                        OverflowError,
                    ):
                        published_time = None

                article_key = (
                    f"{source_name}|"
                    f"{link}|"
                    f"{title}"
                )

                article_id = hashlib.sha256(
                    article_key.encode(
                        "utf-8"
                    )
                ).hexdigest()[:20]

                articles.append(
                    {
                        "id": article_id,
                        "source": source_name,
                        "title": title,
                        "link": link,
                        "summary": summary,
                        "published": (
                            published_time
                        ),
                    }
                )

        except Exception as error:
            failures.append(
                f"{source_name}: {error}"
            )

    unique_articles = {}

    for article in articles:
        title_key = re.sub(
            r"[^a-z0-9]",
            "",
            article["title"].lower(),
        )[:90]

        if (
            title_key
            and title_key not in unique_articles
        ):
            unique_articles[
                title_key
            ] = article

    oldest_time = datetime.min.replace(
        tzinfo=timezone.utc
    )

    ordered_articles = sorted(
        unique_articles.values(),
        key=lambda article: (
            article["published"]
            or oldest_time
        ),
        reverse=True,
    )

    return ordered_articles, failures


# =========================================================
# HELPERS
# =========================================================

def safe_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


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


def article_category(text):
    searchable_text = text.lower()

    if any(
        term in searchable_text
        for term in PRESS_CONFERENCE_TERMS
    ):
        return "Press Conference"

    if any(
        term in searchable_text
        for term in INJURY_TERMS
    ):
        return "Injury & Availability"

    if any(
        term in searchable_text
        for term in TRANSFER_TERMS
    ):
        return "Transfers"

    if any(
        term in searchable_text
        for term in FIXTURE_TERMS
    ):
        return "Fixtures"

    if any(
        term in searchable_text
        for term in FPL_TERMS
    ):
        return "FPL Strategy"

    return "Premier League News"


def freshness_label(published_time):
    if not published_time:
        return "Time unavailable"

    current_time = datetime.now(
        timezone.utc
    )

    published_utc = (
        published_time.astimezone(
            timezone.utc
        )
    )

    age_hours = max(
        (
            current_time
            - published_utc
        ).total_seconds()
        / 3600,
        0,
    )

    if age_hours < 2:
        return "Breaking"

    if age_hours < 24:
        return "Today"

    if age_hours < 72:
        return "Recent"

    return "Older"


def find_article_relevance(
    article,
    player_names,
    club_names,
):
    searchable_text = (
        f"{article['title']} "
        f"{article['summary']}"
    ).lower()

    matched_players = sorted(
        {
            player_name
            for player_name in player_names
            if player_name
            and player_name.lower()
            in searchable_text
        }
    )

    matched_clubs = sorted(
        {
            club_name
            for club_name in club_names
            if club_name
            and club_name.lower()
            in searchable_text
        }
    )

    return (
        matched_players,
        matched_clubs,
    )


def article_card(
    article,
    matched_players,
    matched_clubs,
    is_new=False,
):
    complete_text = (
        f"{article['title']} "
        f"{article['summary']}"
    )

    tags = [
        article_category(
            complete_text
        ),
        freshness_label(
            article["published"]
        ),
        article["source"],
    ]

    if matched_players:
        tags.append(
            "Players: "
            + ", ".join(
                matched_players[:4]
            )
        )

    if matched_clubs:
        tags.append(
            "Clubs: "
            + ", ".join(
                matched_clubs[:3]
            )
        )

    tag_html = "".join(
        (
            f'<span class="news-tag">'
            f'{html.escape(str(tag))}'
            f'</span>'
        )
        for tag in tags
    )

    if article["published"]:
        published_text = (
            article["published"]
            .astimezone()
            .strftime(
                "%d %b %Y, %H:%M"
            )
        )
    else:
        published_text = (
            "Publication time unavailable"
        )

    card_classes = [
        "news-card"
    ]

    if matched_players:
        card_classes.append(
            "priority-story"
        )

    if is_new:
        card_classes.append(
            "new-story"
        )

    complete_class = " ".join(
        card_classes
    )

    safe_link = html.escape(
        article["link"],
        quote=True,
    )

    safe_title = html.escape(
        article["title"]
    )

    safe_summary = html.escape(
        article["summary"]
        or (
            "Open the original article "
            "for full details."
        )
    )

    return (
        f'<div class="{complete_class}">'
        f'<h4>{safe_title}</h4>'
        f'<div class="news-meta">'
        f'{html.escape(published_text)}'
        f'</div>'
        f'<p>{safe_summary}</p>'
        f'<div>{tag_html}</div>'
        f'<p>'
        f'{safe_link}'
        f'Open original article'
        f'</a>'
        f'</p>'
        f'</div>'
    )


def availability_name(status_code):
    names = {
        "a": "Available",
        "d": "Doubtful",
        "i": "Injured",
        "s": "Suspended",
        "u": "Unavailable",
        "n": "Not available",
    }

    return names.get(
        status_code,
        "Availability concern",
    )


# =========================================================
# MAIN PAGE
# =========================================================

try:
    if not entry_id.strip().isdigit():
        st.error(
            "The Entry ID must contain "
            "numbers only."
        )

        st.stop()

    with st.spinner(
        "Loading your squad and "
        "official FPL availability data..."
    ):
        bootstrap = get_bootstrap()

        events = bootstrap.get(
            "events",
            [],
        )

        gameweek = get_current_gameweek(
            events
        )

        entry = get_entry(
            entry_id.strip()
        )

        picks_data = get_picks(
            entry_id.strip(),
            gameweek,
        )

    picks = picks_data.get(
        "picks",
        [],
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

    squad = [
        players.get(
            pick.get("element"),
            {},
        )
        for pick in picks
    ]

    squad_player_names = {
        player.get(
            "web_name",
            "",
        )
        for player in squad
    }

    squad_club_names = {
        teams.get(
            player.get("team"),
            {},
        ).get(
            "name",
            "",
        )
        for player in squad
    }

    squad_player_ids = {
        pick.get("element")
        for pick in picks
    }

    team_name = html.escape(
        str(
            entry.get(
                "name",
                "your squad",
            )
        )
    )

    hero_html = (
        f'<div class="hero">'
        f'<h1>📰 FPL News Centre</h1>'
        f'<p>'
        f'Live RSS headlines, press-conference '
        f'tracking and official FPL availability '
        f'alerts for {team_name}.'
        f'</p>'
        f'</div>'
    )

    st.markdown(
        hero_html,
        unsafe_allow_html=True,
    )

    # =====================================================
    # AUTO-REFRESHING NEWS PANEL
    # =====================================================

    @st.fragment(
        run_every=f"{refresh_seconds}s"
    )
    def live_news_panel():
        articles, feed_failures = (
            read_news_feeds()
        )

        articles = articles[
            :maximum_articles
        ]

        enriched_articles = []

        for article in articles:
            (
                matched_players,
                matched_clubs,
            ) = find_article_relevance(
                article,
                squad_player_names,
                squad_club_names,
            )

            complete_text = (
                f"{article['title']} "
                f"{article['summary']}"
            )

            enriched_articles.append(
                {
                    **article,
                    "category": (
                        article_category(
                            complete_text
                        )
                    ),
                    "freshness": (
                        freshness_label(
                            article[
                                "published"
                            ]
                        )
                    ),
                    "players": (
                        matched_players
                    ),
                    "clubs": (
                        matched_clubs
                    ),
                }
            )

        current_article_ids = {
            article["id"]
            for article
            in enriched_articles
        }

        session_key = (
            "fpl_news_seen_ids"
        )

        if session_key not in st.session_state:
            st.session_state[
                session_key
            ] = current_article_ids

            new_article_ids = set()

        else:
            new_article_ids = (
                current_article_ids
                - st.session_state[
                    session_key
                ]
            )

        new_relevant_articles = [
            article
            for article
            in enriched_articles
            if article["id"]
            in new_article_ids
            and (
                article["players"]
                or article["clubs"]
            )
        ]

        # =================================================
        # SIDEBAR NOTIFICATION
        # =================================================

        if new_relevant_articles:
            st.sidebar.markdown(
                "### 🔴 News alerts"
            )
        else:
            st.sidebar.markdown(
                "### 🟢 News alerts"
            )

        st.sidebar.metric(
            "New relevant stories",
            len(
                new_relevant_articles
            ),
        )

        st.sidebar.caption(
            "This count updates while the "
            "News Centre page is open."
        )

        if new_relevant_articles:
            st.sidebar.warning(
                f"{len(new_relevant_articles)} "
                f"new squad-related item(s) found."
            )

        if st.sidebar.button(
            "Mark news as read",
            key="mark_news_as_read",
            width="stretch",
        ):
            st.session_state[
                session_key
            ] = current_article_ids

            st.rerun()

        # =================================================
        # NEWS METRICS
        # =================================================

        flagged_squad_players = [
            player
            for player in squad
            if (
                player.get(
                    "status",
                    "a",
                ) != "a"
                or player.get("news")
            )
        ]

        captain = next(
            (
                players.get(
                    pick.get("element"),
                    {},
                )
                for pick in picks
                if pick.get("is_captain")
            ),
            {},
        )

        relevant_articles = [
            article
            for article
            in enriched_articles
            if (
                article["players"]
                or article["clubs"]
            )
        ]

        press_conference_articles = [
            article
            for article
            in enriched_articles
            if article["category"]
            == "Press Conference"
        ]

        articles_today = [
            article
            for article
            in enriched_articles
            if article["freshness"]
            in {
                "Breaking",
                "Today",
            }
        ]

        current_check_time = (
            datetime.now()
            .astimezone()
            .strftime(
                "%d %b %Y, %H:%M:%S"
            )
        )

        st.caption(
            f"Last checked: {current_check_time} · "
            f"Auto-refreshes every "
            f"{refresh_seconds} seconds while "
            f"this page is open."
        )

        metric_1, metric_2 = (
            st.columns(2)
        )

        metric_3, metric_4 = (
            st.columns(2)
        )

        metric_1.metric(
            "Squad Alerts",
            len(
                flagged_squad_players
            ),
        )

        metric_2.metric(
            "Relevant Stories",
            len(
                relevant_articles
            ),
        )

        metric_3.metric(
            "Press and Team Updates",
            len(
                press_conference_articles
            ),
        )

        metric_4.metric(
            "Published Today",
            len(
                articles_today
            ),
        )

        # =================================================
        # PERSONAL SQUAD ALERTS
        # =================================================

        st.subheader(
            "🚨 My Squad Alerts"
        )

        if not flagged_squad_players:
            st.success(
                "No official FPL availability "
                "flags are currently listed "
                "for your squad."
            )

        else:
            alert_rows = []

            for player in (
                flagged_squad_players
            ):
                player_pick = next(
                    (
                        pick
                        for pick in picks
                        if pick.get(
                            "element"
                        ) == player.get(
                            "id"
                        )
                    ),
                    {},
                )

                if player_pick.get(
                    "is_captain"
                ):
                    squad_role = (
                        "Captain"
                    )

                elif player_pick.get(
                    "is_vice_captain"
                ):
                    squad_role = (
                        "Vice-captain"
                    )

                else:
                    squad_role = "Squad"

                alert_rows.append(
                    {
                        "Player": player.get(
                            "web_name"
                        ),
                        "Club": teams.get(
                            player.get(
                                "team"
                            ),
                            {},
                        ).get(
                            "name"
                        ),
                        "Role": squad_role,
                        "Status": (
                            availability_name(
                                player.get(
                                    "status"
                                )
                            )
                        ),
                        "Chance of Playing": (
                            player.get(
                                "chance_of_playing_next_round"
                            )
                        ),
                        "Official FPL News": (
                            player.get(
                                "news"
                            )
                        ),
                        "Ownership %": (
                            player.get(
                                "selected_by_percent"
                            )
                        ),
                        "Transfers Out": (
                            safe_int(
                                player.get(
                                    "transfers_out_event"
                                )
                            )
                        ),
                    }
                )

            st.dataframe(
                pd.DataFrame(
                    alert_rows
                ),
                hide_index=True,
                width="stretch",
            )

        if captain and (
            captain.get(
                "status",
                "a",
            ) != "a"
            or captain.get("news")
        ):
            st.error(
                f"Captain alert: "
                f"{captain.get('web_name')} "
                f"has an official FPL "
                f"availability note. Review "
                f"captaincy before the deadline."
            )

        # =================================================
        # NEWS TABS
        # =================================================

        news_tabs = st.tabs(
            [
                "Relevant to My Squad",
                "Press Conferences",
                "Injuries",
                "Transfers",
                "Fixtures",
                "FPL Strategy",
                "All News",
            ]
        )

        news_groups = [
            relevant_articles,
            press_conference_articles,
            [
                article
                for article
                in enriched_articles
                if article["category"]
                == "Injury & Availability"
            ],
            [
                article
                for article
                in enriched_articles
                if article["category"]
                == "Transfers"
            ],
            [
                article
                for article
                in enriched_articles
                if article["category"]
                == "Fixtures"
            ],
            [
                article
                for article
                in enriched_articles
                if article["category"]
                == "FPL Strategy"
            ],
            enriched_articles,
        ]

        for news_tab, news_group in zip(
            news_tabs,
            news_groups,
        ):
            with news_tab:
                if not news_group:
                    st.info(
                        "No matching stories were "
                        "found in the current feeds."
                    )

                for article in news_group[:50]:
                    is_new = (
                        article["id"]
                        in new_article_ids
                    )

                    rendered_card = article_card(
                        article,
                        article[
                            "players"
                        ],
                        article[
                            "clubs"
                        ],
                        is_new=is_new,
                    )

                    st.markdown(
                        rendered_card,
                        unsafe_allow_html=True,
                    )

        # =================================================
        # FEED WARNINGS
        # =================================================

        if feed_failures:
            with st.expander(
                "Feed connection warnings"
            ):
                st.caption(
                    "A failed feed does not stop "
                    "the other sources from loading."
                )

                for failure in feed_failures:
                    st.write(
                        failure
                    )

    live_news_panel()

    # =====================================================
    # FPL AVAILABILITY CENTRE
    # =====================================================

    st.markdown("---")

    st.subheader(
        "🏥 Official FPL Availability Centre"
    )

    all_flagged_players = []

    for player in players.values():
        player_status = player.get(
            "status",
            "a",
        )

        player_news = player.get(
            "news",
            "",
        )

        if (
            player_status == "a"
            and not player_news
        ):
            continue

        all_flagged_players.append(
            {
                "Player": player.get(
                    "web_name"
                ),
                "Club": teams.get(
                    player.get("team"),
                    {},
                ).get(
                    "name"
                ),
                "Position": {
                    1: "Goalkeeper",
                    2: "Defender",
                    3: "Midfielder",
                    4: "Forward",
                }.get(
                    player.get(
                        "element_type"
                    ),
                    "Unknown",
                ),
                "Price": (
                    f"£{safe_int(player.get('now_cost')) / 10:.1f}m"
                ),
                "Status Code": (
                    player_status
                ),
                "Status": (
                    availability_name(
                        player_status
                    )
                ),
                "Chance of Playing": (
                    player.get(
                        "chance_of_playing_next_round"
                    )
                ),
                "Official News": (
                    player_news
                ),
                "Ownership %": (
                    player.get(
                        "selected_by_percent"
                    )
                ),
                "Transfers Out": safe_int(
                    player.get(
                        "transfers_out_event"
                    )
                ),
                "In My Squad": (
                    player.get("id")
                    in squad_player_ids
                ),
            }
        )

    availability_df = pd.DataFrame(
        all_flagged_players
    )

    if availability_df.empty:
        st.success(
            "No flagged players were returned "
            "by the current FPL data."
        )

    else:
        available_clubs = (
            ["All"]
            + sorted(
                availability_df[
                    "Club"
                ]
                .dropna()
                .unique()
                .tolist()
            )
        )

        filter_1, filter_2, filter_3 = (
            st.columns(3)
        )

        with filter_1:
            status_filter = st.selectbox(
                "Availability filter",
                [
                    "All",
                    "My squad",
                    "Doubtful",
                    "Injured",
                    "Suspended",
                    "Unavailable",
                ],
            )

        with filter_2:
            club_filter = st.selectbox(
                "Club filter",
                available_clubs,
            )

        with filter_3:
            high_ownership_only = (
                st.toggle(
                    "Ownership of 10% or more",
                    value=False,
                )
            )

        filtered_availability = (
            availability_df.copy()
        )

        status_codes = {
            "Doubtful": "d",
            "Injured": "i",
            "Suspended": "s",
            "Unavailable": "u",
        }

        if status_filter == "My squad":
            filtered_availability = (
                filtered_availability[
                    filtered_availability[
                        "In My Squad"
                    ]
                ]
            )

        elif status_filter in status_codes:
            filtered_availability = (
                filtered_availability[
                    filtered_availability[
                        "Status Code"
                    ]
                    == status_codes[
                        status_filter
                    ]
                ]
            )

        if club_filter != "All":
            filtered_availability = (
                filtered_availability[
                    filtered_availability[
                        "Club"
                    ] == club_filter
                ]
            )

        if high_ownership_only:
            ownership_values = (
                pd.to_numeric(
                    filtered_availability[
                        "Ownership %"
                    ],
                    errors="coerce",
                ).fillna(0)
            )

            filtered_availability = (
                filtered_availability[
                    ownership_values >= 10
                ]
            )

        displayed_availability = (
            filtered_availability
            .sort_values(
                "Transfers Out",
                ascending=False,
            )
        )

        st.dataframe(
            displayed_availability[
                [
                    "Player",
                    "Club",
                    "Position",
                    "Price",
                    "Status",
                    "Chance of Playing",
                    "Official News",
                    "Ownership %",
                    "Transfers Out",
                    "In My Squad",
                ]
            ],
            hide_index=True,
            width="stretch",
        )

    # =====================================================
    # OFFICIAL LINKS
    # =====================================================

    st.markdown("---")

    st.subheader(
        "🔎 Official Research Links"
    )

    st.caption(
        "These buttons open the original sources. "
        "The News Centre does not reproduce full articles."
    )

    link_columns = st.columns(2)

    for index, link_item in enumerate(
        OFFICIAL_LINKS.items()
    ):
        link_label, link_url = (
            link_item
        )

        link_columns[
            index % 2
        ].link_button(
            link_label,
            link_url,
            width="stretch",
        )

    # =====================================================
    # DEADLINE BRIEFING
    # =====================================================

    flagged_squad_count = len(
        [
            player
            for player in squad
            if (
                player.get(
                    "status",
                    "a",
                ) != "a"
                or player.get("news")
            )
        ]
    )

    st.markdown("---")

    st.subheader(
        "⏰ Deadline Briefing"
    )

    briefing_lines = [
        (
            f"Your squad currently has "
            f"**{flagged_squad_count} flagged "
            f"player(s)** in official FPL data."
        ),
        (
            "Check the Press Conferences tab "
            "again after club media briefings."
        ),
        (
            "Review the official FPL note for "
            "any flagged captain or vice-captain."
        ),
        (
            "Open the original publisher link "
            "before making a transfer based on "
            "a news headline."
        ),
        (
            "Refresh the page near the deadline "
            "because availability information "
            "can change quickly."
        ),
    ]

    st.info(
        "\n\n".join(
            briefing_lines
        )
    )

    st.caption(
        "News articles are displayed as headlines, "
        "short feed descriptions and links to the "
        "original publishers. Classification is "
        "keyword-based and does not use Gemini."
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
        f"A news or FPL source returned "
        f"status code {status_code}. "
        f"Refresh and try again."
    )

except requests.exceptions.Timeout:
    st.error(
        "A news or FPL source took too long "
        "to respond. Refresh and try again."
    )

except requests.exceptions.ConnectionError:
    st.error(
        "The page could not connect to a news "
        "or FPL source. Try again shortly."
    )

except (
    KeyError,
    IndexError,
    TypeError,
    ValueError,
) as error:
    st.error(
        "Some news or availability data was "
        "missing or had an unexpected format."
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
        "loading the FPL News Centre."
    )

    with st.expander(
        "Technical error details"
    ):
        st.code(
            str(error)
        )
