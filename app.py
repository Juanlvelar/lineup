import streamlit as st
import random
from collections import defaultdict
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import landscape, letter
from datetime import datetime

# --- CONFIGURACIÓN INICIAL ---
st.set_page_config(page_title="Smart Lineup Rotator", page_icon="⚽", layout="wide")
st.title("⚽ Smart Football Lineup Generator - Custom Formation & Fair Playtime")
st.markdown("Generate fair rotations with customizable formation, goalkeeper exemption, and professional PDF output.")

# --- SIDEBAR: AJUSTES DEL PARTIDO ---
st.sidebar.header("⚙️ Match Settings")
quarters = st.sidebar.slider("Number of quarters", 1, 4, 4)
intervals = quarters * 2
num_players = st.sidebar.slider("Number of players", 6, 10, 7)
ignore_gk = st.sidebar.checkbox("❌ Do not count goalkeeper minutes", value=True)

# --- FORMACIÓN PERSONALIZABLE ---
st.sidebar.subheader("🧩 Custom Diamond Formation")
formation_x = {}
formation_y = {}
default_positions = {
    "Goalkeeper": (0.5, 3),
    "Defender": (3, 3),
    "Midfielder1": (5, 4.5),
    "Midfielder2": (5, 1.5),
    "Forward": (8.5, 3),
}

# Sliders con claves únicas
for pos, (dx, dy) in default_positions.items():
    formation_x[pos] = st.sidebar.slider(f"{pos} X", 0.0, 10.0, dx, 0.1, key=f"{pos}_x_slider")
    formation_y[pos] = st.sidebar.slider(f"{pos} Y", 0.0, 6.0, dy, 0.1, key=f"{pos}_y_slider")

# --- LISTA DE JUGADORES ---
st.markdown("### 👥 Player list and preferred positions")
positions = ["Goalkeeper", "Defender", "Midfielder", "Forward"]
players = {}
for i in range(num_players):
    col1, col2 = st.columns([2, 3])
    name = col1.text_input(f"Player {i+1}", key=f"name_{i}")
    fav_positions = col2.multiselect("Preferred positions", positions, default=[], key=f"pos_{i}")
    if name:
        players[name] = fav_positions

# --- GENERAR ROTACIONES EQUILIBRADAS ---
if st.button("🎲 Generate Rotations"):
    if len(players) < 6:
        st.error("You must enter at least 6 players.")
    else:
        field_positions = list(default_positions.keys())
        all_players = list(players.keys())
        target_diff = 1  # diferencia máxima aceptable entre minutos
        max_attempts = 1000

        for attempt in range(max_attempts):
            minutes_played = defaultdict(int)
            starters = random.sample(all_players, 5)
            previous_starters = starters.copy()
            lineups = []

            for _ in range(intervals):
                lineup = {}
                available = previous_starters.copy()
                assigned = []

                for pos in field_positions:
                    if "Midfielder" in pos:
                        candidates = [p for p in available if "Midfielder" in players[p]]
                    else:
                        candidates = [p for p in available if pos in players[p]]
                    if not candidates:
                        candidates = available.copy()
                    player = min(candidates, key=lambda x: minutes_played[x])
                    lineup[pos] = player
                    assigned.append(player)
                    available.remove(player)

                lineups.append(lineup)

                # Actualizar minutos (ignorando portero si se selecciona)
                for pos, player in lineup.items():
                    if ignore_gk and pos == "Goalkeeper":
                        continue
                    minutes_played[player] += 1

                # Rotación
                resting = [p for p in all_players if p not in assigned]
                if resting:
                    to_rest = random.sample(assigned, len(resting))
                    previous_starters = [p for p in assigned if p not in to_rest] + resting
                else:
                    previous_starters = assigned

            max_minutes = max(minutes_played.values())
            min_minutes = min(minutes_played.values())
            if max_minutes - min_minutes <= target_diff:
                break

        st.success("✅ Balanced rotations generated successfully!")

        # --- VISUALIZACIÓN ---
        for i, lineup in enumerate(lineups, 1):
            st.subheader(f"🕐 Half-quarter {i}")
            resting_players = [p for p in all_players if p not in lineup.values()]
            st.write("Resting players:", ", ".join(resting_players) if resting_players else "None")

            fig, ax = plt.subplots(figsize=(8, 5))
            ax.add_patch(patches.Rectangle((0, 0), 10, 6, linewidth=2, edgecolor='green', facecolor='lightgreen'))
            ax.add_patch(patches.Circle((5, 3), 1, linewidth=2, edgecolor='white', facecolor='none'))
            ax.plot([5, 5], [0, 6], color='white', linewidth=2)
            ax.add_patch(patches.Rectangle((0, 2), 1.5, 2, linewidth=2, edgecolor='white', facecolor='none'))
            ax.add_patch(patches.Rectangle((8.5, 2), 1.5, 2, linewidth=2, edgecolor='white', facecolor='none'))
            ax.set_xlim(0, 10)
            ax.set_ylim(-1, 6)
            ax.axis('off')

            for pos, player_name in lineup.items():
                x, y = formation_x[pos], formation_y[pos]
                color = "white"
                ax.text(x, y, player_name, ha='c_
