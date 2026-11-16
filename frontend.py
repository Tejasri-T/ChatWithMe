"""Streamlit UI — Hummingbird theme: deep crimson, vivid pink, lush green."""

from __future__ import annotations

import json
import os
import uuid

import httpx
import streamlit as st

BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000/api/v1")

# ─── Colour Palette (extracted from the hummingbird image) ────────────────────
#  BACKGROUND  : Deep Noir       #0d0509   — near-black with warm undertone
#  SURFACE     : Dark Mahogany   #180a0e   — rich dark surface
#  RAISED      : Plum Shadow     #22101a   — raised cards
#  BORDER      : Crimson Mist    #3a1525   — subtle borders
#  ACCENT_1    : Crimson Bloom   #c41e4a   — primary accent (flower crimson)
#  ACCENT_2    : Wild Rose       #e8305a   — hover / active accent
#  ACCENT_3    : Petal Pink      #f06080   — highlights
#  GREEN_1     : Hummingbird     #2d7a3a   — bird body deep green
#  GREEN_2     : Iridescent Teal #3aa855   — bird highlight green
#  GREEN_3     : Bright Wing     #58c870   — bright green for accents
#  TEXT_HI     : Petal White     #fce8f0   — primary text
#  TEXT_MID    : Dusty Rose      #d4a0b0   — secondary text
#  TEXT_LO     : Faded Plum      #8a5068   — muted text
# ─────────────────────────────────────────────────────────────────────────────

CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

/* ══════════════════════════════════════════════════════════════
   DESIGN TOKENS
   ══════════════════════════════════════════════════════════════ */
:root {
  /* Backgrounds */
  --bg-base:    #0d0509;
  --bg-surface: #180a0e;
  --bg-raised:  #22101a;
  --bg-hover:   #2e1521;

  /* Borders */
  --border-lo:  #3a1525;
  --border-mid: #5a2035;
  --border-hi:  #8a3050;

  /* Crimson accent (flower) */
  --crimson:    #c41e4a;
  --rose:       #e8305a;
  --petal:      #f06080;
  --blush:      #f8b0c0;

  /* Green accent (hummingbird) */
  --hbird-dk:   #2d7a3a;
  --hbird:      #3aa855;
  --hbird-lt:   #58c870;

  /* Text */
  --text-hi:    #fce8f0;
  --text-mid:   #d4a0b0;
  --text-lo:    #8a5068;

  /* Alpha helpers */
  --crimson-10: rgba(196,30,74,.10);
  --crimson-20: rgba(196,30,74,.20);
  --crimson-30: rgba(196,30,74,.30);
  --hbird-15:   rgba(58,168,85,.15);
  --hbird-25:   rgba(58,168,85,.25);

  --radius-sm: 6px;
  --radius-md: 12px;
  --radius-lg: 18px;
  --radius-xl: 28px;
  --ease: .22s cubic-bezier(.4,0,.2,1);
}

/* ══════════════════════════════════════════════════════════════
   GLOBAL RESET & BASE
   ══════════════════════════════════════════════════════════════ */
*, *::before, *::after { box-sizing: border-box; }

html, body,
[data-testid="stAppViewContainer"],
[data-testid="stMain"], .main {
  font-family: 'Inter', system-ui, sans-serif !important;
  background: var(--bg-base) !important;
  color: var(--text-mid) !important;
  overflow-x: hidden !important;
}

/* Atmospheric crimson glow — top-right like the flowers */
[data-testid="stAppViewContainer"]::before {
  content: '';
  position: fixed;
  top: -120px; right: -80px;
  width: 500px; height: 500px;
  border-radius: 50%;
  background: radial-gradient(circle,
    rgba(196,30,74,.12) 0%,
    rgba(232,48,90,.05) 45%,
    transparent 72%);
  pointer-events: none;
  z-index: 0;
}
/* Bottom-left green glow — like the hummingbird */
[data-testid="stAppViewContainer"]::after {
  content: '';
  position: fixed;
  bottom: -100px; left: 240px;
  width: 350px; height: 350px;
  border-radius: 50%;
  background: radial-gradient(circle,
    rgba(45,122,58,.10) 0%,
    transparent 65%);
  pointer-events: none;
  z-index: 0;
}

