"""Portfolio monitor dashboard: Bloomberg-terminal style, single page (Streamlit).

Run locally:   streamlit run monitor/dashboard/app.py
It only reads monitor.db (written by `python -m monitor.run`). It never trades.
"""
import html
import os
import sys

import altair as alt
import pandas as pd
import streamlit as st

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from monitor import config, dashboard_data, plan, scanner  # noqa: E402

st.set_page_config(page_title="Portfolio Monitor", page_icon="▣", layout="wide")

AMBER, GREEN, RED, BLUE, YELLOW, GREY = "#FFA62B", "#3DDC84", "#FF5C5C", "#4EA8FF", "#FFE14D", "#8A93A3"
SEV = {"high": RED, "warn": AMBER, "info": BLUE}
SENT = {"positive": GREEN, "neutral": GREY, "negative": RED}

st.markdown(f"""
<style>
  .stApp {{ background:#07090C; }}
  html, body, [class*="css"], .stMarkdown, .stText, p, td, th, div {{ font-family:"IBM Plex Mono","SFMono-Regular",Menlo,Consolas,monospace; }}
  .block-container {{ padding-top:3.6rem; padding-bottom:3rem; max-width:1500px; }}
  h1, h2, h3 {{ font-family:"IBM Plex Mono",Menlo,monospace !important; letter-spacing:.02em; }}
  .hdr {{ display:flex; justify-content:space-between; align-items:baseline; border-bottom:2px solid {AMBER}; padding-bottom:6px; margin-bottom:10px; flex-wrap:wrap; gap:8px; }}
  .hdr b {{ color:{AMBER}; font-size:20px; letter-spacing:.12em; }}
  .hdr span {{ color:{GREY}; font-size:12px; }}
  .sec {{ color:{AMBER}; font-size:12px; letter-spacing:.14em; text-transform:uppercase; border-bottom:1px solid #1E242D; padding:14px 0 4px; margin-bottom:8px; }}
  .strip {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(130px,1fr)); gap:1px; background:#1E242D; border:1px solid #1E242D; }}
  .cell {{ background:#0C1015; padding:8px 10px; }}
  .cell small {{ display:block; color:{GREY}; font-size:10px; letter-spacing:.1em; text-transform:uppercase; }}
  .cell b {{ font-size:18px; color:#E8ECF1; font-variant-numeric:tabular-nums; }}
  .up {{ color:{GREEN} !important; }} .dn {{ color:{RED} !important; }} .am {{ color:{AMBER} !important; }}
  .alert {{ border-left:4px solid; background:#0C1015; padding:6px 10px; margin-bottom:4px; font-size:13px; color:#DDE3EA; }}
  .alert .k {{ font-size:10px; letter-spacing:.1em; text-transform:uppercase; margin-right:8px; }}
  .alert.newstrike {{ background:#16150A; }}
  .tag {{ font-size:10px; padding:1px 5px; border:1px solid; margin-left:6px; }}
  table.grid {{ width:100%; border-collapse:collapse; font-size:12px; color:#DDE3EA; }}
  table.grid th {{ color:{AMBER}; font-weight:500; text-align:right; border-bottom:1px solid #2A313B; padding:4px 6px; white-space:nowrap; font-size:11px; }}
  table.grid th:first-child, table.grid td:first-child {{ text-align:left; }}
  table.grid td {{ text-align:right; padding:4px 6px; border-bottom:1px solid #141920; white-space:nowrap; font-variant-numeric:tabular-nums; }}
  table.grid tr.held td {{ background:#2A2008; color:{AMBER}; }}
  .wrap {{ overflow-x:auto; }}
  .pill {{ display:inline-block; padding:0 7px; border-radius:9px; font-size:11px; }}
  .bar {{ display:inline-block; width:70px; height:7px; background:#1A2028; vertical-align:middle; position:relative; }}
  .bar i {{ position:absolute; left:0; top:0; bottom:0; }}
  .news {{ background:#0C1015; border:1px solid #1E242D; padding:10px 12px; margin-bottom:8px; color:#DDE3EA; font-size:13px; }}
  .news a {{ color:{BLUE}; text-decoration:none; }}
  .news .flag {{ color:{AMBER}; }}
  .muted {{ color:{GREY}; font-size:12px; }}
</style>""", unsafe_allow_html=True)


