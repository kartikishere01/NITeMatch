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
import time

# ================= PAGE CONFIG =================
st.set_page_config(
    page_title="NITeMatch",
    page_icon="💘",
    layout="centered"
)

# ================= ENHANCED GLOBAL STYLES =================
def apply_styles(has_matches=False, is_countdown=False):
    """Apply dynamic styles based on match status and unlock state"""
    
    if has_matches:
        # 🌸 PINK GRADIENT THEME when matches are found! 💕
        background = """
        background:
            radial-gradient(circle at 15% 15%, rgba(236,72,153,0.35), transparent 40%),
            radial-gradient(circle at 85% 20%, rgba(192,132,252,0.30), transparent 45%),
            radial-gradient(circle at 50% 85%, rgba(251,113,133,0.32), transparent 50%),
            radial-gradient(circle at 10% 75%, rgba(244,114,182,0.25), transparent 45%),
            radial-gradient(circle at 90% 60%, rgba(217,70,239,0.28), transparent 40%),
            linear-gradient(135deg, #0f0514 0%, #1a0a1e 50%, #0f0514 100%);
    """
    elif is_countdown:
        # COUNTDOWN THEME - Mysterious and anticipatory
        background = """
        background:
            radial-gradient(circle at 20% 30%, rgba(139,92,246,0.3), transparent 50%),
            radial-gradient(circle at 80% 20%, rgba(236,72,153,0.25), transparent 55%),
            radial-gradient(circle at 50% 80%, rgba(59,130,246,0.28), transparent 50%),
            radial-gradient(circle at 15% 70%, rgba(168,85,247,0.22), transparent 45%),
            radial-gradient(circle at 85% 85%, rgba(244,114,182,0.20), transparent 40%),
            linear-gradient(135deg, #0a0118 0%, #1a0520 25%, #0f0628 50%, #1a0520 75%, #0a0118 100%);
    """
    else:
        # DEFAULT THEME - More aesthetic purples and cyans
        background = """
        background:
            radial-gradient(circle at 25% 25%, rgba(167,139,250,0.25), transparent 45%),
            radial-gradient(circle at 75% 15%, rgba(56,189,248,0.22), transparent 50%),
            radial-gradient(circle at 50% 75%, rgba(139,92,246,0.28), transparent 45%),
            radial-gradient(circle at 10% 60%, rgba(99,102,241,0.20), transparent 40%),
            linear-gradient(135deg, #0a0118 0%, #0f0820 50%, #0a0118 100%);
    """
    
    st.markdown(f"""
<style>
.stApp {{
    {background}
    color: white;
    transition: background 1.5s ease-in-out;
}}
.block-container {{ max-width: 820px; padding-top: 2rem; }}
.title {{
    font-size: 3.5rem;
    font-weight: 900;
    text-align: center;
    background: linear-gradient(90deg, #ff4fd8, #00ffe1, #ff4fd8);
    background-size: 200% auto;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    animation: gradient-shift 4s ease infinite;
    margin-bottom: 0.5rem;
}}

@keyframes gradient-shift {{
    0%, 100% {{ background-position: 0% center; }}
    50% {{ background-position: 100% center; }}
}}

.subtitle {{
    text-align: center;
    font-size: 1.1rem;
    opacity: 0.8;
    margin-bottom: 2rem;
    font-style: italic;
}}

.glass {{
    background: rgba(12,12,22,0.88);
    backdrop-filter: blur(18px);
    border-radius: 24px;
    padding: 28px;
    margin-bottom: 24px;
    border: 1px solid rgba(255,255,255,0.08);
    box-shadow: 0 8px 32px rgba(0,0,0,0.3);
}}

.countdown-box {{
    background: linear-gradient(135deg, rgba(139,92,246,0.2), rgba(236,72,153,0.2));
    backdrop-filter: blur(20px);
    border-radius: 28px;
    padding: 40px;
    margin: 30px 0;
    border: 2px solid rgba(255,255,255,0.15);
    box-shadow: 0 12px 40px rgba(139,92,246,0.3);
    text-align: center;
}}

.countdown-title {{
    font-size: 1.5rem;
    font-weight: 700;
    margin-bottom: 1.5rem;
    background: linear-gradient(90deg, #ec4899, #8b5cf6);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}}

.countdown-timer {{
    font-size: 3rem;
    font-weight: 900;
    margin: 20px 0;
    text-shadow: 0 0 20px rgba(139,92,246,0.5);
    animation: pulse-glow 2s ease-in-out infinite;
}}

@keyframes pulse-glow {{
    0%, 100% {{ 
        text-shadow: 0 0 20px rgba(139,92,246,0.5);
        transform: scale(1);
    }}
    50% {{ 
        text-shadow: 0 0 40px rgba(236,72,153,0.8), 0 0 60px rgba(139,92,246,0.6);
        transform: scale(1.05);
    }}
}}

.unlock-date {{
    font-size: 1.2rem;
    font-weight: 600;
    color: #00ffe1;
    margin-top: 1rem;
}}

.small-note {{ 
    font-size: 0.85rem; 
    opacity: 0.75;
    line-height: 1.6;
}}

/* Enhanced button styling */
.stButton button {{
    background: linear-gradient(135deg, rgba(255,79,216,0.3), rgba(0,255,225,0.3));
    border: 1px solid rgba(255,255,255,0.2);
    border-radius: 12px;
    color: white;
    font-weight: 600;
    transition: all 0.3s ease;
    padding: 0.6rem 1.5rem;
}}
.stButton button:hover {{
    background: linear-gradient(135deg, rgba(255,79,216,0.5), rgba(0,255,225,0.5));
    border: 1px solid rgba(255,255,255,0.4);
    transform: translateY(-2px);
    box-shadow: 0 8px 20px rgba(255,79,216,0.3);
}}

/* Clean dividers */
hr {{
    border: none;
    border-top: 1px solid rgba(255,255,255,0.1);
    margin: 1.5rem 0;
}}

/* Match celebration animations */
@keyframes pulse {{
    0%, 100% {{ opacity: 0.6; transform: scale(1); }}
    50% {{ opacity: 1; transform: scale(1.02); }}
}}

.match-glow {{
    animation: pulse 2s ease-in-out infinite;
}}

@keyframes heartbeat {{
    0%, 100% {{ transform: scale(1); }}
    25% {{ transform: scale(1.15); }}
    50% {{ transform: scale(1); }}
}}

.match-header {{
    font-size: 1.4rem;
    font-weight: 700;
    margin: 1.5rem 0 1rem;
    background: linear-gradient(90deg, #ff4fd8, #00ffe1);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    animation: heartbeat 1.5s ease-in-out;
}}

.match-card {{
    background: rgba(255,255,255,0.05);
    border-radius: 16px;
    padding: 20px;
    margin: 12px 0;
    border: 1px solid rgba(255,255,255,0.1);
    transition: all 0.3s ease;
}}
.match-card:hover {{
    background: rgba(255,255,255,0.08);
    border-color: rgba(255,79,216,0.4);
    transform: translateY(-2px);
}}

.section-header {{
    font-size: 1.15rem;
    font-weight: 700;
    margin: 1.5rem 0 1rem;
    padding-left: 0.5rem;
    border-left: 3px solid #ff4fd8;
}}

.info-box {{
    background: rgba(0,255,225,0.1);
    border: 1px solid rgba(0,255,225,0.3);
    border-radius: 12px;
    padding: 16px;
    margin: 12px 0;
}}

.success-box {{
    background: rgba(34,197,94,0.15);
    border: 1px solid rgba(34,197,94,0.3);
    border-radius: 12px;
    padding: 20px;
    margin: 16px 0;
}}

/* Chat interface styles */
.chat-message {{
    padding: 12px 16px;
    border-radius: 16px;
    margin: 8px 0;
    max-width: 75%;
    word-wrap: break-word;
}}

.chat-sent {{
    background: linear-gradient(135deg, rgba(255,79,216,0.25), rgba(236,72,153,0.25));
    margin-left: auto;
    border: 1px solid rgba(255,79,216,0.3);
}}

.chat-received {{
    background: rgba(255,255,255,0.08);
    margin-right: auto;
    border: 1px solid rgba(255,255,255,0.15);
}}

.chat-timestamp {{
    font-size: 0.75rem;
    opacity: 0.6;
    margin-top: 4px;
}}

.unread-badge {{
    background: #ff4fd8;
    color: white;
    padding: 2px 8px;
    border-radius: 12px;
    font-size: 0.8rem;
    font-weight: 700;
    margin-left: 8px;
}}

.chat-input-container {{
    position: sticky;
    bottom: 0;
    background: rgba(12,12,22,0.95);
    backdrop-filter: blur(10px);
    padding: 16px;
    border-top: 1px solid rgba(255,255,255,0.1);
    margin: 0 -28px -28px;
    border-radius: 0 0 24px 24px;
}}
</style>
""", unsafe_allow_html=True)

