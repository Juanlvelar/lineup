import streamlit as st
import random
from collections import defaultdict
import matplotlib.pyplot as plt
import io
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

# --- INITIAL CONFIG ---
st.set_page_config(page_title="Smart Lineup Rotator", page_icon="⚽", layout="wide")

st.title("⚽ Smart Soccer Lineup Generator")
st.markdown("Generate fair 5-a-side rotations ensuring everyone plays the same amount of time.")

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

        lineups = []
        previous_starters = starters.copy()

        for i in range(intervals):
            lineup = {}
            available = previous_starters.copy()

            # Assign field positions (try to match preferred positions)
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

            # Determine who rests next
            resting = [p for p in all_players if p not in assigned]
            if resting:
                # next half: rotate bench and some players on field
                # bring in resting players, send out some who have played most
                current_on_field = set(assigned)
                if len(resting) < len(all_players) - 5:
                    resting = random.sample(all_players, len(all_players) - 5)
                to_rest = random.sample(current_on_field, len(resting))
                previous_starters = [p for p in current_on_field if p not in to_rest] + resting
            else:
                previous_starters = assigned

        # --- SHOW RESULTS ---
        st.success("✅ Rotations generated successfully!")

        for i, lineup in enumerate(lineups, 1):
            st.subheader(f"🕐 Half-quarter {i}")

            col1, col2 = st.columns([1, 2])
            with col1:
                st.write(f"**Goalkeeper:** {lineup['Goalkeeper']}")
                st.write(f"**Defender:** {lineup['Defender']}")
                mids = [v for k, v in lineup.items() if k.startswith("Midfielder")]
                st.write(f"**Midfielders:** {', '.join(mids)}")
                st.write(f"**Forward:** {lineup['Forward']}")

            with col2:
                fig, ax = plt.subplots(figsize=(4, 6))
                ax.set_xlim(0, 100)
                ax.set_ylim(0, 150)
                ax.axis("off")

                # Field lines
                ax.add_patch(plt.Rectangle((0, 0), 100, 150, fill=False, lw=2))
                plt.plot([0, 100], [75, 75], 'k--')

                # Position coordinates
                coords = {
                    "Goalkeeper": (50, 10),
                    "Defender": (50, 40),
                    "Midfielder1": (30, 80),
                    "Midfielder2": (70, 80),
                    "Forward": (50, 120),
                }

                ax.text(*coords["Goalkeeper"], lineup["Goalkeeper"], ha='center', va='center', color='blue')
                ax.text(*coords["Defender"], lineup["Defender"], ha='center', va='center', color='green')
                ax.text(*coords["Midfielder1"], mids[0], ha='center', va='center', color='orange')
                ax.text(*coords["Midfielder2"], mids[1], ha='center', va='center', color='orange')
                ax.text(*coords["Forward"], lineup["Forward"], ha='center', va='center', color='red')

                st.pyplot(fig)

        st.markdown("---")
        st.subheader("📊 Minutes played per player")
        for p, m in minutes_played.items():
            st.write(f"- {p}: **{m} intervals**")
