import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import hashlib

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
UNLOCK_TIME = datetime(2026, 2, 6, 20, 0)

# ---------------- HELPERS ----------------
SCALE = ["No", "Slightly", "Maybe", "Mostly", "Yes", "Strongly yes"]

def scale_slider(label):
    val = st.select_slider(label, options=SCALE)
    return SCALE.index(val) + 1

def bin_map(x, a, b):
    return 0 if x == a else 1

def cosine(a, b):
    return cosine_similarity([a], [b])[0][0]

def hash_text(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()

def fetch_users():
    return [doc.to_dict() for doc in db.collection("users").stream()]

def get_chat_id(a, b):
    return "_".join(sorted([a, b]))

# ---------------- HEADER ----------------
st.markdown("<div class='title'>NITeMatch 💘</div>", unsafe_allow_html=True)
st.caption("Anonymous psychological compatibility • Exclusive to NIT Jalandhar")

# ================= FORM MODE =================
if datetime.now() < UNLOCK_TIME:

    st.markdown("### Community Guidelines")
    st.markdown("""
    • Be respectful and honest  
    • No abusive or inappropriate language  
    • One account per student  
    """)

    with st.form("form"):
        username = st.text_input("Create a username (this will be shown to your match)")
        password = st.text_input("Create a password", type="password")
        email = st.text_input("Official NIT Jalandhar Email ID")

        st.markdown(
            "<p class='small-note'>Email is used only to ensure exclusivity. "
            "It will never be shown or used for chat.</p>",
            unsafe_allow_html=True
        )

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

        message = st.text_area("Optional message for your match", max_chars=200)
        agree = st.checkbox("I confirm I am from NIT Jalandhar")
        submit = st.form_submit_button("Submit")

    if submit:
        if not username or not password:
            st.error("Username and password are required")
        elif not email.lower().endswith("@nitj.ac.in"):
            st.error("Please use your official NIT Jalandhar email")
        elif not agree:
            st.error("Please confirm eligibility")
        else:
            email_hash = hash_text(email.lower())
            password_hash = hash_text(password)

            if db.collection("users").where("email_hash", "==", email_hash).get():
                st.warning("You have already submitted. Please wait till 6th February 💫")
            else:
                db.collection("users").add({
                    "username": username,
                    "password_hash": password_hash,
                    "email_hash": email_hash,
                    "gender": gender,
                    "answers": {
                        "psych": [q1, q2, q3, q4, q5,
                                  bin_map(q6, "Handling things alone", "Leaning on someone"),
                                  bin_map(q7, "Thinking quietly", "Talking it out"),
                                  q8]
                    },
                    "message": message.strip()
                })
                st.success("Response recorded. Save your username & password. 💘")

# ================= RESULTS MODE =================
else:
    st.markdown("### Login to view your matches")

    login_user = st.text_input("Username")
    login_pass = st.text_input("Password", type="password")

    if st.button("Login"):
        users = fetch_users()
        me = None

        for u in users:
            if u["username"] == login_user and u["password_hash"] == hash_text(login_pass):
                me = u
                break

        if not me:
            st.error("Invalid username or password")
            st.stop()

        st.success("Login successful")
        st.markdown("<div class='glass'>", unsafe_allow_html=True)

        for u in users:
            if u["username"] == me["username"] or u["gender"] == me["gender"]:
                continue

            ps = cosine(me["answers"]["psych"], u["answers"]["psych"])
            score = ps  # psychology-only for now

            if score > 0.75:
                st.markdown(
                    f"<div class='match'><b>{u['username']}</b><br>"
                    f"Compatibility: <b>{round(score*100,2)}%</b></div>",
                    unsafe_allow_html=True
                )

                with st.expander("💬 Chat"):
                    chat_ref = db.collection("chats").document(
                        get_chat_id(me["username"], u["username"])
                    ).collection("messages")

                    for m in chat_ref.order_by("timestamp").stream():
                        d = m.to_dict()
                        sender = "You" if d["sender"] == me["username"] else u["username"]
                        st.markdown(f"**{sender}:** {d['text']}")

                    msg = st.text_input("Message", key=u["username"])
                    if st.button("Send", key=f"send_{u['username']}") and msg.strip():
                        chat_ref.add({
                            "sender": me["username"],
                            "text": msg.strip(),
                            "timestamp": datetime.utcnow()
                        })
                        st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)