def money(v, d=2):
    return "–" if v is None else f"{'-' if v < 0 else ''}${abs(v):,.{d}f}"


def num(v, d=2):
    return "–" if v is None else f"{v:,.{d}f}"


def cls(v):
    return "" if v is None or abs(v) < 1e-9 else ("up" if v > 0 else "dn")


def e(s):
    return html.escape(str(s))


def chart_theme(c):
    return (c.configure(background="#07090C").configure_view(stroke=None)
            .configure_axis(labelColor=GREY, titleColor=GREY, gridColor="#161B22", domainColor="#2A313B",
                            labelFont="monospace", titleFont="monospace")
            .configure_legend(labelColor="#DDE3EA", titleColor=GREY, labelFont="monospace", orient="bottom", columns=3))


def cache_key():
    """Changes whenever the data or the dashboard code changes, so the page never shows stale data."""
    parts = []
    for path in (config.DB_FILE, dashboard_data.__file__, plan.__file__, __file__):
        try:
            parts.append(str(os.path.getmtime(path)))
        except OSError:
            parts.append("0")
    return "|".join(parts)


@st.cache_data(ttl=300)
def get(asof, key):
    data = dashboard_data.load(asof=asof)
    for p in data.get("positions", []):  # make sure every position has a plan label
        if not p.get("action"):
            p["action"], p["action_reason"] = plan.for_position(p)
    for a in data.get("alerts", []):
        a.setdefault("action", plan.ALERT_ACTION.get(a.get("kind")))
    return data


KEY = cache_key()
first = get(None, KEY)
if not first["asof"]:
    st.markdown('<div class="hdr"><b>PORTFOLIO MONITOR</b><span>no data yet</span></div>', unsafe_allow_html=True)
    st.info("No runs stored yet. Run `python -m monitor.run` (or the GitHub workflow) and refresh.")
    st.stop()

with st.sidebar:
    asof = st.selectbox("As of", first["dates"], index=0)
    st.caption("A monitor only: it reports conditions, tracks your own targets, and summarizes news. "
               "Nothing here recommends trades or places orders.")
D = get(asof, KEY)
P, A, M = D["positions"], D["analytics"] or {}, D["macro"]

# ---------- header + status strip ----------
st.markdown(f'<div class="hdr"><b>PORTFOLIO MONITOR</b><span>AS OF {e(D["asof"])} · '
            f'{len(P)} POSITIONS · MONITOR ONLY</span></div>', unsafe_allow_html=True)
nav = A.get("total_value") or sum(p["value"] or 0 for p in P)
pnl, pnl_pct = A.get("pnl"), A.get("pnl_pct")
macro_txt = f"{M['score']:.0f} {M['label'].upper()}" if M and M.get("score") is not None else "–"
macro_cls = "" if not M or M.get("score") is None else ("up" if M["label"] == "Calm" else "dn" if M["label"] == "Stressed" else "am")
n_high = sum(1 for a in D["alerts"] if a["severity"] == "high")
cells = [("NAV", money(nav), ""), ("P&L", f"{money(pnl)} ({num(pnl_pct, 1)}%)" if pnl is not None else "–", cls(pnl)),
         ("Positions", str(len(P)), ""), ("Alerts", f"{len(D['alerts'])}" + (f" · {n_high} HIGH" if n_high else ""),
                                         "dn" if n_high else ""),
         ("Macro score", macro_txt, macro_cls), ("Net delta", f"{num(A.get('net_delta'), 0)} sh", ""),
         ("Daily theta", money(A.get("daily_theta")), cls(A.get("daily_theta"))), ("As of", D["asof"], "")]
st.markdown('<div class="strip">' + "".join(f'<div class="cell"><small>{k}</small><b class="{c}">{v}</b></div>'
                                             for k, v, c in cells) + "</div>", unsafe_allow_html=True)

# ---------- alerts ----------
# ---------- your plan ----------
def plan_pill(action):
    c = plan.COLORS.get(action, GREY)
    return f'<span class="pill" style="background:{c};color:#07090C;font-weight:700">{e(action)}</span>'


