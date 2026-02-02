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
    margin-bottom: 14px;
}
</style>
""", unsafe_allow_html=True)

# ---------------- FIREBASE INIT ----------------
if not firebase_admin._apps:
    cred = credentials.Certificate(dict(st.secrets["firebase"]))
    firebase_admin.initialize_app(cred)

db = firestore.client()

# ---------------- RESULT TIME ----------------
UNLOCK_TIME = datetime(2026, 2, 6, 20, 0)
now = datetime.now()

# ---------------- HEADER ----------------
st.markdown("<div class='title'>NITeMatch 💘</div>", unsafe_allow_html=True)
st.caption("An anonymous compatibility experience • Exclusive to NIT Jalandhar")

# ---------------- INFO: RULES + TIMELINE ----------------
st.markdown("""
<div class="glass">
<h3>Important information</h3>

<h4>Exclusivity</h4>
<ul>
<li>This experience is intended <b>exclusively for students of NIT Jalandhar</b>.</li>
<li>Participation is based on trust and mutual respect.</li>
<li>Please do not participate if you are not from NIT Jalandhar.</li>
</ul>

<h4>How this works</h4>
<ul>
<li>Your identity remains <b>anonymous</b> during the matching process.</li>
<li>Your responses are used only to calculate compatibility.</li>
<li>You will see profiles only after matching, and only with matched participants.</li>
<li>Only your <b>alias, optional Instagram ID, and optional message</b> are shared.</li>
<li>No one else can view your responses, message, or contact details.</li>
<li>There is no way to contact someone through this platform except via the details you choose to share.</li>
<li>If you do not share contact details, no contact is possible.</li>
</ul>

<h4>How matching works</h4>
<ul>
<li>Matching is based on <b>psychological compatibility</b>, not appearance or popularity.</li>
<li>Your answers reflect thinking patterns around communication, emotional safety, conflict handling, and values.</li>
<li>People are matched when these patterns show strong alignment.</li>
<li>The goal is meaningful compatibility, not random pairing.</li>
</ul>

<h4>Timeline</h4>
<ul>
<li><b>Now → Match Day:</b> Responses are collected anonymously.</li>
<li><b>Match Day:</b> Compatibility is calculated based on psychological alignment.</li>
<li><b>After Match Day:</b> You can view only your matches and their shared details.</li>
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
SCALE_LABELS = ["No", "Slightly", "Maybe", "Mostly", "Yes", "Strongly yes"]

def scale_slider(label):
    choice = st.select_slider(label, options=SCALE_LABELS)
    return SCALE_LABELS.index(choice) + 1

def map_choice(x, a, b):
    return 0 if x == a else 1

def fetch_users():
    return [doc.to_dict() for doc in db.collection("users").stream()]

def build_matrix(users):
    return np.array([
        [u["answers"][f"q{i}"] for i in range(1, 11)]
        for u in users
    ])

# ---------------- FORM MODE ----------------
if now < UNLOCK_TIME:

    st.markdown("<div class='glass'>", unsafe_allow_html=True)

    with st.form("form"):
        alias = st.text_input("Choose an anonymous alias")
        gender = st.radio("I identify as", ["Male", "Female"])

        q1 = scale_slider("When overwhelmed, I prefer emotional closeness")
        q2 = scale_slider("I feel emotionally safe opening up to someone")
        q3 = scale_slider("During conflict, I try to understand before reacting")
        q4 = scale_slider("Emotional loyalty matters more than attention")
        q5 = scale_slider("Relationships should help people grow")

        q6 = st.radio("In difficult situations, I prefer",
                      ["Handling things alone", "Leaning on someone"])

        q7 = st.radio("I process emotional pain by",
                      ["Thinking quietly", "Talking it out"])

        q8 = scale_slider("I express care more through actions than words")

        q9 = st.radio("When excitement fades, commitment comes from",
                      ["Stability and trust", "Shared growth"])

        q10 = st.radio("In close relationships, respect means",
                       ["Giving space", "Being emotionally present"])

        instagram = st.text_input("Instagram (optional, without @)")
        consent = st.checkbox("Allow my Instagram to be shared with matches")
        message = st.text_area("Optional message for matches (max 200 characters)", max_chars=200)

        agree = st.checkbox("I confirm that I am from NIT Jalandhar and agree to the above")
        submit = st.form_submit_button("Submit")

    if submit:
        if not alias.strip():
            st.error("Alias is required")
        elif not agree:
            st.error("Please confirm eligibility to continue")
        else:
            db.collection("users").add({
                "alias": alias.strip(),
                "gender": gender,
                "answers": {
                    "q1": q1, "q2": q2, "q3": q3, "q4": q4, "q5": q5,
                    "q6": map_choice(q6, "Handling things alone", "Leaning on someone"),
                    "q7": map_choice(q7, "Thinking quietly", "Talking it out"),
                    "q8": q8,
                    "q9": map_choice(q9, "Stability and trust", "Shared growth"),
                    "q10": map_choice(q10, "Giving space", "Being emotionally present")
                },
                "contact": {
                    "instagram": instagram.strip(),
                    "share_instagram": consent
                },
                "message": message.strip()
            })
            st.success("Response recorded. Results will be available on match day.")

    st.markdown("</div>", unsafe_allow_html=True)

# ---------------- RESULTS MODE ----------------
else:
    users = fetch_users()

    if len(users) < 2:
        st.info("Not enough participants for matching")
        st.stop()

    aliases = [u["alias"] for u in users]
    me = st.selectbox("Select your alias", aliases)
    me_idx = aliases.index(me)

    X = build_matrix(users)
    X = (X - X.mean(axis=0)) / X.std(axis=0)
    sim = cosine_similarity(X)

    MAX_MATCHES = 5
    n = len(users)

    pairs = []
    for i in range(n):
        for j in range(i + 1, n):
            if users[i]["gender"] != users[j]["gender"]:
                pairs.append((i, j, sim[i][j]))

    pairs.sort(key=lambda x: x[2], reverse=True)

    match_count = {i: 0 for i in range(n)}
    matches = {i: [] for i in range(n)}

    for i, j, score in pairs:
        if match_count[i] < MAX_MATCHES and match_count[j] < MAX_MATCHES:
            matches[i].append((j, score))
            matches[j].append((i, score))
            match_count[i] += 1
            match_count[j] += 1

    my_matches = matches[me_idx]

    st.markdown("<div class='glass'>", unsafe_allow_html=True)

    if not my_matches:
        st.info("No compatible profiles available")
    else:
        st.caption("Matches below are based on psychological compatibility.")
        for idx, s in my_matches:
            u = users[idx]
            st.markdown(
                f"<div class='match'><b>{u['alias']}</b><br>"
                f"Compatibility score: <b>{round(s * 100, 2)}%</b></div>",
                unsafe_allow_html=True
            )
            if u["contact"]["share_instagram"]:
                st.caption(f"📸 @{u['contact']['instagram']}")
            if u.get("message"):
                st.caption(f"💬 {u['message']}")

    st.markdown("</div>", unsafe_allow_html=True)
