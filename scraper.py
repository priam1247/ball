"""
scraper.py — ScoreLine Live data layer
========================================
Source: ESPN (site.api.espn.com) — scores, events, live data

MATCH INCLUSION RULES:
  ✅ ANY match where BOTH teams are countries (detected by name)
  ✅ Whitelisted club leagues (EPL, UCL, La Liga, etc.)
  ❌ Everything else — no spam from obscure regional cups
  ❌ CANCELLED / POSTPONED / ABANDONED matches — silently ignored

EXTRA TIME & PENALTIES:
  Detected automatically from ESPN status fields.
  _went_to_et       → True if match went to extra time
  _went_to_penalties→ True if decided by penalty shootout
  _penalty_home/away→ Shootout score (goals scored, not misses)
"""

import time
import requests
from datetime import datetime, timezone


# ══════════════════════════════════════════════════════════════════
# ESPN COMPETITION SLUGS
# ══════════════════════════════════════════════════════════════════

ESPN_CLUB_LEAGUES = {
    "eng.1":            "Premier League",
    "ger.1":            "Bundesliga",
    "esp.1":            "La Liga",
    "ita.1":            "Serie A",
    "fra.1":            "Ligue 1",
    "uefa.champions":   "Champions League",
    "uefa.europa":      "Europa League",
    "uefa.europa.conf": "Europa Conference League",
    "eng.fa":           "FA Cup",
    "eng.2":            "Championship",
    "ned.1":            "Eredivisie",
    "por.1":            "Primeira Liga",
    "usa.1":            "MLS",
    "bra.1":            "Brasileirao",
    "mex.1":            "Liga MX",
    "sco.1":            "Scottish Premiership",
    "tur.1":            "Süper Lig",
    "bel.1":            "Belgian Pro League",
    "ksa.1":            "Saudi Pro League",       # ESPN uses ksa.1, not sau.1
    "afc.champions":    "AFC Champions Elite",    # ESPN slug for AFC CL
    "caf.champions":    "CAF Champions League",
}

ESPN_INTL_LEAGUES = {
    "fifa.friendly":        "International Friendly",
    "fifa.world":           "FIFA World Cup",
    "uefa.euro":            "European Championship",
    "uefa.nations":         "UEFA Nations League",
    "conmebol.america":     "Copa America",
    "concacaf.gold":        "Gold Cup",
    "caf.nations":          "AFCON",
    "fifa.worldq.uefa":     "WC Qualifier Europe",
    "fifa.worldq.caf":      "WC Qualifier Africa",
    "fifa.worldq.concacaf": "WC Qualifier CONCACAF",
    "fifa.worldq.conmebol": "WC Qualifier South America",
    "fifa.worldq.afc":      "WC Qualifier Asia",
    "fifa.worldq.ofc":      "WC Qualifier Oceania",
}

ESPN_CLUB_SLUGS = set(ESPN_CLUB_LEAGUES.keys())

# ESPN status names that mean a game was cancelled / will not be played
_CANCELLED_KEYWORDS = {"CANCEL", "POSTPONE", "SUSPEND", "ABANDON"}


# ══════════════════════════════════════════════════════════════════
# COUNTRY / NATIONAL TEAM DETECTION
# ══════════════════════════════════════════════════════════════════

