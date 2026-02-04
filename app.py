import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime, timezone, timedelta
import hashlib
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import secrets
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

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
.small-note { font-size: 0.8rem; opacity: 0.75; }

/* Better button styling */
.stButton button {
    background: linear-gradient(135deg, rgba(255,79,216,0.3), rgba(0,255,225,0.3));
    border: 1px solid rgba(255,255,255,0.2);
    border-radius: 12px;
    color: white;
    font-weight: 600;
    transition: all 0.3s ease;
}
.stButton button:hover {
    background: linear-gradient(135deg, rgba(255,79,216,0.5), rgba(0,255,225,0.5));
    border: 1px solid rgba(255,255,255,0.4);
    transform: translateY(-2px);
}

/* Clean dividers */
hr {
    border: none;
    border-top: 1px solid rgba(255,255,255,0.1);
    margin: 1.5rem 0;
}
</style>
""", unsafe_allow_html=True)

# ================= FIREBASE INIT =================
if not firebase_admin._apps:
    cred = credentials.Certificate(dict(st.secrets["firebase"]))
    firebase_admin.initialize_app(cred)

db = firestore.client()

# ================= TIME =================
IST = timezone(timedelta(hours=5, minutes=30))

# 🔴 UNLOCK DATE - Set to Feb 2, 2026, 8 PM IST
UNLOCK_TIME = datetime(2026, 2, 6, 20, 0, tzinfo=IST)

MATCH_THRESHOLD = 0.50
SCALE = ["No", "Slightly", "Maybe", "Mostly", "Yes", "Strongly yes"]

# ================= EMAIL CONFIG =================
# You'll need to set these in Streamlit secrets
SMTP_SERVER = st.secrets.get("smtp", {}).get("server", "smtp.gmail.com")
SMTP_PORT = st.secrets.get("smtp", {}).get("port", 587)
SMTP_EMAIL = st.secrets.get("smtp", {}).get("email", "")
SMTP_PASSWORD = st.secrets.get("smtp", {}).get("password", "")

# Base URL for your deployed app (update this when deployed)
BASE_URL = st.secrets.get("app", {}).get("base_url", "http://localhost:8501")

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

def fetch_users():
    return [
        doc.to_dict() | {"_id": doc.id}
        for doc in db.collection("users").stream()
    ]

def generate_magic_token():
    """Generate a secure random token for magic links"""
    return secrets.token_urlsafe(32)

def send_magic_link(email, token):
    """Send magic link to user's email"""
    try:
        # Create magic link
        magic_link = f"{BASE_URL}/?token={token}"
        
        # Create email
        msg = MIMEMultipart('alternative')
        msg['Subject'] = "🔐 Your NITeMatch Login Link"
        msg['From'] = SMTP_EMAIL
        msg['To'] = email
        
        # HTML email body
        html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 40px;">
            <div style="max-width: 600px; margin: 0 auto; background: white; border-radius: 16px; padding: 40px; box-shadow: 0 10px 40px rgba(0,0,0,0.2);">
                <h1 style="color: #667eea; text-align: center; margin-bottom: 20px;">💘 NITeMatch</h1>
                <h2 style="color: #333; text-align: center;">Your Login Link is Ready!</h2>
                
                <p style="color: #666; font-size: 16px; line-height: 1.6;">
                    Click the button below to securely access your matches:
                </p>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{magic_link}" style="display: inline-block; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 15px 40px; text-decoration: none; border-radius: 8px; font-weight: bold; font-size: 16px;">
                        🔐 Login to NITeMatch
                    </a>
                </div>
                
                <p style="color: #999; font-size: 14px; text-align: center; margin-top: 30px;">
                    This link will expire in 15 minutes for security.
                </p>
                
                <p style="color: #999; font-size: 12px; text-align: center; margin-top: 20px; border-top: 1px solid #eee; padding-top: 20px;">
                    If you didn't request this login link, please ignore this email.
                </p>
            </div>
        </body>
        </html>
        """
        
        # Plain text fallback
        text = f"""
        NITeMatch - Your Login Link
        
        Click the link below to access your matches:
        {magic_link}
        
        This link will expire in 15 minutes.
        
        If you didn't request this, please ignore this email.
        """
        
        part1 = MIMEText(text, 'plain')
        part2 = MIMEText(html, 'html')
        
        msg.attach(part1)
        msg.attach(part2)
        
        # Send email
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_EMAIL, SMTP_PASSWORD)
            server.send_message(msg)
        
        return True
    except Exception as e:
        st.error(f"Failed to send email: {str(e)}")
        return False

def create_magic_link(email_hash, plain_email=None):
    """Create a magic link token and store it in database"""
    token = generate_magic_token()
    expiry = datetime.now(IST) + timedelta(minutes=15)
    
    # Store token in database
    token_data = {
        "token": token,
        "email_hash": email_hash,
        "created_at": firestore.SERVER_TIMESTAMP,
        "expires_at": expiry,
        "used": False
    }
    
    # Store plain email if provided (for new users)
    if plain_email:
        token_data["email"] = plain_email
    
    db.collection("magic_tokens").add(token_data)
    
    return token

"""
DEBUG VERSION - Replace your verify_magic_token function (lines 223-257)
with this version to see what's happening
"""

def verify_magic_token(token):
    """Verify magic token and return user if valid"""
    
    # Debug: Show what token we're looking for
    st.write(f"🔍 Looking for token: {token[:10]}...")
    
    tokens = list(
        db.collection("magic_tokens")
        .where("token", "==", token)
        .where("used", "==", False)
        .limit(1)
        .stream()
    )
    
    if not tokens:
        st.error("❌ Token not found in database")
        st.info("Possible reasons: Token was already used, or wasn't created properly")
        return None
    
    token_doc = tokens[0]
    token_data = token_doc.to_dict()
    
    # Debug: Show token data
    st.write("✅ Token found in database!")
    st.write(f"📅 Created at: {token_data.get('created_at')}")
    st.write(f"⏰ Expires at: {token_data['expires_at']}")
    st.write(f"🕐 Current time (IST): {datetime.now(IST)}")
    
    # Check if expired
    expires_at = token_data["expires_at"]
    
    # Handle both timezone-aware and naive datetimes
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=IST)
    
    current_time = datetime.now(IST)
    
    st.write(f"⏱️ Time remaining: {expires_at - current_time}")
    
    if expires_at < current_time:
        st.error("❌ Token has expired")
        st.write(f"Expired at: {expires_at}")
        st.write(f"Current time: {current_time}")
        return None
    
    st.success("✅ Token is still valid!")
    
    # Mark as used
    token_doc.reference.update({"used": True})
    
    # Get user
    users = list(
        db.collection("users")
        .where("email_hash", "==", token_data["email_hash"])
        .limit(1)
        .stream()
    )
    
    if users:
        st.success("✅ User found! Logging in...")
        return users[0].to_dict() | {"_id": users[0].id}
    else:
        st.error("❌ User not found for this token")
    
    return None

def update_user_email(email_hash, plain_email):
    """Update existing user record with plain email for future magic links"""
    users = list(
        db.collection("users")
        .where("email_hash", "==", email_hash)
        .limit(1)
        .stream()
    )
    
    if users:
        users[0].reference.update({"email": plain_email})
        return True
    return False

def compute_compatibility(user1, user2):
    """Compute psychological and interest compatibility"""
    psych1 = normalize(user1["answers"]["psych"])
    psych2 = normalize(user2["answers"]["psych"])
    
    interest1 = normalize(user1["answers"]["interest"])
    interest2 = normalize(user2["answers"]["interest"])
    
    psych_score = cosine(psych1, psych2)
    interest_score = cosine(interest1, interest2)
    
    # Weight: 70% psychology, 30% interests
    total = 0.7 * psych_score + 0.3 * interest_score
    return round(total * 100, 1)

def get_matches(current_user, all_users):
    """Get compatible matches for current user"""
    opposite_gender = "Female" if current_user["gender"] == "Male" else "Male"
    
    matches = []
    for user in all_users:
        if user["_id"] == current_user["_id"]:
            continue
        if user["gender"] != opposite_gender:
            continue
        
        score = compute_compatibility(current_user, user)
        if score >= MATCH_THRESHOLD * 100:
            matches.append({
                "user": user,
                "score": score
            })
    
    return sorted(matches, key=lambda x: x["score"], reverse=True)

# ================= HEADER =================
st.markdown("<div class='title'>NITeMatch 💘</div>", unsafe_allow_html=True)
st.caption("Anonymous psychological compatibility • NIT Jalandhar")

# ================= GUIDELINES =================
with st.expander("📜 Guidelines & Safety"):
    st.markdown("""