st.markdown('<div class="sec">Your plan says</div>', unsafe_allow_html=True)
order = {"SELL": 0, "BUY MORE": 1, "REVIEW": 2, "HOLD": 3}
for p in sorted([x for x in P if x["asset_type"] != "cash"], key=lambda x: order.get(x["action"], 9)):
    nm = (f"{p['ticker']} ${p['strike']:g} {p['option_type']} · {p['expiry']}" if p["asset_type"] == "option"
          else f"{p['ticker']} shares")
    st.markdown(f'<div class="alert" style="border-color:{plan.COLORS.get(p["action"], GREY)};font-size:14px">'
                f'{plan_pill(p["action"])} &nbsp;<b>{e(nm)}</b> <span class="muted">· {e(p["action_reason"])}'
                + (f' · stop {num(p["stop_price"])} · target {num(p["target_price"])}'
                   if p.get("stop_price") is not None else "") + '</span></div>',
                unsafe_allow_html=True)
st.markdown('<div class="muted">Labels apply your own levels from positions.json, or, where you set none, automatic ones: '
            'a trailing stop 3x the stock\'s typical daily move below its highest close, and a 2-to-1 target. '
            'They are rules, not predictions or financial advice.</div>', unsafe_allow_html=True)

def pct(v, d=1):
    return "–" if v is None else f'<span class="{cls(v)}">{v * 100:+.{d}f}%</span>'


# ---------- rotation ----------
R = D.get("rotation") or {}
st.markdown('<div class="sec">Rotation · follow the money</div>', unsafe_allow_html=True)
for sug in R.get("suggestions") or []:
    st.markdown(f'<div class="alert" style="border-color:{plan.COLORS["SWAP"]};font-size:15px;background:#17121F">'
                f'{plan_pill("SWAP")} &nbsp;<b>Sell all {e(sug["sell"])}</b> (about ${sug["amount"]:,.0f}, rank '
                f'#{sug["sell_rank"]}) <b>→ buy {e(sug["buy"])}</b> (rank #{sug["buy_rank"]})'
                f'<div class="muted" style="margin-top:4px">{e(sug["reason"])} Suggested {e(sug["asof"])}.</div></div>',
                unsafe_allow_html=True)
if not R.get("suggestions") and R.get("universe"):
    st.markdown('<div class="muted">No swap right now: no stock you don\'t own clearly beats a holding that\'s free to swap '
                f'(needs a score of {config.ROTATION_MIN_SCORE}+ and a {config.ROTATION_MARGIN}-point lead).</div>',
                unsafe_allow_html=True)
if R.get("universe"):
    c1, c2 = st.columns(2)
    def score_table(items, title):
        t = (f'<div class="muted" style="color:#FFA62B;margin-top:8px">{title}</div><div class="wrap"><table class="grid">'
             '<tr><th>Ticker</th><th>Rank</th><th>Score</th><th>Momentum</th><th>Steadiness</th><th>Trend</th><th>12 mo</th></tr>')
        for x in items:
            t += (f'<tr><td>{e(x["ticker"])}</td><td>#{x["rank"]}</td><td><b>{x["score"]:.0f}</b></td>'
                  f'<td>{x["momentum"]:.0f}</td><td>{x["steadiness"]:.0f}</td><td>{x["trend"]:.0f}</td>'
                  f'<td>{pct(x["ret_12m"], 0)}</td></tr>')
        return t + "</table></div>"
    with c1:
        st.markdown(score_table(R["holdings"], f"YOUR HOLDINGS · RANKED AMONG {R['universe']} STOCKS & ETFS (WEAKEST FIRST)"),
                    unsafe_allow_html=True)
    with c2:
        st.markdown(score_table(R["top"], "STRONGEST YOU DON'T OWN"), unsafe_allow_html=True)
    st.markdown('<div class="muted">Score 0-100 = momentum 40% + steadiness 30% + trend 20% + news 10%. A swap is suggested '
                f'only with a clear lead; each stock can be swapped at most once every {config.ROTATION_COOLDOWN_DAYS} days, '
                f'each into a different stock. Rule-based, not a prediction.</div>', unsafe_allow_html=True)

