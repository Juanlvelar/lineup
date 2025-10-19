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

for pos, (dx, dy) in default_positions.items():
    formation_x[pos] = st.sidebar.slider(f"{pos} X", 0.0, 10.0, dx, 0.1)
    formation_y[pos] = st.sidebar.slider(f"{pos} Y", 0.0, 6.0, dy, 0.1)

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
        target_diff = 1  # max diferencia de minutos
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

                # Actualiza minutos
                for pos, player in lineup.items():
                    if ignore_gk and pos == "Goalkeeper":
                        continue
                    minutes_played[player] += 1

                resting = [p for p in all_players if p not in assigned]
                if resting:
                    to_rest = random.sample(assigned, len(resting))
                    previous_starters = [p for p in assigned if p not in to_rest] + resting
                else:
                    previous_starters = assigned

            # Si el tiempo está equilibrado, paramos
            max_minutes = max(minutes_played.values())
            min_minutes = min(minutes_played.values())
            if max_minutes - min_minutes <= target_diff:
                break

        st.success("✅ Balanced rotations generated successfully!")

        # --- VISUALIZACIÓN EN STREAMLIT ---
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
            ax.set_ylim(0, 6)
            ax.axis('off')

            for pos, player_name in lineup.items():
                x, y = formation_x[pos], formation_y[pos]
                color = "white" if player_name not in resting_players else "red"
                ax.text(x, y, player_name, ha='center', va='center', fontsize=10, bbox=dict(facecolor=color, alpha=0.7, boxstyle='round'))

            for idx, sub in enumerate(resting_players):
                ax.text(1 + idx * 2, -0.5, sub, ha='center', va='center', fontsize=9, bbox=dict(facecolor='gray', alpha=0.7, boxstyle='round'))

            st.pyplot(fig)

        # --- RESUMEN ---
        st.markdown("### ⏱️ Summary of minutes played")
        st.table({player: minutes_played[player] for player in all_players})

        # --- GENERAR PDF ---
        pdf_buffer = BytesIO()
        c = canvas.Canvas(pdf_buffer, pagesize=landscape(letter))

        def draw_field_pdf(c, x_offset, y_offset, lineup, resting_players):
            c.setFillColorRGB(0.7, 1, 0.7)
            c.rect(x_offset, y_offset, 300, 180, fill=1)
            c.setStrokeColorRGB(1, 1, 1)
            c.setLineWidth(2)
            c.line(x_offset + 150, y_offset, x_offset + 150, y_offset + 180)
            c.circle(x_offset + 150, y_offset + 90, 30)
            c.rect(x_offset, y_offset + 60, 45, 60, stroke=1, fill=0)
            c.rect(x_offset + 255, y_offset + 60, 45, 60, stroke=1, fill=0)

            # Jugadores activos
            for pos, player_name in lineup.items():
                x = x_offset + (formation_x[pos] / 10) * 300
                y = y_offset + (formation_y[pos] / 6) * 180
                if player_name in resting_players:
                    c.setFillColorRGB(1, 0, 0)
                else:
                    c.setFillColorRGB(1, 1, 1)
                c.rect(x - 15, y - 10, 30, 20, fill=1)
                c.setFillColorRGB(0, 0, 0)
                c.drawCentredString(x, y, player_name)

            # Suplentes
            for idx, sub in enumerate(resting_players):
                sub_x = x_offset + 40 + idx * 50
                sub_y = y_offset - 25
                c.setFillColorRGB(0.6, 0.6, 0.6)
                c.rect(sub_x - 15, sub_y - 10, 30, 20, fill=1)
                c.setFillColorRGB(0, 0, 0)
                c.drawCentredString(sub_x, sub_y, sub)

        # --- PDF PAGINADO ---
        intervals_per_page = 4
        for page_start in range(0, len(lineups), intervals_per_page):
            c.setFont("Helvetica-Bold", 14)
            c.drawString(20, 560, f"Smart Lineup Rotations - {datetime.now().strftime('%Y-%m-%d')}")
            c.setFont("Helvetica", 10)
            c.drawString(20, 545, f"Players: {', '.join(all_players)}")
            c.drawString(20, 530, f"Goalkeeper time excluded: {'Yes' if ignore_gk else 'No'}")

            y_positions = [350, 100]
            for idx, i in enumerate(range(page_start, min(page_start + intervals_per_page, len(lineups)), 2)):
                y_offset = y_positions[idx % 2]
                lineup1 = lineups[i]
                resting1 = [p for p in all_players if p not in lineup1.values()]
                draw_field_pdf(c, 50, y_offset, lineup1, resting1)
                if i + 1 < len(lineups):
                    lineup2 = lineups[i + 1]
                    resting2 = [p for p in all_players if p not in lineup2.values()]
                    draw_field_pdf(c, 400, y_offset, lineup2, resting2)
            c.showPage()

        c.save()
        pdf_buffer.seek(0)

        st.markdown("### 📄 Download Professional PDF with Substitutes and Custom Formation")
        st.download_button(
            label="Download PDF",
            data=pdf_buffer,
            file_name="rotations_custom_balanced.pdf",
            mime="application/pdf"
        )
