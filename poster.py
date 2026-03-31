"""
poster.py — Facebook posting + message formatters
===================================================
Post format rules:
  • No horizontal separator lines
  • Only TWO hashtags per post: #ScoreLineLive  #CompetitionName
  • National teams get their country flag emoji automatically
  • Extra time and penalty shootout results are clearly labelled
"""

import time
import requests
import config

# ══════════════════════════════════════════════════════════════════
# COUNTRY → FLAG EMOJI
# ══════════════════════════════════════════════════════════════════

COUNTRY_FLAG = {
    # Europe
    "England": "🏴󠁧󠁢󠁥󠁮󠁧󠁿", "Scotland": "🏴󠁧󠁢󠁳󠁣󠁴󠁿", "Wales": "🏴󠁧󠁢󠁷󠁬󠁳󠁿",
    "Germany": "🇩🇪", "France": "🇫🇷", "Spain": "🇪🇸", "Italy": "🇮🇹",
    "Portugal": "🇵🇹", "Netherlands": "🇳🇱", "Belgium": "🇧🇪",
    "Croatia": "🇭🇷", "Serbia": "🇷🇸", "Poland": "🇵🇱",
    "Turkey": "🇹🇷", "Ukraine": "🇺🇦", "Switzerland": "🇨🇭",
    "Austria": "🇦🇹", "Denmark": "🇩🇰", "Sweden": "🇸🇪",
    "Norway": "🇳🇴", "Finland": "🇫🇮", "Hungary": "🇭🇺",
    "Czech Republic": "🇨🇿", "Czechia": "🇨🇿", "Slovakia": "🇸🇰",
    "Romania": "🇷🇴", "Greece": "🇬🇷", "Iceland": "🇮🇸",
    "Ireland": "🇮🇪", "Republic of Ireland": "🇮🇪",
    "Northern Ireland": "🏴󠁧󠁢󠁥󠁮󠁧󠁿",
    "Albania": "🇦🇱", "Kosovo": "🇽🇰", "Montenegro": "🇲🇪",
    "Slovenia": "🇸🇮", "Bosnia": "🇧🇦",
    "Bosnia and Herzegovina": "🇧🇦", "Bosnia & Herzegovina": "🇧🇦",
    "Bulgaria": "🇧🇬", "North Macedonia": "🇲🇰",
    "Georgia": "🇬🇪", "Armenia": "🇦🇲", "Azerbaijan": "🇦🇿",
    "Russia": "🇷🇺", "Belarus": "🇧🇾", "Moldova": "🇲🇩",
    "Lithuania": "🇱🇹", "Latvia": "🇱🇻", "Estonia": "🇪🇪",
    "Luxembourg": "🇱🇺", "Malta": "🇲🇹", "Cyprus": "🇨🇾",
    "Israel": "🇮🇱", "Kazakhstan": "🇰🇿",
    "Faroe Islands": "🇫🇴", "Gibraltar": "🇬🇮",
    "San Marino": "🇸🇲", "Andorra": "🇦🇩", "Liechtenstein": "🇱🇮",
    # Americas
    "Brazil": "🇧🇷", "Argentina": "🇦🇷", "Uruguay": "🇺🇾",
    "Colombia": "🇨🇴", "Chile": "🇨🇱", "Peru": "🇵🇪",
    "Ecuador": "🇪🇨", "Bolivia": "🇧🇴", "Paraguay": "🇵🇾",
    "Venezuela": "🇻🇪",
    "USA": "🇺🇸", "United States": "🇺🇸", "Mexico": "🇲🇽",
    "Canada": "🇨🇦", "Costa Rica": "🇨🇷", "Panama": "🇵🇦",
    "Honduras": "🇭🇳", "Jamaica": "🇯🇲", "Haiti": "🇭🇹",
    "Trinidad and Tobago": "🇹🇹", "Trinidad & Tobago": "🇹🇹",
    "El Salvador": "🇸🇻", "Guatemala": "🇬🇹", "Nicaragua": "🇳🇮",
    "Cuba": "🇨🇺", "Curacao": "🇨🇼", "Martinique": "🇲🇶",
    "Aruba": "🇦🇼", "Bermuda": "🇧🇲",
    # Africa
    "Nigeria": "🇳🇬", "Ghana": "🇬🇭", "Senegal": "🇸🇳",
    "Morocco": "🇲🇦", "Egypt": "🇪🇬", "Cameroon": "🇨🇲",
    "Ivory Coast": "🇨🇮", "Cote d'Ivoire": "🇨🇮",
    "South Africa": "🇿🇦", "Tunisia": "🇹🇳", "Algeria": "🇩🇿",
    "Mali": "🇲🇱", "Zambia": "🇿🇲", "Zimbabwe": "🇿🇼",
    "Tanzania": "🇹🇿", "Uganda": "🇺🇬", "Kenya": "🇰🇪",
    "Ethiopia": "🇪🇹", "Congo": "🇨🇬", "DR Congo": "🇨🇩",
    "Guinea": "🇬🇳", "Guinea-Bissau": "🇬🇼",
    "Burkina Faso": "🇧🇫", "Benin": "🇧🇯",
    "Gabon": "🇬🇦", "Angola": "🇦🇴", "Mozambique": "🇲🇿",
    "Rwanda": "🇷🇼", "Liberia": "🇱🇷", "Sierra Leone": "🇸🇱",
    "Gambia": "🇬🇲", "Togo": "🇹🇬", "Niger": "🇳🇪",
    "Namibia": "🇳🇦", "Botswana": "🇧🇼", "Malawi": "🇲🇼",
    "Mauritania": "🇲🇷", "Cape Verde": "🇨🇻",
    "Cape Verde Islands": "🇨🇻",
    "Equatorial Guinea": "🇬🇶", "Sudan": "🇸🇩",
    "South Sudan": "🇸🇸", "Somalia": "🇸🇴",
    "Central African Republic": "🇨🇫",
    "Sao Tome and Principe": "🇸🇹",
    "Comoros": "🇰🇲", "Seychelles": "🇸🇨",
    "Eswatini": "🇸🇿", "Lesotho": "🇱🇸",
    # Asia
    "Japan": "🇯🇵", "South Korea": "🇰🇷", "Korea Republic": "🇰🇷",
    "China": "🇨🇳", "Australia": "🇦🇺",
    "Iran": "🇮🇷", "IR Iran": "🇮🇷",
    "Saudi Arabia": "🇸🇦", "Qatar": "🇶🇦",
    "UAE": "🇦🇪", "United Arab Emirates": "🇦🇪",
    "Iraq": "🇮🇶", "Jordan": "🇯🇴",
    "Oman": "🇴🇲", "Bahrain": "🇧🇭", "Kuwait": "🇰🇼",
    "India": "🇮🇳", "Thailand": "🇹🇭", "Vietnam": "🇻🇳",
    "Indonesia": "🇮🇩", "Malaysia": "🇲🇾", "Philippines": "🇵🇭",
    "Uzbekistan": "🇺🇿", "Tajikistan": "🇹🇯",
    "North Korea": "🇰🇵", "Korea DPR": "🇰🇵",
    "Syria": "🇸🇾", "Lebanon": "🇱🇧", "Palestine": "🇵🇸",
    "Pakistan": "🇵🇰", "Bangladesh": "🇧🇩",
    "Hong Kong": "🇭🇰", "Singapore": "🇸🇬",
    "Sri Lanka": "🇱🇰", "Nepal": "🇳🇵",
    "Myanmar": "🇲🇲", "Cambodia": "🇰🇭",
    "Kyrgyzstan": "🇰🇬", "Turkmenistan": "🇹🇲",
    # Oceania
    "New Zealand": "🇳🇿", "Fiji": "🇫🇯",
    "Papua New Guinea": "🇵🇬", "Solomon Islands": "🇸🇧",
}