# ---------- wins & losses + swap scorecard ----------
PF = D.get("performance") or {}
st.markdown('<div class="sec">Wins &amp; losses · did the swaps work?</div>', unsafe_allow_html=True)
W = PF.get("wins_losses")
if W and W["trades"]:
    wl_cells = [("Locked in (realized)", money(W["realized"]), cls(W["realized"])),
                ("Still open (unrealized)", money(W["unrealized"]), cls(W["unrealized"])),
                ("Total", money(W["total"]), cls(W["total"])),
                ("Wins / losses", f'{W["wins"]} / {W["losses"]}', ""),
                ("Win rate", f'{W["win_rate"]:.0f}%' if W["win_rate"] is not None else "–", ""),
                ("Avg win / loss", f'{money(W["avg_win"])} / {money(W["avg_loss"])}', ""),
                ("Fees", money(W["fees"]), "")]
    st.markdown('<div class="strip">' + "".join(f'<div class="cell"><small>{k}</small><b class="{c}">{v}</b></div>'
                                                 for k, v, c in wl_cells) + "</div>", unsafe_allow_html=True)
    if W["closed"]:
        t = ('<div class="wrap"><table class="grid"><tr><th>Date</th><th>Sold</th><th>Qty</th><th>Price</th>'
             '<th>Profit / loss</th></tr>')
        for x in W["closed"][:15]:
            t += (f'<tr><td>{e(x["trade_date"])}</td><td>{e(x["ticker"])}</td><td>{x["quantity"]:g}</td>'
                  f'<td>{num(x["price"])}</td><td class="{cls(x["realized"])}"><b>{money(x["realized"])}</b></td></tr>')
        st.markdown(t + "</table></div>", unsafe_allow_html=True)
else:
    st.markdown('<div class="muted">No trades from Interactive Brokers yet. They appear after the Flex Query includes the '
                '<b>Trades</b> section and the next evening run.</div>', unsafe_allow_html=True)

H = [h for h in PF.get("history") or [] if h.get("value")]
if len(H) >= 2 and H[0].get("spy"):
    base_v, base_s = H[0]["value"], H[0]["spy"]
    line = []
    for h in H:
        line.append({"date": h["asof"], "series": "Your book", "return": h["value"] / base_v - 1})
        if h.get("spy"):
            line.append({"date": h["asof"], "series": "S&P 500 (SPY)", "return": h["spy"] / base_s - 1})
    ch = alt.Chart(pd.DataFrame(line)).mark_line(point=True).encode(
        x=alt.X("date:T", title=None), y=alt.Y("return:Q", axis=alt.Axis(format="%"), title="since first tracked day"),
        color=alt.Color("series:N", scale=alt.Scale(range=[AMBER, GREY]), legend=alt.Legend(orient="top")))
    st.altair_chart(chart_theme(ch.properties(height=220)), width="stretch")
    st.markdown('<div class="muted">Book value includes cash; money you add or withdraw moves this line too.</div>',
                unsafe_allow_html=True)

cards = PF.get("scorecard") or []
if cards:
    S = (PF.get("summary") or {}).get("all") or {}
    if S.get("scored"):
        st.markdown(f'<div style="margin:8px 0;font-size:14px"><b>{S["beat"]} of {S["scored"]}</b> swap ideas are ahead of '
                    f'keeping the old stock · average edge <b class="{cls(S["avg_edge"])}">{S["avg_edge"] * 100:+.1f} pts</b>'
                    '</div>', unsafe_allow_html=True)
    fol = {"yes": ("FOLLOWED", GREEN), "partly": ("PARTLY", AMBER), "no": ("SKIPPED", GREY), "open": ("OPEN", BLUE)}
    t = ('<div class="wrap"><table class="grid"><tr><th>Idea date</th><th>Sell</th><th>Buy</th><th>You</th>'
         '<th>Sold stock since</th><th>Bought stock since</th><th>Swap edge</th><th>Days</th></tr>')
    for c in cards:
        lab, col = fol.get(c["followed"], (c["followed"], GREY))
        t += (f'<tr><td>{e(c["suggested_on"])}</td><td>{e(c["sell"])}</td><td>{e(c["buy"])}</td>'
              f'<td><span class="pill" style="background:{col};color:#07090C;font-weight:700">{lab}</span></td>'
              f'<td>{pct(c["sell_ret"])}</td><td>{pct(c["buy_ret"])}</td><td><b>{pct(c["edge"])}</b></td>'
              f'<td>{c["days"]}</td></tr>')
    st.markdown(t + "</table></div>", unsafe_allow_html=True)
    st.markdown('<div class="muted">Swap edge = bought stock\'s return minus sold stock\'s return, from the close on the idea '
                'date. Positive means the swap beat keeping the old stock. Skipped ideas are scored too. Give it several '
                'weeks before judging: the ranking looks 3-12 months back, not days.</div>', unsafe_allow_html=True)

