import streamlit as st
import random
from collections import defaultdict
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import io
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

# --- INITIAL CONFIG ---
st.set_page_config(page_title="Smart Lineup Rotator", page_icon="⚽", layout="wide")

st.title("⚽ Smart Football Lineup Generator")
st.markdown("Generate fair 5-a-side rotations ensuring everyone plays the same amount of time, with field visualization.")

# --- SIDEBAR ---
st.sidebar.header("⚙️ Match Settings")
quarters = st.sidebar.slider("Number of quarters", 1, 4, 4)
intervals = quarters * 2  # two halves per quarter
num_players = st.sidebar.slider("Number of players", 6, 7, 7)

# --- PLAYER INPUT ---
st.markdown("### 👥 Player list and preferred positions")

positions = ["Goalkeeper", "Defender", "Midfielder", "Forward"]
players = {}

for i in range(num_players):
    col1, col2 = st.columns([2, 3])
    name = col1.text_input(f"Player {i+1}", key=f"name_{i}")
    fav_positions = col2.multiselect(
        "Preferred positions",
        positions,
        default=[],
        key=f"pos_{i}"
    )
    if name:
        players[name] = fav_positions

# --- GENERATION LOGIC ---
if st.button("🎲 Generate Rotations"):
    if len(players) < 6:
        st.error("You must enter at least 6 players.")
    else:
        field_positions = ["Goalkeeper", "Defender", "Midfielder", "Midfielder", "Forward"]
        minutes_played = defaultdict(int)
        all_players = list(players.keys())

        # Initial starting 5 and substitutes
        starters = random.sample(all_players, 5)
        subs = [p for p in all_players if p not in starters]
        previous_starters = starters.copy()

        lineups = []

        for i in range(intervals):
            lineup = {}
            available = previous_starters.copy()

            # Assign positions
            assigned = []
            for pos in field_positions:
                candidates = [p for p in available if pos in players[p]]
                if not candidates:
                    player = random.choice(available)
                else:
                    player = min(candidates, key=lambda x: minutes_played[x])
                lineup[pos] = player
                assigned.append(player)
                available.remove(player)

            # Save lineup
            lineups.append(lineup)

            # Update minutes played
            for player in lineup.values():
                minutes_played[player] += 1

            # Rotation logic
            resting = [p for p in all_players if p not in assigned]
            if resting:
                to_rest = random.sample(assigned, len(resting))
                previous_starters = [p for p in assigned if p not in to_rest] + resting
            else:
                previous_starters = assigned

        # --- DISPLAY RESULTS ---
        st.success("✅ Rotations generated successfully!")

        for i, lineup in enumerate(lineups, 1):
            st.subheader(f"🕐 Half-quarter {i}")

            col1, col2 = st.columns([1, 2])
            
