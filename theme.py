"""
Shared design system for the Streamlit apps (GiftxAI / DeepS&P / QuantMaven).

One visual language, one accent hue per product. Import it, call `apply()` once
right after `st.set_page_config`, then build the page out of the helpers below
instead of hand-rolling HTML.

    from theme import apply, hero, stat_row, panel, section, badge, style_fig

    apply("quantmaven")
    hero("Quant<em>Maven</em>", "Markets, translated.")

Design notes
------------
Near-black canvas, hairline borders, no drop shadows, no gradient blobs. Type
carries the hierarchy: a tight editorial serif-free display face for headings,
tabular monospace for every number so columns line up and digits stop dancing
on rerun. One accent per app, used sparingly — it marks the live value, the
selected tab, the primary action, and nothing else.
"""

from __future__ import annotations

import streamlit as st

# --------------------------------------------------------------------------
# Palettes
# --------------------------------------------------------------------------

# Each app gets one hue. `accent` is the interactive/《live》colour, `accent_dim`
# backs low-emphasis fills, `accent_ink` is legible text on a solid accent fill.
PALETTES: dict[str, dict[str, str]] = {
    "giftxai": {
        "accent": "#E0563F",
        "accent_soft": "rgba(224, 86, 63, 0.14)",
        "accent_line": "rgba(224, 86, 63, 0.38)",
        "accent_ink": "#12100F",
        "accent_2": "#D9A441",
    },
    "deepsp": {
        "accent": "#4C8DFF",
        "accent_soft": "rgba(76, 141, 255, 0.14)",
        "accent_line": "rgba(76, 141, 255, 0.38)",
        "accent_ink": "#0A0F1A",
        "accent_2": "#9B7BFF",
    },
    "quantmaven": {
        "accent": "#19C27E",
        "accent_soft": "rgba(25, 194, 126, 0.13)",
        "accent_line": "rgba(25, 194, 126, 0.36)",
        "accent_ink": "#04140D",
        "accent_2": "#5AD6E0",
    },
}

BASE = {
    "bg": "#08090B",
    "surface": "#0E1014",
    "surface_2": "#14171D",
    "line": "rgba(255,255,255,0.07)",
    "line_strong": "rgba(255,255,255,0.14)",
    "text": "#E9EBEF",
    "muted": "#8A919E",
    "faint": "#565D69",
    "pos": "#2FD48F",
    "neg": "#FF6B6B",
    "warn": "#E3B341",
}

_FONTS = (
    "@import url('https://fonts.googleapis.com/css2?"
    "family=Inter:wght@400;500;600;700;800&"
    "family=JetBrains+Mono:wght@400;500;600&display=swap');"
)

_active: dict[str, str] = {}


def palette(app: str | None = None) -> dict[str, str]:
    """Merged base + accent tokens for `app` (defaults to the applied one)."""
    tokens = dict(BASE)
    tokens.update(PALETTES.get(app or _active.get("app", ""), PALETTES["quantmaven"]))
    return tokens


# --------------------------------------------------------------------------
# Stylesheet
# --------------------------------------------------------------------------