st.markdown('<div class="sec">Active alerts</div>', unsafe_allow_html=True)
if not D["alerts"]:
    st.markdown('<div class="muted">No alerts.</div>', unsafe_allow_html=True)
for a in D["alerts"]:
    newstrike = a["kind"] in ("new_strikes", "new_expiry")
    color = YELLOW if newstrike else SEV.get(a["severity"], GREY)
    st.markdown(f'<div class="alert{" newstrike" if newstrike else ""}" style="border-color:{color}">'
                f'<span class="k" style="color:{color}">{e(a["severity"])} · {e(a["kind"])}</span>{e(a["message"])}'
                + (f' &nbsp;<span class="muted">your plan:</span> {plan_pill(a["action"])}' if a.get("action") else "")
                + (f'<span class="tag" style="color:{color}">NEW</span>' if a["is_new"] and not newstrike else "")
                + "</div>", unsafe_allow_html=True)

# ---------- positions grid ----------
st.markdown('<div class="sec">Positions</div>', unsafe_allow_html=True)


def bar(pct, color):
    if pct is None:
        return '<span class="muted">–</span>'
    w = max(0, min(100, pct))
    return f'<span class="bar"><i style="width:{w}%;background:{color}"></i></span> {pct:.0f}%'


def dte_pill(d):
    if d is None:
        return "–"
    c = RED if d < 21 else AMBER if d < config.DTE_WATCH_DAYS else "#2E8B57"
    return f'<span class="pill" style="background:{c};color:#07090C">{d}d</span>'


head = ["Position", "Plan", "Strike", "Expiry", "DTE", "Entry", "Mark", "Value", "P&L $", "P&L %", "Delta", "Theta/day",
        "Vega", "IV", "IV rank", "To target", "To stop", "Status"]
body = []
for p in P:
    opt = p["asset_type"] == "option"
    name = (f"{p['ticker']} {p['option_type'].upper()} x{p['contracts']:g}" if opt else
            "CASH" if p["asset_type"] == "cash" else f"{p['ticker']} SHARES x{p['contracts']:g}")
    iv = D["iv_env"].get(p["position_id"], {})
    rank = (f"{iv['iv_rank']:.0f}" if iv.get("iv_rank") is not None else
            ("building" if iv.get("label", "").startswith("building") else "–"))
    body.append([e(name), plan_pill(p["action"]), num(p["strike"], 2) if opt else "–", e(p["expiry"] or "–"), dte_pill(p["dte"]) if opt else "–",
                 num(p["entry_price"]), num(p["mark"]), money(p["value"]),
                 f'<span class="{cls(p["pnl"])}">{money(p["pnl"])}</span>',
                 f'<span class="{cls(p["pnl_pct"])}">{num(p["pnl_pct"], 1)}%</span>',
                 num(p["delta"]), f'<span class="{cls(p["pos_theta"])}">{money(p["pos_theta"])}</span>' if opt else "–",
                 money(p["pos_vega"]) if opt else "–", f"{p['iv'] * 100:.0f}%" if p.get("iv") else "–", rank,
                 bar(p["progress_target"], GREEN), bar(p["progress_stop"], RED),
                 e(p["status"]) if p["status"] != "ok" else '<span class="up">ok</span>'])
st.markdown('<div class="wrap"><table class="grid"><tr>' + "".join(f"<th>{h}</th>" for h in head) + "</tr>"
            + "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in body) + "</table></div>",
            unsafe_allow_html=True)

