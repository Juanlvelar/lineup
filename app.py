import streamlit as st
import random
from collections import defaultdict
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# --- CONFIG ---
st.set_page_config(page_title="Smart Lineup Rotator", page_icon="⚽", layout="wide")
st.title("⚽ Smart Football Lineup Generator - Diamante Formation")
st.markdown("Generate fair 5-a-side rotations with diamond formation and field visualization.")

# --- SIDEBAR SETTINGS ---
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

# --- GENERATE ROTATIONS ---
if st.button("🎲 Generate Rotations"):
    if len(players) < 6:
        st.error("You must enter at least 6 players.")
    else:
        field_positions = ["Goalkeeper", "Defender", "Midfielder1", "Midfielder2", "Forward"]
        minutes_played = defaultdict(int)
        all_players = list(players.keys())
        starters = random.sample(all_players, 5)
        previous_starters = starters.copy()
        lineups = []

        for i in range(intervals):
            lineup = {}
            available = previous_starters.copy()
            assigned = []

            # Assign positions fairly
            for pos in field_positions:
                candidates = [p for p in available if pos.startswith("Midfielder") and "Midfielder" in players[p]] \
                             if "Midfielder" in pos else [p for p in available if pos in players[p]]
                if not candidates:
                    player = random.choice(available)
                else:
                    player = min(candidates, key=lambda x: minutes_played[x])
                lineup[pos] = player
                assigned.append(player)
                available.remove(player)

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

        st.success("✅ Rotations generated successfully!")

        # --- DISPLAY LINEUPS AND FIELD ---
        for i, lineup in enumerate(lineups, 1):
            st.subheader(f"🕐 Half-quarter {i}")
            st.table(lineup.items())

            # Draw field
            fig, ax = plt.subplots(figsize=(8, 5))
            field = patches.Rectangle((0, 0), 10, 6, linewidth=2, edgecolor='green', facecolor='lightgreen')
            ax.add_patch(field)

            # Center circle
            center_circle = patches.Circle((5, 3), 1, linewidth=2, edgecolor='white', facecolor='none')
            ax.add_patch(center_circle)

            # Penalty areas
            penalty_left = patches.Rectangle((0, 2), 1.5, 2, linewidth=2, edgecolor='white', facecolor='none')
            penalty_right = patches.Rectangle((8.5, 2), 1.5, 2, linewidth=2, edgecolor='white', facecolor='none')
            ax.add_patch(penalty_left)
            ax.add_patch(penalty_right)

            ax.set_xlim(0, 10)
            ax.set_ylim(0, 6)
            ax.axis('off')

            # Diamond formation coordinates
            diamond_coords = {
                "Goalkeeper": (0.5, 3),
                "Defender": (3, 3),
                "Midfielder1": (5, 4.5),
                "Midfielder2": (5, 1.5),
                "Forward": (8.5, 3)
            }

            for pos, player_name in lineup.items():
                x, y = diamond_coords.get(pos, (0, 0))
                ax.text(x, y, player_name, ha='center', va='center',
                        fontsize=10, bbox=dict(facecolor='white', alpha=0.7, boxstyle='round'))

            st.pyplot(fig)

        # --- SUMMARY OF MINUTES ---
        st.markdown("### ⏱️ Summary of minutes played")
        summary_table = {player: minutes_played[player] for player in all_players}
        st.table(summary_table)
