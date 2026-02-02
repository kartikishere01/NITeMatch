import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import hashlib
import time

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
.small-note {
    font-size: 0.8rem;
    opacity: 0.7;
}
</style>
""", unsafe_allow_html=True)

# ---------------- FIREBASE INIT ----------------
if not firebase_admin._apps:
    cred = credentials.Certificate(dict(st.secrets["firebase"]))
    firebase_admin.initialize_app(cred)

db = firestore.client()

# ---------------- TIMELINE ----------------
UNLOCK_TIME = datetime(2026, 2, 6, 20, 0)  # 6th Feb night
now = datetime.now()

# ---------------- HELPERS ----------------
SCALE = ["No", "Slightly", "Maybe", "Mostly", "Yes", "Strongly yes"]

def scale_slider(label):
    val = st.select_slider(label, options=SCALE)
    return SCALE.index(val) + 1

def bin_map(x, a, b):
    return 0 if x == a else 1

def cosine(a, b):
    return cosine_similarity([a], [b])[0][0]

def fetch_users():
    return [doc.to_dict() for doc in db.collection("users").stream()]

def hash_email(email: str) -> str:
    return hashlib.sha256(email.lower().strip().encode()).hexdigest()

def get_chat_id(a, b):
    return "_".join(sorted([a, b]))

# ✅ FIXED countdown (uses st.rerun)
def render_countdown(target_time):
    remaining = int((target_time - datetime.now()).total_seconds())
    if remaining <= 0:
        return

    d, r = divmod(remaining, 86400)
    h, r = divmod(r, 3600)
    m, s = divmod(r, 60)

    st.markdown(
        f"""
        <div style="text-align:center; margin: 10px 0 25px 0;">
            <div style="font-size:1.1rem; opacity:0.85;">⏳ Matches reveal in</div>
            <div style="font-size:1.9rem; font-weight:700;">
                {d:02d}d {h:02d}h {m:02d}m {s:02d}s
            </div>
            <div style="font-size:0.85rem; opacity:0.7;">
                6th February, Night • Before Valentine’s Week
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    time.sleep(1)
    st.rerun()

# ---------------- HEADER ----------------
st.markdown("<div class='title'>NITeMatch 💘</div>", unsafe_allow_html=True)
st.caption("Anonymous psychological compatibility • Exclusive to NIT Jalandhar")

if now < UNLOCK_TIME:
    render_countdown(UNLOCK_TIME)

# ---------------- FORM MODE ----------------
if now < UNLOCK_TIME:

    with st.form("form"):
        alias = st.text_input("Choose an anonymous alias")
        email = st.text_input("Official NIT Jalandhar Email ID")

        st.markdown(
            "<p class='small-note'>"
            "This email is collected only to maintain exclusivity. "
            "It is stored in a secure, irreversible form and never shared."
            "</p>",
            unsafe_allow_html=True
        )

        gender = st.radio("I identify as", ["Male", "Female"])

        # Psychological
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
        q9 = st.radio("Music era you connect with most",
                      ["Before 2000", "2000–2009", "2010–2019", "2020–Present"])
        q10 = st.radio("Preferred music genre",
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
        q15 = st.radio("After a disagreement, you prefer",
                       ["Cool off first", "Talk it out"])

        instagram = st.text_input("Instagram (optional, without @)")
        consent = st.checkbox("Allow my Instagram to be shared with matches")
        message = st.text_area("Optional message for matches", max_chars=200)

        agree = st.checkbox("I confirm I am from NIT Jalandhar")
        submit = st.form_submit_button("Submit")

    if submit:
        if not alias.strip():
            st.error("Alias is required")
        elif not email.lower().endswith("@nitj.ac.in"):
            st.error("Please enter a valid NIT Jalandhar email")
        elif not agree:
            st.error("Please confirm eligibility")
        else:
            email_hash = hash_email(email)
            exists = db.collection("users").where("email_hash", "==", email_hash).get()

            if exists:
                st.warning("You have already submitted. Please wait till 6th February 💫")
            else:
                db.collection("users").add({
                    "alias": alias.strip(),
                    "email_hash": email_hash,
                    "gender": gender,
                    "answers": {
                        "psych": [q1, q2, q3, q4, q5,
                                  bin_map(q6, "Handling things alone", "Leaning on someone"),
                                  bin_map(q7, "Thinking quietly", "Talking it out"),
                                  q8],
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
                st.success("Response recorded. Matches will be revealed on 6th February at night 💘")

# ---------------- RESULTS MODE (WITH CHAT) ----------------
else:
    users = fetch_users()
    aliases = [u["alias"] for u in users]

    if not users:
        st.info("No participants yet.")
        st.stop()

    me = st.selectbox("Select your alias", aliases)
    me_u = users[aliases.index(me)]

    st.markdown("<div class='glass'>", unsafe_allow_html=True)
    st.caption("Your matches and private chats")

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
                f"Compatibility: <b>{round(score*100,2)}%</b>"
                f"<div class='why'>Why you matched:<br>"
                f"- Similar emotional approach<br>"
                f"- Shared interests<br>"
                f"- Similar decision style</div></div>",
                unsafe_allow_html=True
            )

            chat_id = get_chat_id(me, u["alias"])
            with st.expander("💬 Chat (text only)"):
                msgs_ref = db.collection("chats").document(chat_id).collection("messages")
                msgs = msgs_ref.order_by("timestamp").stream()

                for m in msgs:
                    d = m.to_dict()
                    sender = "You" if d["sender"] == me else u["alias"]
                    st.markdown(f"**{sender}:** {d['text']}")

                new_msg = st.text_input(f"Message {u['alias']}", key=f"msg_{chat_id}")
                if st.button("Send", key=f"send_{chat_id}") and new_msg.strip():
                    if len(new_msg) > 300:
                        st.warning("Message too long")
                    else:
                        msgs_ref.add({
                            "sender": me,
                            "text": new_msg.strip(),
                            "timestamp": datetime.utcnow()
                        })
                        st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)