def _css(p: dict[str, str]) -> str:
    return f"""
<style>
{_FONTS}

:root {{
  --bg: {p['bg']};
  --surface: {p['surface']};
  --surface-2: {p['surface_2']};
  --line: {p['line']};
  --line-strong: {p['line_strong']};
  --text: {p['text']};
  --muted: {p['muted']};
  --faint: {p['faint']};
  --accent: {p['accent']};
  --accent-soft: {p['accent_soft']};
  --accent-line: {p['accent_line']};
  --accent-ink: {p['accent_ink']};
  --accent-2: {p['accent_2']};
  --pos: {p['pos']};
  --neg: {p['neg']};
  --warn: {p['warn']};
  --sans: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  --mono: 'JetBrains Mono', 'SF Mono', Menlo, Consolas, monospace;
  --r: 10px;
}}

/* ---------- canvas ---------------------------------------------------- */

html, body, [data-testid="stAppViewContainer"] {{
  background: var(--bg);
  color: var(--text);
  font-family: var(--sans);
  -webkit-font-smoothing: antialiased;
}}

[data-testid="stHeader"] {{ background: transparent; }}
#MainMenu, footer, [data-testid="stDecoration"] {{ visibility: hidden; }}

.block-container {{
  padding-top: 2.4rem;
  padding-bottom: 4rem;
  max-width: 1500px;
}}

/* Numbers are monospaced and tabular everywhere so columns align and digits
   keep a fixed width between reruns. */
.mono, [data-testid="stMetricValue"], .tk-stat-value, .tk-kv-value {{
  font-family: var(--mono);
  font-variant-numeric: tabular-nums;
  font-feature-settings: 'tnum' 1;
}}

/* ---------- typography ------------------------------------------------ */

h1, h2, h3, h4 {{
  font-family: var(--sans);
  color: var(--text);
  letter-spacing: -0.02em;
  font-weight: 700;
}}
h1 {{ font-size: 2.1rem; }}
h2 {{ font-size: 1.45rem; }}
h3 {{ font-size: 1.12rem; }}

p, li, label, .stMarkdown {{ color: var(--text); }}
a {{ color: var(--accent); text-decoration: none; }}
a:hover {{ text-decoration: underline; }}
hr {{ border: 0; border-top: 1px solid var(--line); margin: 1.6rem 0; }}

.tk-eyebrow {{
  font-size: 0.68rem;
  font-weight: 600;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: var(--faint);
}}

/* ---------- hero ------------------------------------------------------ */

.tk-hero {{
  border-bottom: 1px solid var(--line);
  padding: 0.2rem 0 1.5rem;
  margin-bottom: 1.8rem;
}}
.tk-hero-top {{ display: flex; align-items: center; gap: 0.9rem; }}
.tk-hero-mark {{
  width: 38px; height: 38px; border-radius: 9px;
  object-fit: cover; border: 1px solid var(--line-strong);
}}
.tk-hero h1 {{
  font-size: clamp(2rem, 4.4vw, 3rem);
  font-weight: 800;
  margin: 0.55rem 0 0;
  line-height: 1.03;
  letter-spacing: -0.035em;
}}
.tk-hero h1 em {{ font-style: normal; color: var(--accent); }}
.tk-hero-sub {{
  color: var(--muted);
  font-size: 1.02rem;
  margin-top: 0.6rem;
  max-width: 62ch;
  line-height: 1.55;
}}
.tk-hero-meta {{
  display: flex; flex-wrap: wrap; gap: 0.45rem;
  margin-top: 1.1rem;
}}

/* ---------- badges ---------------------------------------------------- */

.tk-badge {{
  display: inline-flex; align-items: center; gap: 0.4rem;
  padding: 0.24rem 0.62rem;
  border: 1px solid var(--line);
  border-radius: 999px;
  font-size: 0.72rem;
  font-weight: 500;
  letter-spacing: 0.01em;
  color: var(--muted);
  background: var(--surface);
  white-space: nowrap;
}}
.tk-badge b {{ font-weight: 600; color: var(--text); }}
.tk-badge.is-accent {{
  color: var(--accent); border-color: var(--accent-line); background: var(--accent-soft);
}}
.tk-badge.is-pos {{ color: var(--pos); border-color: rgba(47,212,143,.35); background: rgba(47,212,143,.10); }}
.tk-badge.is-neg {{ color: var(--neg); border-color: rgba(255,107,107,.35); background: rgba(255,107,107,.10); }}
.tk-badge.is-warn {{ color: var(--warn); border-color: rgba(227,179,65,.35); background: rgba(227,179,65,.10); }}
.tk-dot {{ width: 6px; height: 6px; border-radius: 50%; background: currentColor; }}

/* ---------- stat cards ------------------------------------------------ */

.tk-stats {{
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(165px, 1fr));
  gap: 1px;
  background: var(--line);
  border: 1px solid var(--line);
  border-radius: var(--r);
  overflow: hidden;
  margin: 0.4rem 0 1.4rem;
}}
.tk-stat {{
  background: var(--surface);
  padding: 1rem 1.15rem 1.05rem;
  min-width: 0;
}}
.tk-stat-label {{
  font-size: 0.68rem;
  font-weight: 600;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--faint);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}}
.tk-stat-value {{
  font-size: 1.52rem;
  font-weight: 600;
  letter-spacing: -0.02em;
  margin-top: 0.42rem;
  line-height: 1.1;
  overflow-wrap: anywhere;
}}
.tk-stat-delta {{ font-size: 0.78rem; color: var(--muted); margin-top: 0.34rem; }}
.tk-stat.is-accent .tk-stat-value {{ color: var(--accent); }}
.tk-stat.is-pos   .tk-stat-value {{ color: var(--pos); }}
.tk-stat.is-neg   .tk-stat-value {{ color: var(--neg); }}
.tk-stat.is-pos .tk-stat-delta {{ color: var(--pos); }}
.tk-stat.is-neg .tk-stat-delta {{ color: var(--neg); }}

/* ---------- panels ---------------------------------------------------- */

.tk-panel {{
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: var(--r);
  padding: 1.25rem 1.35rem;
  margin-bottom: 1rem;
}}
.tk-panel h4 {{
  margin: 0 0 0.8rem;
  font-size: 0.72rem;
  font-weight: 600;
  letter-spacing: 0.13em;
  text-transform: uppercase;
  color: var(--accent);
}}
.tk-panel p {{ color: var(--muted); font-size: 0.9rem; line-height: 1.62; margin: 0 0 0.6rem; }}
.tk-panel p:last-child {{ margin-bottom: 0; }}
.tk-panel ul {{ margin: 0; padding-left: 1.05rem; }}
.tk-panel li {{ color: var(--muted); font-size: 0.9rem; line-height: 1.75; }}
.tk-panel li strong {{ color: var(--text); font-weight: 600; }}

/* key/value rows inside a panel */
.tk-kv {{ display: flex; justify-content: space-between; gap: 1rem; padding: 0.42rem 0; border-bottom: 1px solid var(--line); }}
.tk-kv:last-child {{ border-bottom: 0; }}
.tk-kv-key {{ color: var(--faint); font-size: 0.82rem; }}
.tk-kv-value {{ color: var(--text); font-size: 0.85rem; font-weight: 500; text-align: right; }}

/* ---------- section heads --------------------------------------------- */

.tk-section {{ margin: 2.2rem 0 1rem; }}
.tk-section-head {{ display: flex; align-items: baseline; gap: 0.75rem; }}
.tk-section h3 {{ margin: 0; font-size: 1.08rem; letter-spacing: -0.015em; }}
.tk-section .tk-rule {{ flex: 1; height: 1px; background: var(--line); }}
.tk-section-sub {{ color: var(--faint); font-size: 0.85rem; margin-top: 0.4rem; line-height: 1.5; }}

/* ---------- streamlit widget overrides -------------------------------- */

[data-testid="stSidebar"] {{
  background: var(--surface);
  border-right: 1px solid var(--line);
}}
[data-testid="stSidebar"] .block-container {{ padding-top: 1.6rem; }}

.stTabs [data-baseweb="tab-list"] {{
  gap: 0.3rem;
  background: transparent;
  border-bottom: 1px solid var(--line);
  padding: 0;
}}
.stTabs [data-baseweb="tab"] {{
  height: 42px;
  padding: 0 0.95rem;
  background: transparent;
  color: var(--faint);
  font-size: 0.88rem;
  font-weight: 500;
  border-radius: 0;
  border-bottom: 2px solid transparent;
}}
.stTabs [data-baseweb="tab"]:hover {{ color: var(--text); }}
.stTabs [aria-selected="true"] {{
  color: var(--text) !important;
  border-bottom-color: var(--accent);
  background: transparent !important;
}}
.stTabs [data-baseweb="tab-highlight"], .stTabs [data-baseweb="tab-border"] {{ display: none; }}

.stButton > button {{
  background: var(--surface-2);
  color: var(--text);
  border: 1px solid var(--line-strong);
  border-radius: 8px;
  padding: 0.5rem 1rem;
  font-size: 0.87rem;
  font-weight: 500;
  transition: border-color .15s ease, background .15s ease;
}}
.stButton > button:hover {{ border-color: var(--accent-line); background: var(--surface); color: var(--text); }}
.stButton > button:focus:not(:active) {{ color: var(--text); border-color: var(--accent); }}
.stButton > button[kind="primary"] {{
  background: var(--accent);
  color: var(--accent-ink);
  border-color: var(--accent);
  font-weight: 600;
}}
.stButton > button[kind="primary"]:hover {{ filter: brightness(1.08); color: var(--accent-ink); }}

[data-testid="stMetric"] {{
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: var(--r);
  padding: 0.85rem 1rem;
}}
[data-testid="stMetricLabel"] {{ color: var(--faint); }}
[data-testid="stMetricLabel"] p {{
  font-size: 0.68rem !important;
  font-weight: 600;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--faint);
}}
[data-testid="stMetricValue"] {{ font-size: 1.28rem; font-weight: 600; color: var(--text); }}

/* inputs */
.stTextInput input, .stDateInput input, .stNumberInput input,
[data-baseweb="select"] > div {{
  background: var(--surface-2) !important;
  border-color: var(--line-strong) !important;
  color: var(--text) !important;
  border-radius: 8px !important;
}}
.stTextInput input:focus, .stDateInput input:focus {{ border-color: var(--accent) !important; }}
.stTextInput label, .stDateInput label, .stSelectbox label,
.stSlider label, .stFileUploader label, .stNumberInput label {{
  font-size: 0.68rem !important;
  font-weight: 600 !important;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--faint) !important;
}}
[data-testid="stFileUploaderDropzone"] {{
  background: var(--surface-2);
  border: 1px dashed var(--line-strong);
  border-radius: var(--r);
}}
[data-testid="stSliderTickBar"] {{ background: var(--line); }}
.stSlider [data-baseweb="slider"] [role="slider"] {{ background: var(--accent); }}

/* expanders, alerts, tables */
[data-testid="stExpander"] {{
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: var(--r);
}}
[data-testid="stExpander"] summary {{ font-size: 0.86rem; color: var(--muted); }}
[data-testid="stNotification"], .stAlert {{
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: var(--r);
  color: var(--text);
}}
[data-testid="stDataFrame"] {{ border: 1px solid var(--line); border-radius: var(--r); }}
[data-testid="stChatInput"] textarea {{ background: var(--surface-2); }}
[data-testid="stChatMessage"] {{
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: var(--r);
  padding: 1rem 1.15rem;
}}
[data-testid="stProgress"] > div > div > div {{ background: var(--accent); }}

/* ---------- misc ------------------------------------------------------ */

.tk-footer {{
  margin-top: 3.5rem;
  padding-top: 1.3rem;
  border-top: 1px solid var(--line);
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 0.7rem;
  color: var(--faint);
  font-size: 0.79rem;
}}
.tk-footer b {{ color: var(--muted); font-weight: 600; }}

.tk-empty {{
  border: 1px dashed var(--line-strong);
  border-radius: var(--r);
  padding: 3rem 2rem;
  text-align: center;
  background: var(--surface);
}}
.tk-empty h3 {{ margin: 0 0 0.5rem; font-size: 1.05rem; }}
.tk-empty p {{ color: var(--faint); font-size: 0.89rem; margin: 0 auto; max-width: 46ch; line-height: 1.6; }}

@media (max-width: 640px) {{
  .block-container {{ padding-left: 1rem; padding-right: 1rem; }}
  .tk-stats {{ grid-template-columns: repeat(auto-fit, minmax(132px, 1fr)); }}
  .tk-stat-value {{ font-size: 1.24rem; }}
}}
</style>
"""


