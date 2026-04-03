
from auth import auth_bp
import os
import random
from flask import render_template, request, redirect, url_for, session, flash
import bcrypt
from db import get_db_connection
import pyotp
from time import time
import secrets
from flask import make_response
from db import save_auth_metrics



MAX_ATTEMPTS = 5
LOCKOUT_SECONDS = 300  # 5 minutes
RECALL_CHALLENGES = [
    "third_image",
    "reverse_order",
    "second_and_fourth",
    "first_and_last"
]


@auth_bp.route("/")
def home():

    session.pop("consent", None)

    return redirect(url_for("auth.information"))

@auth_bp.route("/start")
def start():

    if not session.get("consent"):
        return redirect(url_for("auth.information"))

    return render_template("index.html")

@auth_bp.route("/information")
def information():
    return render_template("information.html")

@auth_bp.route("/consent")
def consent():
    return render_template("consent.html")

@auth_bp.route("/submit_consent", methods=["POST"])
def submit_consent():

    if request.form.get("agree"):

        session["consent"] = True
        return redirect(url_for("auth.training"))

    flash("You must provide consent to continue.")
    return redirect(url_for("auth.consent"))















@auth_bp.route("/register-username", methods=["GET", "POST"])
def register_username():

    if not session.get("consent"):
        return redirect(url_for("auth.information"))

    if request.method == "POST":
        username = request.form.get("username")


        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT id FROM users WHERE username = ?",
            (username,)
        )
        exists = cursor.fetchone()
        conn.close()

        if exists:
            return render_template(
                "username_error.html",
                username=username
            ), 400

        return redirect(url_for("auth.register", username=username))

    return render_template("register_username.html")

@auth_bp.route("/login-username", methods=["GET", "POST"])
def login_username():

    if not session.get("consent"):
        return redirect(url_for("auth.information"))

    if request.method == "POST":
        username = request.form.get("username")

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT id FROM users WHERE username = ?",
            (username,)
        )
        user = cursor.fetchone()
        conn.close()

        if not user:
            return render_template(
                "login_username_error.html",
                username=username
            ), 404

        return redirect(url_for("auth.login", username=username))

    return render_template("login_username.html")


@auth_bp.route("/register/<username>", methods=["GET", "POST"])
def register(username):
    if request.method == "GET":
        images = sorted(os.listdir("images"))
        random.shuffle(images)
        return render_template("register.html", images=images, username=username)
    
    

    # POST: handle registration
    sequence = request.form.get("sequence")

    if not sequence:
        return "Invalid sequence", 400

    parts = sequence.split("|")
    if len(set(parts)) != len(parts):
        return "Duplicate images not allowed", 400
    
    # Prevent trivially ordered sequences (e.g. straight rows/columns)
    clean_ids = [p.replace(".svg", "") for p in parts]

    if clean_ids == sorted(clean_ids):
        return "Trivial sequence not allowed, choose another sequence.", 400


    sequence_bytes = sequence.encode("utf-8")

    pattern_hash = bcrypt.hashpw(sequence_bytes, bcrypt.gensalt())

    
    totp_secret = pyotp.random_base32()


    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO users (username, pattern_hash, totp_secret)
    VALUES (?, ?, ?)
