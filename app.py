import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="NITeMatch",
    page_icon="💘",
    layout="centered"
)

# ---------------- STYLES ----------------
st.markdown("""
<style>
.stApp {
    background:
        radial-gradient(circle at 20% 20%, rgba(255,79,216,0.30), transparent 40%),
        radial-gradient(circle at 80% 10%, rgba(0,255,225,0.30), transparent 40%),
        radial-gradient(circle at 50% 80%, rgba(106,0,255,0.30), transparent 45%),
        #05000a;
    color: white;
}
.block-container { max-width: 820px; padding-top: 2rem; }
.title {
    font-size: 3rem;
    font-weight: 900;
    text-align: center;
    background: linear-gradient(90deg, #ff4fd8, #00ffe1);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
.glass {
    background: rgba(12,12,22,0.88);
    backdrop-filter: blur(18px);
    border-radius: 24px;
    padding: 32px;
    margin-bottom: 40px;
}
.match {
    background: rgba(255,255,255,0.06);
    border-radius: 18px;
    padding: 16px;
    margin-bottom: 18px;
}
.why {
    opacity: 0.85;
    font-size: 0.9rem;
}
</style>
""", unsafe_allow_html=True)

# ---------------- FIREBASE INIT ----------------
if not firebase_admin._apps:
    cred = credentials.Certificate(dict(st.secrets["firebase"]))
    firebase_admin.initialize_app(cred)

db = firestore.client()

# ---------------- TIMELINE ----------------
UNLOCK_TIME = datetime(2026, 2, 6, 20, 0)  # 6th Feb, night
now = datetime.now()

# ---------------- HEADER ----------------
st.markdown("<div class='title'>NITeMatch 💘</div>", unsafe_allow_html=True)
st.caption("Anonymous psychological compatibility • Exclusive to NIT Jalandhar")

# ---------------- INFO SECTION ----------------
st.markdown("""
<div class="glass">
<h3>Important information</h3>

<h4>Exclusivity</h4>
<ul>
<li>This experience is exclusively for <b>NIT Jalandhar students</b>.</li>
<li>Participation is based on honesty and mutual respect.</li>
</ul>

<h4>How this works</h4>
<ul>
<li>Your identity remains <b>anonymous</b> during the entire matching process.</li>
<li>Your responses are used only to calculate compatibility.</li>
<li>You will see profiles only after matching, and only with people you are matched with.</li>
<li>Only your <b>alias, optional Instagram ID, and optional message</b> are shared.</li>
<li>There is no way to contact someone except via the details you choose to share.</li>
</ul>

<h4>How matching works</h4>
<ul>
<li>Matching is based primarily on <b>psychological compatibility</b>.</li>
<li>Shared interests and lifestyle preferences are used to refine matches.</li>
<li>The goal is meaningful compatibility, not random pairing.</li>
</ul>

<h4>Timeline</h4>
<ul>
<li><b>Now → 6th February:</b> You fill in your responses and interests anonymously.</li>
<li><b>6th February:</b> Compatibility matching is computed based on psychological thinking.</li>
<li><b>6th February (Night):</b> Your best matches are revealed before Valentine’s Week.</li>
</ul>

<h4>Community guidelines</h4>
<ul>
<li>Please avoid foul, abusive, or inappropriate language.</li>
<li>Such content may affect matching quality or lead to exclusion.</li>
<li>Honest responses lead to better matches.</li>
</ul>

<p style="opacity:0.8;">
By continuing, you confirm that you are from NIT Jalandhar and agree to participate respectfully.
</p>
</div>
""", unsafe_allow_html=True)

# ---------------- HELPERS ----------------
SCALE = ["No", "Slightly", "Maybe", "Mostly", "Yes", "Strongly yes"]

def scale_slider(label):
    val = st.select_slider(label, options=SCALE)
    return SCALE.index(val) + 1

def bin_map(x, a, b):
    return 0 if x == a else 1

def fetch_users():
    return [doc.to_dict() for doc in db.collection("users").stream()]

def cosine(a, b):
    return cosine_similarity([a], [b])[0][0]