def apply(app: str) -> dict[str, str]:
    """Inject the stylesheet for `app` and return its palette."""
    p = palette(app)
    _active["app"] = app
    st.markdown(_css(p), unsafe_allow_html=True)
    return p


# --------------------------------------------------------------------------
# Components
# --------------------------------------------------------------------------

def esc(text: str) -> str:
    """Escape text bound for one of the raw-HTML helpers."""
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


_esc = esc  # internal alias


def badge(label: str, tone: str = "", dot: bool = False) -> str:
    """Return badge markup. `tone` ∈ '', 'accent', 'pos', 'neg', 'warn'."""
    cls = f"tk-badge is-{tone}" if tone else "tk-badge"
    inner = ('<span class="tk-dot"></span>' if dot else "") + _esc(label)
    return f'<span class="{cls}">{inner}</span>'


def hero(
    title: str,
    subtitle: str = "",
    eyebrow: str = "",
    meta: list[str] | None = None,
    mark: str | None = None,
) -> None:
    """Page header. `title` may contain <em> to accent a word; `meta` takes
    pre-built badge markup (see `badge`)."""
    top = ""
    if mark or eyebrow:
        bits = []
        if mark:
            bits.append(f'<img class="tk-hero-mark" src="{mark}" alt="">')
        if eyebrow:
            bits.append(f'<span class="tk-eyebrow">{_esc(eyebrow)}</span>')
        top = f'<div class="tk-hero-top">{"".join(bits)}</div>'

    sub = f'<div class="tk-hero-sub">{_esc(subtitle)}</div>' if subtitle else ""
    meta_html = f'<div class="tk-hero-meta">{"".join(meta)}</div>' if meta else ""

    st.markdown(
        f'<div class="tk-hero">{top}<h1>{title}</h1>{sub}{meta_html}</div>',
        unsafe_allow_html=True,
    )