""", (username, pattern_hash, totp_secret))


    conn.commit()
    conn.close()

    return redirect(url_for("auth.register_success"))

@auth_bp.route("/login/<username>", methods=["GET", "POST"])
def login(username):
    if request.method == "GET":
        images = sorted(os.listdir("images"))
        random.shuffle(images)
        return render_template("login.html", images=images, username=username)
    
    

    # POST: handle login
    sequence = request.form.get("sequence")
    if not sequence:
        return "Invalid sequence", 400
    
    # Start tracking authentication session
    if "login_start" not in session:
        session["login_start"] = time()
        session["graphical_attempts"] = 0
        session["incorrect_images"] = 0

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, pattern_hash, failed_attempts, lock_until
        FROM users
        WHERE username = ?
    """, (username,))
    user = cursor.fetchone()

    if not user:
        conn.close()
        return "No user found", 400

    user_id = user["id"]
    stored_hash = user["pattern_hash"]
    failed_attempts = user["failed_attempts"] or 0
    lock_until = user["lock_until"]

    now = int(time())

    # 🔒 Check if account is currently locked
    if lock_until and now < lock_until:
        remaining_seconds = lock_until - now
        remaining_minutes = max(1, remaining_seconds // 60)
        conn.close()
        return (
            f"Account locked. Try again in {remaining_minutes} minutes.",
            403
        )
    
    session["graphical_attempts"] += 1

    # 🔐 Check graphical password
    if not bcrypt.checkpw(sequence.encode("utf-8"), stored_hash):
        failed_attempts += 1

        # 🚨 Trigger lockout
        if failed_attempts >= MAX_ATTEMPTS:
            lock_until = now + LOCKOUT_SECONDS
            cursor.execute("""
                UPDATE users
                SET failed_attempts = ?, lock_until = ?
                WHERE id = ?
            """, (failed_attempts, lock_until, user_id))
            conn.commit()
            conn.close()
            return (
                "Account locked due to too many failed attempts. "
                "Try again in 5 minutes.",
                403
            )

        # ❌ Normal failure
        cursor.execute("""
            UPDATE users
            SET failed_attempts = ?
            WHERE id = ?
        """, (failed_attempts, user_id))
        conn.commit()
        conn.close()

        remaining = MAX_ATTEMPTS - failed_attempts
        return f"Login failed. {remaining} attempts remaining.", 401

    # ✅ SUCCESS — prepare recall stage

    cursor.execute("""
         UPDATE users
        SET failed_attempts = 0, lock_until = NULL
         WHERE id = ?
    """, (user_id,))
    conn.commit()
    conn.close()

    session["login_time"] = time() - session["login_start"]

    # Store original sequence in session
    original_sequence = sequence.split("|")

    session["graphical_verified"] = True
    session["graphical_sequence"] = original_sequence
    session["recall_attempts"] = 0
    session["username"] = username

    return redirect(url_for("auth.recall"))


@auth_bp.route("/recall", methods=["GET", "POST"])
def recall():

    if not session.get("graphical_verified"):
        return redirect(url_for("auth.login_username"))

    original = session.get("graphical_sequence")

    if not original:
        session.clear()
        return redirect(url_for("auth.login_username"))

    if request.method == "GET":

        if "recall_start" not in session:
            session["recall_start"] = time()

        if "recall_type" not in session:
            session["recall_type"] = random.choice(RECALL_CHALLENGES)

        challenge_type = session["recall_type"]
        instruction = get_recall_instruction(challenge_type)

        images = sorted(os.listdir("images"))
        random.shuffle(images)

        required_count = get_required_count(challenge_type)

        return render_template(
             "recall.html",
             images=images,
             instruction=instruction,
             required_count=required_count
        )

    # POST — validate recall response
    user_selection = request.form.get("sequence")

    if not user_selection:
        return "Invalid selection", 400

    selected_parts = user_selection.split("|")
    challenge_type = session.get("recall_type")

    expected = calculate_expected_sequence(original, challenge_type)

    if selected_parts == expected:
         
         session["recall_time"] = time() - session["recall_start"]

         session["recall_verified"] = True
         session.pop("recall_type", None)

          # 🔐 Generate secure OTP
         otp = secrets.randbelow(1000000)
         session["otp_code"] = f"{otp:06d}"  # zero padded 6-digit
         session["otp_expiry"] = int(time()) + 60  # valid 60 seconds
         session["otp_attempts"] = 0

         return redirect(url_for("auth.otp_token"))

    else:
         session["recall_attempts"] += 1

         if session["recall_attempts"] >= 3:
             session.clear()
             return redirect(url_for("auth.login_username"))

         return redirect(url_for("auth.recall_error"))

      
    

@auth_bp.route("/success")
def success():

    if not session.get("fully_authenticated"):
        return redirect(url_for("auth.login_username"))

    total_auth_time = time() - session.get("login_start", time())

    metrics = {
        "user_id": session.get("username"),
        "registration_time": None,
        "login_time": session.get("login_time"),
        "graphical_attempts": session.get("graphical_attempts"),
        "recall_attempts": session.get("recall_attempts"),
        "recall_time": session.get("recall_time"),
        "otp_attempts": session.get("otp_attempts"),
        "otp_time": session.get("otp_time"),
        "total_auth_time": total_auth_time,
        "login_success": 1
    }

    save_auth_metrics(metrics)

    session.clear()

    return render_template("success.html")

@auth_bp.route("/register-success")
def register_success():
    return render_template("register_success.html")

def get_recall_instruction(challenge_type):

    if challenge_type == "third_image":
        return "Select the image you chose 3rd during registration."

    elif challenge_type == "reverse_order":
        return "Select your images in reverse order."

    elif challenge_type == "second_and_fourth":
        return "Select only the 2nd and 4th images."

    elif challenge_type == "first_and_last":
        return "Select your first and last image."

@auth_bp.route("/recall-error")
def recall_error():
    return render_template("recall_error.html")

def calculate_expected_sequence(original, challenge_type):

    if challenge_type == "third_image":
        return [original[2]]

    elif challenge_type == "reverse_order":
        return list(reversed(original))

    elif challenge_type == "second_and_fourth":
        return [original[1], original[3]]

    elif challenge_type == "first_and_last":
        return [original[0], original[-1]]
    
def get_required_count(challenge_type):

    if challenge_type == "third_image":
        return 1

    elif challenge_type == "reverse_order":
        return 4

    elif challenge_type == "second_and_fourth":
        return 2

    elif challenge_type == "first_and_last":
        return 2


@auth_bp.route("/otp-token")
def otp_token():

    if not session.get("recall_verified"):
        return redirect(url_for("auth.login_username"))

    remaining = session.get("otp_expiry", 0) - int(time())

    if "otp_start" not in session:
        session["otp_start"] = time()
        session["otp_attempts"] = 0

    if remaining <= 0:
        # regenerate new OTP
        otp = secrets.randbelow(1000000)
        session["otp_code"] = f"{otp:06d}"
        session["otp_expiry"] = int(time()) + 60
        session["otp_attempts"] = 0
        remaining = 60

    response = make_response(
        render_template("otp_token.html", remaining=remaining)
    )

    # 🔒 Prevent browser caching of OTP page
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"

    return response

@auth_bp.route("/otp", methods=["GET", "POST"])
def otp():

    if not session.get("recall_verified"):
        return redirect(url_for("auth.login_username"))

    if request.method == "POST":

        user_code = request.form.get("otp")
        now = int(time())

        if session.get("otp_attempts", 0) >= 3:
            session.clear()
            return "Too many attempts. Login again.", 403

        if now > session.get("otp_expiry", 0):
            session.clear()
            return "Code expired. Login again.", 403

        if user_code == session.get("otp_code"):
            session["otp_time"] = time() - session["otp_start"]

            session.pop("otp_code", None)
            session.pop("otp_expiry", None)
            session.pop("otp_attempts", None)

            session["fully_authenticated"] = True

            return redirect(url_for("auth.success"))

        else:
            session["otp_attempts"] += 1
            return render_template("otp_token.html", 
                                   remaining=session["otp_expiry"] - int(time()),
                                   error="Invalid code.")

    return redirect(url_for("auth.otp_token"))

@auth_bp.route("/training")
def training():

    if not session.get("consent"):
        return redirect(url_for("auth.information"))

    return render_template("training.html")