# ================= FIREBASE INITIALIZATION =================
if not firebase_admin._apps:
    cred = credentials.Certificate({
        "type": "service_account",
        "project_id": st.secrets["firebase"]["project_id"],
        "private_key_id": st.secrets["firebase"]["private_key_id"],
        "private_key": st.secrets["firebase"]["private_key"],
        "client_email": st.secrets["firebase"]["client_email"],
        "client_id": st.secrets["firebase"]["client_id"],
        "auth_uri": st.secrets["firebase"]["auth_uri"],
        "token_uri": st.secrets["firebase"]["token_uri"],
        "auth_provider_x509_cert_url": st.secrets["firebase"]["auth_provider_x509_cert_url"],
        "client_x509_cert_url": st.secrets["firebase"]["client_x509_cert_url"]
    })
    firebase_admin.initialize_app(cred)

db = firestore.client()

# ================= SESSION STATE INITIALIZATION =================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "current_user" not in st.session_state:
    st.session_state.current_user = None
if "active_chat" not in st.session_state:
    st.session_state.active_chat = None
if "all_users_cache" not in st.session_state:
    st.session_state.all_users_cache = None
if "all_users_cache_time" not in st.session_state:
    st.session_state.all_users_cache_time = None
if "computed_matches_cache" not in st.session_state:
    st.session_state.computed_matches_cache = {}
