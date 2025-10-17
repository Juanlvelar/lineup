import streamlit as st
import random
from collections import defaultdict
import matplotlib.pyplot as plt
import io
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

# --- INITIAL CONFIGURATION ---
st.set_page_config(page_title="Lineup Rotator", page_icon="⚽", layout="wide")

st.title("⚽ Automatic Soccer Lineup Generator")
st.markdown("Create balanced 5-a-side rotations with your players and their preferred positions.")

# --- SIDEBAR SETTINGS ---
st.sidebar.header("⚙️ Match Settings")
quarters = st.sidebar.slider("Number of quarters", 1, 4, 4)
subs_per_quarter = st.sidebar.slider("Substitutions per quarter", 1, 3, 2)
intervals = quarters * subs_per_quarter

st.sidebar.markdown("---")
num_players = st.sidebar.slider("Number of players", 6, 7, 7)

# --- PLAYER INPUT ---
st.markdown("### 👥 Player list and preferred positions")

possible_positions = ["Goalkeeper", "Defender", "Midfielder", "Forward"]
players = {}

for i in range(num_players):
    col1, col2 = st.columns([2, 3])
    name = col1.text_input(f"Player {i+1}", key=f"name_{i}")
    positions = col2.multiselect(
        "Preferred positions",
        possible_positions,
        default=[],
        key=f"pos_{i}"
    )
    if name:
        players[name] = positions

# --- GENERATE BUTTON ---
if st.button("🎲 Generate Lineups"):
    if len(players) < 6:
        st.error("You must enter at least 6 players.")
    else:
        required_positions = ["Goalkeeper", "Defender", "Midfielder", "Midfielder", "Forward"]
        minutes_played = defaultdict(int)
        lineups = []

        for i in range(intervals):
            lineup = {}
            available = list(players.keys())

            # Goalkeeper
            gks = [p for p in available if "Goalkeeper" in players[p]]
            goalkeeper = min(gks or available, key=lambda x: minutes_played[x])
            lineup["Goalkeeper"] = goalkeeper
            available.remove(goalkeeper)

            # Defender
            defs = [p for p in available if "Defender" in players[p]]
            defender = min(defs or available, key=lambda x: minutes_played[x])
            lineup["Defender"] = defender
            available.remove(defender)

            # Midfielders
            mids = [p for p in available if "Midfielder" in players[p]]
            if len(mids) < 2:
                others = [p for p in available if p not in mids]
                mids += random.sample(others, 2 - len(mids))
            else:
                mids = random.sample(mids, 2)
            lineup["Midfielders"] = mids
            for m in mids:
                available.remove(m)

            # Forward
            fwds = [p for p in available if "Forward" in players[p]]
            forward = min(fwds or available, key=lambda x: minutes_played[x])
            lineup["Forward"] = forward

            # Update playing time
            for p in lineup.values():
                if isinstance(p, list):
                    for x in p:
                        minutes_played[x] += 1
                else:
                    minutes_played[p] += 1

            lineups.append(lineup)

        st.success("✅ Lineups generated successfully")

        # --- DISPLAY RESULTS ---
        for i, l in enumerate(lineups, 1):
            st.subheader(f"🕐 Half-quarter {i}")

            col1, col2 = st.columns([1, 2])

            with col1:
                st.write(f"**Goalkeeper:** {l['Goalkeeper']}")
                st.write(f"**Defender:** {l['Defender']}")
                st.write(f"**Midfielders:** {', '.join(l['Midfielders'])}")
                st.write(f"**Forward:** {l['Forward']}")

            # --- DRAW THE FIELD ---
            with col2:
                fig, ax = plt.subplots(figsize=(4, 6))
                ax.set_xlim(0, 100)
                ax.set_ylim(0, 150)
                ax.axis("off")

                # Field outline
                rect = plt.Rectangle((0, 0), 100, 150, fill=False, lw=2)
                ax.add_patch(rect)
                plt.plot([0, 100], [75, 75], 'k--')  # half line

                # Player positions (x, y)
                field_positions = {
                    "Goalkeeper": (50, 10),
                    "Defender": (50, 40),
                    "Mid1": (30, 80),
                    "Mid2": (70, 80),
                    "Forward": (50, 120)
                }

                # Player names
                ax.text(*field_positions["Goalkeeper"], l["Goalkeeper"], ha='center', va='center', fontsize=10, color='blue')
                ax.text(*field_positions["Defender"], l["Defender"], ha='center', va='center', fontsize=10, color='green')
                ax.text(*field_positions["Mid1"], l["Midfielders"][0], ha='center', va='center', fontsize=10, color='orange')
                ax.text(*field_positions["Mid2"], l["Midfielders"][1], ha='center', va='center', fontsize=10, color='orange')
                ax.text(*field_positions["Forward"], l["Forward"], ha='center', va='center', fontsize=10, color='red')

                st.pyplot(fig)

        # --- MINUTES TABLE ---
        st.markdown("---")
        st.subheader("📊 Minutes played per player")
        for p, m in minutes_played.items():
            st.write(f"- {p}: **{m} intervals**")

        # --- EXPORT TO PDF ---
        pdf_buffer = io.BytesIO()
        doc = SimpleDocTemplate(pdf_buffer)
        styles = getSampleStyleSheet()
        story = []

        story.append(Paragraph("⚽ Generated Lineups", styles["Title"]))
        story.append(Spacer(1, 12))

        for i, l in enumerate(lineups, 1):
            story.append(Paragraph(f"<b>Half-quarter {i}</b>", styles["Heading2"]))
            story.append(Paragraph(f"Goalkeeper: {l['Goalkeeper']}", styles["Normal"]))
            story.append(Paragraph(f"Defender: {l['Defender']}", styles["Normal"]))
            story.append(Paragraph(f"Midfielders: {', '.join(l['Midfielders'])}", styles["Normal"]))
            story.append(Paragraph(f"Forward: {l['Forward']}", styles["Normal"]))
            story.append(Spacer(1, 12))

        story.append(Paragraph("📊 Minutes played", styles["Heading2"]))
        for p, m in minutes_played.items():
            story.append(Paragraph(f"{p}: {m} intervals", styles["Normal"]))

        doc.build(story)
        st.download_button(
            label="💾 Download lineups as PDF",
            data=pdf_buffer.getvalue(),
            file_name="lineups.pdf",
            mime="application/pdf"
        )
