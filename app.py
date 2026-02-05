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
    10%, 30% {{ transform: scale(1.15); }}
    20%, 40% {{ transform: scale(1); }}
}}

.heart-beat {{
    animation: heartbeat 1.5s ease-in-out infinite;
    display: inline-block;
}}

/* Floating hearts animation */
@keyframes float-heart {{
    0% {{
        transform: translateY(0) rotate(0deg);
        opacity: 1;
    }}
    100% {{
        transform: translateY(-100px) rotate(15deg);
        opacity: 0;
    }}
}}

.floating-heart {{
    animation: float-heart 3s ease-in-out infinite;
    position: absolute;
}}

/* Enhanced form styling */
.stTextInput input, .stTextArea textarea {{
    background: rgba(255,255,255,0.05) !important;
    border: 1px solid rgba(255,255,255,0.15) !important;
    border-radius: 10px !important;
    color: white !important;
    transition: all 0.3s ease !important;
}}

.stTextInput input:focus, .stTextArea textarea:focus {{
    background: rgba(255,255,255,0.08) !important;
    border: 1px solid rgba(0,255,225,0.4) !important;
    box-shadow: 0 0 15px rgba(0,255,225,0.2) !important;
}}

/* Radio button enhancement */
.stRadio > label {{
    font-weight: 600 !important;
    margin-bottom: 0.5rem !important;
}}

/* Info box styling */
.info-box {{
    background: rgba(59,130,246,0.15);
    border-left: 4px solid #3b82f6;
    padding: 1rem;
    border-radius: 8px;
    margin: 1rem 0;
}}

.warning-box {{
    background: rgba(251,191,36,0.15);
    border-left: 4px solid #fbbf24;
    padding: 1rem;
    border-radius: 8px;
    margin: 1rem 0;
}}

.success-box {{
    background: rgba(34,197,94,0.15);
    border-left: 4px solid #22c55e;
    padding: 1rem;
    border-radius: 8px;
    margin: 1rem 0;
}}

