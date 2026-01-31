import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import json

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="NITeMatch 💘",
    page_icon="💘",
    layout="centered"
)

# ---------------- STYLES ----------------
st.markdown("""
<style>
html, body, .stApp {
    overflow-y: auto;
}

.stApp {
    background:
        radial-gradient(circle at 20% 20%, rgba(255,79,216,0.30), transparent 40%),
        radial-gradient(circle at 80% 10%, rgba(0,255,225,0.30), transparent 40%),
        radial-gradient(circle at 50% 80%, rgba(106,0,255,0.30), transparent 45%),
        #05000a;
    color: white;
}

.block-container {
    max-width: 820px;
    padding-top: 2rem;
    padding-bottom: 4rem;
}

.title {
    font-size: 3rem;
    font-weight: 900;
    text-align: center;
    background: linear-gradient(90deg, #ff4fd8, #00ffe1);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.subtitle {
    text-align: center;
    color: #d6d6d6;
    margin-bottom: 1.5rem;
}

.quote {
    text-align: center;
    font-size: 0.95rem;
    color: #f2f2f2;
    margin-bottom: 2.5rem;
    padding: 14px;
    border-radius: 14px;
    background: rgba(255,255,255,0.06);
    border: 1px solid rgba(255,255,255,0.15);
}

.glass {
    background: rgba(12,12,22,0.88);
    backdrop-filter: blur(18px);
    border-radius: 24px;
    padding: 36px;
    margin-bottom: 40px;
    border: 1px solid rgba(255,255,255,0.22);
    box-shadow: 0 0 30px rgba(255,79,216,0.25);
}

.section {
    font-size: 1.25rem;
    font-weight: 800;
    color: #00ffe1;
    margin-top: 2rem;
    margin-bottom: 0.6rem;
}

label, .stMarkdown, .stSlider, .stRadio {
    color: white !important;
}

input, textarea {
    background: rgba(0,0,0,0.55) !important;
    color: white !important;
    border-radius: 12px !important;
}

.match {
    background: rgba(255,255,255,0.06);
    border-radius: 18px;
    padding: 18px;
    margin-bottom: 16px;
    border: 1px solid rgba(255,255,255,0.15);
}

.stButton > button {
    width: 100%;
    background: linear-gradient(90deg, #ff4fd8, #00ffe1);
    color: black;
    font-size: 1.1rem;
    font-weight: 900;
    border-radius: 999px;
    padding: 1em;
}

.footer {
    text-align: center;
    margin-top: 60px;
    font-size: 0.8rem;
    color: #aaa;
}
</style>
""", unsafe_allow_html=True)

# ---------------- FIREBASE INIT (STREAMLIT SECRETS ONLY) ----------------
if not firebase_admin._apps:
    key_dict = json.loads(st.secrets["FIREBASE_KEY"])
    cred = credentials.Certificate(key_dict)
    firebase_admin.initialize_app(cred)

db = firestore.client()

# ---------------- RESULT UNLOCK TIME ----------------
# Results unlock on 6 Feb at 8 PM
UNLOCK_TIME = datetime(2026, 2, 6, 20, 0)
now = datetime.now()

# ---------------- HEADER ----------------
st.markdown("<div class='title'>NITeMatch 💘</div>", unsafe_allow_html=True)
st.markdown(
    "<div class='subtitle'>Swipe less. Feel more.<br>"
    "A Gen-Z match experiment for NIT Jalandhar ✨</div>",
    unsafe_allow_html=True
)
st.markdown(
    "<div class='quote'>"
    "“Love looks not with the eyes, but with the mind.” — William Shakespeare"
    "</div>",
    unsafe_allow_html=True
)

# ---------------- HELPERS ----------------
def fetch_users():
    return [doc.to_dict() for doc in db.collection("users").stream()]

def build_matrix(users):
    return np.array([
        [
            u["answers"]["q1"], u["answers"]["q2"], u["answers"]["q3"],
            u["answers"]["q4"], u["answers"]["q5"],
            u["answers"]["q6"], u["answers"]["q7"], u["answers"]["q8"],
            u["answers"]["q9"], u["answers"]["q10"]
        ]
        for u in users
    ])