if "chat_messages_cache" not in st.session_state:
    st.session_state.chat_messages_cache = {}
if "unread_counts_cache" not in st.session_state:
    st.session_state.unread_counts_cache = {}

# ================= CONFIGURATION =================
SMTP_SERVER = st.secrets.get("smtp", {}).get("server", "smtp.gmail.com")
SMTP_PORT = st.secrets.get("smtp", {}).get("port", 587)
SMTP_EMAIL = st.secrets.get("smtp", {}).get("email", "")
SMTP_PASSWORD = st.secrets.get("smtp", {}).get("password", "")
BASE_URL = st.secrets.get("app", {}).get("base_url", "https://nitematch.streamlit.app")

# ================= HELPER FUNCTIONS =================
def hash_email(email):
    """Hash email for privacy"""
    return hashlib.sha256(email.lower().strip().encode()).hexdigest()

def bin_map(value, opt1, opt2):
    """Map binary question to 0 or 1"""
    return 0 if value == opt1 else 1

def pad_to_length(arr, target_length, fill_value=0):
    """
    CRITICAL FIX: Pad or truncate array to target length.
    This prevents dimension mismatch errors.
    """
    arr = list(arr)
    if len(arr) < target_length:
        arr.extend([fill_value] * (target_length - len(arr)))
    elif len(arr) > target_length:
        arr = arr[:target_length]
    return arr

# ================= OPTIMIZED FIRESTORE FUNCTIONS =================

def fetch_users():
    """Fetch all users with caching"""
    if st.session_state.all_users_cache is not None:
        return st.session_state.all_users_cache
    
    users_ref = db.collection("users")
    docs = users_ref.stream()
    
    users = []
    for doc in docs:
        data = doc.to_dict()
        data["id"] = doc.id
        users.append(data)
    
    st.session_state.all_users_cache = users
    st.session_state.all_users_cache_time = datetime.now(timezone.utc)
    
    return users

def invalidate_user_cache():
    """Invalidate user cache"""
    st.session_state.all_users_cache = None
    st.session_state.all_users_cache_time = None
    st.session_state.computed_matches_cache = {}

def fetch_user_by_email_hash(email_hash):
    """Fetch user by email hash using indexed query"""
    users_ref = db.collection("users")
    query = users_ref.where("email_hash", "==", email_hash).limit(1)
    docs = list(query.stream())
    
    if not docs:
        return None
    
    data = docs[0].to_dict()
    data["id"] = docs[0].id
    return data

def fetch_user_by_email_hash_and_alias(email_hash, alias):
    """Fetch user by email hash and alias using compound query"""
    users_ref = db.collection("users")
    query = users_ref.where("email_hash", "==", email_hash).where("alias", "==", alias).limit(1)
    docs = list(query.stream())
    
    if not docs:
        return None
    
    data = docs[0].to_dict()
    data["id"] = docs[0].id
    return data

def compute_matches(user, all_users):
    """
    FIXED: Compute matches with lenient validation (auto-fixes data).
    This prevents the "profile data incomplete" error.
    """
    user_id = user.get("id")
    
    # Check cache first
    if user_id in st.session_state.computed_matches_cache:
        return st.session_state.computed_matches_cache[user_id]
    
    # LENIENT FIX: Just check if answers exist, don't reject
    if "answers" not in user or "psych" not in user["answers"] or "interest" not in user["answers"]:
        st.session_state.computed_matches_cache[user_id] = []
        return []
    
    user_gender = user.get("gender")
    
    # LENIENT FIX: Auto-pad to expected lengths instead of rejecting
    user_psych_raw = user["answers"].get("psych", [])
    user_interest_raw = user["answers"].get("interest", [])
    
    user_psych = pad_to_length(user_psych_raw, 10, 3)  # Fill with middle value
    user_interest = pad_to_length(user_interest_raw, 5, 0)
    
    # Filter opposite gender
    opposite_gender = "Female" if user_gender == "Male" else "Male"
    candidates = [u for u in all_users if u.get("gender") == opposite_gender and u.get("id") != user_id]
    
    if not candidates:
        st.session_state.computed_matches_cache[user_id] = []
        return []
    
    # Calculate similarity scores
    scores = []
    for candidate in candidates:
        try:
            # LENIENT FIX: Skip validation, just check if data exists
            if "answers" not in candidate or "psych" not in candidate["answers"] or "interest" not in candidate["answers"]:
                continue
            
            # LENIENT FIX: Auto-pad candidate data too
            cand_psych_raw = candidate["answers"].get("psych", [])
            cand_interest_raw = candidate["answers"].get("interest", [])
            
            cand_psych = pad_to_length(cand_psych_raw, 10, 3)
            cand_interest = pad_to_length(cand_interest_raw, 5, 0)
            
            # Compute cosine similarity
            vec_user = np.array(user_psych + user_interest, dtype=float).reshape(1, -1)
            vec_cand = np.array(cand_psych + cand_interest, dtype=float).reshape(1, -1)
            
            score = cosine_similarity(vec_user, vec_cand)[0][0]
            scores.append((candidate, score))
            
        except Exception as e:
            # Silently skip problematic candidates
            continue
    
    scores.sort(key=lambda x: x[1], reverse=True)
    
    # Apply gender-based limits
    if user_gender == "Male":
        top_matches = scores[:3]
    else:
        top_matches = scores[:5]
    
    matches = [{"user": m[0], "score": m[1]} for m in top_matches]
    
    st.session_state.computed_matches_cache[user_id] = matches
    
    return matches