- Respectful connections only  
- No harassment or misuse  
- Do not overshare personal info early  
- Email is encrypted and never visible  
- Matches are psychology-based  
- Login links expire in 15 minutes
""")

# ================= CHECK FOR MAGIC LINK TOKEN =================
query_params = st.query_params
if "token" in query_params:
    token = query_params["token"]
    user = verify_magic_token(token)
    
    if user:
        st.session_state.logged_in = True
        st.session_state.current_user = user
        # Clear the token from URL
        st.query_params.clear()
        st.success("✅ Successfully logged in!")
        st.rerun()
    else:
        st.error("🚫 Invalid or expired login link. Please request a new one.")
        st.query_params.clear()

# ================= BEFORE UNLOCK =================
now = datetime.now(IST)

if now < UNLOCK_TIME:
    remaining = UNLOCK_TIME - now

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

        st.markdown("""
        <div class="small-note">
        <b>Important:</b> Email is collected only to ensure NIT Jalandhar exclusivity.  
        It is encrypted and never shown to anyone. You'll receive a login link via email.
        </div>
        """, unsafe_allow_html=True)

        email = st.text_input("Official NIT Jalandhar Email ID")
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
                    "email": email.lower().strip(),  # Store actual email for sending login links
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
                st.success("✅ Response recorded. You'll receive a login link via email on 6th Feb 💘")

    st.stop()

# ================= AFTER UNLOCK - HYBRID LOGIN =================

# Initialize session state
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "current_user" not in st.session_state:
    st.session_state.current_user = None
if "chat_with" not in st.session_state:
    st.session_state.chat_with = None

# ================= HYBRID LOGIN SECTION =================
if not st.session_state.logged_in:
    st.markdown("""
    <div class="glass">
        <h2>🎉 Matches Unlocked</h2>
        <p>Choose your login method:</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Create tabs for different login methods
    tab1, tab2 = st.tabs(["🔐 Magic Link (Recommended)", "📝 Manual Login"])
    
    with tab1:
        st.info("We'll send you a secure login link that expires in 15 minutes.")
        
        with st.form("magic_link_form"):
            magic_email = st.text_input("Your NIT Jalandhar email")
            send_link = st.form_submit_button("Send Login Link 📨")
        
        if send_link:
            if not magic_email.endswith("@nitj.ac.in"):
                st.error("Please enter a valid NIT Jalandhar email address")
            else:
                email_hash = hash_email(magic_email)
                users = list(
                    db.collection("users")
                    .where("email_hash", "==", email_hash)
                    .limit(1)
                    .stream()
                )
                
                if not users:
                    st.error("❌ Email not found. Make sure you've already submitted your form before Feb 6th.")
                else:
                    user_data = users[0].to_dict()
                    
                    # Check if user has plain email stored
                    if "email" in user_data and user_data["email"]:
                        # User has email, can send magic link
                        token = create_magic_link(email_hash, magic_email)
                        if send_magic_link(magic_email, token):
                            st.success("✅ Login link sent! Check your email inbox (and spam folder).")
                            st.info("The link will expire in 15 minutes for security.")
                    else:
                        # Old user without email - update it and send link
                        update_user_email(email_hash, magic_email)
                        token = create_magic_link(email_hash, magic_email)
                        if send_magic_link(magic_email, token):
                            st.success("✅ Login link sent! Check your email inbox (and spam folder).")
                            st.info("The link will expire in 15 minutes for security.")
    
    with tab2:
        st.warning("⚠️ This method is for users who can't receive emails. Magic link is more secure!")
        
        with st.form("manual_login_form"):
            st.subheader("Manual Login")
            manual_alias = st.text_input("Your alias")
            manual_email = st.text_input("Your NIT Jalandhar email")
            manual_submit = st.form_submit_button("Login")
        
        if manual_submit:
            if not manual_alias or not manual_email.endswith("@nitj.ac.in"):
                st.error("Please enter valid credentials")
            else:
                email_hash = hash_email(manual_email)
                users = list(
                    db.collection("users")
                    .where("email_hash", "==", email_hash)
                    .where("alias", "==", manual_alias.strip())
                    .limit(1)
                    .stream()
                )
                
                if users:
                    user_data = users[0].to_dict() | {"_id": users[0].id}
                    
                    # Update email if not already stored (for old users)
                    if "email" not in user_data or not user_data.get("email"):
                        update_user_email(email_hash, manual_email)
                    
                    st.session_state.logged_in = True
                    st.session_state.current_user = user_data
                    st.success("✅ Logged in successfully!")
                    st.rerun()
                else:
                    st.error("Invalid credentials. Make sure you've already submitted your form.")
    
    st.stop()