COUNTRIES = {
    # Europe
    "Albania","Andorra","Armenia","Austria","Azerbaijan","Belarus",
    "Belgium","Bosnia","Bosnia & Herzegovina","Bosnia and Herzegovina",
    "Bulgaria","Croatia","Cyprus","Czech Republic","Czechia",
    "Denmark","England","Estonia","Faroe Islands","Finland","France",
    "Georgia","Germany","Gibraltar","Greece","Hungary","Iceland",
    "Ireland","Republic of Ireland","Northern Ireland",
    "Israel","Italy","Kazakhstan","Kosovo","Latvia",
    "Liechtenstein","Lithuania","Luxembourg","Malta","Moldova",
    "Montenegro","Netherlands","North Macedonia","Norway","Poland",
    "Portugal","Romania","Russia","Football Union of Russia",
    "San Marino","Scotland","Serbia","Slovakia","Slovenia","Spain",
    "Sweden","Switzerland","Turkey","Ukraine","Wales",
    # Americas
    "Argentina","Aruba","Bahamas","Barbados","Belize","Bermuda",
    "Bolivia","Brazil","Canada","Cayman Islands","Chile","Colombia",
    "Costa Rica","Cuba","Curacao","Dominican Republic","Ecuador",
    "El Salvador","Grenada","Guatemala","Guyana","Haiti","Honduras",
    "Jamaica","Martinique","Mexico","Nicaragua","Panama","Paraguay",
    "Peru","Puerto Rico","St. Kitts and Nevis","St Kitts and Nevis",
    "St. Lucia","St Lucia","Suriname","Trinidad and Tobago",
    "Trinidad & Tobago","Turks and Caicos","Uruguay",
    "USA","United States","Venezuela","Virgin Islands",
    "Antigua and Barbuda","Dominica","Saint Vincent and the Grenadines",
    "Montserrat","Anguilla",
    # Africa
    "Algeria","Angola","Benin","Botswana","Burkina Faso","Burundi",
    "Cameroon","Cape Verde","Cape Verde Islands","Central African Republic",
    "Chad","Comoros","Congo","DR Congo","Djibouti","Egypt",
    "Equatorial Guinea","Eritrea","Ethiopia","Gabon","Gambia","Ghana",
    "Guinea","Guinea-Bissau","Ivory Coast","Cote d'Ivoire",
    "Kenya","Lesotho","Liberia","Libya","Madagascar","Malawi","Mali",
    "Mauritania","Mauritius","Morocco","Mozambique","Namibia","Niger",
    "Nigeria","Rwanda","Sao Tome and Principe","Senegal","Seychelles",
    "Sierra Leone","Somalia","South Africa","South Sudan","Sudan",
    "Swaziland","Eswatini","Tanzania","Togo","Tunisia","Uganda",
    "Zambia","Zimbabwe",
    # Asia
    "Afghanistan","Bahrain","Bangladesh","Bhutan","Brunei","Cambodia",
    "China","Chinese Taipei","Taiwan","Guam","Hong Kong","India",
    "Indonesia","Iran","IR Iran","Iraq","Japan","Jordan","Kuwait",
    "Kyrgyzstan","Laos","Lebanon","Macau","Malaysia","Maldives",
    "Mongolia","Myanmar","Nepal","North Korea","Korea DPR",
    "Oman","Pakistan","Palestine","Philippines","Qatar","Saudi Arabia",
    "Singapore","South Korea","Korea Republic","Sri Lanka","Syria",
    "Tajikistan","Thailand","Timor-Leste","Turkmenistan",
    "UAE","United Arab Emirates","Uzbekistan","Vietnam","Yemen",
    # Oceania
    "American Samoa","Australia","Cook Islands","Fiji","New Caledonia",
    "New Zealand","Papua New Guinea","Samoa","Solomon Islands",
    "Tahiti","Tonga","Vanuatu",
}

CLUB_INDICATORS = [
    " fc", " cf", " sc", " ac", " bc", " bk", " sk", " fk", " nk",
    " united", " city", " town", " rovers", " wanderers", " athletic",
    " albion", " hotspur", " villa", " palace", " wednesday", " county",
    " forest", " rangers", " celtic", " thistle", " sporting", " benfica",
    " porto", " ajax", " psv", " feyenoord", " madrid", " barcelona",
    " atletico", " sevilla", " valencia", " juventus", " milan", " inter",
    " napoli", " roma", " lazio", " munich", " dortmund", " leverkusen",
    " frankfurt", " paris", " lyon", " marseille", " monaco",
    " arsenal", " chelsea", " liverpool", " tottenham",
    " galatasaray", " fenerbahce", " besiktas",
]


def is_national_team(name: str) -> bool:
    if not name:
        return False
    name_clean = name.strip()
    if name_clean in COUNTRIES:
        return True
    name_lower = name_clean.lower()
    if any(c.lower() == name_lower for c in COUNTRIES):
        return True
    if any(ind in f" {name_lower} " or name_lower.endswith(ind.strip())
           for ind in CLUB_INDICATORS):
        return False
    for country in COUNTRIES:
        if country.lower() in name_lower:
            return True
    return False


