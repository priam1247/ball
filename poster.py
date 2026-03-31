"""
poster.py — Facebook posting + message formatters
===================================================
Post format matches the app screenshots exactly:

  Daily preview:
    📌 Today's games:
    🇩🇪 Germany - 🇬🇭 Ghana (20:45)
    🇬🇧 England - 🇯🇵 Japan (20:45)
    #scorelinelive

  Kickoff:
    ▶️ Live: 🇩🇪 Germany 0-0 🇬🇭 Ghana
    ⚽ Kickoff!
    #scorelinelive

  Goal:
    ▶️ Live: 🇩🇪 Germany 1-1 🇬🇭 Ghana
    ⚽ Goal: Fatawu (70')
    #scorelinelive

  Full time:
    ▶️ FT: 🇬🇩 Grenada 0-3 🇰🇪 Kenya
    ⚽ Goal: Obiero (82')
    #scorelinelive

No halftime posts. No red card posts.
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
    "Aruba": "🇦🇼", "Bermuda": "🇧🇲", "Grenada": "🇬🇩",
    "Guyana": "🇬🇾", "Belize": "🇧🇿", "Suriname": "🇸🇷",
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
    if name in COUNTRY_FLAG:
        return COUNTRY_FLAG[name]
    for country, flag in COUNTRY_FLAG.items():
        if country.lower() in name.lower():
            return flag
    return ""


def _td(name: str) -> str:
    """Team display: flag + name."""
    f = team_flag(name)
    return f"{f} {name}" if f else name


def _scoreline(match: dict) -> str:
    """e.g.  🇩🇪 Germany 1-1 🇬🇭 Ghana"""
    h  = match["score"]["fullTime"].get("home")
    a  = match["score"]["fullTime"].get("away")
    hs = str(h) if h is not None else "0"
    as_= str(a) if a is not None else "0"
    return f"{_td(match['homeTeam']['name'])} {hs}-{as_} {_td(match['awayTeam']['name'])}"


def _minute(minute) -> str:
    return str(minute).rstrip("'").strip()


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
# MESSAGE FORMATTERS — match the app screenshots exactly
# ══════════════════════════════════════════════════════════════════

def fmt_daily_preview(matches: list) -> str:
    """
    📌 Today's games:
    🇩🇪 Germany - 🇬🇭 Ghana (20:45)
    🇬🇧 England - 🇯🇵 Japan (20:45)
    #scorelinelive
    """
    from datetime import datetime, timezone

    if not matches:
        return "📌 Today's games:\nNo big matches today. Check back tomorrow!\n\n#scorelinelive"

    lines = ["📌 Today's games:"]
    sorted_m = sorted(matches, key=lambda m: m.get("utcDate", ""))
    for m in sorted_m:
        h = _td(m["homeTeam"]["name"])
        a = _td(m["awayTeam"]["name"])
        try:
            ko = datetime.fromisoformat(m["utcDate"].replace("Z", "+00:00"))
            t  = ko.strftime("%H:%M")
        except Exception:
            t = "TBD"
        lines.append(f"{h} - {a} ({t})")

    lines.append("\n#scorelinelive")
    return "\n".join(lines)


def fmt_lineup(match: dict) -> str:
    """
    📌 Lineups: 🇩🇪 Germany vs 🇬🇭 Ghana
    Germany: Neuer, Kimmich, Wirtz...
    Ghana: Ati-Zigi, Kudus...
    #scorelinelive
    """
    h = _td(match["homeTeam"]["name"])
    a = _td(match["awayTeam"]["name"])
    lines = [f"📌 Lineups: {h} vs {a}"]
    for lu in match.get("lineups", []):
        team    = lu.get("team", "")
        players = [p["player"].get("name", "?") for p in lu.get("startXI", [])]
        if players:
            lines.append(f"{team}: {', '.join(players)}")
    lines.append("\n#scorelinelive")
    return "\n".join(lines)


def fmt_kickoff(match: dict) -> str:
    """
    ▶️ Live: 🇩🇪 Germany 0-0 🇬🇭 Ghana
    ⚽ Kickoff!
    #scorelinelive
    """
    h = _td(match["homeTeam"]["name"])
    a = _td(match["awayTeam"]["name"])
    return f"▶️ Live: {h} 0-0 {a}\n⚽ Kickoff!\n\n#scorelinelive"


def fmt_goal(match: dict, goal: dict) -> str:
    """
    ▶️ Live: 🇩🇪 Germany 1-1 🇬🇭 Ghana
    ⚽ Goal: Fatawu (70')
    #scorelinelive
    """
    scorer = goal["scorer"]["name"]
    minute = _minute(goal["minute"])

    # Score at moment of goal
    sc = goal.get("score", [])
    if sc and len(sc) == 2 and sc[0] is not None:
        h_sc, a_sc = sc[0], sc[1]
        scoreline = (f"{_td(match['homeTeam']['name'])} {h_sc}-{a_sc} "
                     f"{_td(match['awayTeam']['name'])}")
    else:
        scoreline = _scoreline(match)

    lines = [
        f"▶️ Live: {scoreline}",
        f"⚽ Goal: {scorer} ({minute}')",
    ]
    assist = goal.get("assist", {}).get("name", "")
    if assist:
        lines.append(f"🅰️ Assist: {assist}")
    lines.append("\n#scorelinelive")
    return "\n".join(lines)


def fmt_fulltime(match: dict) -> str:
    """
    ▶️ FT: 🇬🇩 Grenada 0-3 🇰🇪 Kenya
    ⚽ Goal: Obiero (82')
    ⚽ Goal: Obiero (45')
    #scorelinelive
    """
    scoreline = _scoreline(match)

    # AET / penalties label
    prefix = "FT"
    if match.get("_went_to_penalties"):
        ph = match.get("_penalty_home", "")
        pa = match.get("_penalty_away", "")
        prefix = f"FT (Pen: {ph}-{pa})"
    elif match.get("_went_to_et"):
        prefix = "FT (AET)"

    lines = [f"▶️ {prefix}: {scoreline}"]

    for g in match.get("goals", []):
        scorer = g["scorer"]["name"]
        minute = _minute(g["minute"])
        lines.append(f"⚽ Goal: {scorer} ({minute}')")

    lines.append("\n#scorelinelive")
    return "\n".join(lines)


def fmt_extratime(match: dict) -> str:
    """
    ▶️ Live: 🇩🇪 Germany 1-1 🇬🇭 Ghana
    ⏱️ Extra time underway!
    #scorelinelive
    """
    return (f"▶️ Live: {_scoreline(match)}\n"
            f"⏱️ Extra time underway!\n\n#scorelinelive")


# Kept for bot.py compatibility — no longer posts but referenced
def fmt_halftime(match: dict) -> str:
    return ""

def fmt_red_card(match: dict, booking: dict) -> str:
    return ""