def get_or_create_chat(user1_id, user2_id):
    """Get or create chat with caching"""
    chat_id = "_".join(sorted([user1_id, user2_id]))
    
    cache_key = f"chat_exists_{chat_id}"
    if cache_key in st.session_state:
        return chat_id
    
    chat_ref = db.collection("chats").document(chat_id)
    chat_doc = chat_ref.get()
    
    if not chat_doc.exists:
        chat_ref.set({
            "participants": [user1_id, user2_id],
            "created_at": firestore.SERVER_TIMESTAMP,
            "last_message_at": firestore.SERVER_TIMESTAMP
        })
    
    st.session_state[cache_key] = True
    
    return chat_id

def fetch_messages(chat_id, force_refresh=False):
    """Fetch messages with caching"""
    if not force_refresh and chat_id in st.session_state.chat_messages_cache:
        return st.session_state.chat_messages_cache[chat_id]
    
    messages_ref = db.collection("chats").document(chat_id).collection("messages")
    messages_query = messages_ref.order_by("timestamp", direction=firestore.Query.ASCENDING)
    
    messages = []
    for doc in messages_query.stream():
        data = doc.to_dict()
        data["id"] = doc.id
        messages.append(data)
    
    st.session_state.chat_messages_cache[chat_id] = messages
    
    return messages

def send_message(chat_id, sender_id, text):
    """Send message and invalidate cache"""
    message_data = {
        "sender_id": sender_id,
        "text": text,
        "timestamp": firestore.SERVER_TIMESTAMP,
        "read": False
    }
    
    db.collection("chats").document(chat_id).collection("messages").add(message_data)
    
    db.collection("chats").document(chat_id).update({
        "last_message_at": firestore.SERVER_TIMESTAMP
    })
    
    if chat_id in st.session_state.chat_messages_cache:
        del st.session_state.chat_messages_cache[chat_id]
    
    st.session_state.unread_counts_cache = {}

def get_unread_count(chat_id, current_user_id):
    """Get count of unread messages for current user (no composite index needed)"""
    cache_key = f"{chat_id}_{current_user_id}"
    
    if cache_key in st.session_state.unread_counts_cache:
        return st.session_state.unread_counts_cache[cache_key]
    
    messages_ref = db.collection("chats").document(chat_id).collection("messages")
    
    # Query only unread messages (single-field index, usually auto-created)
    unread_query = messages_ref.where("read", "==", False)
    
    # Filter out current user's messages in Python (not in Firestore)
    unread_count = 0
    for msg in unread_query.stream():
        msg_data = msg.to_dict()
        if msg_data.get("sender_id") != current_user_id:
            unread_count += 1
    
    st.session_state.unread_counts_cache[cache_key] = unread_count
    
    return unread_count

def mark_messages_read(chat_id, current_user_id):
    """Mark messages as read in batch (no composite index needed)"""
    messages_ref = db.collection("chats").document(chat_id).collection("messages")
    
    # Query only unread messages (single-field index)
    unread_query = messages_ref.where("read", "==", False)
    
    batch = db.batch()
    for doc in unread_query.stream():
        # Filter out current user's messages in Python
        msg_data = doc.to_dict()
        if msg_data.get("sender_id") != current_user_id:
            batch.update(doc.reference, {"read": True})
    
    batch.commit()
    
    cache_key = f"{chat_id}_{current_user_id}"
    if cache_key in st.session_state.unread_counts_cache:
        del st.session_state.unread_counts_cache[cache_key]

# ================= MAGIC LINK FUNCTIONS =================
def create_magic_link(email_hash, email):
    """Generate a secure token and store in Firestore"""
    token = secrets.token_urlsafe(32)
    expiry = datetime.now(timezone.utc) + timedelta(hours=24)
    
    db.collection("magic_links").document(token).set({
        "email_hash": email_hash,
        "email": email,
        "created_at": firestore.SERVER_TIMESTAMP,
        "expires_at": expiry,
        "used": False
    })
    
    return token