def is_international_match(match: dict) -> bool:
    home = match.get("homeTeam", {}).get("name", "")
    away = match.get("awayTeam", {}).get("name", "")
    return is_national_team(home) and is_national_team(away)


# ══════════════════════════════════════════════════════════════════
# ESPN — SOLE DATA SOURCE
# ══════════════════════════════════════════════════════════════════

ESPN_API = "http://site.api.espn.com/apis/site/v2/sports/soccer"
ESPN_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/131.0.0.0 Safari/537.36",
    "Accept":     "application/json, */*",
}


def _espn_get(url: str, timeout: int = 10) -> dict | None:
    try:
        r = requests.get(url, headers=ESPN_HEADERS, timeout=timeout)
        if r.status_code == 200:
            return r.json()
        elif r.status_code == 429:
            print("[ESPN] ⚠️  Rate limited — waiting 30s")
            time.sleep(30)
            return _espn_get(url, timeout)
        else:
            print(f"[ESPN] HTTP {r.status_code}: {url[:80]}")
    except Exception as e:
        print(f"[ESPN] ❌ {e}")
    return None


def espn_get_league(slug: str, league_name: str) -> list[dict]:
    from datetime import timedelta
    now       = datetime.now(timezone.utc)
    today     = now.strftime("%Y%m%d")
    yesterday = (now - timedelta(days=1)).strftime("%Y%m%d")
    today_str     = now.strftime("%Y-%m-%d")
    yesterday_str = (now - timedelta(days=1)).strftime("%Y-%m-%d")

    seen_ids = set()   # BUG5 FIX: deduplicate — same match can appear in both date fetches
    results  = []
    # Fetch both today AND yesterday to catch late-night matches still running
    for date_str, date_prefix in [(today, today_str), (yesterday, yesterday_str)]:
        data = _espn_get(f"{ESPN_API}/{slug}/scoreboard?dates={date_str}")
        if not data:
            continue
        for e in data.get("events", []):
            event_date = e.get("date", "")
            # Skip if not from the date we fetched
            if event_date and not event_date.startswith(date_prefix):
                continue
            n = _normalize_espn(e, slug, league_name)
            if not n:
                continue
            # Always include live/active matches regardless of date
            # Only skip yesterday's matches if they are already finished
            if date_str == yesterday and n["status"] == "FINISHED":
                continue
            # BUG5 FIX: skip if we already have this match from today's fetch
            if n["id"] in seen_ids:
                continue
            seen_ids.add(n["id"])
            results.append(n)
    return results


def espn_get_all_matches() -> list[dict]:
    print("[ESPN] Fetching today's matches...")
    all_matches = []
    for slug, name in {**ESPN_CLUB_LEAGUES, **ESPN_INTL_LEAGUES}.items():
        m = espn_get_league(slug, name)
        if m:
            print(f"[ESPN] {name}: {len(m)}")
        all_matches.extend(m)
        time.sleep(0.2)
    return all_matches