/* Section headers */
.section-header {{
    font-size: 1.3rem;
    font-weight: 700;
    margin: 1.5rem 0 1rem 0;
    background: linear-gradient(90deg, #ff4fd8, #00ffe1);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}}

/* Locked state styling */
.locked-message {{
    background: rgba(255,79,216,0.1);
    border: 2px solid rgba(255,79,216,0.3);
    border-radius: 16px;
    padding: 2rem;
    text-align: center;
    margin: 2rem 0;
}}

.lock-icon {{
    font-size: 3rem;
    margin-bottom: 1rem;
    animation: pulse 2s ease-in-out infinite;
}}

/* Chat-specific styles */
.chat-container {{
    background: rgba(12,12,22,0.95);
    border-radius: 20px;
    padding: 20px;
    margin: 20px 0;
    border: 1px solid rgba(255,255,255,0.1);
    max-height: 500px;
    overflow-y: auto;
}}

.chat-message {{
    background: rgba(255,255,255,0.05);
    border-radius: 12px;
    padding: 12px 16px;
    margin: 8px 0;
    border-left: 3px solid rgba(0,255,225,0.5);
}}

.chat-message.sent {{
    background: linear-gradient(135deg, rgba(255,79,216,0.2), rgba(0,255,225,0.15));
    border-left: 3px solid rgba(255,79,216,0.7);
    margin-left: 20px;
}}

.chat-message.received {{
    background: rgba(139,92,246,0.15);
    border-left: 3px solid rgba(139,92,246,0.7);
    margin-right: 20px;
}}

.chat-sender {{
    font-size: 0.85rem;
    font-weight: 700;
    color: #00ffe1;
    margin-bottom: 4px;
}}

.chat-text {{
    font-size: 0.95rem;
    line-height: 1.4;
    word-wrap: break-word;
}}

.chat-time {{
    font-size: 0.75rem;
    opacity: 0.6;
    margin-top: 4px;
    text-align: right;
}}

.chat-input-container {{
    background: rgba(255,255,255,0.05);
    border-radius: 12px;
    padding: 12px;
    margin-top: 12px;
    border: 1px solid rgba(255,255,255,0.1);
}}

.unread-badge {{
    background: linear-gradient(135deg, #ff4fd8, #ec4899);
    color: white;
    font-size: 0.75rem;
    font-weight: 700;
    padding: 4px 10px;
    border-radius: 12px;
    display: inline-block;
    margin-left: 8px;
    animation: pulse 2s ease-in-out infinite;
}}

/* Scrollbar styling for chat */
.chat-container::-webkit-scrollbar {{
    width: 8px;
}}

.chat-container::-webkit-scrollbar-track {{
    background: rgba(255,255,255,0.05);
    border-radius: 10px;
}}

.chat-container::-webkit-scrollbar-thumb {{
    background: linear-gradient(135deg, #ff4fd8, #00ffe1);
    border-radius: 10px;
}}

.chat-container::-webkit-scrollbar-thumb:hover {{
    background: linear-gradient(135deg, #ec4899, #00d4b8);
}}
</style>
""", unsafe_allow_html=True)

# ================= FIREBASE INIT =================
if not firebase_admin._apps:
    cred = credentials.Certificate(dict(st.secrets["firebase"]))
    firebase_admin.initialize_app(cred)

db = firestore.client()

# ================= TIME =================
IST = timezone(timedelta(hours=5, minutes=30))

# 🔴 UNLOCK DATE - Set to Feb 6, 2026, 8 PM IST
UNLOCK_TIME = datetime(2026, 2, 5, 20, 0, tzinfo=IST)

MATCH_THRESHOLD = 0.50
SCALE = ["No", "Slightly", "Maybe", "Mostly", "Yes", "Strongly yes"]

# Match limits based on gender to handle disproportion
# Strategy: To balance gender disparity and ensure fair matching
# - Females get more matches (10) because there are fewer female users
# - Males get fewer matches (4) because there are more male users  
# - This ensures most users get matches despite unequal gender ratios
FEMALE_MATCH_LIMIT = 10  # Females get top 10 matches
MALE_MATCH_LIMIT = 4      # Males get top 4 matches

# ================= EMAIL CONFIG =================
SMTP_SERVER = st.secrets.get("smtp", {}).get("server", "smtp.gmail.com")
SMTP_PORT = st.secrets.get("smtp", {}).get("port", 587)
SMTP_EMAIL = st.secrets.get("smtp", {}).get("email", "")
SMTP_PASSWORD = st.secrets.get("smtp", {}).get("password", "")
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

def pad_to_length(arr, target_length, fill_value=0):
    """Pad or truncate array to target length"""
    arr = list(arr)
    if len(arr) < target_length:
        arr.extend([fill_value] * (target_length - len(arr)))
    elif len(arr) > target_length:
        arr = arr[:target_length]
    return arr

def cosine(a, b):
    # Ensure both arrays have the same length
    max_len = max(len(a), len(b))
    a = pad_to_length(a, max_len)
    b = pad_to_length(b, max_len)
    
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

def create_magic_link(email_hash, email=None):
    """Create a magic link token and store in database"""
    token = generate_magic_token()
    expiry = datetime.now(IST) + timedelta(hours=24)
    
    token_data = {
        "email_hash": email_hash,
        "token": token,
        "expires_at": expiry,
        "created_at": firestore.SERVER_TIMESTAMP
    }
    
    if email:
        token_data["email"] = email
    
    db.collection("magic_tokens").document(token).set(token_data)
    return token

def verify_magic_token(token):
    """Verify magic link token and return email_hash if valid"""
    try:
        doc = db.collection("magic_tokens").document(token).get()
        if not doc.exists:
            return None
        
        data = doc.to_dict()
        if data["expires_at"].replace(tzinfo=IST) < datetime.now(IST):
            return None
        
        return data["email_hash"]
    except:
        return None

def send_magic_link(email, token):
    """Send magic link to user's email"""
    
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

def compute_matches(current_user, all_users):
    """Compute compatibility scores and return matches above threshold"""
    matches = []
    opposite_gender = "Female" if current_user["gender"] == "Male" else "Male"
    
    # Validate current user has answers
    if "answers" not in current_user or "psych" not in current_user["answers"] or "interest" not in current_user["answers"]:
        return []
    
    # Expected lengths
    PSYCH_LENGTH = 10
    INTEREST_LENGTH = 5
    
    # Pad current user's answers to expected lengths
    current_psych_raw = current_user["answers"]["psych"]
    current_interest_raw = current_user["answers"]["interest"]
    
    current_psych_raw = pad_to_length(current_psych_raw, PSYCH_LENGTH, 3)  # Default to middle value
    current_interest_raw = pad_to_length(current_interest_raw, INTEREST_LENGTH, 0)
    
    current_psych = normalize(current_psych_raw)
    current_interest = normalize(current_interest_raw)
    
    for user in all_users:
        if user["_id"] == current_user["_id"]:
            continue
        if user["gender"] != opposite_gender:
            continue
        
        # Validate user has answers
        if "answers" not in user or "psych" not in user["answers"] or "interest" not in user["answers"]:
            continue
        
        # Pad user's answers to expected lengths
        user_psych_raw = user["answers"]["psych"]
        user_interest_raw = user["answers"]["interest"]
        
        user_psych_raw = pad_to_length(user_psych_raw, PSYCH_LENGTH, 3)
        user_interest_raw = pad_to_length(user_interest_raw, INTEREST_LENGTH, 0)
        
        user_psych = normalize(user_psych_raw)
        user_interest = normalize(user_interest_raw)
        
        try:
            psych_score = cosine(current_psych, user_psych)
            interest_score = cosine(current_interest, user_interest)
            
            combined = 0.7 * psych_score + 0.3 * interest_score
            
            if combined >= MATCH_THRESHOLD:
                matches.append({
                    "user": user,
                    "score": combined,
                    "psych_score": psych_score,
                    "interest_score": interest_score
                })
        except Exception as e:
            # Skip this user if there's an error computing similarity
            # print(f"Error computing match for user {user.get('alias', 'unknown')}: {e}")
            continue
    
    # Sort by score (highest first)
    matches = sorted(matches, key=lambda x: x["score"], reverse=True)
    
    # Apply gender-based match limits
    if current_user["gender"] == "Female":
        # Females get top 10 matches
        matches = matches[:FEMALE_MATCH_LIMIT]
    else:
        # Males get top 4 matches
        matches = matches[:MALE_MATCH_LIMIT]
    
    return matches

def show_compatibility_details(current_user, matched_user):
    """Display detailed compatibility breakdown"""
    
    st.markdown("### 🔍 Compatibility Breakdown")
    
    # Expected lengths
    PSYCH_LENGTH = 10
    INTEREST_LENGTH = 5
    
    try:
        # Validate and pad current user's answers
        current_psych_raw = current_user.get("answers", {}).get("psych", [])
        current_interest_raw = current_user.get("answers", {}).get("interest", [])
        
        current_psych_raw = pad_to_length(current_psych_raw, PSYCH_LENGTH, 3)
        current_interest_raw = pad_to_length(current_interest_raw, INTEREST_LENGTH, 0)
        
        current_psych = normalize(current_psych_raw)
        current_interest = normalize(current_interest_raw)
        
        # Validate and pad matched user's answers
        matched_psych_raw = matched_user.get("answers", {}).get("psych", [])
        matched_interest_raw = matched_user.get("answers", {}).get("interest", [])
        
        matched_psych_raw = pad_to_length(matched_psych_raw, PSYCH_LENGTH, 3)
        matched_interest_raw = pad_to_length(matched_interest_raw, INTEREST_LENGTH, 0)
        
        matched_psych = normalize(matched_psych_raw)
        matched_interest = normalize(matched_interest_raw)
        
        psych_score = cosine(current_psych, matched_psych) * 100
        interest_score = cosine(current_interest, matched_interest) * 100
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("🧠 Psychological", f"{psych_score:.0f}%")
        with col2:
            st.metric("🎵 Interests", f"{interest_score:.0f}%")
    except Exception as e:
        st.warning("⚠️ Unable to display detailed compatibility breakdown")
        # print(f"Error in show_compatibility_details: {e}")

# ================= CHAT FUNCTIONS =================
def get_chat_id(user1_id, user2_id):
    """Generate a consistent chat ID for two users"""
    return "_".join(sorted([user1_id, user2_id]))

def send_message(chat_id, sender_id, sender_alias, message_text):
    """Send a message in a chat"""
    # Validate message
    if not message_text or not message_text.strip():
        return False
    
    message_data = {
        "sender_id": sender_id,
        "sender_alias": sender_alias,
        "message": message_text.strip(),
        "timestamp": firestore.SERVER_TIMESTAMP,
        "read": False
    }
    
    try:
        db.collection("chats").document(chat_id).collection("messages").add(message_data)
        
        # Update chat metadata
        chat_ref = db.collection("chats").document(chat_id)
        chat_doc = chat_ref.get()
        
        if not chat_doc.exists:
            chat_ref.set({
                "participants": [sender_id],
                "last_message": message_text.strip(),
                "last_message_time": firestore.SERVER_TIMESTAMP,
                "created_at": firestore.SERVER_TIMESTAMP
            })
        else:
            chat_ref.update({
                "last_message": message_text.strip(),
                "last_message_time": firestore.SERVER_TIMESTAMP
            })
        
        return True
    except Exception as e:
        # Log error for debugging (optional)
        # print(f"Error sending message: {e}")
        return False

def get_messages(chat_id, limit=50):
    """Get messages from a chat"""
    messages = []
    try:
        docs = db.collection("chats").document(chat_id).collection("messages")\
                .order_by("timestamp", direction=firestore.Query.ASCENDING)\
                .limit(limit).stream()
        
        for doc in docs:
            msg_data = doc.to_dict()
            msg_data["_id"] = doc.id
            
            # Only include messages with required fields
            if msg_data.get("message") and msg_data.get("sender_id"):
                messages.append(msg_data)
    except Exception as e:
        # Log error for debugging (optional)
        # print(f"Error getting messages: {e}")
        pass
    
    return messages

def mark_messages_as_read(chat_id, current_user_id):
    """Mark all messages from other user as read"""
    try:
        messages = db.collection("chats").document(chat_id).collection("messages")\
                    .where("sender_id", "!=", current_user_id)\
                    .where("read", "==", False).stream()
        
        for msg in messages:
            msg.reference.update({"read": True})
    except:
        pass

def get_unread_count(chat_id, current_user_id):
    """Get count of unread messages for current user"""
    try:
        messages = db.collection("chats").document(chat_id).collection("messages")\
                    .where("sender_id", "!=", current_user_id)\
                    .where("read", "==", False).stream()
        
        count = 0
        for msg in messages:
            # Verify message has required fields
            msg_data = msg.to_dict()
            if msg_data.get("message") and msg_data.get("sender_id"):
                count += 1
        
        return count
    except Exception as e:
        # Log error for debugging (optional)
        # print(f"Error getting unread count: {e}")
        return 0

def display_chat(current_user, matched_user):
    """Display chat interface for a matched user"""
    
    chat_id = get_chat_id(current_user["_id"], matched_user["_id"])
    
    st.markdown(f"""
    <div class="glass">
        <div style="text-align:center;">
            <div style="font-size:1.5rem;font-weight:700;margin-bottom:0.5rem;">
                💬 Chat with {matched_user['alias']}
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Messages container
    messages = get_messages(chat_id)
    
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    
    if not messages:
        st.markdown("""
        <div style="text-align:center;padding:40px;opacity:0.7;">
            <div style="font-size:2rem;margin-bottom:1rem;">💭</div>
            <div>No messages yet. Start the conversation!</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        for msg in messages:
            # Skip messages without required fields
            if not msg.get("message") or not msg.get("sender_id"):
                continue
                
            is_sent = msg["sender_id"] == current_user["_id"]
            msg_class = "sent" if is_sent else "received"
            
            # Get sender alias safely
            sender_name = "You" if is_sent else msg.get("sender_alias", "Unknown")
            
            timestamp = ""
            if msg.get("timestamp"):
                try:
                    dt = msg["timestamp"].replace(tzinfo=timezone.utc).astimezone(IST)
                    timestamp = dt.strftime("%I:%M %p")
                except:
                    pass
            
            # Escape HTML in message to prevent injection
            message_text = str(msg.get("message", "")).replace("<", "&lt;").replace(">", "&gt;")
            
            st.markdown(f"""
            <div class="chat-message {msg_class}">
                <div class="chat-sender">{sender_name}</div>
                <div class="chat-text">{message_text}</div>
                <div class="chat-time">{timestamp}</div>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Mark messages as read
    mark_messages_as_read(chat_id, current_user["_id"])
    
    # Message input
    st.markdown('<div class="chat-input-container">', unsafe_allow_html=True)
    
    with st.form(key=f"chat_form_{chat_id}", clear_on_submit=True):
        col1, col2 = st.columns([4, 1])
        
        with col1:
            new_message = st.text_input(
                "Message",
                placeholder="Type your message...",
                label_visibility="collapsed",
                key=f"msg_input_{chat_id}"
            )
        
        with col2:
            send_btn = st.form_submit_button("📤 Send", use_container_width=True)
        
        if send_btn and new_message.strip():
            success = send_message(
                chat_id,
                current_user["_id"],
                current_user["alias"],
                new_message.strip()
            )
            if success:
                st.rerun()
            else:
                st.error("Failed to send message. Please try again.")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Auto-refresh button
    if st.button("🔄 Refresh Messages", key=f"refresh_{chat_id}"):
        st.rerun()

# ================= MAIN APP =================

# Header
st.markdown('<div class="title">💘 NITeMatch</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Find your perfect match at NIT Jalandhar</div>', unsafe_allow_html=True)

# Get current time
now = datetime.now(IST)

# Check for magic link token in URL (only works after unlock time)
params = st.query_params
token = params.get("token", None)

# Initialize session state
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "current_user" not in st.session_state:
    st.session_state.current_user = None
if "active_chat" not in st.session_state:
    st.session_state.active_chat = None
if "view_mode" not in st.session_state:
    st.session_state.view_mode = "matches"  # "matches" or "chat"

# Verify magic link token if present and after unlock time
if token and not st.session_state.logged_in and now >= UNLOCK_TIME:
    email_hash = verify_magic_token(token)
    if email_hash:
        users = fetch_users()
        user = next((u for u in users if u.get("email_hash") == email_hash), None)
        if user:
            st.session_state.logged_in = True
            st.session_state.current_user = user
            st.query_params.clear()
            st.rerun()
        else:
            st.error("❌ User not found")
    else:
        st.error("❌ Invalid or expired login link")

# ================= LOGGED IN STATE =================
if st.session_state.logged_in and st.session_state.current_user:
    current_user = st.session_state.current_user
    
    if now >= UNLOCK_TIME:
        # Apply matched theme if matches exist
        all_users = fetch_users()
        matches = compute_matches(current_user, all_users)
        apply_styles(has_matches=len(matches) > 0)
        
        st.markdown(f"""
        <div class="glass">
            <div style="text-align:center;">
                <h2 style="margin-bottom:0.5rem;">Welcome back, {current_user['alias']}! 👋</h2>
                <p style="opacity:0.8;">Here are your compatibility results</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Navigation buttons
        col1, col2, col3 = st.columns([2, 2, 1])
        
        with col1:
            if st.button("📋 View Matches", use_container_width=True, 
                        type="primary" if st.session_state.view_mode == "matches" else "secondary"):
                st.session_state.view_mode = "matches"
                st.session_state.active_chat = None
                st.rerun()
        
        with col2:
            # Count total unread messages
            total_unread = 0
            for match in matches:
                chat_id = get_chat_id(current_user["_id"], match["user"]["_id"])
                total_unread += get_unread_count(chat_id, current_user["_id"])
            
            chat_label = f"💬 Messages"
            if total_unread > 0:
                chat_label += f" ({total_unread})"
            
            if st.button(chat_label, use_container_width=True,
                        type="primary" if st.session_state.view_mode == "chat" else "secondary"):
                st.session_state.view_mode = "chat"
                st.rerun()
        
        with col3:
            if st.button("🚪 Logout", use_container_width=True):
                st.session_state.logged_in = False
                st.session_state.current_user = None
                st.session_state.active_chat = None
                st.session_state.view_mode = "matches"
                st.rerun()
        
        st.markdown("---")
        
        # VIEW MODES
        if st.session_state.view_mode == "matches":
            # MATCHES VIEW
            if matches:
                st.markdown(f"""
                <div class="success-box">
                    <div style="font-size:1.3rem;font-weight:700;text-align:center;">
                        <span class="heart-beat">💕</span> You have {len(matches)} compatible match{"es" if len(matches) > 1 else ""}! <span class="heart-beat">💕</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Show match limit info
                if current_user["gender"] == "Female":
                    st.markdown("""
                    <div class="info-box">
                        <div style="text-align:center;font-size:0.9rem;">
                            ℹ️ Showing your top 10 most compatible matches
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown("""
                    <div class="info-box">
                        <div style="text-align:center;font-size:0.9rem;">
                            ℹ️ Showing your top 4 most compatible matches
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
                for idx, match in enumerate(matches, 1):
                    matched_user = match["user"]
                    score = match["score"] * 100
                    chat_id = get_chat_id(current_user["_id"], matched_user["_id"])
                    unread = get_unread_count(chat_id, current_user["_id"])
                    
                    st.markdown(f"""
                    <div class="glass match-glow">
                        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:1rem;">
                            <div style="font-size:1.4rem;font-weight:700;">
                                Match #{idx}
                            </div>
                            <div style="font-size:1.8rem;font-weight:900;background:linear-gradient(90deg,#ff4fd8,#00ffe1);-webkit-background-clip:text;-webkit-text-fill-color:transparent;">
                                {score:.0f}%
                            </div>
                        </div>
                        <div style="background:rgba(255,255,255,0.05);padding:16px;border-radius:12px;margin-bottom:16px;">
                            <div style="font-size:1.5rem;font-weight:700;text-align:center;color:#00ffe1;">
                                {matched_user['alias']}
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    # Show Instagram if shared
                    if matched_user.get("share_instagram", False) and matched_user.get("instagram"):
                        instagram_handle = matched_user['instagram'].replace('@', '')
                        st.markdown(f"""
                        <div style="background: rgba(255,255,255,0.05); padding: 14px; border-radius: 10px; margin-bottom: 12px; text-align:center;">
                            <span style="font-size:1.2rem;">📸</span> <strong>Instagram:</strong> 
                            <a href="https://instagram.com/{instagram_handle}" 
                            target="_blank" style="color: #00ffe1; font-weight:600; text-decoration:none;">
                            @{instagram_handle}
                            </a>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    # Show message for matches
                    if matched_user.get("match_message"):
                        st.markdown(f"""
                        <div style="background: linear-gradient(135deg, rgba(255,79,216,0.15), rgba(0,255,225,0.15)); padding: 18px; border-radius: 12px; margin-bottom: 12px; border-left: 4px solid #ff4fd8;">
                            <div style="font-weight: 600; margin-bottom: 8px; color: #ff4fd8;">💬 Message from {matched_user['alias']}:</div>
                            <div style="font-style: italic; opacity: 0.95; line-height: 1.5;">"{matched_user['match_message']}"</div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    st.markdown("</div>", unsafe_allow_html=True)
                    
                    # Chat button
                    chat_btn_label = f"💬 Chat with {matched_user['alias']}"
                    if unread > 0:
                        chat_btn_label += f" ({unread} new)"
                    
                    if st.button(chat_btn_label, key=f"chat_btn_{matched_user['_id']}", use_container_width=True):
                        st.session_state.view_mode = "chat"
                        st.session_state.active_chat = matched_user["_id"]
                        st.rerun()
                    
                    show_compatibility_details(current_user, matched_user)
                    st.markdown("---")
            else:
                st.markdown("""
                <div class="info-box">
                    <div style="text-align:center;">
                        <div style="font-size:2rem;margin-bottom:1rem;">🔍</div>
                        <div style="font-size:1.1rem;font-weight:600;margin-bottom:0.5rem;">No matches found yet</div>
                        <div style="opacity:0.8;">Don't worry! More people are joining. Check back later!</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        
        elif st.session_state.view_mode == "chat":
            # CHAT VIEW
            if not matches:
                st.markdown("""
                <div class="info-box">
                    <div style="text-align:center;">
                        <div style="font-size:2rem;margin-bottom:1rem;">💬</div>
                        <div style="font-size:1.1rem;font-weight:600;margin-bottom:0.5rem;">No matches to chat with</div>
                        <div style="opacity:0.8;">Find matches first to start chatting!</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                # If no active chat selected, show list of matches
                if not st.session_state.active_chat:
                    st.markdown("""
                    <div class="glass">
                        <div style="text-align:center;margin-bottom:1.5rem;">
                            <div style="font-size:1.3rem;font-weight:700;">Select a match to chat with</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    for match in matches:
                        matched_user = match["user"]
                        chat_id = get_chat_id(current_user["_id"], matched_user["_id"])
                        unread = get_unread_count(chat_id, current_user["_id"])
                        
                        btn_label = f"💬 {matched_user['alias']}"
                        if unread > 0:
                            btn_label += f" • {unread} new"
                        
                        if st.button(btn_label, key=f"select_chat_{matched_user['_id']}", use_container_width=True):
                            st.session_state.active_chat = matched_user["_id"]
                            st.rerun()
                
                # If active chat selected, show chat interface
                else:
                    matched_user = next((m["user"] for m in matches if m["user"]["_id"] == st.session_state.active_chat), None)
                    
                    if matched_user:
                        # Back button
                        if st.button("⬅️ Back to chat list", key="back_to_list"):
                            st.session_state.active_chat = None
                            st.rerun()
                        
                        display_chat(current_user, matched_user)
                    else:
                        st.session_state.active_chat = None
                        st.rerun()
    
    else:
        # Logged in but before unlock time
        apply_styles(is_countdown=True)
        remaining = UNLOCK_TIME - now
        
        st.markdown(f"""
        <div class="countdown-box">
            <div class="countdown-title">Welcome back, {current_user['alias']}! 👋</div>
            <div style="font-size:1.2rem;margin-bottom:1rem;opacity:0.9;">Your matches will be revealed in:</div>
            <div class="countdown-timer">
                {remaining.days}d {remaining.seconds//3600}h {(remaining.seconds//60)%60}m
            </div>
            <div class="unlock-date">📅 6th February 2026 • 8:00 PM IST</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="info-box">
            <div style="text-align:center;">
                <div style="font-size:1.1rem;margin-bottom:0.5rem;">✅ Your profile is saved!</div>
                <div style="opacity:0.9;">Come back after the unlock time to see your matches</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.current_user = None
            st.rerun()

# ================= NOT LOGGED IN - BEFORE UNLOCK =================
elif now < UNLOCK_TIME:
    apply_styles(is_countdown=True)
    remaining = UNLOCK_TIME - now

    st.markdown(f"""
    <div class="countdown-box">
        <div class="countdown-title">⏳ Matches Unlock In:</div>
        <div class="countdown-timer">
            {remaining.days}d {remaining.seconds//3600}h {(remaining.seconds//60)%60}m
        </div>
        <div class="unlock-date">📅 6th February 2026 • 8:00 PM IST</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="glass">
        <div style="text-align:center;margin-bottom:1.5rem;">
            <div style="font-size:1.3rem;font-weight:700;margin-bottom:0.5rem;">Join NITeMatch Today!</div>
            <div style="opacity:0.85;">Fill out the form below to find your perfect match</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    with st.form("pre_unlock_form"):
        st.markdown('<div class="section-header">📝 Basic Information</div>', unsafe_allow_html=True)
        
        alias = st.text_input("Choose an anonymous alias", placeholder="Your creative alias...")

        st.markdown("""
        <div class="warning-box">
            <strong>🔒 Privacy Notice:</strong> Your email is encrypted and used only for NIT Jalandhar verification. 
            You'll receive a login link via email after the unlock time.
        </div>
        """, unsafe_allow_html=True)

        email = st.text_input("Official NIT Jalandhar Email ID", placeholder="yourname@nitj.ac.in")
        
        gender = st.radio("I identify as", ["Male", "Female"], horizontal=True)
        
        st.markdown("---")
        st.markdown('<div class="section-header">🧠 Psychological Questions</div>', unsafe_allow_html=True)
        st.caption("Answer honestly for better matches ✨")
        
        q1 = scale_slider("When overwhelmed, I prefer emotional closeness")
        q2 = scale_slider("I feel emotionally safe opening up")
        q3 = scale_slider("During conflict, I try to understand before reacting")
        q4 = scale_slider("Emotional loyalty matters more than attention")
        q5 = scale_slider("Relationships should help people grow")
        q6 = st.radio("In difficult situations, I prefer", ["Handling things alone", "Leaning on someone"], horizontal=True)
        q7 = st.radio("I process emotional pain by", ["Thinking quietly", "Talking it out"], horizontal=True)
        q8 = scale_slider("I express care more through actions than words")
        q9 = st.radio("If extremely busy but someone important needs you", 
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
                # Process binary questions
                q6_val = bin_map(q6, "Handling things alone", "Leaning on someone")
                q7_val = bin_map(q7, "Thinking quietly", "Talking it out")
                q9_val = bin_map(q9, "Drop everything for them", "Ask to catch up later")
                q10_val = bin_map(q10, "Talk it out immediately", "Take time to cool off")
                
                # Map interest answers to indices
                music_era_val = ["Before 2000", "2000–2009", "2010–2019", "2020–Present"].index(music_era)
                music_genre_val = ["Pop", "Rock", "Hip-hop / Rap", "EDM", "Metal", "Classical", "Indie"].index(music_genre)
                travel_val = 0 if travel == "Beaches" else 1
                movies_val = ["Romance / Drama", "Thriller / Mystery", "Comedy", "Action / Sci-Fi"].index(movies)
                hangout_val = ["Nescafe near Verka", "Nescafe near MBH", "Night Canteen", "Snackers", 
                               "Dominos", "Yadav Canteen", "Rimjhim Area", "Campus Cafe"].index(hangout)
                
                # Save to database
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

# ================= AFTER UNLOCK - LOGIN SECTION (ONLY AVAILABLE AFTER UNLOCK TIME) =================
else:
    apply_styles()
    
    st.markdown("""
    <div class="glass" style="text-align:center;">
        <div style="font-size:2rem;margin-bottom:1rem;">🎉</div>
        <div style="font-size:1.5rem;font-weight:700;margin-bottom:1rem;">Matches Are Live!</div>
        <div class="small-note">Choose your preferred login method below</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Create two columns for login options
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
                    
                    # Find user by email hash and alias
                    users = fetch_users()
                    user = next((u for u in users 
                               if u.get("email_hash") == login_hash 
                               and u.get("alias") == login_alias), None)
                    
                    if not user:
                        st.error("❌ Invalid alias or email. Please check your credentials.")
                    else:
                        # Log the user in
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
                    
                    # Check if user exists
                    users = fetch_users()
                    user = next((u for u in users if u.get("email_hash") == magic_hash), None)
                    
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