def send_magic_link(email, token):
    """Send magic link via email using SMTP"""
    
    if not SMTP_EMAIL or not SMTP_PASSWORD:
        st.error("⚠️ Email not configured. Please set up SMTP credentials.")
        return False
    
    try:
        magic_link = f"{BASE_URL}/?token={token}"
        
        msg = MIMEMultipart('alternative')
        msg['Subject'] = "🔐 Your NITeMatch Login Link"
        msg['From'] = SMTP_EMAIL
        msg['To'] = email
        
        html = f"""
        <html>
        <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 0; background-color: #0a0118;">
            <table width="100%" cellpadding="0" cellspacing="0" style="background: linear-gradient(135deg, #0a0118 0%, #1a0520 50%, #0a0118 100%); padding: 40px 20px;">
                <tr>
                    <td align="center">
                        <table width="600" cellpadding="0" cellspacing="0" style="background: rgba(20,20,40,0.95); border-radius: 24px; overflow: hidden; border: 1px solid rgba(255,255,255,0.1);">
                            <tr>
                                <td style="padding: 40px; text-align: center;">
                                    <h1 style="margin: 0 0 10px 0; font-size: 2.5rem; background: linear-gradient(90deg, #ff4fd8, #00ffe1); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;">
                                        💘 NITeMatch
                                    </h1>
                                    <p style="margin: 0 0 30px 0; color: #a0a0a0; font-size: 1rem;">Your matches are waiting!</p>
                                    
                                    <div style="background: rgba(139,92,246,0.2); border-radius: 16px; padding: 30px; margin: 20px 0;">
                                        <p style="color: white; font-size: 1.1rem; margin: 0 0 20px 0;">
                                            Click the button below to access your account:
                                        </p>
                                        <a href="{magic_link}" style="display: inline-block; background: linear-gradient(135deg, #ff4fd8, #00ffe1); color: white; text-decoration: none; padding: 16px 40px; border-radius: 12px; font-weight: 600; font-size: 1.1rem; margin: 10px 0;">
                                            🔓 Login to NITeMatch
                                        </a>
                                    </div>
                                    
                                    <div style="background: rgba(255,255,255,0.05); border-radius: 12px; padding: 20px; margin: 20px 0;">
                                        <p style="color: #a0a0a0; font-size: 0.9rem; margin: 0;">
                                            🔒 This link expires in 24 hours<br>
                                            For security, don't share this link with anyone
                                        </p>
                                    </div>
                                    
                                    <p style="color: #707070; font-size: 0.85rem; margin: 30px 0 0 0; line-height: 1.6;">
                                        If you didn't request this login, you can safely ignore this email.<br>
                                        This is an automated message from NITeMatch.
                                    </p>
                                </td>
                            </tr>
                        </table>
                    </td>
                </tr>
            </table>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(html, 'html'))
        
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_EMAIL, SMTP_PASSWORD)
            server.send_message(msg)
        
        return True
        
    except Exception as e:
        st.error(f"Email error: {str(e)}")
        return False

def verify_magic_link(token):
    """Verify magic link token"""
    doc_ref = db.collection("magic_links").document(token)
    doc = doc_ref.get()
    
    if not doc.exists:
        return None
    
    data = doc.to_dict()
    
    if data.get("used"):
        return None
    
    expires_at = data.get("expires_at")
    if expires_at and datetime.now(timezone.utc) > expires_at:
        return None
    
    doc_ref.update({"used": True})
    
    user = fetch_user_by_email_hash(data.get("email_hash"))
    
    return user

# ================= COUNTDOWN & UNLOCK LOGIC =================
# FIXED: Use IST timezone like the working old code
IST = timezone(timedelta(hours=5, minutes=30))

# OPTION 1: For immediate unlock (testing)
# UNLOCK_TIME = datetime(2026, 2, 1, 0, 0, 0, tzinfo=IST)

# OPTION 2: For proper Feb 6, 8 PM IST unlock
UNLOCK_TIME = datetime(2026, 2, 6, 20, 0, 0, tzinfo=IST)

def is_unlocked():
    """Check if matches are unlocked"""
    return datetime.now(IST) >= UNLOCK_TIME

def get_countdown():
    """Get time remaining until unlock"""
    now = datetime.now(IST)
    if now >= UNLOCK_TIME:
        return None
    delta = UNLOCK_TIME - now
    days = delta.days
    hours, remainder = divmod(delta.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return {"days": days, "hours": hours, "minutes": minutes, "seconds": seconds}

# ================= MAGIC LINK AUTHENTICATION =================
query_params = st.query_params
if "token" in query_params and not st.session_state.logged_in:
    token = query_params["token"]
    user = verify_magic_link(token)
    
    if user:
        st.session_state.logged_in = True
        st.session_state.current_user = user
        st.success("✅ Login successful via magic link!")
        st.query_params.clear()
        st.rerun()
    else:
        st.error("❌ Invalid or expired magic link")
        st.query_params.clear()

# ================= LOGGED-IN STATE: SHOW MATCHES & CHAT =================
if st.session_state.logged_in and st.session_state.current_user:
    current_user = st.session_state.current_user
    
    all_users = fetch_users()
    matches = compute_matches(current_user, all_users)
    
    has_matches = len(matches) > 0
    apply_styles(has_matches=has_matches)
    
    st.markdown(f"""
    <div class="glass" style="text-align:center;">
        <div class="title">💘 NITeMatch</div>
        <div class="subtitle">Welcome back, {current_user.get('alias')}!</div>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("🚪 Logout"):
        st.session_state.logged_in = False
        st.session_state.current_user = None
        st.session_state.active_chat = None
        st.session_state.all_users_cache = None
        st.session_state.computed_matches_cache = {}
        st.session_state.chat_messages_cache = {}
        st.session_state.unread_counts_cache = {}
        st.rerun()
    
    if not matches:
        st.markdown("""
        <div class="glass" style="text-align:center;">
            <div style="font-size:3rem;margin-bottom:1rem;">😔</div>
            <div style="font-size:1.3rem;font-weight:600;margin-bottom:0.5rem;">No matches found</div>
            <div class="small-note">Try again later or check back for new registrations!</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        if st.session_state.active_chat is None:
            st.markdown(f"""
            <div class="match-header">
                🎉 Your Top {len(matches)} Match{"es" if len(matches) > 1 else ""}
            </div>
            """, unsafe_allow_html=True)
            
            for idx, match in enumerate(matches, 1):
                match_user = match["user"]
                score = match["score"]
                
                chat_id = get_or_create_chat(current_user["id"], match_user["id"])
                unread = get_unread_count(chat_id, current_user["id"])
                
                with st.container():
                    st.markdown(f"""
                    <div class="match-card">
                        <div style="display:flex;justify-content:space-between;align-items:center;">
                            <div>
                                <div style="font-size:1.2rem;font-weight:700;">Match #{idx}: {match_user.get('alias')}</div>
                                <div class="small-note">Compatibility: {score*100:.1f}%</div>
                            </div>
                            <div>
                                {"<span class='unread-badge'>" + str(unread) + " new</span>" if unread > 0 else ""}
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if match_user.get("match_message"):
                        st.markdown(f"""
                        <div class="match-card" style="margin-top:0.8rem;padding:10px;background:rgba(255,255,255,0.03);border-radius:8px;font-style:italic;">
                            "{match_user['match_message']}"
                        </div>
                        """, unsafe_allow_html=True)
                    
                    if match_user.get("share_instagram") and match_user.get("instagram"):
                        st.markdown(f"""
                        <div class="match-card" style="margin-top:0.5rem;padding:10px;">
                            📸 Instagram: <a href="https://instagram.com/{match_user['instagram'].replace('@','')}" 
                               style="color:#00ffe1;text-decoration:none;" target="_blank">
                               {match_user['instagram']}
                            </a>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    if st.button(f"💬 Chat with {match_user.get('alias')}", key=f"chat_{match_user['id']}"):
                        st.session_state.active_chat = {
                            "chat_id": chat_id,
                            "match_user": match_user
                        }
                        mark_messages_read(chat_id, current_user["id"])
                        st.rerun()
        
        else:
            active_chat = st.session_state.active_chat
            chat_id = active_chat["chat_id"]
            match_user = active_chat["match_user"]
            
            st.markdown(f"""
            <div class="glass">
                <div style="display:flex;justify-content:space-between;align-items:center;">
                    <div style="font-size:1.3rem;font-weight:700;">💬 Chat with {match_user.get('alias')}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("⬅️ Back to Matches"):
                st.session_state.active_chat = None
                st.rerun()
            
            messages = fetch_messages(chat_id)
            
            st.markdown('<div class="glass" style="max-height:500px;overflow-y:auto;">', unsafe_allow_html=True)
            
            if not messages:
                st.markdown("""
                <div style="text-align:center;padding:3rem;opacity:0.6;">
                    <div style="font-size:2rem;margin-bottom:1rem;">💬</div>
                    <div>No messages yet. Start the conversation!</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                for msg in messages:
                    is_sent = msg["sender_id"] == current_user["id"]
                    css_class = "chat-sent" if is_sent else "chat-received"
                    
                    ts = msg.get("timestamp")
                    if ts:
                        ts_str = ts.strftime("%b %d, %I:%M %p")
                    else:
                        ts_str = "Just now"
                    
                    st.markdown(f"""
                    <div class="chat-message {css_class}">
                        <div>{msg['text']}</div>
                        <div class="chat-timestamp">{ts_str}</div>
                    </div>
                    """, unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            st.markdown('<div class="chat-input-container">', unsafe_allow_html=True)
            with st.form("message_form", clear_on_submit=True):
                msg_text = st.text_input("Type a message...", key="msg_input", label_visibility="collapsed")
                send_btn = st.form_submit_button("📤 Send", use_container_width=True)
                
                if send_btn and msg_text.strip():
                    send_message(chat_id, current_user["id"], msg_text.strip())
                    st.rerun()
            
            st.markdown('</div>', unsafe_allow_html=True)

# ================= NOT LOGGED IN: SHOW COUNTDOWN OR LOGIN/REGISTER =================
elif not is_unlocked():
    apply_styles(is_countdown=True)
    
    st.markdown('<div class="title">💘 NITeMatch</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Find Your Perfect Match at NIT Jalandhar</div>', unsafe_allow_html=True)
    
    countdown = get_countdown()
    if countdown:
        st.markdown(f"""
        <div class="countdown-box">
            <div class="countdown-title">🎯 Matches Unlock In</div>
            <div class="countdown-timer">
                {countdown['days']}d {countdown['hours']}h {countdown['minutes']}m {countdown['seconds']}s
            </div>
            <div class="unlock-date">📅 February 6, 2026 at 8:00 PM IST</div>
            <div class="small-note" style="margin-top:1.5rem;">
                Register now to be matched when the countdown ends!
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="glass" style="text-align:center;">
        <div style="font-size:1.5rem;font-weight:700;margin-bottom:1rem;">
            📝 Register Now
        </div>
        <div class="small-note">
            Fill out the form below to get matched on Feb 6!
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    with st.form("registration_form"):
        st.markdown('<div class="section-header">👤 Basic Information</div>', unsafe_allow_html=True)
        
        alias = st.text_input("Choose an Alias", 
                              help="This is how your matches will see you",
                              placeholder="e.g., StarGazer, MusicLover")
        email = st.text_input("Your NIT Jalandhar Email", 
                              placeholder="yourname@nitj.ac.in")
        gender = st.radio("I identify as", ["Male", "Female"], horizontal=True)
        
        st.markdown("---")
        st.markdown('<div class="section-header">💭 About You</div>', unsafe_allow_html=True)
        
        q1 = st.slider("How introverted/extroverted are you?", 0, 10, 5, 
                       help="0 = Very Introverted, 10 = Very Extroverted")
        q2 = st.slider("How much do you value routine vs spontaneity?", 0, 10, 5,
                       help="0 = Love Routine, 10 = Love Spontaneity")
        q3 = st.slider("How important is alone time to you?", 0, 10, 5,
                       help="0 = Not Important, 10 = Very Important")
        q4 = st.slider("How much do you enjoy deep conversations?", 0, 10, 5,
                       help="0 = Prefer Light Talk, 10 = Love Deep Talks")
        q5 = st.slider("How organized are you?", 0, 10, 5,
                       help="0 = Very Disorganized, 10 = Very Organized")
        
        st.markdown("---")
        st.markdown('<div class="section-header">🤝 Relationship Style</div>', unsafe_allow_html=True)
        
        q6 = st.radio("When stressed, you prefer", 
                      ["Handling things alone", "Leaning on someone"], horizontal=True)
        q7 = st.radio("When making decisions, you rely more on", 
                      ["Thinking quietly", "Talking it out"], horizontal=True)
        q8 = st.slider("How much personal space do you need in relationships?", 0, 10, 5,
                       help="0 = Very Little, 10 = A Lot")
        q9 = st.radio("If your partner needs you during your busy time", 
                      ["Drop everything for them", "Ask to catch up later"], horizontal=True)
        q10 = st.radio("After a disagreement, you prefer", 
                       ["Talk it out immediately", "Take time to cool off"], horizontal=True)
        
        st.markdown("---")
        st.markdown('<div class="section-header">🎵 Interests & Preferences</div>', unsafe_allow_html=True)
        
        music_era = st.radio("Music era you connect with most", 
            ["Before 2000", "2000–2009", "2010–2019", "2020–Present"], horizontal=True)
        music_genre = st.radio("Preferred music genre",
            ["Pop", "Rock", "Hip-hop / Rap", "EDM", "Metal", "Classical", "Indie"], horizontal=True)
        travel = st.radio("You would rather go to", ["Beaches", "Mountains"], horizontal=True)
        movies = st.radio("Movies you enjoy the most",
            ["Romance / Drama", "Thriller / Mystery", "Comedy", "Action / Sci-Fi"], horizontal=True)
        hangout = st.radio("Your go-to hangout spot",
            ["Nescafe near Verka", "Nescafe near MBH", "Night Canteen", "Snackers", 
             "Dominos", "Yadav Canteen", "Rimjhim Area", "Campus Cafe"], horizontal=False)
        
        st.markdown("---")
        st.markdown('<div class="section-header">📱 Optional Information</div>', unsafe_allow_html=True)
        
        instagram = st.text_input("Instagram (optional)", placeholder="@username")
        share_instagram = st.checkbox("✓ Allow my Instagram to be shared with matches")
        
        match_message = st.text_area("Optional message for matches", 
                                      placeholder="A fun fact or message your matches will see...",
                                      max_chars=200, height=80)
        
        st.markdown("---")
        
        confirm_nitj = st.checkbox("✓ I confirm I am from NIT Jalandhar")
        
        submitted = st.form_submit_button("🚀 Submit My Profile", use_container_width=True)
        
        if submitted:
            if not alias or not email:
                st.error("❌ Please fill in all required fields")
            elif not email.endswith("@nitj.ac.in"):
                st.error("❌ Please use your official NIT Jalandhar email (@nitj.ac.in)")
            elif not confirm_nitj:
                st.error("❌ Please confirm you are from NIT Jalandhar")
            else:
                q6_val = bin_map(q6, "Handling things alone", "Leaning on someone")
                q7_val = bin_map(q7, "Thinking quietly", "Talking it out")
                q9_val = bin_map(q9, "Drop everything for them", "Ask to catch up later")
                q10_val = bin_map(q10, "Talk it out immediately", "Take time to cool off")
                
                music_era_val = ["Before 2000", "2000–2009", "2010–2019", "2020–Present"].index(music_era)
                music_genre_val = ["Pop", "Rock", "Hip-hop / Rap", "EDM", "Metal", "Classical", "Indie"].index(music_genre)
                travel_val = 0 if travel == "Beaches" else 1
                movies_val = ["Romance / Drama", "Thriller / Mystery", "Comedy", "Action / Sci-Fi"].index(movies)
                hangout_val = ["Nescafe near Verka", "Nescafe near MBH", "Night Canteen", "Snackers", 
                               "Dominos", "Yadav Canteen", "Rimjhim Area", "Campus Cafe"].index(hangout)
                
                email_hash_val = hash_email(email)
                
                user_data = {
                    "alias": alias,
                    "email_hash": email_hash_val,
                    "gender": gender,
                    "answers": {
                        "psych": [q1, q2, q3, q4, q5, q6_val, q7_val, q8, q9_val, q10_val],
                        "interest": [music_era_val, music_genre_val, travel_val, movies_val, hangout_val]
                    },
                    "instagram": instagram.strip() if instagram else "",
                    "share_instagram": share_instagram,
                    "match_message": match_message.strip() if match_message else "",
                    "created_at": firestore.SERVER_TIMESTAMP
                }
                
                db.collection("users").add(user_data)
                
                invalidate_user_cache()
                
                st.success("✅ Registration successful!")
                st.balloons()
                
                st.markdown("""
                <div class="success-box" style="margin-top:1rem;">
                    <div style="text-align:center;">
                        <div style="font-size:1.2rem;margin-bottom:0.5rem;">🎉 You're all set!</div>
                        <div style="margin-bottom:0.8rem;">Come back on <strong>Feb 6, 8 PM IST</strong> to login and see your matches</div>
                        <div style="font-size:0.9rem;opacity:0.85;margin-top:1rem;padding:1rem;background:rgba(255,255,255,0.05);border-radius:8px;">
                            <strong>How to login after unlock:</strong><br>
                            Option 1: Use your <strong>alias as username</strong> and <strong>email as password</strong><br>
                            Option 2: Request a <strong>magic login link</strong> sent to your email
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

# ================= AFTER UNLOCK - LOGIN SECTION =================
else:
    apply_styles()
    
    st.markdown("""
    <div class="glass" style="text-align:center;">
        <div style="font-size:2rem;margin-bottom:1rem;">🎉</div>
        <div style="font-size:1.5rem;font-weight:700;margin-bottom:1rem;">Matches Are Live!</div>
        <div class="small-note">Choose your preferred login method below</div>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="glass" style="text-align:center;padding:20px;">
            <div style="font-size:1.2rem;font-weight:700;margin-bottom:1rem;background:linear-gradient(90deg,#ff4fd8,#00ffe1);-webkit-background-clip:text;-webkit-text-fill-color:transparent;">
                Option 1: Direct Login
            </div>
            <div style="font-size:0.9rem;opacity:0.8;margin-bottom:1rem;">Login with your alias and email</div>
        </div>
        """, unsafe_allow_html=True)
        
        with st.form("direct_login_form"):
            login_alias = st.text_input("Your Alias", placeholder="Enter your alias")
            login_email = st.text_input("Your Email", placeholder="yourname@nitj.ac.in")
            direct_login_btn = st.form_submit_button("🚀 Login", use_container_width=True)
            
            if direct_login_btn:
                if not login_alias or not login_email:
                    st.error("❌ Please fill in both fields")
                elif not login_email.endswith("@nitj.ac.in"):
                    st.error("❌ Please use your official NIT Jalandhar email")
                else:
                    login_hash = hash_email(login_email)
                    
                    user = fetch_user_by_email_hash_and_alias(login_hash, login_alias)
                    
                    if not user:
                        st.error("❌ Invalid alias or email. Please check your credentials.")
                    else:
                        st.session_state.logged_in = True
                        st.session_state.current_user = user
                        st.success("✅ Login successful! Loading your matches...")
                        st.rerun()
    
    with col2:
        st.markdown("""
        <div class="glass" style="text-align:center;padding:20px;">
            <div style="font-size:1.2rem;font-weight:700;margin-bottom:1rem;background:linear-gradient(90deg,#ff4fd8,#00ffe1);-webkit-background-clip:text;-webkit-text-fill-color:transparent;">
                Option 2: Magic Link
            </div>
            <div style="font-size:0.9rem;opacity:0.8;margin-bottom:1rem;">Get a login link via email</div>
        </div>
        """, unsafe_allow_html=True)
        
        with st.form("magic_link_form"):
            magic_email = st.text_input("Your Email", placeholder="yourname@nitj.ac.in", key="magic_email")
            magic_link_btn = st.form_submit_button("📧 Send Login Link", use_container_width=True)
            
            if magic_link_btn:
                if not magic_email.endswith("@nitj.ac.in"):
                    st.error("❌ Please use your official NIT Jalandhar email")
                else:
                    magic_hash = hash_email(magic_email)
                    
                    user = fetch_user_by_email_hash(magic_hash)
                    
                    if not user:
                        st.error("❌ No account found with this email.")
                    else:
                        token = create_magic_link(magic_hash, magic_email)
                        
                        if send_magic_link(magic_email, token):
                            st.success("✅ Login link sent to your email!")
                            st.markdown("""
                            <div class="info-box" style="margin-top:1rem;">
                                <div style="text-align:center;font-size:0.9rem;">
                                    📧 Check your inbox and click the link to login<br>
                                    <span class="small-note">Link expires in 24 hours</span>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                        else:
                            st.error("❌ Failed to send email. Please try again.")