# ---------- theta decay + allocation ----------
left, right = st.columns([3, 2])
with left:
    st.markdown('<div class="sec">Theta decay · options value if spot & IV stay unchanged (illustrative, not predictive)</div>',
                unsafe_allow_html=True)
    if D["theta_stacked"]:
        df = pd.DataFrame(D["theta_stacked"])
        df["date"] = pd.to_datetime(df["date"])
        c = alt.Chart(df).mark_area(opacity=.85).encode(
            x=alt.X("date:T", title=None), y=alt.Y("value:Q", stack="zero", title="$ value", axis=alt.Axis(format="$,.0f")),
            color=alt.Color("position:N", title=None, scale=alt.Scale(scheme="set2")),
            tooltip=["position", alt.Tooltip("date:T"), alt.Tooltip("value:Q", format="$,.2f")]).properties(height=260)
        st.altair_chart(chart_theme(c), width="stretch")
        dx = pd.DataFrame(D["extrinsic"])
        dx["date"] = pd.to_datetime(dx["date"])
        c2 = alt.Chart(dx).mark_line(strokeWidth=2).encode(
            x=alt.X("date:T", title=None), y=alt.Y("extrinsic:Q", title="Extrinsic $ / share"),
            color=alt.Color("position:N", title=None, scale=alt.Scale(scheme="set2")),
            tooltip=["position", alt.Tooltip("date:T"), alt.Tooltip("extrinsic:Q", format="$.2f")]).properties(height=260)
        st.altair_chart(chart_theme(c2), width="stretch")
    else:
        st.markdown('<div class="muted">No priced options to project.</div>', unsafe_allow_html=True)
with right:
    st.markdown('<div class="sec">Allocation</div>', unsafe_allow_html=True)
    if D["allocation"]:
        palette = ["#4EA8FF", "#FFA62B", "#3DDC84", "#C792EA", "#FF7AA2", "#7FDBCA", "#FFE14D", "#8A93A3"]
        for kind, title in (("ticker", "BY TICKER"), ("sector", "BY SECTOR")):
            items = [x for x in D["allocation"] if x["kind"] == kind]
            segs = "".join(
                f'<div title="{e(x["name"])} {x["pct"]:.1f}%" style="width:{x["pct"]:.2f}%;background:{palette[i % len(palette)]};'
                f'height:22px;{"outline:2px solid " + RED + ";outline-offset:-2px;" if x["over_cap"] else ""}"></div>'
                for i, x in enumerate(items))
            legend = " ".join(
                f'<span style="color:{palette[i % len(palette)]}">■</span> {e(x["name"])} {x["pct"]:.0f}%'
                + (f' <span class="dn">over {x["cap_pct"]:.0f}% cap</span>' if x["over_cap"] else "")
                for i, x in enumerate(items))
            st.markdown(f'<div class="muted" style="margin-top:6px">{title}</div>'
                        f'<div style="display:flex;width:100%;background:#1A2028">{segs}</div>'
                        f'<div style="font-size:12px;margin:4px 0 8px;line-height:1.7">{legend}</div>',
                        unsafe_allow_html=True)
        over = [x for x in D["allocation"] if x["over_cap"]]
        for x in over:
            st.markdown(f'<div class="alert" style="border-color:{RED}"><span class="k" style="color:{RED}">concentration</span>'
                        f'{e(x["name"])} is {x["pct"]:.0f}% of the book (cap {x["cap_pct"]:.0f}%)</div>', unsafe_allow_html=True)
        if not over:
            st.markdown('<div class="muted">No concentration flags.</div>', unsafe_allow_html=True)
    # macro panel
    st.markdown('<div class="sec">Market environment · macro gate</div>', unsafe_allow_html=True)
    if M and M.get("score") is not None:
        st.markdown(f'<div class="strip"><div class="cell"><small>Score</small><b class="{macro_cls}">{M["score"]:.0f} / 100</b></div>'
                    f'<div class="cell"><small>Read</small><b class="{macro_cls}">{e(M["label"])}</b></div></div>',
                    unsafe_allow_html=True)
        comp = pd.DataFrame([{"component": k.replace("_", " "), "score": v["score"], "weight": v["weight"]}
                             for k, v in M["components"].items()])
        c = alt.Chart(comp).mark_bar(color=AMBER, size=12).encode(
            y=alt.Y("component:N", title=None, sort="-x", axis=alt.Axis(labelLimit=160)), x=alt.X("score:Q", scale=alt.Scale(domain=[0, 100]), title="0 = stressed · 100 = calm"),
            tooltip=["component", "score", "weight"]).properties(height=230)
        st.altair_chart(chart_theme(c), width="stretch")
        if M["missing"]:
            st.markdown(f'<div class="muted">Not available this run: {e(", ".join(M["missing"]))}</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="muted">Macro score not available for this date.</div>', unsafe_allow_html=True)

