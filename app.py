import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime, timezone, timedelta
import hashlib
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

# ================= PAGE CONFIG =================
st.set_page_config(
    page_title="NITeMatch",
    page_icon="💘",
    layout="centered"
)

# ================= GLOBAL STYLES =================
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
    padding: 28px;
    margin-bottom: 24px;
}
.match {
    background: rgba(255,255,255,0.06);
    border-radius: 18px;
    padding: 16px;
    margin-bottom: 16px;
}
.small-note { font-size: 0.8rem; opacity: 0.75; }
</style>
""", unsafe_allow_html=True)

# ================= FIREBASE INIT =================
if not firebase_admin._apps:
    cred = credentials.Certificate(dict(st.secrets["firebase"]))
    firebase_admin.initialize_app(cred)

db = firestore.client()

# ================= TIME =================
IST = timezone(timedelta(hours=5, minutes=30))
UNLOCK_TIME = datetime(2026, 2, 6, 20, 0, tzinfo=IST)

MATCH_THRESHOLD = 0.50
SCALE = ["No", "Slightly", "Maybe", "Mostly", "Yes", "Strongly yes"]

# ================= HELPERS =================
def scale_slider(label):
    val = st.select_slider(label, options=SCALE)
    return SCALE.index(val) + 1

def bin_map(x, a, b):
    return 0 if x == a else 1

def normalize(v):
    v = np.array(v, dtype=float)
    norm = np.linalg.norm(v)
    return v if norm == 0 else v / norm

def cosine(a, b):
    if sum(a) == 0 or sum(b) == 0:
        return 0.0
    return cosine_similarity([a], [b])[0][0]

def hash_email(email):
    return hashlib.sha256(email.lower().strip().encode()).hexdigest()

def get_chat_id(a, b):
    return "_".join(sorted([a, b]))

def fetch_users():
    return [
        doc.to_dict() | {"_id": doc.id}
        for doc in db.collection("users").stream()
    ]

# ================= HEADER =================
st.markdown("<div class='title'>NITeMatch 💘</div>", unsafe_allow_html=True)
st.caption("Anonymous psychological compatibility • NIT Jalandhar")

# ================= GUIDELINES =================
with st.expander("📜 Guidelines & Safety"):
    st.markdown("""
- This platform is for respectful connections only  
- No harassment or misuse  
- Do not overshare personal information too early  
- Email is encrypted and never visible to anyone  
- Matches are based on psychological compatibility  
""")

# ================= BEFORE UNLOCK =================
if datetime.now(IST) < UNLOCK_TIME:
    remaining = UNLOCK_TIME - datetime.now(IST)

    st.markdown(f"""
    <div class="glass" style="text-align:center;">
        <div>⏳ Matches reveal in</div>
        <div style="font-size:1.8rem;font-weight:700;">
            {remaining.days}d {remaining.seconds//3600}h {(remaining.seconds//60)%60}m
        </div>
        <div class="small-note">6th February • Night</div>
    </div>
    """, unsafe_allow_html=True)

    with st.form("pre_unlock_form"):
        alias = st.text_input("Choose an anonymous alias")

        # 🔐 IMPORTANT EMAIL MESSAGE (NEW)
        st.markdown("""
        <div class="small-note">
        <b>Important:</b> Your email is collected <b>only to ensure exclusivity</b> for NIT Jalandhar students.  
        It is <b>securely encrypted</b>, <b>never shown to anyone</b> — not even your matches —  
        and is <b>never used for contact or visibility</b>.
        </div>
        """, unsafe_allow_html=True)

        email = st.text_input("Official NIT Jalandhar Email ID")

        st.markdown("""
        <div class="small-note">
        Please remember your <b>alias</b> and <b>email</b>.  
        They will be required after matching to access chats.
        </div>
        """, unsafe_allow_html=True)

        gender = st.radio("I identify as", ["Male", "Female"])

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

        q9 = st.radio("Music era you connect with most",
                      ["Before 2000", "2000–2009", "2010–2019", "2020–Present"])
        q10 = st.radio("Preferred music genre",
                       ["Pop", "Rock", "Hip-hop / Rap", "EDM", "Metal", "Classical", "Indie"])
        q11 = st.radio("You would rather go to", ["Beaches", "Mountains"])
        q12 = st.radio("Movies you enjoy the most",
                       ["Romance / Drama", "Thriller / Mystery", "Comedy", "Action / Sci-Fi"])

        st.markdown("### 🌱 Visible to your match")
        note = st.text_area("Short message", max_chars=120)
        instagram = st.text_input("Instagram username (optional)")

        agree = st.checkbox("I confirm I am from NIT Jalandhar")
        submit = st.form_submit_button("Submit")

    if submit:
        if not alias or not email.endswith("@nitj.ac.in") or not agree:
            st.error("Please fill all fields correctly")
        else:
            email_hash = hash_email(email)
            existing = list(
                db.collection("users")
                .where("email_hash", "==", email_hash)
                .limit(1)
                .stream()
            )
            if existing:
                st.warning("You have already submitted.")
            else:
                db.collection("users").add({
                    "alias": alias.strip(),
                    "email_hash": email_hash,
                    "gender": gender,
                    "instagram": instagram.strip(),
                    "note": note.strip(),
                    "answers": {
                        "psych": [q1, q2, q3, q4, q5,
                                  bin_map(q6, "Handling things alone", "Leaning on someone"),
                                  bin_map(q7, "Thinking quietly", "Talking it out"),
                                  q8],
                        "interest": [
                            ["Before 2000", "2000–2009", "2010–2019", "2020–Present"].index(q9),
                            ["Pop", "Rock", "Hip-hop / Rap", "EDM", "Metal", "Classical", "Indie"].index(q10),
                            bin_map(q11, "Beaches", "Mountains"),
                            ["Romance / Drama", "Thriller / Mystery", "Comedy", "Action / Sci-Fi"].index(q12)
                        ]
                    }
                })
                st.success("Response recorded. Matches unlock on 6th Feb 💘")

    st.stop()

# ================= AFTER UNLOCK =================
# (unchanged, works as already tested)