def team_flag(name: str) -> str:
    """Return the country flag emoji for a team name, or '' if it's a club."""
    if name in COUNTRY_FLAG:
        return COUNTRY_FLAG[name]
    for country, flag in COUNTRY_FLAG.items():
        if country.lower() in name.lower():
            return flag
    return ""


def team_display(name: str) -> str:
    """Append flag emoji to team name if it's a national team."""
    flag = team_flag(name)
    return f"{flag} {name}" if flag else name


# ══════════════════════════════════════════════════════════════════
# FACEBOOK POSTER
# ══════════════════════════════════════════════════════════════════

_last_post_time  = 0.0
_posts_this_hour = 0
_hour_start      = time.time()


def _rate_ok() -> bool:
    global _posts_this_hour, _hour_start
    now = time.time()
    if now - _hour_start > 3600:
        _posts_this_hour = 0
        _hour_start      = now
    if _posts_this_hour >= config.MAX_POSTS_PER_HOUR:
        print(f"[POSTER] ⚠️  Hourly limit ({config.MAX_POSTS_PER_HOUR}) reached")
        return False
    gap = config.MIN_POST_GAP - (now - _last_post_time)
    if gap > 0:
        time.sleep(gap)
    return True


def post(message: str) -> bool:
    """Post to the Facebook page. Returns True on success."""
    global _last_post_time, _posts_this_hour

    if not config.FB_PAGE_ID:
        print(f"\n{'='*50}\n[FB POST]\n{message}\n{'='*50}\n")
        return True

    if not _rate_ok():
        return False

    try:
        r = requests.post(
            f"https://graph.facebook.com/v19.0/{config.FB_PAGE_ID}/feed",
            data={"message": message, "access_token": config.FB_PAGE_ACCESS_TOKEN},
            timeout=15,
        )
        if r.status_code == 200:
            _last_post_time   = time.time()
            _posts_this_hour += 1
            print(f"[POSTER] ✅ Posted! id={r.json().get('id','?')}")
            return True
        err = r.json().get("error", {})
        print(f"[POSTER] ❌ {r.status_code}: {err.get('message', r.text[:120])}")
        return False
    except Exception as e:
        print(f"[POSTER] ❌ {e}")
        return False