def _normalize_espn(event: dict, slug: str, league_name: str) -> dict | None:
    """
    Convert an ESPN event to our standard match dict.

    Cancelled/postponed/abandoned games return None — they are silently
    dropped and never posted.

    Extra time and penalty shootout fields:
      _went_to_et        True if the match entered extra time
      _went_to_penalties True if decided by a penalty shootout
      _penalty_home/away Shootout goal counts (not miss counts)
    """
    try:
        competitions = event.get("competitions", [{}])
        comp         = competitions[0] if competitions else {}
        competitors  = comp.get("competitors", [])
        if len(competitors) < 2:
            return None

        home = next((c for c in competitors if c.get("homeAway") == "home"), competitors[0])
        away = next((c for c in competitors if c.get("homeAway") == "away"), competitors[1])

        home_name = home.get("team", {}).get("displayName", "")
        away_name = away.get("team", {}).get("displayName", "")
        if not home_name or not away_name:
            return None

        state_str = event.get("status", {}).get("type", {}).get("state", "pre").lower()
        name_str  = event.get("status", {}).get("type", {}).get("name", "").upper()

        # ── Cancelled / postponed / abandoned — drop silently ─────
        if any(kw in name_str for kw in _CANCELLED_KEYWORDS):
            print(f"[ESPN] ⛔ Skipping cancelled/postponed: {home_name} vs {away_name}")
            return None

        # ── Status mapping (most specific first) ──────────────────
        went_to_et         = False
        went_to_penalties  = False
        penalty_home       = None
        penalty_away       = None

        if "SHOOTOUT" in name_str:
            norm_status       = "SHOOTOUT"
            went_to_et        = True
            went_to_penalties = True

        elif "OVER_TIME" in name_str or "OVERTIME" in name_str:
            # Covers STATUS_OVER_TIME, STATUS_FIRST_OVER_TIME, STATUS_SECOND_OVER_TIME
            norm_status  = "EXTRA_TIME"
            went_to_et   = True

        elif "HALFTIME" in name_str:
            norm_status = "PAUSED"

        elif state_str == "post":
            norm_status = "FINISHED"
            # Penalty shootout result — ESPN stores these as integers on the comp object
            sh = comp.get("shootoutHome")
            sa = comp.get("shootoutAway")
            if sh is not None and sa is not None:
                try:
                    # BUG2 FIX: ESPN sometimes returns "3.0" — use int(float()) to be safe
                    penalty_home      = int(float(str(sh)))
                    penalty_away      = int(float(str(sa)))
                    went_to_penalties = True
                    went_to_et        = True
                except (ValueError, TypeError):
                    pass
            elif "AET" in name_str or "OVER_TIME" in name_str:
                # Ended after ET but no shootout
                went_to_et = True

        elif state_str == "in":
            norm_status = "IN_PLAY"

        else:
            norm_status = "SCHEDULED"

        # ── Goals ─────────────────────────────────────────────────
        home_id = home.get("team", {}).get("id", "")
        goals   = []

        for play in comp.get("scoringPlays", []) or []:
            is_home = play.get("team", {}).get("id", "") == home_id
            goals.append({
                "minute": play.get("clock", {}).get("displayValue", "?"),
                "scorer": {"name": play.get("text", "Unknown")},
                "assist": {},
                "team":   {"shortName": home_name if is_home else away_name},
                "isHome": is_home,
                "score":  [],
            })

        if not goals:
            for detail in comp.get("details", []):
                dtype = detail.get("type", {}).get("text", "").lower()
                if "goal" in dtype or "penalty" in dtype:
                    is_home  = detail.get("team", {}).get("id", "") == home_id
                    athletes = detail.get("athletesInvolved", [{}])
                    goals.append({
                        "minute": detail.get("clock", {}).get("displayValue", "?"),
                        "scorer": {"name": athletes[0].get("displayName", "Unknown") if athletes else "Unknown"},
                        "assist": {},
                        "team":   {"shortName": home_name if is_home else away_name},
                        "isHome": is_home,
                        "score":  [],
                    })

        # ── Red cards ─────────────────────────────────────────────
        bookings = []
        for detail in comp.get("details", []):
            dtype = detail.get("type", {}).get("text", "").lower()
            if "red card" in dtype or "ejection" in dtype:
                is_home  = detail.get("team", {}).get("id", "") == home_id
                athletes = detail.get("athletesInvolved", [{}])
                bookings.append({
                    "minute": detail.get("clock", {}).get("displayValue", "?"),
                    "card":   "RED_CARD",
                    "player": {"name": athletes[0].get("displayName", "Unknown") if athletes else "Unknown"},
                    "team":   {"shortName": home_name if is_home else away_name},
                    "isHome": is_home,
                })

        home_sc = home.get("score")
        away_sc = away.get("score")

        return {
            "id":                  f"espn_{event.get('id', '')}",
            "utcDate":             event.get("date", ""),
            "status":              norm_status,
            "_minute":             event.get("status", {}).get("displayClock", ""),
            "_source":             "espn",
            "_comp_name":          league_name,
            "_comp_flag":          _comp_flag(league_name),
            "_is_intl":            slug in ESPN_INTL_LEAGUES,
            # Extra time / penalty flags
            "_went_to_et":         went_to_et,
            "_went_to_penalties":  went_to_penalties,
            "_penalty_home":       penalty_home,
            "_penalty_away":       penalty_away,
            "homeTeam": {
                "id":        str(home.get("team", {}).get("id", "")),
                "name":      home_name,
                "shortName": home.get("team", {}).get("abbreviation", home_name),
            },
            "awayTeam": {
                "id":        str(away.get("team", {}).get("id", "")),
                "name":      away_name,
                "shortName": away.get("team", {}).get("abbreviation", away_name),
            },
            "score": {
                "halfTime": {"home": None, "away": None},
                "fullTime": {
                    "home": int(home_sc) if home_sc is not None else None,
                    "away": int(away_sc) if away_sc is not None else None,
                },
            },
            "goals":    goals,
            "bookings": bookings,
            "lineups":  [],  # ESPN scoreboard API does not provide lineup data
        }

    except Exception as e:
        print(f"[ESPN] Normalize error: {e}")
        return None