/* ══════════════════════════════════════════════════════════════
   SIDEBAR — FIXED, NO SHAKE
   ══════════════════════════════════════════════════════════════ */
[data-testid="stSidebar"] {
  background: linear-gradient(180deg,
    #100508 0%,
    var(--bg-surface) 35%,
    #120709 100%) !important;
  border-right: 1px solid var(--border-lo) !important;
  box-shadow: 4px 0 40px rgba(0,0,0,.8),
              inset -1px 0 0 rgba(196,30,74,.06) !important;
  /* Prevent sidebar from jumping/shaking during reruns */
  min-width: 260px !important;
  max-width: 320px !important;
  will-change: auto !important;
  transform: none !important;
  transition: none !important;
}
/* Freeze the sidebar inner scroll container */
[data-testid="stSidebar"] > div:first-child {
  padding-top: 0 !important;
  overflow-y: auto !important;
  overflow-x: hidden !important;
  height: 100% !important;
}
/* Prevent Streamlit's internal sidebar animations causing shake */
[data-testid="stSidebar"] section {
  transform: none !important;
  transition: none !important;
}

/* ── Brand Header */
.brand-header {
  background: linear-gradient(150deg,
    #1a0810 0%,
    var(--crimson) 55%,
    var(--rose) 85%,
    #ff7090 100%);
  margin: 0 0 1.4rem 0;
  padding: 1.6rem 1.4rem 1.4rem;
  position: relative;
  overflow: hidden;
  border-bottom: 1px solid var(--border-mid);
  flex-shrink: 0;
}
.brand-header::before {
  content: '';
  position: absolute;
  top: -50px; right: -50px;
  width: 150px; height: 150px;
  border-radius: 50%;
  background: rgba(255,255,255,.06);
}
.brand-header::after {
  content: '';
  position: absolute;
  bottom: -20px; left: 10px;
  width: 90px; height: 90px;
  border-radius: 50%;
  background: rgba(0,0,0,.20);
}
.brand-header h1 {
  font-size: 1.18rem !important;
  font-weight: 700 !important;
  color: #fff !important;
  margin: 0 !important;
  letter-spacing: -.3px;
  line-height: 1.3 !important;
  text-shadow: 0 2px 10px rgba(0,0,0,.5);
  position: relative; z-index: 1;
}
.brand-header p {
  font-size: .68rem !important;
  color: rgba(255,210,220,.65) !important;
  margin: 4px 0 0 !important;
  font-weight: 400;
  position: relative; z-index: 1;
}

/* ── Status pill */
.status-pill {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  padding: 5px 12px;
  border-radius: 20px;
  font-size: .71rem;
  font-weight: 600;
  letter-spacing: .3px;
  margin-bottom: 10px;
}
.status-pill.online {
  background: var(--hbird-15);
  border: 1px solid rgba(58,168,85,.30);
  color: var(--hbird-lt);
}
.status-pill.offline {
  background: var(--crimson-10);
  border: 1px solid rgba(196,30,74,.30);
  color: var(--petal);
}
.status-dot { width: 7px; height: 7px; border-radius: 50%; flex-shrink: 0; }
.status-pill.online  .status-dot {
  background: var(--hbird-lt);
  box-shadow: 0 0 7px var(--hbird-lt);
  animation: blink 2.2s infinite;
}
.status-pill.offline .status-dot { background: var(--crimson); }
@keyframes blink { 0%,100%{opacity:1} 50%{opacity:.3} }

/* offline error card */
.offline-card {
  background: var(--crimson-10);
  border: 1px solid rgba(196,30,74,.22);
  border-radius: var(--radius-md);
  padding: 9px 12px;
  font-size: .72rem;
  color: var(--blush);
  line-height: 1.65;
  margin-bottom: 8px;
}
.offline-card code {
  background: rgba(0,0,0,.35);
  color: #ffb0c0;
  padding: 1px 6px;
  border-radius: 4px;
  font-family: 'JetBrains Mono', monospace;
  font-size: .68rem;
}

/* ── Section labels */
.sec-label {
  font-size: .60rem !important;
  font-weight: 700 !important;
  letter-spacing: 1.4px !important;
  text-transform: uppercase !important;
  color: var(--crimson) !important;
  margin: 1.1rem 0 .5rem !important;
  padding-bottom: 5px;
  border-bottom: 1px solid var(--border-lo);
  display: block;
}

/* ── New Chat button */
[data-testid="stSidebar"] button[kind="primary"] {
  background: linear-gradient(135deg, var(--crimson) 0%, var(--rose) 60%, var(--petal) 100%) !important;
  color: #fff !important;
  border: 1px solid var(--border-mid) !important;
  border-radius: var(--radius-md) !important;
  font-weight: 600 !important;
  font-size: .85rem !important;
  box-shadow: 0 4px 18px rgba(196,30,74,.40),
              inset 0 1px 0 rgba(255,255,255,.12) !important;
  transition: all var(--ease) !important;
}
[data-testid="stSidebar"] button[kind="primary"]:hover {
  background: linear-gradient(135deg, var(--rose) 0%, var(--petal) 60%, #ff90aa 100%) !important;
  transform: translateY(-1px) !important;
  box-shadow: 0 7px 26px rgba(196,30,74,.50) !important;
}

/* ── Thread list buttons */
[data-testid="stSidebar"] .stButton > button {
  background: transparent !important;
  color: var(--text-lo) !important;
  border: 1px solid transparent !important;
  border-radius: var(--radius-sm) !important;
  font-size: .78rem !important;
  font-weight: 400 !important;
  text-align: left !important;
  padding: 5px 10px !important;
  transition: all var(--ease) !important;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
[data-testid="stSidebar"] .stButton > button:hover {
  background: var(--crimson-10) !important;
  border-color: var(--border-lo) !important;
  color: var(--text-mid) !important;
}

/* delete button */
[data-testid="stSidebar"] .stButton > button[title="Delete chat"] {
  color: var(--border-mid) !important;
  font-size: .75rem !important;
  padding: 4px 7px !important;
}
[data-testid="stSidebar"] .stButton > button[title="Delete chat"]:hover {
  color: var(--rose) !important;
  background: var(--crimson-10) !important;
  border-color: var(--border-mid) !important;
}

/* ── File uploader */
[data-testid="stFileUploader"] {
  border: 1.5px dashed var(--border-mid) !important;
  border-radius: var(--radius-md) !important;
  background: var(--crimson-10) !important;
  transition: border-color var(--ease), background var(--ease);
}
[data-testid="stFileUploader"]:hover {
  border-color: var(--crimson) !important;
  background: var(--crimson-20) !important;
}
[data-testid="stFileUploader"] label {
  color: var(--text-lo) !important;
  font-size: .78rem !important;
}

/* ── Doc badge */
.doc-badge {
  background: linear-gradient(135deg, var(--bg-raised) 0%, var(--bg-hover) 100%);
  border: 1px solid var(--border-lo);
  border-left: 3px solid var(--crimson);
  border-radius: var(--radius-md);
  padding: 10px 13px;
  font-size: .76rem;
  color: var(--petal);
  line-height: 1.65;
}
.doc-badge strong { color: var(--text-hi); display: block; margin-bottom: 2px; font-size: .78rem; }
.doc-badge .meta  { color: var(--text-lo); font-size: .68rem; }

/* ── Sidebar footer */
.sidebar-footer {
  text-align: center;
  font-size: .60rem;
  color: var(--text-lo);
  line-height: 2;
  padding: 12px 12px 8px;
  border-top: 1px solid var(--border-lo);
  margin-top: 1rem;
}
.sidebar-footer .dot { color: var(--crimson); }

/* ══════════════════════════════════════════════════════════════
   MAIN CHAT AREA — STRUCTURED LAYOUT
   ══════════════════════════════════════════════════════════════ */

/* Constrain the main column so it doesn't stretch unboundedly */
[data-testid="stMain"] .block-container {
  max-width: 860px !important;
  margin: 0 auto !important;
  padding: 1rem 2rem 2rem !important;
}

/* ── Chat header */
.chat-header {
  display: flex;
  align-items: center;
  gap: 13px;
  padding: 1rem 0 .9rem;
  border-bottom: 1px solid var(--border-lo);
  margin-bottom: 1rem;
  position: sticky;
  top: 0;
  background: var(--bg-base);
  z-index: 10;
}
.chat-header .icon-box {
  width: 42px; height: 42px;
  border-radius: var(--radius-md);
  background: linear-gradient(135deg, var(--bg-hover), var(--crimson));
  display: flex; align-items: center; justify-content: center;
  font-size: 1.15rem;
  box-shadow: 0 4px 16px rgba(196,30,74,.35),
              inset 0 1px 0 rgba(255,255,255,.08);
  flex-shrink: 0;
  border: 1px solid var(--border-mid);
}
.chat-header h2 {
  font-size: 1.05rem !important;
  font-weight: 600 !important;
  color: var(--text-hi) !important;
  margin: 0 !important;
  letter-spacing: -.2px;
}
.chat-header .tid {
  font-size: .60rem;
  color: var(--text-lo);
  font-family: 'JetBrains Mono', monospace;
  margin-top: 2px;
}

/* ── Empty state */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 4rem 2rem;
  text-align: center;
}
.orb-wrap { position: relative; display: inline-block; margin-bottom: 1.4rem; }
.orb {
  width: 90px; height: 90px;
  border-radius: 50%;
  background: linear-gradient(135deg,
    var(--bg-hover) 0%,
    var(--crimson) 45%,
    var(--rose) 75%,
    var(--petal) 100%);
  display: flex; align-items: center; justify-content: center;
  font-size: 2.2rem;
  box-shadow:
    0 8px 36px rgba(196,30,74,.40),
    0 0 0 1px var(--border-mid),
    0 0 60px rgba(196,30,74,.12);
  animation: float 3.8s ease-in-out infinite;
}
/* Green wing glow — hummingbird accent */
.orb-wrap::after {
  content: '';
  position: absolute;
  top: 2px; right: 2px;
  width: 15px; height: 15px;
  background: var(--hbird-lt);
  border-radius: 50%;
  border: 2px solid var(--bg-base);
  box-shadow: 0 0 10px rgba(88,200,112,.60);
  animation: wingpulse 2.2s ease-in-out infinite;
}
@keyframes float    { 0%,100%{transform:translateY(0)}   50%{transform:translateY(-10px)} }
@keyframes wingpulse{ 0%,100%{opacity:1;transform:scale(1)} 50%{opacity:.5;transform:scale(.8)} }

.empty-state h3 {
  font-size: 1.12rem; font-weight: 600;
  color: var(--text-hi); margin: 0 0 .5rem;
}
.empty-state p {
  font-size: .82rem; color: var(--text-lo);
  max-width: 340px; line-height: 1.65;
}
.chips {
  display: flex; gap: 8px; flex-wrap: wrap;
  justify-content: center; margin-top: 1.6rem;
}
.chip {
  display: inline-flex; align-items: center; gap: 5px;
  padding: 5px 14px;
  border-radius: 20px;
  font-size: .73rem; font-weight: 500;
  border: 1px solid var(--border-lo);
  background: var(--bg-raised);
  color: var(--petal);
  transition: all var(--ease);
  cursor: default;
}
.chip:hover {
  background: var(--crimson-20);
  border-color: var(--border-mid);
  color: var(--blush);
}

/* ══════════════════════════════════════════════════════════════
   CHAT BUBBLES — PROPERLY ALIGNED
   ══════════════════════════════════════════════════════════════ */

/* Base message container */
[data-testid="stChatMessage"] {
  border-radius: var(--radius-lg) !important;
  padding: .9rem 1.1rem !important;
  margin-bottom: .7rem !important;
  animation: slide-in .22s ease both;
  max-width: 80% !important;
  width: fit-content !important;
  min-width: 120px !important;
  clear: both !important;
}
@keyframes slide-in {
  from { opacity:0; transform:translateY(10px); }
  to   { opacity:1; transform:none; }
}

/* USER bubble — align RIGHT */
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {
  margin-left: auto !important;
  margin-right: 0 !important;
  background: linear-gradient(135deg,
    rgba(196,30,74,.30) 0%,
    rgba(165,20,55,.45) 100%) !important;
  border: 1px solid var(--border-mid) !important;
  border-right: 2px solid var(--crimson) !important;
  box-shadow:
    0 2px 16px rgba(0,0,0,.35),
    inset 0 1px 0 rgba(196,30,74,.10) !important;
}

/* ASSISTANT bubble — align LEFT */
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) {
  margin-left: 0 !important;
  margin-right: auto !important;
  background: linear-gradient(135deg,
    var(--bg-raised) 0%,
    rgba(30,12,22,.95) 100%) !important;
  border: 1px solid var(--border-lo) !important;
  border-left: 2px solid var(--hbird) !important;
  box-shadow: 0 2px 14px rgba(0,0,0,.30) !important;
}

/* Avatar circles */
[data-testid="chatAvatarIcon-user"] {
  background: linear-gradient(135deg, var(--crimson), var(--rose)) !important;
  border: none !important;
  box-shadow: 0 2px 10px rgba(196,30,74,.50) !important;
}
[data-testid="chatAvatarIcon-assistant"] {
  background: linear-gradient(135deg, var(--hbird-dk), var(--hbird)) !important;
  border: 1px solid rgba(58,168,85,.30) !important;
  box-shadow: 0 2px 10px rgba(45,122,58,.40) !important;
}

/* Text inside bubbles */
[data-testid="stChatMessage"] p,
[data-testid="stChatMessage"] li,
[data-testid="stChatMessage"] span {
  color: var(--text-mid) !important;
  line-height: 1.65 !important;
}
[data-testid="stChatMessage"] strong { color: var(--text-hi) !important; }

/* ══════════════════════════════════════════════════════════════
   CHAT INPUT BAR
   ══════════════════════════════════════════════════════════════ */
[data-testid="stChatInput"] {
  border-radius: var(--radius-xl) !important;
  border: 1.5px solid var(--border-mid) !important;
  background: var(--bg-raised) !important;
  box-shadow: 0 4px 32px rgba(0,0,0,.40),
              inset 0 1px 0 rgba(196,30,74,.06) !important;
  transition: border-color var(--ease), box-shadow var(--ease) !important;
}
[data-testid="stChatInput"]:focus-within {
  border-color: var(--crimson) !important;
  box-shadow:
    0 4px 32px rgba(0,0,0,.45),
    0 0 0 3px rgba(196,30,74,.18) !important;
}
[data-testid="stChatInput"] textarea {
  background: transparent !important;
  color: var(--text-mid) !important;
  font-family: 'Inter', sans-serif !important;
  font-size: .9rem !important;
  caret-color: var(--rose) !important;
}
[data-testid="stChatInput"] textarea::placeholder {
  color: var(--text-lo) !important;
}

/* Send button — hummingbird green for contrast */
[data-testid="stChatInput"] button {
  background: linear-gradient(135deg, var(--hbird-dk), var(--hbird)) !important;
  border-radius: 50% !important;
  border: none !important;
  color: #fff !important;
  box-shadow: 0 2px 12px rgba(45,122,58,.45) !important;
  transition: all var(--ease) !important;
}
[data-testid="stChatInput"] button:hover {
  background: linear-gradient(135deg, var(--hbird), var(--hbird-lt)) !important;
  transform: scale(1.1) !important;
  box-shadow: 0 4px 20px rgba(58,168,85,.55) !important;
}

/* ══════════════════════════════════════════════════════════════
   TOOL STATUS & ALERTS
   ══════════════════════════════════════════════════════════════ */
[data-testid="stStatusWidget"] {
  background: var(--bg-raised) !important;
  border: 1px solid var(--border-lo) !important;
  border-radius: var(--radius-md) !important;
  color: var(--petal) !important;
}

div.stSuccess {
  background: var(--hbird-15) !important;
  border-left: 3px solid var(--hbird) !important;
  border-radius: var(--radius-md) !important;
  color: var(--hbird-lt) !important;
}
div.stInfo {
  background: var(--bg-raised) !important;
  border-left: 3px solid var(--border-mid) !important;
  border-radius: var(--radius-md) !important;
  color: var(--text-mid) !important;
}
div.stError {
  background: var(--crimson-10) !important;
  border-left: 3px solid var(--crimson) !important;
  border-radius: var(--radius-md) !important;
  color: var(--petal) !important;
}

/* ══════════════════════════════════════════════════════════════
   MISC
   ══════════════════════════════════════════════════════════════ */
hr { border-color: var(--border-lo) !important; }

/* Thin scrollbar */
::-webkit-scrollbar { width: 4px; height: 4px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--border-mid); border-radius: 10px; }
::-webkit-scrollbar-thumb:hover { background: var(--crimson); }

/* Code inside chat */
[data-testid="stChatMessage"] code {
  background: var(--bg-surface) !important;
  border: 1px solid var(--border-lo) !important;
  border-radius: 4px !important;
  font-family: 'JetBrains Mono', monospace !important;
  font-size: .81rem !important;
  color: var(--petal) !important;
  padding: 1px 5px !important;
}
[data-testid="stChatMessage"] pre {
  background: var(--bg-surface) !important;
  border: 1px solid var(--border-lo) !important;
  border-radius: var(--radius-sm) !important;
  padding: 10px 14px !important;
}
[data-testid="stChatMessage"] pre code {
  border: none !important;
  padding: 0 !important;
}

/* Links */
[data-testid="stChatMessage"] a { color: var(--petal) !important; }
[data-testid="stChatMessage"] a:hover { color: var(--blush) !important; }

/* Headings inside chat */
[data-testid="stChatMessage"] h1,
[data-testid="stChatMessage"] h2,
[data-testid="stChatMessage"] h3 {
  color: var(--text-hi) !important;
}

/* Blockquote */
[data-testid="stChatMessage"] blockquote {
  border-left: 3px solid var(--border-mid) !important;
  color: var(--text-lo) !important;
  margin: 8px 0 !important;
  padding-left: 10px !important;
}

/* ── Suppress Streamlit's default slide/fade transitions on sidebar
   that cause the visible "shake" on rerun ── */
[data-testid="stSidebar"] * {
  animation-duration: 0s !important;
  transition-property: background, color, border-color, box-shadow, opacity !important;
  transition-duration: .15s !important;
}
/* Keep the orb and wing animations working in main area only */
.orb { animation: float 3.8s ease-in-out infinite !important; }
.orb-wrap::after { animation: wingpulse 2.2s ease-in-out infinite !important; }
.status-pill.online .status-dot { animation: blink 2.2s infinite !important; }
</style>
"""

st.set_page_config(
    page_title="Enterprise AI Chatbot",
    page_icon="🌺",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# ─── API Helpers ───────────────────────────────────────────────────────────────

def check_backend_health() -> bool:
    try:
        resp = httpx.get(f"{BACKEND_URL.replace('/api/v1', '')}/health", timeout=3.0)
        return resp.status_code == 200
    except Exception:
        return False


def fetch_all_threads() -> dict[str, str]:
    try:
        resp = httpx.get(f"{BACKEND_URL}/threads", timeout=5.0)
        if resp.status_code == 200:
            return {t["thread_id"]: t["chat_name"] for t in resp.json()}
    except Exception as exc:
        st.sidebar.error(f"Failed to fetch threads: {exc}")
    return {}


def load_conversation(thread_id: str) -> dict:
    try:
        resp = httpx.get(f"{BACKEND_URL}/threads/{thread_id}", timeout=5.0)
        if resp.status_code == 200:
            return resp.json()
    except Exception as exc:
        st.error(f"Failed to load conversation: {exc}")
    return {"messages": [], "document_metadata": None}


def upload_document_to_backend(thread_id: str, file_name: str, file_bytes: bytes) -> dict | None:
    try:
        files = {"file": (file_name, file_bytes, "application/pdf")}
        data  = {"thread_id": thread_id}
        resp  = httpx.post(
            f"{BACKEND_URL}/documents/upload", data=data, files=files, timeout=60.0
        )
        if resp.status_code == 200:
            return resp.json()
        st.sidebar.error(f"Upload failed: {resp.text}")
    except Exception as exc:
        st.sidebar.error(f"Upload error: {exc}")
    return None


def delete_thread_from_backend(thread_id: str) -> bool:
    try:
        resp = httpx.delete(f"{BACKEND_URL}/threads/{thread_id}", timeout=5.0)
        return resp.status_code == 200
    except Exception:
        return False


# ─── Session State ─────────────────────────────────────────────────────────────

if "thread_id"    not in st.session_state:
    st.session_state["thread_id"]    = str(uuid.uuid4())
if "message_hist" not in st.session_state:
    st.session_state["message_hist"] = []
if "chat_threads" not in st.session_state:
    st.session_state["chat_threads"] = fetch_all_threads()
if "doc_meta"     not in st.session_state:
    st.session_state["doc_meta"]     = None


def reset_chat() -> None:
    new_id = str(uuid.uuid4())
    st.session_state["thread_id"]    = new_id
    st.session_state["message_hist"] = []
    st.session_state["doc_meta"]     = None
    st.session_state["chat_threads"][new_id] = "New Chat"


current_thread_id = st.session_state["thread_id"]
if current_thread_id not in st.session_state["chat_threads"]:
    st.session_state["chat_threads"][current_thread_id] = "New Chat"


# ─── Sidebar ───────────────────────────────────────────────────────────────────

st.sidebar.markdown(
    """
    <div class="brand-header">
      <h1>🌺 Enterprise AI</h1>
      <p>LangGraph · RAG · Gemini Flash</p>
    </div>
    """,
    unsafe_allow_html=True,
)

backend_online = check_backend_health()

if backend_online:
    st.sidebar.markdown(
        '<div class="status-pill online">'
        '<span class="status-dot"></span>API Connected'
        '</div>',
        unsafe_allow_html=True,
    )
else:
    st.sidebar.markdown(
        '<div class="status-pill offline">'
        '<span class="status-dot"></span>API Offline'
        '</div>',
        unsafe_allow_html=True,
    )
    st.sidebar.markdown(
        '<div class="offline-card">'
        'Start the server:<br>'
        '<code>uvicorn app.main:app --reload</code>'
        '</div>',
        unsafe_allow_html=True,
    )

if st.sidebar.button("＋  New Chat", use_container_width=True, type="primary"):
    reset_chat()
    st.rerun()

# ── Document RAG ───────────────────────────────────────────────────────────────
st.sidebar.markdown('<span class="sec-label">📄  Document RAG</span>', unsafe_allow_html=True)

if st.session_state["doc_meta"]:
    meta = st.session_state["doc_meta"]
    st.sidebar.markdown(
        f'<div class="doc-badge">'
        f'<strong>📎 {meta.get("filename", "document.pdf")}</strong>'
        f'<span class="meta">'
        f'{meta.get("chunks", 0)} chunks &nbsp;·&nbsp; '
        f'{meta.get("documents", 0)} pages'
        f'</span></div>',
        unsafe_allow_html=True,
    )
else:
    st.sidebar.markdown(
        '<p style="font-size:.73rem;color:#5a2035;font-style:italic;padding:2px 0 8px;">'
        'No document attached yet.</p>',
        unsafe_allow_html=True,
    )

uploaded_file = st.sidebar.file_uploader(
    "Drop a PDF to enable RAG",
    type=["pdf"],
    key=f"uploader_{current_thread_id}",
    label_visibility="visible",
)

if uploaded_file and backend_online:
    existing = (
        st.session_state["doc_meta"].get("filename")
        if st.session_state["doc_meta"] else None
    )
    if uploaded_file.name != existing:
        with st.sidebar.status("⚙️  Indexing PDF…", expanded=True) as sbox:
            summary = upload_document_to_backend(
                thread_id=current_thread_id,
                file_name=uploaded_file.name,
                file_bytes=uploaded_file.getvalue(),
            )
            if summary:
                st.session_state["doc_meta"] = summary
                sbox.update(label="✅ Indexed", state="complete", expanded=False)
                st.rerun()

# ── Conversations ──────────────────────────────────────────────────────────────
st.sidebar.markdown('<span class="sec-label">💬  Conversations</span>', unsafe_allow_html=True)

threads_dict = fetch_all_threads()
if threads_dict:
    st.session_state["chat_threads"] = threads_dict

sorted_threads = list(st.session_state["chat_threads"].items())[::-1]

if sorted_threads:
    for tid, tname in sorted_threads:
        col1, col2 = st.sidebar.columns([0.84, 0.16])
        is_active  = tid == current_thread_id
        label      = f"▶  {tname}" if is_active else f"    {tname}"

        if col1.button(label, key=f"thread_{tid}", use_container_width=True):
            st.session_state["thread_id"]    = tid
            details = load_conversation(tid)
            st.session_state["message_hist"] = details.get("messages", [])
            st.session_state["doc_meta"]     = details.get("document_metadata")
            st.rerun()

        if col2.button("✕", key=f"del_{tid}", help="Delete chat"):
            delete_thread_from_backend(tid)
            st.session_state["chat_threads"].pop(tid, None)
            if tid == current_thread_id:
                reset_chat()
            st.rerun()
else:
    st.sidebar.markdown(
        '<p style="font-size:.73rem;color:#5a2035;font-style:italic;">'
        'No conversations yet.</p>',
        unsafe_allow_html=True,
    )

st.sidebar.markdown(
    '<div class="sidebar-footer">'
    'Enterprise AI Platform<br>'
    '<span class="dot">●</span> LangGraph &nbsp;'
    '<span class="dot">●</span> FastAPI &nbsp;'
    '<span class="dot">●</span> Gemini'
    '</div>',
    unsafe_allow_html=True,
)


# ─── Main Chat Area ────────────────────────────────────────────────────────────

current_title = st.session_state["chat_threads"].get(current_thread_id, "New Chat")
short_id      = current_thread_id[:8] + "…"

st.markdown(
    f'<div class="chat-header">'
    f'  <div class="icon-box">🌺</div>'
    f'  <div>'
    f'    <h2>{current_title}</h2>'
    f'    <span class="tid">Thread #{short_id}</span>'
    f'  </div>'
    f'</div>',
    unsafe_allow_html=True,
)

if not st.session_state["message_hist"]:
    st.markdown(
        """
        <div class="empty-state">
          <div class="orb-wrap">
            <div class="orb">🌺</div>
          </div>
          <h3>How can I help you today?</h3>
          <p>Ask me anything, upload a PDF to chat with your documents,
             or let me search the web for real-time answers.</p>
          <div class="chips">
            <span class="chip">🌐 Web Search</span>
            <span class="chip">📄 PDF RAG</span>
            <span class="chip">⚡ Token Streaming</span>
            <span class="chip">🧠 LangGraph Agent</span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

for message in st.session_state["message_hist"]:
    role    = message.get("role", "user")
    content = message.get("content", "")
    with st.chat_message(role):
        st.markdown(content)


# ─── Chat Input & SSE Stream ───────────────────────────────────────────────────

placeholder = (
    "Type your message…"
    if backend_online
    else "⚠️  Backend offline — start the API server first"
)
user_prompt = st.chat_input(placeholder, disabled=not backend_online)

if user_prompt:
    st.session_state["message_hist"].append({"role": "user", "content": user_prompt})
    with st.chat_message("user"):
        st.markdown(user_prompt)

    with st.chat_message("assistant"):
        status_holder: dict = {"box": None}
        meta_holder:   dict = {"title": None}

        def stream_response_generator():
            url     = f"{BACKEND_URL}/chat/stream"
            payload = {"message": user_prompt, "thread_id": current_thread_id}

            with httpx.Client(timeout=120.0) as client:
                with client.stream("POST", url, json=payload) as response:
                    for line in response.iter_lines():
                        if not line or not line.startswith("data: "):
                            continue
                        raw = line[6:].strip()
                        try:
                            event = json.loads(raw)
                        except json.JSONDecodeError:
                            continue

                        etype = event.get("event")

                        if etype == "tool_start":
                            tname = event.get("tool", "tool")
                            if status_holder["box"] is None:
                                status_holder["box"] = st.status(
                                    f"🔧  Running `{tname}`…", expanded=True
                                )
                            else:
                                status_holder["box"].update(
                                    label=f"🔧  Running `{tname}`…",
                                    state="running", expanded=True,
                                )
                        elif etype == "tool_complete":
                            tname = event.get("tool", "tool")
                            if status_holder["box"] is not None:
                                status_holder["box"].update(
                                    label=f"✅  `{tname}` done",
                                    state="running", expanded=False,
                                )
                        elif etype == "token":
                            yield event.get("text", "")
                        elif etype == "done":
                            meta_holder["title"] = event.get("title")
                        elif etype == "error":
                            st.error(f"Error: {event.get('detail')}")

        ai_text = st.write_stream(stream_response_generator())

        if status_holder["box"] is not None:
            status_holder["box"].update(label="✅  Ready", state="complete", expanded=False)

    st.session_state["message_hist"].append({"role": "assistant", "content": ai_text})

    new_title = meta_holder["title"]
    if new_title and new_title != st.session_state["chat_threads"].get(current_thread_id):
        st.session_state["chat_threads"][current_thread_id] = new_title
        st.rerun()