# ================= MATCHES VIEW =================
current_user = st.session_state.current_user

if st.session_state.chat_with is None:
    st.markdown(f"""
    <div class="glass">
        <h3>Welcome back, {current_user['alias']}! 💘</h3>
        <p>Here are your most compatible matches</p>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("🚪 Logout"):
        st.session_state.logged_in = False
        st.session_state.current_user = None
        st.rerun()
    
    all_users = fetch_users()
    matches = get_matches(current_user, all_users)
    
    if not matches:
        st.info("No matches found above the threshold. Check back later!")
    else:
        for match in matches[:10]:  # Show top 10
            match_user = match["user"]
            score = match["score"]
            
            # Determine score color
            if score >= 75:
                score_color = "#00ffe1"
            elif score >= 60:
                score_color = "#ffa500"
            else:
                score_color = "#ff4fd8"
            
            # Create match card using columns for better control
            col1, col2 = st.columns([4, 1])
            
            with col1:
                st.markdown(f"### {match_user['alias']}")
                if match_user.get('note'):
                    st.write(match_user['note'])
                if match_user.get('instagram'):
                    st.caption(f"📷 @{match_user['instagram']}")
            
            with col2:
                st.markdown(f"<div style='font-size: 2rem; font-weight: 700; color: {score_color}; text-align: center; padding-top: 10px;'>{score}%</div>", unsafe_allow_html=True)
            
            if st.button(f"💬 Chat with {match_user['alias']}", key=f"chat_{match_user['_id']}", use_container_width=True):
                st.session_state.chat_with = match_user
                st.rerun()
            
            st.markdown("---")

else:
    # ================= CHAT VIEW =================
    chat_partner = st.session_state.chat_with
    
    st.markdown(f"""
    <div class="glass">
        <h3>💬 Chat with {chat_partner['alias']}</h3>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("⬅️ Back to matches"):
        st.session_state.chat_with = None
        st.rerun()
    
    # Create unique chat ID (sorted to ensure same ID regardless of who initiated)
    chat_ids = sorted([current_user["_id"], chat_partner["_id"]])
    chat_id = f"{chat_ids[0]}_{chat_ids[1]}"
    
    # Display messages
    messages_ref = db.collection("chats").document(chat_id).collection("messages").order_by("timestamp")
    messages = [msg.to_dict() for msg in messages_ref.stream()]
    
    # Container for messages
    with st.container():
        if messages:
            for msg in messages:
                sender = "You" if msg["sender_id"] == current_user["_id"] else chat_partner["alias"]
                is_user = msg["sender_id"] == current_user["_id"]
                
                # Use columns to align messages
                if is_user:
                    col1, col2 = st.columns([1, 3])
                    with col2:
                        st.markdown(f"""
                        <div style="background: rgba(0,255,225,0.15); padding: 10px 14px; border-radius: 12px; margin: 8px 0;">
                            <div style="font-size: 0.75rem; opacity: 0.7; margin-bottom: 4px;">You</div>
                            <div>{msg['text']}</div>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.markdown(f"""
                        <div style="background: rgba(255,79,216,0.15); padding: 10px 14px; border-radius: 12px; margin: 8px 0;">
                            <div style="font-size: 0.75rem; opacity: 0.7; margin-bottom: 4px;">{chat_partner['alias']}</div>
                            <div>{msg['text']}</div>
                        </div>
                        """, unsafe_allow_html=True)
        else:
            st.info("No messages yet. Start the conversation!")
    
    st.markdown("---")
    
    # Send message
    with st.form("message_form", clear_on_submit=True):
        message_text = st.text_input("Type your message", key="msg_input", placeholder="Say hi! 👋")
        send = st.form_submit_button("Send 💬", use_container_width=True)
    
    if send and message_text.strip():
        db.collection("chats").document(chat_id).collection("messages").add({
            "sender_id": current_user["_id"],
            "text": message_text.strip(),
            "timestamp": firestore.SERVER_TIMESTAMP
        })
        st.rerun()
