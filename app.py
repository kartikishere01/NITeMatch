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

# ================= GLOBAL STYLES WITH DYNAMIC BACKGROUND =================
def apply_styles(has_matches=False):
    """Apply dynamic styles based on match status"""
    
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
    font-size: 3rem;
    font-weight: 900;
    text-align: center;
    background: linear-gradient(90deg, #ff4fd8, #00ffe1);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}}
.glass {{
    background: rgba(12,12,22,0.88);
    backdrop-filter: blur(18px);
    border-radius: 24px;
    padding: 28px;
    margin-bottom: 24px;
}}
.small-note {{ font-size: 0.8rem; opacity: 0.75; }}

/* Better button styling */
.stButton button {{
    background: linear-gradient(135deg, rgba(255,79,216,0.3), rgba(0,255,225,0.3));
    border: 1px solid rgba(255,255,255,0.2);
    border-radius: 12px;
    color: white;
    font-weight: 600;
    transition: all 0.3s ease;
}}
.stButton button:hover {{
    background: linear-gradient(135deg, rgba(255,79,216,0.5), rgba(0,255,225,0.5));
    border: 1px solid rgba(255,255,255,0.4);
    transform: translateY(-2px);
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
</style>
""", unsafe_allow_html=True)

# Apply default styles initially
apply_styles()

# ================= FIREBASE INIT =================
if not firebase_admin._apps:
    cred = credentials.Certificate(dict(st.secrets["firebase"]))
    firebase_admin.initialize_app(cred)

db = firestore.client()

# ================= TIME =================
IST = timezone(timedelta(hours=5, minutes=30))

# 🔴 UNLOCK DATE - Set to Feb 6, 2026, 8 PM IST
UNLOCK_TIME = datetime(2026, 2, 6, 20, 0, tzinfo=IST)

MATCH_THRESHOLD = 0.50
SCALE = ["No", "Slightly", "Maybe", "Mostly", "Yes", "Strongly yes"]

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
        <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 0; background-color: #f7f7f7;">
            <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #f7f7f7; padding: 40px 20px;">
                <tr>
                    <td align="center">
                        <table width="600" cellpadding="0" cellspacing="0" style="background: white; border-radius: 16px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                            <tr>
                                <td style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 40px; text-align: center;">
                                    <h1 style="color: white; margin: 0; font-size: 32px;">💘 NITeMatch</h1>
                                    <p style="color: rgba(255,255,255,0.9); margin: 10px 0 0 0; font-size: 16px;">Your Login Link is Ready</p>
                                </td>
                            </tr>
                            
                            <tr>
                                <td style="padding: 40px;">
                                    <p style="color: #333; font-size: 16px; line-height: 1.6; margin: 0 0 20px 0;">
                                        Hi there! 👋
                                    </p>
                                    <p style="color: #666; font-size: 16px; line-height: 1.6; margin: 0 0 30px 0;">
                                        Click the button below to securely access your NITeMatch profile and view your matches:
                                    </p>
                                    
                                    <table width="100%" cellpadding="0" cellspacing="0">
                                        <tr>
                                            <td align="center" style="padding: 20px 0;">
                                                <a href="{magic_link}" style="display: inline-block; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 16px 48px; text-decoration: none; border-radius: 8px; font-weight: 600; font-size: 16px;">
                                                    🔐 Login to NITeMatch
                                                </a>
                                            </td>
                                        </tr>
                                    </table>
                                    
                                    <p style="color: #999; font-size: 14px; text-align: center; margin: 20px 0 0 0;">
                                        Or copy this link:<br>
                                        <a href="{magic_link}" style="color: #667eea; word-break: break-all; font-size: 12px;">{magic_link}</a>
                                    </p>
                                </td>
                            </tr>
                            
                            <tr>
                                <td style="background: #f9f9f9; padding: 30px; border-top: 1px solid #eee;">
                                    <p style="color: #999; font-size: 14px; text-align: center; margin: 0 0 10px 0;">
                                        ⏰ This link will expire in <strong>15 minutes</strong> for security.
                                    </p>
                                    <p style="color: #999; font-size: 12px; text-align: center; margin: 0;">
                                        If you didn't request this login link, please ignore this email.
                                    </p>
                                </td>
                            </tr>
                        </table>
                        
                        <p style="color: #999; font-size: 12px; text-align: center; margin: 20px 0 0 0;">
                            © 2026 NITeMatch • NIT Jalandhar
                        </p>
                    </td>
                </tr>
            </table>
        </body>
        </html>
        """
        
        text = f"""
NITeMatch - Your Login Link

Click the link below to access your matches:
{magic_link}

This link will expire in 15 minutes for security.

If you didn't request this, please ignore this email.

---
© 2026 NITeMatch • NIT Jalandhar
        """
        
        part1 = MIMEText(text, 'plain')
        part2 = MIMEText(html, 'html')
        
        msg.attach(part1)
        msg.attach(part2)
        
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=15) as server:
            server.starttls()
            server.login(SMTP_EMAIL, SMTP_PASSWORD)
            server.send_message(msg)
        
        return True
        
    except smtplib.SMTPAuthenticationError:
        st.error("❌ Email authentication failed. Check your App Password in secrets.")
        return False
    except smtplib.SMTPException as e:
        st.error(f"❌ SMTP Error: {str(e)}")
        return False
    except Exception as e:
        st.error(f"❌ Failed to send email: {str(e)}")
        return False

def create_magic_link(email_hash, plain_email=None):
    """Create a magic link token and store it in database"""
    token = generate_magic_token()
    expiry = datetime.now(IST) + timedelta(minutes=15)
    
    token_data = {
        "token": token,
        "email_hash": email_hash,
        "created_at": firestore.SERVER_TIMESTAMP,
        "expires_at": expiry,
        "used": False
    }
    
    if plain_email:
        token_data["email"] = plain_email
    
    db.collection("magic_tokens").add(token_data)
    
    return token

def verify_magic_token(token):
    """Verify magic token and return user if valid"""
    tokens = list(
        db.collection("magic_tokens")
        .where("token", "==", token)
        .where("used", "==", False)
        .limit(1)
        .stream()
    )
    
    if not tokens:
        return None
    
    token_doc = tokens[0]
    token_data = token_doc.to_dict()
    
    expires_at = token_data["expires_at"]
    
    if hasattr(expires_at, 'timestamp'):
        expires_at = datetime.fromtimestamp(expires_at.timestamp(), tz=IST)
    elif expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=IST)
    
    current_time = datetime.now(IST)
    
    if expires_at < current_time:
        return None
    
    token_doc.reference.update({"used": True})
    
    users = list(
        db.collection("users")
        .where("email_hash", "==", token_data["email_hash"])
        .limit(1)
        .stream()
    )
    
    if users:
        return users[0].to_dict() | {"_id": users[0].id}
    
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

def show_compatibility_details(user1, user2):
    """Display detailed compatibility breakdown between two users"""
    
    psych_questions = [
        "When overwhelmed, I prefer emotional closeness",
        "I feel emotionally safe opening up",
        "During conflict, I try to understand before reacting",
        "Emotional loyalty matters more than attention",
        "Relationships should help people grow",
        "In difficult situations, I prefer",
        "I process emotional pain by",
        "I express care more through actions than words"
    ]
    
    interest_questions = [
        "Music era you connect with most",
        "Preferred music genre",
        "You would rather go to",
        "Movies you enjoy the most",
        "Favorite hangout spot"
    ]
    
    user1_psych = user1["answers"]["psych"]
    user2_psych = user2["answers"]["psych"]
    user1_interest = user1["answers"]["interest"]
    user2_interest = user2["answers"]["interest"]
    
    psych1 = normalize(user1_psych)
    psych2 = normalize(user2_psych)
    interest1 = normalize(user1_interest)
    interest2 = normalize(user2_interest)
    
    psych_score = round(cosine(psych1, psych2) * 100, 1)
    interest_score = round(cosine(interest1, interest2) * 100, 1)
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("🧠 Psychological Match", f"{psych_score}%")
    with col2:
        st.metric("🎵 Interest Match", f"{interest_score}%")
    
    st.markdown("---")
    
    st.markdown("### 🧠 Psychological Compatibility")
    
    for i, question in enumerate(psych_questions):
        user1_val = user1_psych[i]
        user2_val = user2_psych[i]
        
        if i not in [5, 6]:
            diff = abs(user1_val - user2_val)
            if diff == 0:
                icon = "✅"
                color = "#00ffe1"
            elif diff <= 1:
                icon = "🟡"
                color = "#ffa500"
            else:
                icon = "⚠️"
                color = "#ff4fd8"
            
            user1_label = SCALE[user1_val - 1]
            user2_label = SCALE[user2_val - 1]
            
        else:
            if user1_val == user2_val:
                icon = "✅"
                color = "#00ffe1"
            else:
                icon = "⚠️"
                color = "#ff4fd8"
            
            if i == 5:
                labels = ["Handling things alone", "Leaning on someone"]
            else:
                labels = ["Thinking quietly", "Talking it out"]
            
            user1_label = labels[user1_val]
            user2_label = labels[user2_val]
        
        st.markdown(f"""
        <div style="background: rgba(255,255,255,0.05); padding: 12px; border-radius: 8px; margin-bottom: 8px;">
            <div style="color: {color}; font-weight: 600; margin-bottom: 6px;">{icon} {question}</div>
            <div style="font-size: 0.9rem; opacity: 0.8;">You: {user1_label} | Them: {user2_label}</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    st.markdown("### 🎵 Interests & Lifestyle")
    
    interest_options = [
        ["Before 2000", "2000–2009", "2010–2019", "2020–Present"],
        ["Pop", "Rock", "Hip-hop / Rap", "EDM", "Metal", "Classical", "Indie"],
        ["Beaches", "Mountains"],
        ["Romance / Drama", "Thriller / Mystery", "Comedy", "Action / Sci-Fi"],
        ["Nescafe near Verka", "Nescafe near MBH", "Night Canteen", "Snackers", "Dominos", "Yadav Canteen", "Rimjhim Area", "Campus Cafe"]
    ]
    
    for i, question in enumerate(interest_questions):
        user1_val = user1_interest[i]
        user2_val = user2_interest[i]
        
        if user1_val == user2_val:
            icon = "✅"
            color = "#00ffe1"
        else:
            diff = abs(user1_val - user2_val)
            if diff <= 1:
                icon = "🟡"
                color = "#ffa500"
            else:
                icon = "⚠️"
                color = "#ff4fd8"
        
        user1_label = interest_options[i][user1_val]
        user2_label = interest_options[i][user2_val]
        
        st.markdown(f"""
        <div style="background: rgba(255,255,255,0.05); padding: 12px; border-radius: 8px; margin-bottom: 8px;">
            <div style="color: {color}; font-weight: 600; margin-bottom: 6px;">{icon} {question}</div>
            <div style="font-size: 0.9rem; opacity: 0.8;">You: {user1_label} | Them: {user2_label}</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    st.caption("✅ = Similar  |  🟡 = Somewhat different  |  ⚠️ = Different")

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
        st.query_params.clear()
        st.success("✅ Successfully logged in!")
        st.rerun()
    else:
        st.error("🚫 Invalid or expired login link. Please request a new one.")
        st.query_params.clear()

# ================= MAIN APP LOGIC =================
now = datetime.now(IST)

# Check if user is logged in
if st.session_state.get("logged_in", False):
    current_user = st.session_state.current_user
    
    if now >= UNLOCK_TIME:
        # 🎉 MATCHES ARE UNLOCKED!
        all_users = fetch_users()
        matches = get_matches(current_user, all_users)
        
        # 🌸 APPLY PINK GRADIENT IF MATCHES EXIST! 💕
        if matches:
            apply_styles(has_matches=True)
        
        st.markdown(f"""
        <div class="glass match-glow">
            <h2 style="text-align:center;">
                <span class="heart-beat">💕</span> Your Matches, {current_user['alias']}! <span class="heart-beat">💕</span>
            </h2>
        </div>
        """, unsafe_allow_html=True)
        
        if not matches:
            st.markdown("""
            <div class="glass" style="text-align:center;">
                <div style="font-size:3rem;">😔</div>
                <div style="font-size:1.3rem;margin-top:1rem;">No matches yet</div>
                <div class="small-note" style="margin-top:0.5rem;">
                Check back later as more people join!
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style="text-align:center;margin-bottom:2rem;">
                <div style="font-size:1.5rem;font-weight:700;background:linear-gradient(90deg,#ff1493,#ff69b4);-webkit-background-clip:text;-webkit-text-fill-color:transparent;">
                    Found {len(matches)} compatible match{"es" if len(matches) != 1 else ""}!
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            for idx, match in enumerate(matches, 1):
                matched_user = match["user"]
                score = match["score"]
                
                with st.expander(f"💘 Match #{idx}: {matched_user['alias']} • {score}% compatible", expanded=(idx == 1)):
                    st.markdown(f"""
                    <div class="glass">
                        <div style="font-size:1.5rem;font-weight:700;margin-bottom:1.5rem;text-align:center;">
                            {matched_user['alias']}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    st.markdown("---")
                    show_compatibility_details(current_user, matched_user)
        
        if st.button("🚪 Logout"):
            st.session_state.logged_in = False
            st.session_state.current_user = None
            st.rerun()
    
    else:
        remaining = UNLOCK_TIME - now
        st.markdown(f"""
        <div class="glass" style="text-align:center;">
            <div style="font-size:1.2rem;margin-bottom:1rem;">Welcome back, {current_user['alias']}!</div>
            <div>⏳ Matches reveal in</div>
            <div style="font-size:1.8rem;font-weight:700;">
                {remaining.days}d {remaining.seconds//3600}h {(remaining.seconds//60)%60}m
            </div>
            <div class="small-note">6th February • 8:00 PM IST</div>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🚪 Logout"):
            st.session_state.logged_in = False
            st.session_state.current_user = None
            st.rerun()

# ================= NOT LOGGED IN - BEFORE UNLOCK =================
elif now < UNLOCK_TIME:
    remaining = UNLOCK_TIME - now

    st.markdown(f"""
    <div class="glass" style="text-align:center;">
        <div>⏳ Matches reveal in</div>
        <div style="font-size:1.8rem;font-weight:700;">
            {remaining.days}d {remaining.seconds//3600}h {(remaining.seconds//60)%60}m
        </div>
        <div class="small-note">6th February • 8:00 PM IST</div>
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

        email = st.text_input("Official NIT Jalandhar Email (@nitj.ac.in)")
        
        gender = st.radio("Gender", ["Male", "Female"], horizontal=True)
        
        st.markdown("---")
        st.markdown("### 🧠 Psychological Questions")
        st.caption("Answer honestly for better matches")
        
        q1 = scale_slider("When overwhelmed, I prefer emotional closeness")
        q2 = scale_slider("I feel emotionally safe opening up")
        q3 = scale_slider("During conflict, I try to understand before reacting")
        q4 = scale_slider("Emotional loyalty matters more than attention")
        q5 = scale_slider("Relationships should help people grow")
        q6 = st.radio("In difficult situations, I prefer", ["Handling things alone", "Leaning on someone"], horizontal=True)
        q7 = st.radio("I process emotional pain by", ["Thinking quietly", "Talking it out"], horizontal=True)
        q8 = scale_slider("I express care more through actions than words")
        
        st.markdown("---")
        st.markdown("### 🎵 Interests & Preferences")
        
        music_era = st.radio("Music era you connect with most", 
            ["Before 2000", "2000–2009", "2010–2019", "2020–Present"], horizontal=True)
        music_genre = st.radio("Preferred music genre",
            ["Pop", "Rock", "Hip-hop / Rap", "EDM", "Metal", "Classical", "Indie"], horizontal=True)
        travel = st.radio("You would rather go to", ["Beaches", "Mountains"], horizontal=True)
        movies = st.radio("Movies you enjoy the most",
            ["Romance / Drama", "Thriller / Mystery", "Comedy", "Action / Sci-Fi"], horizontal=True)
        hangout = st.radio("Favorite hangout spot",
            ["Nescafe near Verka", "Nescafe near MBH", "Night Canteen", "Snackers", "Dominos", "Yadav Canteen", "Rimjhim Area", "Campus Cafe"], horizontal=False)
        
        submitted = st.form_submit_button("Submit")
        
        if submitted:
            # Process binary questions
            q6_val = bin_map(q6, "Handling things alone", "Leaning on someone")
            q7_val = bin_map(q7, "Thinking quietly", "Talking it out")
            
            # Map interest answers to indices
            music_era_val = ["Before 2000", "2000–2009", "2010–2019", "2020–Present"].index(music_era)
            music_genre_val = ["Pop", "Rock", "Hip-hop / Rap", "EDM", "Metal", "Classical", "Indie"].index(music_genre)
            travel_val = 0 if travel == "Beaches" else 1
            movies_val = ["Romance / Drama", "Thriller / Mystery", "Comedy", "Action / Sci-Fi"].index(movies)
            hangout_val = ["Nescafe near Verka", "Nescafe near MBH", "Night Canteen", "Snackers", "Dominos", "Yadav Canteen", "Rimjhim Area", "Campus Cafe"].index(hangout)
            
            # Save to database
            email_hash_val = hash_email(email)
            
            user_data = {
                "alias": alias,
                "email_hash": email_hash_val,
                "gender": gender,
                "answers": {
                    "psych": [q1, q2, q3, q4, q5, q6_val, q7_val, q8],
                    "interest": [music_era_val, music_genre_val, travel_val, movies_val, hangout_val]
                },
                "created_at": firestore.SERVER_TIMESTAMP
            }
            
            db.collection("users").add(user_data)
            
            # Create and send magic link
            token = create_magic_link(email_hash_val, email)
            
            if send_magic_link(email, token):
                st.success("✅ Registration successful! Check your email for login link.")
                st.balloons()
            else:
                st.warning("⚠️ Registration saved but email failed. Please use login below.")

# ================= AFTER UNLOCK - LOGIN SECTION =================
else:
    st.markdown("""
    <div class="glass" style="text-align:center;">
        <div style="font-size:1.5rem;font-weight:700;margin-bottom:1rem;">🎉 Matches Are Live!</div>
        <div class="small-note">Login to view your compatible matches</div>
    </div>
    """, unsafe_allow_html=True)
    
    with st.form("login_form"):
        login_email = st.text_input("Your NIT Jalandhar Email")
        login_submit = st.form_submit_button("📧 Send Login Link")
        
        if login_submit:
            login_hash = hash_email(login_email)
            token = create_magic_link(login_hash)
            update_user_email(login_hash, login_email)
            
            if send_magic_link(login_email, token):
                st.success("✅ Login link sent! Check your email.")
            else:
                st.error("❌ Failed to send email. Please try again.")