# ══════════════════════════════════════════════════════════════════
# COMPETITION FLAG HELPER
# ══════════════════════════════════════════════════════════════════

_FLAG_MAP = {
    "Champions League": "🏆", "Premier League": "🏴󠁧󠁢󠁥󠁮󠁧󠁿",
    "Bundesliga": "🇩🇪", "La Liga": "🇪🇸", "Serie A": "🇮🇹",
    "Ligue 1": "🇫🇷", "World Cup": "🌍", "Friendly": "🤝",
    "European Championship": "🇪🇺", "Nations League": "🏆",
    "Europa League": "🟠", "Conference": "🟢", "FA Cup": "🏴󠁧󠁢󠁥󠁮󠁧󠁿",
    "Copa America": "🌎", "CONCACAF": "🌎", "Gold Cup": "🌎",
    "AFCON": "🌍", "Africa Cup": "🌍", "CAF": "🌍",
    "Asian": "🌏", "Qualifier": "🌍", "MLS": "🇺🇸",
    "Brasileirao": "🇧🇷", "Liga MX": "🇲🇽",
    "Scottish": "🏴󠁧󠁢󠁳󠁣󠁴󠁿", "Eredivisie": "🇳🇱",
    "Championship": "🏴󠁧󠁢󠁥󠁮󠁧󠁿",
}


def _comp_flag(comp_name: str) -> str:
    comp_lower = comp_name.lower()
    for k, v in _FLAG_MAP.items():
        if k.lower() in comp_lower:
            return v
    return "⚽"


# ══════════════════════════════════════════════════════════════════
# PUBLIC API — called by bot.py
# ══════════════════════════════════════════════════════════════════

def _is_stale_finished(match: dict) -> bool:
    """
    Returns True if a FINISHED match kicked off more than 4 hours ago.
    We never want to post these even if ESPN still shows them today.
    Matches still in EXTRA_TIME or SHOOTOUT are never stale.
    """
    if match.get("status") not in ("FINISHED",):
        return False
    utc_str = match.get("utcDate", "")
    if not utc_str:
        return False
    try:
        ko      = datetime.fromisoformat(utc_str.replace("Z", "+00:00"))
        elapsed = (datetime.now(timezone.utc) - ko).total_seconds() / 3600
        # BUG6 FIX: 4h was too tight — a 22:00 KO with ET + pens + delays can hit ~2.5h play time.
        # 6h gives safe headroom without leaking genuinely old results.
        return elapsed > 6
    except Exception:
        return False


def get_todays_matches() -> list[dict]:
    """
    All of today's relevant matches from ESPN.
    Cancelled / postponed / abandoned games are already filtered by
    _normalize_espn returning None — they never reach this list.
    """
    all_matches = espn_get_all_matches()

    # Keep whitelisted club leagues + any country vs country fixture
    matches = [
        m for m in all_matches
        if is_international_match(m)
        or any(
            m.get("_comp_name") == name
            for name in ESPN_CLUB_LEAGUES.values()
        )
    ]

    # Drop stale finished matches
    before  = len(matches)
    matches = [m for m in matches if not _is_stale_finished(m)]
    dropped = before - len(matches)
    if dropped:
        print(f"[SCRAPER] Dropped {dropped} stale finished match(es) from >4h ago")

    return matches