def stat_row(items: list[dict]) -> None:
    """Grid of stat cards. Each item: {label, value, delta?, tone?}."""
    cards = []
    for it in items:
        tone = it.get("tone", "")
        cls = f"tk-stat is-{tone}" if tone else "tk-stat"
        delta = (
            f'<div class="tk-stat-delta">{_esc(it["delta"])}</div>'
            if it.get("delta")
            else ""
        )
        cards.append(
            f'<div class="{cls}">'
            f'<div class="tk-stat-label">{_esc(it["label"])}</div>'
            f'<div class="tk-stat-value">{_esc(it["value"])}</div>'
            f"{delta}</div>"
        )
    st.markdown(f'<div class="tk-stats">{"".join(cards)}</div>', unsafe_allow_html=True)


def section(title: str, sub: str = "") -> None:
    """Section heading with a hairline rule and optional standfirst."""
    sub_html = f'<div class="tk-section-sub">{_esc(sub)}</div>' if sub else ""
    st.markdown(
        f'<div class="tk-section"><div class="tk-section-head">'
        f"<h3>{_esc(title)}</h3><div class=\"tk-rule\"></div></div>{sub_html}</div>",
        unsafe_allow_html=True,
    )


def panel(title: str, body_html: str) -> None:
    """Bordered card with an uppercase accent title. `body_html` is raw HTML."""
    st.markdown(
        f'<div class="tk-panel"><h4>{_esc(title)}</h4>{body_html}</div>',
        unsafe_allow_html=True,
    )