# ══════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════

def _score_line(match: dict) -> str:
    h   = match["score"]["fullTime"].get("home")
    a   = match["score"]["fullTime"].get("away")
    hs  = str(h) if h is not None else "-"
    as_ = str(a) if a is not None else "-"
    return (f"{team_display(match['homeTeam']['name'])} "
            f"{hs} - {as_} "
            f"{team_display(match['awayTeam']['name'])}")


def _ht_score_line(match: dict) -> str:
    h = match["score"]["halfTime"].get("home")
    a = match["score"]["halfTime"].get("away")
    if h is None or a is None:
        return ""
    return f"HT: {h} - {a}"


def _tags(match: dict) -> str:
    """
    Exactly two hashtags:
      #ScoreLineLive   — always present
      #CompetitionName — no spaces, e.g. #ChampionsLeague
    """
    comp = match.get("_comp_name", "Football").replace(" ", "")
    return f"#ScoreLineLive #{comp}"


# ══════════════════════════════════════════════════════════════════
# MESSAGE FORMATTERS
# ══════════════════════════════════════════════════════════════════

def fmt_lineup(match: dict) -> str:
    comp = match.get("_comp_name", "Football")
    flag = match.get("_comp_flag", "⚽")
    lines = [
        f"{flag} LINEUP CONFIRMED | {comp}",
        f"⚽ {team_display(match['homeTeam']['name'])} vs "
        f"{team_display(match['awayTeam']['name'])}",
        "",
    ]
    for lu in match.get("lineups", []):
        team = lu.get("team", "")
        xi   = lu.get("startXI", [])
        lines.append(f"📋 {team}")
        for i, p in enumerate(xi, 1):
            num     = p["player"].get("number", "")
            name    = p["player"].get("name", "?")
            num_str = f"({num}) " if num else ""
            lines.append(f"  {i}. {num_str}{name}")
        lines.append("")
    lines.append(_tags(match))
    return "\n".join(lines)


def fmt_kickoff(match: dict) -> str:
    comp = match.get("_comp_name", "Football")
    flag = match.get("_comp_flag", "⚽")
    return "\n".join([
        f"{flag} KICK OFF! | {comp}",
        f"⚽ {_score_line(match)}",
        "",
        "The match has started! Follow us for live updates 🔔",
        "",
        _tags(match),
    ])


def fmt_goal(match: dict, goal: dict) -> str:
    comp   = match.get("_comp_name", "Football")
    flag   = match.get("_comp_flag", "⚽")
    scorer = goal["scorer"]["name"]
    team   = goal["team"]["shortName"]
    minute = goal["minute"]
    assist = goal.get("assist", {}).get("name", "")

    sc = goal.get("score", [])
    if sc and len(sc) == 2 and sc[0] is not None:
        score_now = f"{sc[0]} - {sc[1]}"
    else:
        h = match["score"]["fullTime"].get("home", "-")
        a = match["score"]["fullTime"].get("away", "-")
        score_now = f"{h} - {a}"

    team_flag_emoji = (
        team_flag(team)
        or team_flag(match["homeTeam"]["name"] if goal.get("isHome") else match["awayTeam"]["name"])
    )

    lines = [
        f"⚽ GOAL! {flag} | {comp}",
        f"{team_display(match['homeTeam']['name'])} {score_now} {team_display(match['awayTeam']['name'])}",
        "",
        f"🎯 {scorer} {team_flag_emoji} — {minute}'",
    ]
    if assist:
        lines.append(f"🅰️  Assist: {assist}")
    lines.append(f"   ({team})")
    lines.append("")
    lines.append(_tags(match))
    return "\n".join(lines)


