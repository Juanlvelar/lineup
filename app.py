import streamlit as st
import random
from collections import defaultdict
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib.units import cm

# --- CONFIG ---
st.set_page_config(page_title="Smart Lineup Rotator", page_icon="⚽", layout="wide")
st.title("⚽ Smart Football Lineup Generator - Diamante Formation PDF")
st.markdown("Generate rotations and download a PDF with all intervals on the same page (two per row).")

# --- SIDEBAR SETTINGS ---
st.sidebar.header("⚙️ Match Settings")
quarters = st.sidebar.slider("Number of quarters", 1, 4, 4)
intervals = quarters * 2
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

            # Assign positions giving priority to players with fewer minutes
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

            for player in lineup.values():
                minutes_played[player] += 1

            resting = [p for p in all_players if p not in assigned]
            if resting:
                to_rest = random.sample(assigned, len(resting))
                previous_starters = [p for p in assigned if p not in to_rest] + resting
            else:
                previous_starters = assigned

        st.success("✅ Rotations generated successfully!")

        # --- DISPLAY LINEUPS AND FIELD IN STREAMLIT ---
        for i, lineup in enumerate(lineups, 1):
            st.subheader(f"🕐 Half-quarter {i}")
            resting_players = [p for p in all_players if p not in lineup.values()]
            st.write("Resting players:", ", ".join(resting_players) if resting_players else "None")

            fig, ax = plt.subplots(figsize=(8, 5))
            field = patches.Rectangle((0, 0), 10, 6, linewidth=2, edgecolor='green', facecolor='lightgreen')
            ax.add_patch(field)

            center_circle = patches.Circle((5, 3), 1, linewidth=2, edgecolor='white', facecolor='none')
            ax.add_patch(center_circle)
            ax.plot([5, 5], [0, 6], color='white', linewidth=2)
            penalty_left = patches.Rectangle((0, 2), 1.5, 2, linewidth=2, edgecolor='white', facecolor='none')
            penalty_right = patches.Rectangle((8.5, 2), 1.5, 2, linewidth=2, edgecolor='white', facecolor='none')
            ax.add_patch(penalty_left)
            ax.add_patch(penalty_right)
            ax.set_xlim(0, 10)
            ax.set_ylim(0, 6)
            ax.axis('off')

            diamond_coords = {
                "Goalkeeper": (0.5, 3),
                "Defender": (3, 3),
                "Midfielder1": (5, 4.5),
                "Midfielder2": (5, 1.5),
                "Forward": (8.5, 3)
            }

            for pos, player_name in lineup.items():
                x, y = diamond_coords[pos]
                color = "white" if player_name not in resting_players else "red"
                ax.text(x, y, player_name, ha='center', va='center',
                        fontsize=10, bbox=dict(facecolor=color, alpha=0.7, boxstyle='round'))

            st.pyplot(fig)

        # --- SUMMARY ---
        st.markdown("### ⏱️ Summary of minutes played")
        summary_table = {player: minutes_played[player] for player in all_players}
        st.table(summary_table)

        # --- PDF GENERATION (all intervals in the same page, two per row) ---
        pdf_buffer = BytesIO()
        c = canvas.Canvas(pdf_buffer, pagesize=landscape(letter))
        c.setFont("Helvetica", 10)

        def draw_field_pdf(c, x_offset, y_offset, lineup, resting_players):
            c.setFillColorRGB(0.7, 1, 0.7)
            c.rect(x_offset, y_offset, 300, 180, fill=1)
            c.setStrokeColorRGB(1, 1, 1)
            c.setLineWidth(2)
            c.line(x_offset + 150, y_offset, x_offset + 150, y_offset + 180)
            c.circle(x_offset + 150, y_offset + 90, 30)
            c.rect(x_offset, y_offset + 60, 45, 60, stroke=1, fill=0)
            c.rect(x_offset + 255, y_offset + 60, 45, 60, stroke=1, fill=0)
            coords = {
                "Goalkeeper": (x_offset + 15, y_offset + 90),
                "Defender": (x_offset + 90, y_offset + 90),
                "Midfielder1": (x_offset + 150, y_offset + 140),
                "Midfielder2": (x_offset + 150, y_offset + 40),
                "Forward": (x_offset + 270, y_offset + 90)
            }
            for pos, player_name in lineup.items():
                x, y = coords[pos]
                c.setFillColorRGB(1, 0, 0) if player_name in resting_players else c.setFillColorRGB(1, 1, 1)
                c.rect(x-15, y-10, 30, 20, fill=1)
                c.setFillColorRGB(0, 0, 0)
                c.drawCentredString(x, y, player_name)

        # Draw all intervals in pairs on same page (max 2 rows)
        y_start = 350
        for i in range(0, len(lineups), 2):
            c.setFont("Helvetica-Bold", 12)
            c.drawString(20, y_start + 180, f"Intervals {i+1} & {i+2}")
            # Left field
            lineup1 = lineups[i]
            resting1 = [p for p in all_players if p not in lineup1.values()]
            draw_field_pdf(c, 50, y_start, lineup1, resting1)
            # Right field
            if i+1 < len(lineups):
                lineup2 = lineups[i+1]
                resting2 = [p for p in all_players if p not in lineup2.values()]
                draw_field_pdf(c, 400, y_start, lineup2, resting2)
            y_start -= 200  # move to next row if needed
        c.showPage()
        c.save()
        pdf_buffer.seek(0)

        st.markdown("### 📄 Download PDF with All Rotations (two per row)")
        st.download_button(
            label="Download PDF",
            data=pdf_buffer,
            file_name="rotations_all_intervals.pdf",
            mime="application/pdf"
        )