# ---------- strike ladders ----------
st.markdown('<div class="sec">Strike ladder · ±6 strikes around each held option</div>', unsafe_allow_html=True)
opts = [p for p in P if p["asset_type"] == "option"]
if opts:
    cols = st.columns(min(len(opts), 3))
    for i, p in enumerate(opts):
        with cols[i % len(cols)]:
            st.markdown(f'<div class="muted" style="color:{AMBER}">{e(p["ticker"])} {e(p["option_type"]).upper()} {e(p["expiry"])}</div>',
                        unsafe_allow_html=True)
            lad = D["ladders"].get(p["position_id"]) or []
            if not lad:
                st.markdown('<div class="muted">No chain data.</div>', unsafe_allow_html=True)
                continue
            t = ('<div class="wrap"><table class="grid"><tr><th>Strike</th><th>Bid</th><th>Ask</th><th>Last</th><th>IV</th>'
                 '<th>Vol</th><th>OI</th></tr>')
            for r in lad:
                badge = f'<span class="tag" style="color:{YELLOW}">NEW</span>' if r["new"] else ""
                t += (f'<tr class="{"held" if r["held"] else ""}"><td>{r["strike"]:g}{" ◄" if r["held"] else ""}{badge}</td>'
                      f'<td>{num(r["bid"])}</td><td>{num(r["ask"])}</td><td>{num(r["last"])}</td>'
                      f'<td>{(r["iv"] or 0) * 100:.0f}%</td><td>{num(r["volume"], 0)}</td><td>{num(r["open_interest"], 0)}</td></tr>')
            st.markdown(t + "</table></div>", unsafe_allow_html=True)
else:
    st.markdown('<div class="muted">No options held.</div>', unsafe_allow_html=True)

# ---------- opportunities ----------
st.markdown('<div class="sec">Opportunities · watchlist and S&amp;P 500 scan (candidates to research, not recommendations)</div>',
            unsafe_allow_html=True)


def pct(v, d=1):
    return "–" if v is None else f'<span class="{cls(v)}">{v * 100:+.{d}f}%</span>'


def dist(v):
    return "–" if v is None else f"{v:+.1f}%"


W = D.get("watchlist", [])
if W:
    t = ('<div class="muted" style="color:#FFA62B">WATCHLIST · BUY only when a stock reaches the buy level you set in '
         'watchlist.json</div><div class="wrap"><table class="grid"><tr><th>Ticker</th><th>Plan</th><th>Price</th>'
         '<th>Your buy level</th><th>Distance</th><th>1 day</th><th>12 months</th><th>vs 200-day</th><th>Status</th></tr>')
    for w in W:
        t += (f'<tr><td>{e(w["ticker"])}</td><td>{plan_pill(w["action"]) if w["action"] else "–"}</td>'
              f'<td>{num(w["price"])}</td><td>{num(w["buy_below"])}</td>'
              f'<td>{dist(w["to_buy_pct"])}</td>'
              f'<td>{pct(w["chg_1d"])}</td><td>{pct(w["ret_12m"], 0)}</td><td>{pct(w["vs_200d"], 0)}</td>'
              f'<td style="text-align:left">{e(w["status"])}</td></tr>')
    st.markdown(t + "</table></div>", unsafe_allow_html=True)
else:
    st.markdown('<div class="muted">No watchlist yet. Add stocks and buy levels to monitor/watchlist.json.</div>',
                unsafe_allow_html=True)