# ---------------- FORM MODE ----------------
if now < UNLOCK_TIME:

    st.markdown("<div class='glass'>", unsafe_allow_html=True)

    with st.form("form"):
        alias = st.text_input("Choose an anonymous alias")
        gender = st.radio("I identify as", ["Male", "Female"])

        # Psychological (8)
        q1 = scale_slider("When overwhelmed, I prefer emotional closeness")
        q2 = scale_slider("I feel emotionally safe opening up")
        q3 = scale_slider("During conflict, I try to understand before reacting")
        q4 = scale_slider("Emotional loyalty matters more than attention")
        q5 = scale_slider("Relationships should help people grow")
        q6 = st.radio("In difficult situations, I prefer",
                      ["Handling things alone", "Leaning on someone"])
        q7 = st.radio("I process emotional pain by",
                      ["Thinking quietly", "Talking it out"])
        q8 = scale_slider("I express care more through actions than words")

        # Interests
        q9 = st.radio("The music era you connect with the most",
                      ["Before 2000", "2000–2009", "2010–2019", "2020–Present"])
        q10 = st.radio("Your preferred music genre",
                       ["Pop", "Rock", "Hip-hop / Rap", "EDM", "Metal", "Classical", "Indie"])
        q11 = st.radio("You would rather go to", ["Beaches", "Mountains"])
        q12 = st.radio("Movies you enjoy the most",
                       ["Romance / Drama", "Thriller / Mystery", "Comedy", "Action / Sci-Fi"])
        q13 = st.radio("Your go-to hangout spot",
                       ["Nescafe near Verka", "Campus Cafe", "Night Canteen",
                        "Yadav Canteen", "Snackers", "Domino’s",
                        "Nescafe near Boys Hostel", "Rimjhim area"])

        # Situational
        q14 = st.radio("If extremely busy but someone important needs you",
                       ["Prioritize work", "Make time"])
        q15 = st.radio("After a disagreement, you prefer to",
                       ["Cool off first", "Talk it out"])

        instagram = st.text_input("Instagram (optional, without @)")
        consent = st.checkbox("Allow my Instagram to be shared with matches")
        message = st.text_area("Optional message for matches (max 200 characters)", max_chars=200)

        agree = st.checkbox("I confirm I am from NIT Jalandhar and agree to the above")
        submit = st.form_submit_button("Submit")

    if submit:
        if not alias.strip():
            st.error("Alias is required")
        elif not agree:
            st.error("Please confirm eligibility")
        else:
            db.collection("users").add({
                "alias": alias.strip(),
                "gender": gender,
                "answers": {
                    "psych": [
                        q1, q2, q3, q4, q5,
                        bin_map(q6, "Handling things alone", "Leaning on someone"),
                        bin_map(q7, "Thinking quietly", "Talking it out"),
                        q8
                    ],
                    "interest": [
                        ["Before 2000", "2000–2009", "2010–2019", "2020–Present"].index(q9),
                        ["Pop", "Rock", "Hip-hop / Rap", "EDM", "Metal", "Classical", "Indie"].index(q10),
                        bin_map(q11, "Beaches", "Mountains"),
                        ["Romance / Drama", "Thriller / Mystery", "Comedy", "Action / Sci-Fi"].index(q12),
                        ["Nescafe near Verka", "Campus Cafe", "Night Canteen",
                         "Yadav Canteen", "Snackers", "Domino’s",
                         "Nescafe near Boys Hostel", "Rimjhim area"].index(q13)
                    ],
                    "situation": [
                        bin_map(q14, "Prioritize work", "Make time"),
                        bin_map(q15, "Cool off first", "Talk it out")
                    ]
                },
                "contact": {
                    "instagram": instagram.strip(),
                    "share_instagram": consent
                },
                "message": message.strip()
            })
            st.success("Response recorded. Matches will be revealed on 6th February at night 💫")

    st.markdown("</div>", unsafe_allow_html=True)

# ---------------- RESULTS MODE ----------------
else:
    users = fetch_users()
    aliases = [u["alias"] for u in users]
    me = st.selectbox("Select your alias", aliases)
    me_u = users[aliases.index(me)]

    st.markdown("<div class='glass'>", unsafe_allow_html=True)
    st.caption("Matches below are based on psychological compatibility and shared interests.")

    for u in users:
        if u["alias"] == me:
            continue

        ps = cosine(me_u["answers"]["psych"], u["answers"]["psych"])
        it = cosine(me_u["answers"]["interest"], u["answers"]["interest"])
        si = cosine(me_u["answers"]["situation"], u["answers"]["situation"])

        score = 0.7 * ps + 0.2 * it + 0.1 * si

        if score > 0.75:
            st.markdown(
                f"<div class='match'><b>{u['alias']}</b><br>"
                f"Compatibility: <b>{round(score * 100, 2)}%</b>"
                f"<div class='why'>Why you matched:<br>"
                f"- Similar emotional approach<br>"
                f"- Overlapping interests<br>"
                f"- Comparable decision-making style</div></div>",
                unsafe_allow_html=True
            )
            if u["contact"]["share_instagram"]:
                st.caption(f"📸 @{u['contact']['instagram']}")
            if u["message"]:
                st.caption(f"💬 {u['message']}")

    st.markdown("</div>", unsafe_allow_html=True)