# ---------------- FORM MODE ----------------
if now < UNLOCK_TIME:

    st.markdown("<div class='glass'>", unsafe_allow_html=True)

    with st.form("nitematch"):
        alias = st.text_input("Choose an alias")
        gender = st.radio("I identify as", ["Male", "Female"])

        st.markdown("<div class='section'>🧠 Compatibility</div>", unsafe_allow_html=True)
        q1 = st.slider("I enjoy deep conversations", 1, 5)
        q2 = st.slider("I open up emotionally", 1, 5)
        q3 = st.slider("I stay calm during conflicts", 1, 5)
        q4 = st.slider("I value emotional understanding", 1, 5)
        q5 = st.slider("I need personal space", 1, 5)

        st.markdown("<div class='section'>⚡ Lifestyle</div>", unsafe_allow_html=True)
        q6 = st.slider("My energy level is high", 1, 5)
        q7 = st.slider("I prefer late nights", 1, 5)
        q8 = st.slider("I enjoy spontaneous plans", 1, 5)

        st.markdown("<div class='section'>😄 Vibe</div>", unsafe_allow_html=True)
        q9 = st.slider("I enjoy playful humour", 1, 5)
        q10 = st.slider("I like late-night talks", 1, 5)

        st.markdown("<div class='section'>📸 Contact (Optional)</div>", unsafe_allow_html=True)
        instagram = st.text_input("Instagram handle (without @)")
        consent = st.checkbox("I allow my Instagram to be shared with matches")

        st.markdown("<div class='section'>💌 Message</div>", unsafe_allow_html=True)
        message = st.text_area("One message your match should read 💖", max_chars=200)

        submit = st.form_submit_button("Submit 💘")

    if submit:
        if not alias.strip():
            st.error("Alias cannot be empty.")
        else:
            db.collection("users").add({
                "alias": alias.strip(),
                "gender": gender,
                "answers": {
                    "q1": q1, "q2": q2, "q3": q3, "q4": q4, "q5": q5,
                    "q6": q6, "q7": q7, "q8": q8,
                    "q9": q9, "q10": q10
                },
                "message": message.strip(),
                "contact": {
                    "instagram": instagram.strip(),
                    "share_instagram": consent
                }
            })
            st.success("💖 Submitted! Come back on Feb 6 night.")

    st.markdown("</div>", unsafe_allow_html=True)

# ---------------- RESULTS MODE ----------------
else:
    users = fetch_users()

    if len(users) < 2:
        st.warning("Not enough participants yet.")
    else:
        aliases = [u["alias"] for u in users]
        me = st.selectbox("Select your alias", aliases)
        me_idx = aliases.index(me)

        X = build_matrix(users)
        X = (X - X.mean(axis=0)) / X.std(axis=0)
        similarity = cosine_similarity(X)

        my_gender = users[me_idx]["gender"]
        scores = []

        for i, score in enumerate(similarity[me_idx]):
            if i == me_idx:
                continue
            if users[i]["gender"] == my_gender:
                continue
            scores.append((i, score))

        scores.sort(key=lambda x: x[1], reverse=True)
        top_matches = scores[:5]

        st.markdown("<div class='glass'>", unsafe_allow_html=True)
        st.markdown("<div class='section'>🔥 Your Top Matches</div>", unsafe_allow_html=True)

        for rank, (i, s) in enumerate(top_matches, 1):
            u = users[i]
            st.markdown(
                f"<div class='match'><b>{rank}. {u['alias']}</b><br>"
                f"Compatibility: <b>{round(s*100, 2)}%</b></div>",
                unsafe_allow_html=True
            )

            if u["contact"]["share_instagram"]:
                st.caption(f"📸 Instagram: @{u['contact']['instagram']}")
            if u.get("message"):
                st.caption(f"💌 “{u['message']}”")

        st.markdown("</div>", unsafe_allow_html=True)

# ---------------- FOOTER ----------------
st.markdown(
    "<div class='footer'>Built with ❤️, caffeine & zero sleep</div>",
    unsafe_allow_html=True
)