def fmt_red_card(match: dict, booking: dict) -> str:
    comp   = match.get("_comp_name", "Football")
    flag   = match.get("_comp_flag", "⚽")
    player = booking["player"]["name"]
    team   = booking["team"]["shortName"]
    minute = booking["minute"]
    return "\n".join([
        f"🟥 RED CARD! {flag} | {comp}",
        f"⚽ {_score_line(match)}",
        "",
        f"🟥 {player} ({team}) — {minute}'",
        "",
        _tags(match),
    ])


def fmt_halftime(match: dict) -> str:
    comp = match.get("_comp_name", "Football")
    flag = match.get("_comp_flag", "⚽")
    ht   = _ht_score_line(match)

    goal_lines = []
    for g in match.get("goals", []):
        scorer  = g["scorer"]["name"]
        team    = g["team"]["shortName"]
        minute  = g["minute"]
        goal_lines.append(f"  ⚽ {scorer} ({team}) {minute}'")
    goals_str = "\n".join(goal_lines) if goal_lines else "  No goals yet"

    lines = [
        f"{flag} HALF TIME | {comp}",
        f"🕐 {_score_line(match)}",
    ]
    if ht:
        lines.append(ht)
    lines += ["", "1st Half Goals:", goals_str, "", _tags(match)]
    return "\n".join(lines)


def fmt_extratime(match: dict) -> str:
    """Posted once when a match enters extra time."""
    comp = match.get("_comp_name", "Football")
    flag = match.get("_comp_flag", "⚽")
    return "\n".join([
        f"{flag} EXTRA TIME! | {comp}",
        f"⏱️ {_score_line(match)}",
        "",
        "90 minutes weren't enough — extra time is underway! 🔥",
        "",
        _tags(match),
    ])


def fmt_fulltime(match: dict) -> str:
    comp = match.get("_comp_name", "Football")
    flag = match.get("_comp_flag", "⚽")
    ht   = _ht_score_line(match)

    # Build result suffix — AET / Penalties
    result_line = ""
    if match.get("_went_to_penalties") and match.get("_penalty_home") is not None:
        ph = match["_penalty_home"]
        pa = match["_penalty_away"]
        h_name = match["homeTeam"]["name"]
        a_name = match["awayTeam"]["name"]
        # Determine winner
        if ph > pa:
            winner = team_display(h_name)
        elif pa > ph:
            winner = team_display(a_name)
        else:
            winner = "Draw"
        result_line = f"🥅 Penalties: {ph} - {pa}  ({winner} wins)"
    elif match.get("_went_to_et"):
        result_line = "⏱️ After Extra Time (AET)"

    goal_lines = []
    for g in match.get("goals", []):
        scorer = g["scorer"]["name"]
        team   = g["team"]["shortName"]
        minute = g["minute"]
        goal_lines.append(f"  ⚽ {scorer} ({team}) {minute}'")
    goals_str = "\n".join(goal_lines) if goal_lines else "  No goals"

    lines = [
        f"{flag} FULL TIME | {comp}",
        f"🏁 {_score_line(match)}",
    ]
    if ht:
        lines.append(ht)
    if result_line:
        lines.append(result_line)
    lines += ["", "Goals:", goals_str, "", _tags(match)]
    return "\n".join(lines)


def fmt_daily_preview(matches: list) -> str:
    if not matches:
        return (
            "⚽ No big matches on the schedule today.\n"
            "Check back tomorrow!\n\n"
            "#ScoreLineLive #Football"
        )
    from itertools import groupby
    from datetime import datetime, timezone

    lines = ["⚽ TODAY'S BIG MATCHES"]

    sorted_m = sorted(
        matches,
        key=lambda m: (m.get("_comp_name", ""), m.get("utcDate", ""))
    )

    for comp_name, grp in groupby(sorted_m, key=lambda m: m.get("_comp_name", "")):
        grp_list  = list(grp)
        comp_flag = grp_list[0].get("_comp_flag", "⚽") if grp_list else "⚽"
        lines.append(f"\n{comp_flag} {comp_name}")
        for m in grp_list:
            h = team_display(m["homeTeam"]["name"])
            a = team_display(m["awayTeam"]["name"])
            try:
                ko = datetime.fromisoformat(m["utcDate"].replace("Z", "+00:00"))
                t  = ko.strftime("%H:%M UTC")
            except Exception:
                t = "TBD"
            lines.append(f"  ⚔️  {h} vs {a}  🕐 {t}")

    lines += [
        "",
        f"🔔 {len(matches)} matches today — follow us for live goals, red cards & results!",
        "",
        "#ScoreLineLive #Football",
    ]
    return "\n".join(lines)