def kv_panel(title: str, rows: list[tuple[str, str]]) -> None:
    """Panel of key/value rows — values are monospaced and right-aligned."""
    body = "".join(
        f'<div class="tk-kv"><span class="tk-kv-key">{_esc(k)}</span>'
        f'<span class="tk-kv-value">{_esc(v)}</span></div>'
        for k, v in rows
    )
    panel(title, body)


def bullets(items: list[str]) -> str:
    """<ul> body for `panel`. Wrap a leading label in **bold** to emphasise it."""
    out = []
    for raw in items:
        text = _esc(raw)
        if text.count("**") >= 2:
            head, rest = text.split("**", 2)[1], text.split("**", 2)[2]
            out.append(f"<li><strong>{head}</strong>{rest}</li>")
        else:
            out.append(f"<li>{text}</li>")
    return f'<ul>{"".join(out)}</ul>'


def empty_state(title: str, body: str) -> None:
    st.markdown(
        f'<div class="tk-empty"><h3>{_esc(title)}</h3><p>{_esc(body)}</p></div>',
        unsafe_allow_html=True,
    )


def footer(name_html: str, note: str = "") -> None:
    right = f"<span>{_esc(note)}</span>" if note else ""
    st.markdown(
        f'<div class="tk-footer"><span>{name_html}</span>{right}</div>',
        unsafe_allow_html=True,
    )


# --------------------------------------------------------------------------
# Plotly
# --------------------------------------------------------------------------

def style_fig(fig, height: int | None = None, legend: bool = True):
    """Apply the shared chart look: transparent canvas, hairline grid, mono
    tick labels, legend floated above the plot so it never covers data."""
    p = palette()
    sans = "Inter, -apple-system, Segoe UI, sans-serif"

    # Passing a title dict to a figure that has no title text makes Plotly.js
    # render the literal string "undefined" in the corner — only touch the
    # title when there is one.
    has_title = bool(fig.layout.title.text)
    if has_title:
        fig.update_layout(
            title=dict(
                font=dict(color=p["text"], size=15, family=sans), x=0, xanchor="left"
            )
        )

    fig.update_layout(
        height=height,
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family=sans, color=p["muted"], size=12),
        margin=dict(l=8, r=8, t=48 if has_title else 24, b=8),
        hovermode="x unified",
        hoverlabel=dict(
            bgcolor=p["surface_2"],
            bordercolor=p["line_strong"],
            font=dict(family="JetBrains Mono, monospace", size=11, color=p["text"]),
        ),
        showlegend=legend,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.01,
            xanchor="left",
            x=0,
            bgcolor="rgba(0,0,0,0)",
            font=dict(size=11),
        ),
    )
    fig.update_xaxes(
        showgrid=False,
        zeroline=False,
        linecolor=p["line"],
        tickfont=dict(family="JetBrains Mono, monospace", size=10.5),
    )
    fig.update_yaxes(
        showgrid=True,
        gridcolor=p["line"],
        zeroline=False,
        linecolor="rgba(0,0,0,0)",
        tickfont=dict(family="JetBrains Mono, monospace", size=10.5),
    )
    return fig


def series_colors() -> list[str]:
    """Categorical sequence for multi-series charts — accent first, then hues
    chosen to stay distinguishable on a near-black canvas."""
    p = palette()
    return [p["accent"], p["accent_2"], "#E3B341", "#FF8FA3", "#7BE0AD", "#9AA4B2"]