S = D.get("scan", {})
if S:
    cols = st.columns(2)
    for i, (key, title) in enumerate(scanner.SCREENS.items()):
        items = S.get(key, [])
        with cols[i % 2]:
            t = (f'<div class="muted" style="color:#FFA62B;margin-top:10px">{e(title).upper()}</div>'
                 '<div class="wrap"><table class="grid"><tr><th>#</th><th>Ticker</th><th>Price</th><th>1 day</th>'
                 '<th>12 mo</th><th>Why it showed up</th></tr>')
            for x in items[:10]:
                n = D.get("candidate_news", {}).get(x["ticker"])
                chip = (f' <span class="pill" style="background:{SENT.get(n["sentiment"], GREY)};color:#07090C">'
                        f'{e(n["sentiment"])}</span>' if n and n.get("sentiment") else "")
                t += (f'<tr><td>{x["rank"]}</td><td>{e(x["ticker"])}{chip}</td><td>{num(x["price"])}</td>'
                      f'<td>{pct(x["chg_1d"])}</td><td>{pct(x["ret_12m"], 0)}</td>'
                      f'<td style="text-align:left;white-space:normal">{e(x["reason"])}</td></tr>')
            if not items:
                t += '<tr><td colspan="6" class="muted" style="text-align:left">Nothing today.</td></tr>'
            st.markdown(t + "</table></div>", unsafe_allow_html=True)
    cn = [n for n in D.get("candidate_news", {}).values() if n.get("status") == "ok" and n.get("summary")]
    if cn:
        st.markdown('<div class="muted" style="color:#FFA62B;margin-top:12px">TOP CANDIDATES · CLAUDE NEWS SUMMARY</div>',
                    unsafe_allow_html=True)
        cols = st.columns(2)
        for i, n in enumerate(cn):
            with cols[i % 2]:
                heads = "".join(f'<div>· <a href="{e(h.get("link") or "#")}" target="_blank">{e(h["title"])}</a></div>'
                                for h in n["headlines"][:3])
                st.markdown(f'<div class="news"><b style="color:{AMBER}">{e(n["ticker"])}</b>'
                            f'<span class="pill" style="background:{SENT.get(n["sentiment"], GREY)};color:#07090C;margin-left:8px">'
                            f'{e(n["sentiment"])}</span><div style="margin:6px 0">{e(n["summary"])}</div>{heads}</div>',
                            unsafe_allow_html=True)
else:
    st.markdown('<div class="muted">The market scan appears after the next monitor run.</div>', unsafe_allow_html=True)

# ---------- news ----------
st.markdown('<div class="sec">News · Claude summaries (facts only, never buy/sell)</div>', unsafe_allow_html=True)
SENT = {"positive": GREEN, "neutral": GREY, "negative": RED}
if not D.get("held_news", D.get("news", [])):
    st.markdown('<div class="muted">No news analysis for this date (needs the ANTHROPIC_API_KEY secret).</div>',
                unsafe_allow_html=True)
cols = st.columns(2)
for i, n in enumerate(D.get("held_news", D.get("news", []))):
    c = SENT.get(n["sentiment"], GREY)
    flags = "".join(f'<div class="flag">⚑ {e(f.get("position_id"))}: {e(f["flag"])}</div>' for f in n["position_flags"])
    heads = "".join(f'<div>· <a href="{e(h.get("link") or "#")}" target="_blank">{e(h["title"])}</a> '
                    f'<span class="muted">{e(h.get("publisher") or "")} {e(h.get("published") or "")}</span></div>'
                    for h in n["headlines"][:6])
    with cols[i % 2]:
        st.markdown(f'<div class="news"><b style="color:{AMBER}">{e(n["ticker"])}</b>'
                    f'<span class="pill" style="background:{c};color:#07090C;margin-left:8px">{e(n["sentiment"] or "–")}</span>'
                    f'<div style="margin:6px 0">{e(n["summary"] or "")}</div>'
                    + (f'<div class="muted">Drivers: {e("; ".join(n["drivers"]))}</div>' if n["drivers"] else "")
                    + flags + f'<div style="margin-top:6px">{heads}</div></div>', unsafe_allow_html=True)

st.markdown('<div class="muted" style="margin-top:20px">Monitor only. It reports conditions, tracks your own targets, '
            'and Claude summarizes the news. Nothing here recommends trades or routes orders.</div>', unsafe_allow_html=True)
