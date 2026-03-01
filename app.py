from flask import Flask, render_template, request, redirect, session, Response
import mysql.connector
import os
from datetime import datetime, timedelta



app = Flask(__name__)
app.secret_key = "intellimess_secret"

# ---------------- DATABASE ----------------
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="8121",
        database="intellimess"
    )

# ---------------- HOME ----------------
@app.route('/')
def home():
    return redirect('/login')

# ---------------- REGISTER ----------------
@app.route('/register')
def register_page():
    return render_template("register.html")

@app.route('/register', methods=['POST'])
def register():
    username = request.form['username']
    password = request.form['password']
    roll_no = request.form['roll_no']
    phone_no = request.form['phone_no']
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO users (username, password, role, roll_no, phone_no)
        VALUES (%s, %s, 'student', %s, %s)
    """, (username, password, roll_no, phone_no))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect('/login')

# ---------------- LOGIN ----------------
@app.route('/login')
def login_page():
    return render_template("login.html")

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE username=%s AND password=%s", (username, password))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    if user:
        session['user_id'] = user['id']
        session['role'] = user['role']
        session['username'] = user['username']
        if user['role'] == 'admin':
            return redirect('/admin')
        else:
            return redirect('/student')
    else:
        return "Invalid username or password"

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

# ---------------- STUDENT DASHBOARD ----------------
@app.route('/student')
def student_dashboard():
    if 'user_id' not in session or session['role'] != 'student':
        return redirect('/login')

    # ---- Meal reminder banner ----
    now = datetime.now()
    today = now.date()
    user_id = session['user_id']

    # Meal closing times (booking window closes before the meal)
    meal_closing = [
        ("Breakfast", 6,  0),
        ("Lunch",     9,  0),
        ("Snacks",    12, 0),
        ("Dinner",    16, 30),
    ]
    # Actual meal serve times (used to know which date it's for)
    meal_serve_hour = {"Breakfast": 8, "Lunch": 13, "Snacks": 16, "Dinner": 20}

    reminder = None

    # Check DB for today's bookings by this student
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True, buffered=True)

    for meal, close_h, close_m in meal_closing:
        close_time = now.replace(hour=close_h, minute=close_m, second=0, microsecond=0)
        if now < close_time:
            # This meal's booking window is still open
            # Check if student already booked this meal today
            cur.execute("""
                SELECT id FROM bookings
                WHERE user_id=%s AND meal=%s AND booking_date=%s
            """, (user_id, meal, today))
            already_booked = cur.fetchone() is not None

            mins_left = int((close_time - now).total_seconds() / 60)
            if mins_left >= 60:
                h = mins_left // 60; m = mins_left % 60
                time_str = f"{h}h {m}m" if m else f"{h}h"
            else:
                time_str = f"{mins_left} min"

            reminder = {
                "meal":           meal,
                "time_str":       time_str,
                "urgent":         mins_left <= 30,
                "closed":         False,
                "already_booked": already_booked,
                "meal_date":      "today",
            }
            break

    # All today's windows closed — check tomorrow's Breakfast
    if reminder is None:
        tomorrow = today + timedelta(days=1)
        tomorrow_close = now.replace(hour=6, minute=0, second=0, microsecond=0) + timedelta(days=1)
        mins_left = int((tomorrow_close - now).total_seconds() / 60)
        h = mins_left // 60; m = mins_left % 60
        time_str = f"{h}h {m}m" if m else f"{h}h"

        cur.execute("""
            SELECT id FROM bookings
            WHERE user_id=%s AND meal='Breakfast' AND booking_date=%s
        """, (user_id, tomorrow))
        already_booked = cur.fetchone() is not None

        reminder = {
            "meal":           "Breakfast",
            "time_str":       time_str,
            "urgent":         False,
            "closed":         True,
            "already_booked": already_booked,
            "meal_date":      "tomorrow",
        }

    cur.close(); conn.close()

    # Fetch streak for dashboard mini-display
    conn2 = get_db_connection()
    cur2 = conn2.cursor(dictionary=True, buffered=True)
    cur2.execute("SELECT current_streak, total_feedbacks FROM user_streaks WHERE user_id=%s", (user_id,))
    streak_info = cur2.fetchone() or {'current_streak': 0, 'total_feedbacks': 0}
    cur2.execute("SELECT badge_key FROM user_badges WHERE user_id=%s ORDER BY awarded_at DESC LIMIT 3", (user_id,))
    recent_badges = [r['badge_key'] for r in cur2.fetchall()]
    cur2.close(); conn2.close()

    return render_template("student.html",
        username=session.get('username', ''),
        reminder=reminder,
        streak_info=streak_info,
        recent_badges=recent_badges,
    )

# ---------------- MENU ----------------
@app.route('/menu')
def menu():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True, buffered=True)
    meal_times = [("Breakfast","07:30"),("Lunch","11:45"),("Snacks","16:30"),("Dinner","19:30")]
    now = datetime.now()
    today = now.strftime("%A")
    current_time = now.strftime("%H:%M")
    next_meals = []
    day_index = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
    today_date = now.date()
    start_day = day_index.index(today)
    i = 0
    while len(next_meals) < 4:
        day = day_index[(start_day + i) % 7]
        actual_date = today_date + timedelta(days=i)
        for meal, time in meal_times:
            if i == 0 and time <= current_time:
                continue
            next_meals.append((day, actual_date, meal))
            if len(next_meals) == 4:
                break
        i += 1
    menu_data = []
    for day, actual_date, meal in next_meals:
        cursor.execute("""
            SELECT d.dish_name FROM weekly_menu wm
            JOIN menu_items mi ON wm.id = mi.weekly_menu_id
            JOIN dishes d ON mi.dish_id = d.id
            WHERE wm.day_of_week = %s AND wm.meal = %s
        """, (day, meal))
        dishes = [row['dish_name'] for row in cursor.fetchall()]
        # Option C: poll winner shown as special dish for this specific date
        cursor.execute("""
            SELECT winner_dish FROM polls
            WHERE poll_date = %s AND meal = %s
            AND status = 'closed' AND winner_dish IS NOT NULL
            ORDER BY id DESC LIMIT 1
        """, (actual_date, meal))
        poll_winner = cursor.fetchone()
        special = poll_winner['winner_dish'] if poll_winner else None
        menu_data.append({"day": day, "date": actual_date, "meal": meal,
                          "dishes": dishes, "special": special})
    cursor.close()
    conn.close()
    return render_template("menu.html", menu_data=menu_data)

# ---------------- BOOKING ----------------
@app.route('/booking')
def booking_page():
    if 'user_id' not in session:
        return redirect('/login')
    return render_template("booking.html")

@app.route('/book', methods=['POST'])
def book():
    if 'user_id' not in session:
        return redirect('/login')
    user_id = session['user_id']
    meal = request.form['meal']
    food_type = request.form['food_type']
    date_str = request.form['date']

    # Guest booking
    bring_guest = request.form.get('bring_guest') == 'on'
    guest_count = 0
    guest_food_type = None
    if bring_guest:
        try:
            guest_count = int(request.form.get('guest_count', 0))
        except ValueError:
            guest_count = 0
        if guest_count < 1 or guest_count > 10:
            return "Invalid guest count. Must be 1–10."
        guest_food_type = request.form.get('guest_food_type', food_type)

    now = datetime.now()
    today = now.date()
    tomorrow = today + timedelta(days=1)
    booking_date = datetime.strptime(date_str, "%Y-%m-%d").date()

    if booking_date not in [today, tomorrow]:
        return "Booking allowed only for today or tomorrow."

    meal_times = {"Breakfast": 8, "Lunch": 13, "Snacks": 16, "Dinner": 20}
    meal_hour = meal_times[meal]
    meal_datetime = datetime.combine(booking_date, datetime.min.time()).replace(hour=meal_hour)

    if meal == "Breakfast":
        closing_time = meal_datetime.replace(hour=6, minute=0)
    elif meal == "Dinner":
        closing_time = meal_datetime.replace(hour=16, minute=30)
    else:
        closing_time = meal_datetime - timedelta(hours=4)

    if now >= meal_datetime:
        return f"{meal} time has already passed."
    if now >= closing_time:
        return f"Booking for {meal} is closed."

    current_time = now.strftime("%H:%M:%S")
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id FROM bookings WHERE user_id=%s AND meal=%s AND booking_date=%s
    """, (user_id, meal, booking_date))
    if cursor.fetchone():
        cursor.close()
        conn.close()
        return "<script>alert('You have already booked this meal.'); window.location.href='/student';</script>"

    cursor.execute("""
        INSERT INTO bookings (user_id, meal, food_type, booking_date, booking_time, guest_count, guest_food_type)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (user_id, meal, food_type, booking_date, current_time, guest_count, guest_food_type))
    conn.commit()
    cursor.close()
    conn.close()
    return "<script>alert('Booking Successful!'); window.location.href='/student';</script>"

# ---------------- FEEDBACK ----------------
@app.route('/feedback')
def feedback():
    if 'user_id' not in session:
        return redirect('/login')
    user_id = session['user_id']
    now = datetime.now()
    today = now.date()
    meal_times = {"Breakfast": 7, "Lunch": 12, "Snacks": 16, "Dinner": 19}
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True, buffered=True)
    three_days_ago = today - timedelta(days=3)
    cursor.execute("""
        SELECT id, meal, food_type, booking_date FROM bookings
        WHERE user_id = %s AND booking_date <= %s AND booking_date >= %s
    """, (user_id, today, three_days_ago))
    bookings = cursor.fetchall()
    feedback_data = []
    for booking in bookings:
        meal = booking['meal']
        food_type = booking['food_type']
        booking_id = booking['id']
        booking_date = booking['booking_date']
        meal_hour = meal_times.get(meal)
        meal_time = datetime.combine(booking_date, datetime.min.time()).replace(hour=meal_hour)
        if now < meal_time:
            continue
        cursor.execute("SELECT COUNT(*) as count FROM feedback WHERE booking_id = %s", (booking_id,))
        if cursor.fetchone()['count'] > 0:
            continue
        day_name = booking_date.strftime('%A')
        if food_type == "Veg":
            cursor.execute("""
                SELECT d.id, d.dish_name FROM dishes d
                JOIN menu_items mi ON d.id = mi.dish_id
                JOIN weekly_menu wm ON wm.id = mi.weekly_menu_id
                WHERE wm.day_of_week = %s AND wm.meal = %s
                AND d.dish_name NOT LIKE '%Chicken%' AND d.dish_name NOT LIKE '%Egg%'
            """, (day_name, meal))
        else:
            cursor.execute("""
                SELECT d.id, d.dish_name FROM dishes d
                JOIN menu_items mi ON d.id = mi.dish_id
                JOIN weekly_menu wm ON wm.id = mi.weekly_menu_id
                WHERE wm.day_of_week = %s AND wm.meal = %s
            """, (day_name, meal))
        dishes = cursor.fetchall()
        feedback_data.append({"booking_id": booking_id, "meal": meal, "dishes": dishes, "booking_date": booking_date})
    cursor.close()
    conn.close()
    return render_template("feedback.html", feedback_data=feedback_data)

@app.route('/submit_feedback', methods=['POST'])
def submit_feedback():
    if 'user_id' not in session:
        return redirect('/login')
    user_id = session['user_id']
    booking_id = request.form.get('booking_id')
    feedback_date = datetime.now().date()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM feedback WHERE booking_id = %s", (booking_id,))
    if cursor.fetchone():
        cursor.close()
        conn.close()
        return redirect('/student')
    for key in request.form.keys():
        if key.startswith("consumed_"):
            dish_id = key.split("_")[1]
            rating = request.form.get(f'rating_{dish_id}')
            comment = request.form.get(f'comment_{dish_id}')
            if rating:
                cursor.execute("""
                    INSERT INTO feedback (user_id, booking_id, dish_id, rating, feedback_date, comment)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (user_id, booking_id, dish_id, rating, feedback_date, comment))
    conn.commit()
    # Update streak and check for new badges
    update_streak_and_badges(user_id, conn)
    cursor.close()
    conn.close()
    return redirect('/achievements')

# ================================================================
# ----------------  POLLING SYSTEM  ------------------------------
# ================================================================

@app.route('/admin/polls')
def admin_polls():
    if session.get('role') != 'admin':
        return redirect('/login')
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True, buffered=True)
    cursor.execute("""
        SELECT p.id, p.question, p.meal, p.poll_date, p.closing_time, p.status,
               p.winner_dish,
               COUNT(DISTINCT pv.user_id) as total_votes
        FROM polls p
        LEFT JOIN poll_votes pv ON p.id = pv.poll_id
        GROUP BY p.id ORDER BY p.id DESC
    """)
    polls = cursor.fetchall()
    for poll in polls:
        cursor.execute("""
            SELECT po.id, po.option_text, COUNT(pv.id) as vote_count
            FROM poll_options po
            LEFT JOIN poll_votes pv ON po.id = pv.option_id
            WHERE po.poll_id = %s GROUP BY po.id ORDER BY vote_count DESC
        """, (poll['id'],))
        poll['options'] = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template("admin_polls.html", polls=polls)

@app.route('/admin/polls/create', methods=['POST'])
def create_poll():
    if session.get('role') != 'admin':
        return redirect('/login')
    question = request.form['question']
    meal = request.form['meal']
    poll_date = request.form['poll_date']
    closing_time = request.form['closing_time']
    options = [o.strip() for o in request.form.getlist('options[]') if o.strip()]
    if len(options) < 2:
        return "Please provide at least 2 options."
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO polls (question, meal, poll_date, closing_time, status)
        VALUES (%s, %s, %s, %s, 'open')
    """, (question, meal, poll_date, closing_time))
    poll_id = cursor.lastrowid
    for option_text in options:
        cursor.execute("INSERT INTO poll_options (poll_id, option_text) VALUES (%s, %s)", (poll_id, option_text))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect('/admin/polls')

@app.route('/admin/polls/close/<int:poll_id>')
def close_poll(poll_id):
    if session.get('role') != 'admin':
        return redirect('/login')
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True, buffered=True)
    # Find winning option — just save winner_dish on the poll row (Option C)
    cursor.execute("""
        SELECT po.option_text, COUNT(pv.id) as vote_count
        FROM poll_options po
        LEFT JOIN poll_votes pv ON po.id = pv.option_id
        WHERE po.poll_id = %s
        GROUP BY po.id ORDER BY vote_count DESC LIMIT 1
    """, (poll_id,))
    winner = cursor.fetchone()
    dish_name = winner['option_text'] if winner and winner['vote_count'] > 0 else None
    c = conn.cursor()
    c.execute("UPDATE polls SET status='closed', winner_dish=%s WHERE id=%s", (dish_name, poll_id))
    conn.commit()
    c.close(); cursor.close(); conn.close()
    return redirect('/admin/polls')

@app.route('/polls')
def polls():
    if 'user_id' not in session or session['role'] != 'student':
        return redirect('/login')
    user_id = session['user_id']
    now = datetime.now()
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True, buffered=True)

    # Auto-close expired polls — just save winner_dish (Option C, no menu pollution)
    cursor.execute("""
        SELECT id FROM polls
        WHERE status='open' AND CONCAT(poll_date, ' ', closing_time) < %s
    """, (now.strftime('%Y-%m-%d %H:%M:%S'),))
    expired = cursor.fetchall()
    for ep in expired:
        c2 = conn.cursor(dictionary=True, buffered=True)
        c2.execute("""
            SELECT po.option_text, COUNT(pv.id) as vote_count
            FROM poll_options po
            LEFT JOIN poll_votes pv ON po.id = pv.option_id
            WHERE po.poll_id = %s GROUP BY po.id ORDER BY vote_count DESC LIMIT 1
        """, (ep['id'],))
        winner = c2.fetchone()
        dish_name = winner['option_text'] if winner and winner['vote_count'] > 0 else None
        c3 = conn.cursor()
        c3.execute("UPDATE polls SET status='closed', winner_dish=%s WHERE id=%s", (dish_name, ep['id']))
        conn.commit()
        c2.close(); c3.close()

    # Open polls — show ALL polls with future closing time
    cursor.execute("""
        SELECT id, question, meal, poll_date, closing_time
        FROM polls WHERE status='open'
        ORDER BY poll_date ASC, closing_time ASC
    """)
    open_polls = cursor.fetchall()
    polls_data = []
    for poll in open_polls:
        cursor.execute("SELECT option_id FROM poll_votes WHERE poll_id=%s AND user_id=%s", (poll['id'], user_id))
        user_vote = cursor.fetchone()
        cursor.execute("""
            SELECT po.id, po.option_text, COUNT(pv.id) as vote_count
            FROM poll_options po LEFT JOIN poll_votes pv ON po.id = pv.option_id
            WHERE po.poll_id = %s GROUP BY po.id
        """, (poll['id'],))
        poll['options'] = cursor.fetchall()
        poll['user_voted'] = user_vote is not None
        poll['user_vote_option'] = user_vote['option_id'] if user_vote else None
        polls_data.append(poll)
    # Recent closed polls
    cursor.execute("""
        SELECT DISTINCT p.id, p.question, p.meal, p.poll_date FROM polls p
        JOIN poll_votes pv ON p.id = pv.poll_id
        WHERE p.status = 'closed' AND pv.user_id = %s ORDER BY p.id DESC LIMIT 5
    """, (user_id,))
    past_polls_raw = cursor.fetchall()
    past_polls = []
    for poll in past_polls_raw:
        cursor.execute("""
            SELECT po.option_text, COUNT(pv.id) as vote_count FROM poll_options po
            LEFT JOIN poll_votes pv ON po.id = pv.option_id
            WHERE po.poll_id = %s GROUP BY po.id ORDER BY vote_count DESC
        """, (poll['id'],))
        poll['options'] = cursor.fetchall()
        past_polls.append(poll)
    cursor.close()
    conn.close()
    return render_template("polls.html", polls=polls_data, past_polls=past_polls)

@app.route('/polls/vote', methods=['POST'])
def vote_poll():
    if 'user_id' not in session or session['role'] != 'student':
        return redirect('/login')
    user_id = session['user_id']
    poll_id = request.form.get('poll_id')
    option_id = request.form.get('option_id')
    if not poll_id or not option_id:
        return redirect('/polls')
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT status FROM polls WHERE id=%s", (poll_id,))
    poll = cursor.fetchone()
    if not poll or poll['status'] != 'open':
        cursor.close()
        conn.close()
        return "<script>alert('This poll is closed.'); window.location.href='/polls';</script>"
    cursor.execute("SELECT id FROM poll_votes WHERE poll_id=%s AND user_id=%s", (poll_id, user_id))
    if cursor.fetchone():
        cursor.close()
        conn.close()
        return "<script>alert('You have already voted.'); window.location.href='/polls';</script>"
    cursor2 = conn.cursor()
    cursor2.execute("INSERT INTO poll_votes (poll_id, option_id, user_id) VALUES (%s, %s, %s)", (poll_id, option_id, user_id))
    conn.commit()
    cursor.close()
    cursor2.close()
    conn.close()
    return "<script>alert('Vote submitted successfully!'); window.location.href='/polls';</script>"

# ================================================================
# ----------------  SENTIMENT ANALYSIS HELPER  ------------------
# ================================================================
def analyze_sentiment(text):
    """
    Rule-based sentiment scorer — no external ML library needed.
    Returns: 'Positive', 'Negative', or 'Neutral'  + a score -1..+1
    """
    if not text or not text.strip():
        return 'Neutral', 0.0

    text_lower = text.lower()

    positive_words = [
        'good','great','excellent','amazing','delicious','tasty','loved',
        'fantastic','wonderful','nice','perfect','enjoyed','fresh','hot',
        'crispy','yummy','best','awesome','superb','happy','satisfied',
        'well','better','clean','quality','flavour','flavor','rich','soft'
    ]
    negative_words = [
        'bad','poor','terrible','awful','horrible','disgusting','cold',
        'stale','overcooked','undercooked','oily','bland','worst','hate',
        'unhappy','disappointed','tasteless','hard','burnt','raw','dirty',
        'spicy','less','no','not','never','complaint','issue','problem',
        'delay','late','slow','waste','watery'
    ]
    negation_words = ['not','no','never','neither','nor','without']

    words = text_lower.split()
    score = 0
    i = 0
    while i < len(words):
        word = words[i].strip('.,!?;:')
        negated = (i > 0 and words[i-1].strip('.,!?;:') in negation_words)
        if word in positive_words:
            score += -1 if negated else +1
        elif word in negative_words:
            score += +1 if negated else -1
        i += 1

    if score > 0:
        return 'Positive', min(score / 3, 1.0)
    elif score < 0:
        return 'Negative', max(score / 3, -1.0)
    else:
        return 'Neutral', 0.0


# ---------------- ADMIN DASHBOARD ----------------
@app.route('/admin')
def admin():
    if session.get('role') != 'admin':
        return redirect('/login')
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True, buffered=True)

    cursor.execute("""
        SELECT b.*, u.username, u.roll_no
        FROM bookings b JOIN users u ON b.user_id = u.id
        ORDER BY b.booking_date DESC, b.booking_time DESC
    """)
    bookings = cursor.fetchall() or []

    meal_schedule = [("Breakfast",7),("Lunch",12),("Snacks",16),("Dinner",19)]
    now = datetime.now()
    today_date = now.date()
    next_meal = None
    for meal, hour in meal_schedule:
        if now < datetime.combine(today_date, datetime.min.time()).replace(hour=hour):
            next_meal = meal
            break
    if not next_meal:
        next_meal = "Breakfast"
        today_date += timedelta(days=1)

    cursor.execute("""
        SELECT
            COUNT(*) as student_count,
            COALESCE(SUM(guest_count), 0) as total_guests,
            SUM(CASE WHEN food_type='Veg' THEN 1 ELSE 0 END) as veg_students,
            SUM(CASE WHEN food_type='Non-Veg' THEN 1 ELSE 0 END) as nonveg_students,
            SUM(CASE WHEN guest_food_type='Veg' THEN COALESCE(guest_count,0) ELSE 0 END) as veg_guests,
            SUM(CASE WHEN guest_food_type='Non-Veg' THEN COALESCE(guest_count,0) ELSE 0 END) as nonveg_guests
        FROM bookings WHERE meal=%s AND booking_date=%s
    """, (next_meal, today_date))
    ms = cursor.fetchone()
    student_count = ms['student_count'] or 0
    total_guests = int(ms['total_guests'] or 0)
    next_meal_count = student_count + total_guests
    veg_count = int(ms['veg_students'] or 0) + int(ms['veg_guests'] or 0)
    nonveg_count = int(ms['nonveg_students'] or 0) + int(ms['nonveg_guests'] or 0)

    # lightweight queries only
    cursor.execute("SELECT COUNT(*) as total FROM bookings")
    bookings_total = cursor.fetchone()['total'] or 0
    cursor.execute("SELECT COUNT(*) as cnt FROM polls WHERE status='open'")
    open_polls_count = cursor.fetchone()['cnt']
    cursor.execute("SELECT AVG(rating) as overall FROM feedback")
    ov = cursor.fetchone()
    overall_avg = round(float(ov['overall']), 2) if ov and ov['overall'] else 0
    cursor.execute("SELECT COUNT(*) as total FROM bookings")
    total_bk = cursor.fetchone()['total'] or 1
    cursor.execute("SELECT COUNT(DISTINCT booking_id) as fb FROM feedback")
    fb_bk = cursor.fetchone()['fb'] or 0
    feedback_rate = round(fb_bk / total_bk * 100, 1)

    # ── Engagement / gamification summary ──
    cursor.execute("""
        SELECT COUNT(*) as active_streaks FROM user_streaks
        WHERE current_streak > 0
    """)
    active_streaks = cursor.fetchone()['active_streaks'] or 0

    cursor.execute("""
        SELECT u.username, us.current_streak, us.total_feedbacks,
               (SELECT COUNT(*) FROM user_badges ub WHERE ub.user_id=u.id) as badges
        FROM user_streaks us JOIN users u ON us.user_id=u.id
        WHERE u.role='student' AND us.current_streak > 0
        ORDER BY us.current_streak DESC LIMIT 5
    """)
    top_streaks = cursor.fetchall() or []

    cursor.execute("SELECT COUNT(*) as c FROM user_badges")
    total_badges_awarded = cursor.fetchone()['c'] or 0

    cursor.execute("""
        SELECT badge_key, COUNT(*) as cnt FROM user_badges
        GROUP BY badge_key ORDER BY cnt DESC LIMIT 3
    """)
    top_badge_rows = cursor.fetchall() or []
    badge_icons = {'first_bite':'🌱','on_a_roll':'🔥','week_warrior':'⭐','fortnight':'🏅',
                   'monthly_hero':'👑','critic':'🎯','connoisseur':'🍽️','mess_legend':'🏆',
                   'five_star':'💫','honest_critic':'📝'}
    top_badges = [{'icon': badge_icons.get(r['badge_key'],'🏅'),
                   'key':  r['badge_key'].replace('_',' ').title(),
                   'cnt':  r['cnt']} for r in top_badge_rows]

    # ── Comeback suggestions (high-rated dishes not served in 14+ days) ──
    cursor.execute("""
        SELECT d.dish_name,
               ROUND(AVG(f.rating), 1) as avg_rating,
               MAX(b.booking_date) as last_served,
               DATEDIFF(CURDATE(), MAX(b.booking_date)) as days_ago
        FROM feedback f
        JOIN dishes d ON f.dish_id = d.id
        JOIN bookings b ON f.booking_id = b.id
        GROUP BY d.dish_name
        HAVING avg_rating >= 4.0
           AND MAX(b.booking_date) <= DATE_SUB(CURDATE(), INTERVAL 14 DAY)
        ORDER BY avg_rating DESC
        LIMIT 5
    """)
    comeback_dishes = cursor.fetchall() or []

    cursor.close()
    conn.close()

    return render_template("admin.html",
        next_meal=next_meal, next_meal_date=today_date,
        next_meal_count=next_meal_count, student_count=student_count,
        total_guests=total_guests, veg_count=veg_count, nonveg_count=nonveg_count,
        bookings_total=bookings_total, open_polls_count=open_polls_count,
        overall_avg=overall_avg, feedback_rate=feedback_rate,
        active_streaks=active_streaks, top_streaks=top_streaks,
        total_badges_awarded=total_badges_awarded, top_badges=top_badges,
        comeback_dishes=comeback_dishes,
    )


# ================================================================
# ----------------  WEEKLY PDF REPORT  ---------------------------
# ================================================================
@app.route('/admin/report')
def download_report():
    if session.get('role') != 'admin':
        return redirect('/login')

    import io, matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import numpy as np
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                    Table, TableStyle, HRFlowable, PageBreak,
                                    Image as RLImage)
    from reportlab.lib.enums import TA_CENTER, TA_LEFT

    import io, matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import numpy as np
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                    Table, TableStyle, HRFlowable, PageBreak,
                                    Image as RLImage)
    from reportlab.lib.enums import TA_CENTER, TA_LEFT

    CLR_GREEN='#2e7d32';CLR_LGREEN='#e8f5e9';CLR_ORANGE='#e65100'
    CLR_BLUE='#1565c0';CLR_RED='#c62828';CLR_GREY='#616161'
    MEAL_COLORS={'Breakfast':'#FF9800','Lunch':'#4CAF50','Snacks':'#9c27b0','Dinner':'#1976d2'}
    RATING_COLORS=['#ef5350','#ff9800','#ffc107','#8bc34a','#4CAF50']
    plt.rcParams.update({'font.family':'DejaVu Sans','axes.spines.top':False,'axes.spines.right':False})

    def _img(fig, w, h):
        b = io.BytesIO()
        fig.savefig(b, format='png', dpi=160, bbox_inches='tight', facecolor='white', edgecolor='none')
        plt.close(fig); b.seek(0)
        return RLImage(b, width=w*cm, height=h*cm)

    def _trend(dates, counts, w=16, h=5.5):
        fig, ax = plt.subplots(figsize=(w*.38, h*.38))
        xs = range(len(dates))
        ax.fill_between(xs, counts, alpha=0.12, color=CLR_GREEN)
        ax.plot(xs, counts, color=CLR_GREEN, lw=2.2, marker='o', ms=6, mfc=CLR_GREEN, mec='white', mew=1.5, zorder=5)
        ax.set_xticks(list(xs)); ax.set_xticklabels(dates, fontsize=8, rotation=25, ha='right')
        ax.set_ylabel('Bookings', fontsize=8, color=CLR_GREY)
        ax.set_title('Daily Booking Trend', fontsize=10, fontweight='bold', color=CLR_GREEN, pad=10)
        ax.yaxis.grid(True, ls='--', alpha=0.4, zorder=0); ax.set_axisbelow(True)
        ax.set_facecolor('#fafafa'); fig.patch.set_facecolor('white')
        for i, v in enumerate(counts):
            ax.annotate(str(v), (i,v), xytext=(0,7), textcoords='offset points',
                        ha='center', fontsize=8, color='#333', fontweight='bold')
        plt.tight_layout(pad=1.2); return _img(fig, w, h)

    def _bar(labels, values, bcolors, title, ylabel='Count', w=8, h=6):
        fig, ax = plt.subplots(figsize=(w*.38, h*.38))
        bars = ax.bar(labels, values, color=bcolors, edgecolor='white', lw=0.8, zorder=3, width=0.55)
        ax.set_title(title, fontsize=9.5, fontweight='bold', color=CLR_GREEN, pad=8)
        ax.set_ylabel(ylabel, fontsize=8, color=CLR_GREY)
        ax.tick_params(labelsize=8); ax.set_facecolor('#fafafa'); fig.patch.set_facecolor('white')
        ax.yaxis.grid(True, ls='--', alpha=0.4, zorder=0); ax.set_axisbelow(True)
        for b in bars:
            v = b.get_height()
            if v > 0:
                ax.text(b.get_x()+b.get_width()/2, v+0.08,
                        str(int(v)) if v == int(v) else f'{v:.1f}',
                        ha='center', va='bottom', fontsize=8, fontweight='bold', color='#333')
        plt.tight_layout(pad=1.2); return _img(fig, w, h)

    def _hbar(labels, values, bcolors, title, w=16, h=5.5):
        fig, ax = plt.subplots(figsize=(w*.38, max(h*.38, len(labels)*.55)))
        ys = range(len(labels))
        bars = ax.barh(list(ys), values, color=bcolors, edgecolor='white', lw=0.8, height=0.55, zorder=3)
        ax.set_yticks(list(ys)); ax.set_yticklabels(labels, fontsize=8.5)
        ax.set_xlim(0, 5.6); ax.axvline(5, color='#ddd', lw=1, ls='--')
        ax.set_xlabel('Average Rating (out of 5)', fontsize=8, color=CLR_GREY)
        ax.set_title(title, fontsize=9.5, fontweight='bold', color=CLR_GREEN, pad=8)
        ax.xaxis.grid(True, ls='--', alpha=0.4, zorder=0); ax.set_axisbelow(True)
        ax.set_facecolor('#fafafa'); fig.patch.set_facecolor('white')
        for b, v in zip(bars, values):
            ax.text(v+0.08, b.get_y()+b.get_height()/2, f'{v:.1f}',
                    va='center', fontsize=8.5, fontweight='bold', color='#333')
        plt.tight_layout(pad=1.2); return _img(fig, w, h)

    def _donut(labels, values, clrs, title, w=8, h=6):
        fig, ax = plt.subplots(figsize=(w*.38, h*.38))
        wedges, _, autos = ax.pie(values, colors=clrs, autopct='%1.0f%%', startangle=90,
            wedgeprops=dict(width=0.52, edgecolor='white', lw=2.5), pctdistance=0.72)
        for a in autos: a.set(fontsize=9, color='white', fontweight='bold')
        ax.set_title(title, fontsize=9.5, fontweight='bold', color=CLR_GREEN, pad=8)
        ax.legend(wedges, [f'{l}  ({v})' for l,v in zip(labels,values)],
            loc='lower center', bbox_to_anchor=(0.5,-0.14), ncol=2, fontsize=8, frameon=False)
        plt.tight_layout(pad=1.2); return _img(fig, w, h)

    def _sent_stack(names, pos, neg, neu, w=16, h=6):
        fig, ax = plt.subplots(figsize=(w*.38, max(h*.38, len(names)*.6)))
        ys = np.arange(len(names))
        pos_a, neg_a, neu_a = np.array(pos), np.array(neg), np.array(neu)
        ax.barh(ys, pos_a, color='#66bb6a', label='Positive', zorder=3, height=0.55)
        ax.barh(ys, neu_a, left=pos_a, color='#bdbdbd', label='Neutral', zorder=3, height=0.55)
        ax.barh(ys, neg_a, left=pos_a+neu_a, color='#ef5350', label='Negative', zorder=3, height=0.55)
        ax.set_yticks(ys); ax.set_yticklabels(names, fontsize=8.5)
        ax.set_xlim(0, 100); ax.set_xlabel('% of Comments', fontsize=8, color=CLR_GREY)
        ax.set_title('Comment Sentiment per Dish', fontsize=9.5, fontweight='bold', color=CLR_GREEN, pad=8)
        ax.xaxis.grid(True, ls='--', alpha=0.4, zorder=0); ax.set_axisbelow(True)
        ax.set_facecolor('#fafafa'); fig.patch.set_facecolor('white')
        ax.legend(loc='lower right', fontsize=8, frameon=False)
        plt.tight_layout(pad=1.2); return _img(fig, w, h)


    # ── data collection ──
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True, buffered=True)
    now = datetime.now()
    week_ago = now.date() - timedelta(days=7)

    cursor.execute("""
        SELECT COUNT(*) as total,
               SUM(CASE WHEN food_type='Veg' THEN 1 ELSE 0 END) as veg,
               SUM(CASE WHEN food_type='Non-Veg' THEN 1 ELSE 0 END) as nonveg,
               COALESCE(SUM(guest_count),0) as guests
        FROM bookings WHERE booking_date >= %s
    """, (week_ago,))
    bk = cursor.fetchone()

    cursor.execute("SELECT DATE(booking_date) as bdate, COUNT(*) as cnt FROM bookings WHERE booking_date >= %s GROUP BY DATE(booking_date) ORDER BY bdate ASC", (week_ago,))
    daily = cursor.fetchall() or []
    cursor.execute("SELECT meal, COUNT(*) as cnt FROM bookings WHERE booking_date >= %s GROUP BY meal ORDER BY cnt DESC", (week_ago,))
    meal_bk = cursor.fetchall() or []
    cursor.execute("SELECT food_type, COUNT(*) as cnt FROM bookings WHERE booking_date >= %s GROUP BY food_type", (week_ago,))
    food_bk = cursor.fetchall() or []
    cursor.execute("SELECT rating, COUNT(*) as cnt FROM feedback JOIN bookings b ON feedback.booking_id=b.id WHERE b.booking_date >= %s GROUP BY rating ORDER BY rating", (week_ago,))
    rdist = cursor.fetchall() or []
    cursor.execute("""
        SELECT d.dish_name, AVG(f.rating) as avg_r, COUNT(f.id) as reviews,
               GROUP_CONCAT(f.comment SEPARATOR '||||') as comments
        FROM feedback f JOIN dishes d ON f.dish_id=d.id JOIN bookings b ON f.booking_id=b.id
        WHERE b.booking_date >= %s GROUP BY d.dish_name ORDER BY avg_r DESC
    """, (week_ago,))
    dish_rows = cursor.fetchall() or []
    cursor.execute("SELECT b.meal, AVG(f.rating) as avg_r FROM feedback f JOIN bookings b ON f.booking_id=b.id WHERE b.booking_date >= %s GROUP BY b.meal ORDER BY avg_r DESC", (week_ago,))
    meal_sat = cursor.fetchall() or []
    cursor.execute("""
        SELECT p.question, p.meal, p.poll_date, p.winner_dish,
               COUNT(DISTINCT pv.user_id) as votes FROM polls p
        LEFT JOIN poll_votes pv ON p.id=pv.poll_id
        WHERE p.poll_date >= %s GROUP BY p.id ORDER BY p.poll_date DESC
    """, (week_ago,))
    poll_rows = cursor.fetchall() or []
    cursor.execute("""
        SELECT ds.dish_name, ds.meal, ds.votes, ds.reason, u.username
        FROM dish_suggestions ds JOIN users u ON ds.user_id=u.id
        WHERE ds.status != 'declined' ORDER BY ds.votes DESC, ds.submitted_at DESC LIMIT 10
    """)
    top_suggestions = cursor.fetchall() or []
    cursor.execute("SELECT AVG(rating) as avg FROM feedback JOIN bookings b ON feedback.booking_id=b.id WHERE b.booking_date >= %s", (week_ago,))
    avg_row = cursor.fetchone()
    overall_avg = round(float(avg_row['avg']), 2) if avg_row and avg_row['avg'] else 0
    cursor.close(); conn.close()

    # ── sentiment ──
    POS = {'good','great','excellent','amazing','delicious','tasty','loved','fantastic','wonderful','nice','perfect','enjoyed','fresh','hot','crispy','yummy','best','awesome','superb','satisfied','clean'}
    NEG = {'bad','poor','terrible','awful','horrible','disgusting','cold','stale','overcooked','oily','bland','worst','hate','unhappy','disappointed','tasteless','burnt','not','never','late','slow','waste'}
    def qsent(t):
        if not t: return 'Neutral'
        wds=t.lower().split(); p=sum(1 for w in wds if w.strip('.,!?') in POS); n=sum(1 for w in wds if w.strip('.,!?') in NEG)
        return 'Positive' if p>n else ('Negative' if n>p else 'Neutral')
    dsentiment=[]
    for d in dish_rows:
        cmts=[c.strip() for c in (d['comments'] or '').split('||||') if c.strip()]
        pos=sum(1 for c in cmts if qsent(c)=='Positive'); neg=sum(1 for c in cmts if qsent(c)=='Negative')
        neu=len(cmts)-pos-neg; tc=len(cmts)
        label='Mostly Positive' if pos>neg else ('Needs Improvement' if neg>pos else ('Mixed' if tc else 'No comments'))
        dsentiment.append({'name':d['dish_name'],'label':label,'total':tc,
            'pos_pct':round(pos/tc*100) if tc else 0,'neg_pct':round(neg/tc*100) if tc else 0,'neu_pct':round(neu/tc*100) if tc else 0,
            'top_neg':next((c for c in cmts if qsent(c)=='Negative'),None)})

    # ── PDF setup ──
    buf=io.BytesIO(); PAGE_W=A4[0]-4*cm
    doc=SimpleDocTemplate(buf,pagesize=A4,leftMargin=2*cm,rightMargin=2*cm,topMargin=2*cm,bottomMargin=2.5*cm)
    RL_GREEN=colors.HexColor(CLR_GREEN); RL_LGREEN=colors.HexColor(CLR_LGREEN)
    RL_ORANGE=colors.HexColor(CLR_ORANGE); RL_RED=colors.HexColor(CLR_RED)
    RL_GREY=colors.HexColor(CLR_GREY); RL_LGREY=colors.HexColor('#f5f5f5')
    RL_BLUE=colors.HexColor(CLR_BLUE)

    def PS(name,**k): return ParagraphStyle(name,**k)
    sTitle=PS('t',fontSize=28,textColor=RL_GREEN,fontName='Helvetica-Bold',alignment=TA_CENTER,spaceAfter=4)
    sSub  =PS('s',fontSize=11,textColor=RL_GREY,alignment=TA_CENTER,spaceAfter=2)
    sH2   =PS('h2',fontSize=10,textColor=RL_GREY,fontName='Helvetica-Bold',spaceBefore=8,spaceAfter=4)
    sBody =PS('b',fontSize=9,textColor=colors.black,leading=14,spaceAfter=4)
    sSmall=PS('sm',fontSize=7.5,textColor=RL_GREY,spaceAfter=2,alignment=TA_CENTER)
    sNote =PS('n',fontSize=8.5,textColor=RL_ORANGE,spaceAfter=4,leading=13)
    sCent =PS('c',fontSize=9,alignment=TA_CENTER,textColor=RL_GREY)

    def tbl(data,cw,accent=None):
        t=Table(data,colWidths=cw,repeatRows=1)
        ts=TableStyle([
            ('BACKGROUND',(0,0),(-1,0),RL_LGREEN),('TEXTCOLOR',(0,0),(-1,0),RL_GREEN),
            ('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),('FONTSIZE',(0,0),(-1,0),9),
            ('TOPPADDING',(0,0),(-1,0),9),('BOTTOMPADDING',(0,0),(-1,0),9),
            ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,RL_LGREY]),
            ('FONTSIZE',(0,1),(-1,-1),8.5),('TOPPADDING',(0,1),(-1,-1),7),('BOTTOMPADDING',(0,1),(-1,-1),7),
            ('LEFTPADDING',(0,0),(-1,-1),10),('RIGHTPADDING',(0,0),(-1,-1),10),
            ('GRID',(0,0),(-1,-1),0.3,colors.HexColor('#e0e0e0')),
            ('LINEBELOW',(0,0),(-1,0),1.5,RL_GREEN),('VALIGN',(0,0),(-1,-1),'MIDDLE'),
        ])
        if accent is not None:
            ts.add('TEXTCOLOR',(accent,1),(accent,-1),RL_GREEN); ts.add('FONTNAME',(accent,1),(accent,-1),'Helvetica-Bold')
        t.setStyle(ts); return t

    def kpi_row(items):
        n=len(items); cw=PAGE_W/n
        data=[[Paragraph(f'<font size="20" color="{c}"><b>{v}</b></font><br/><font size="7.5" color="{CLR_GREY}">{l}</font>',sCent) for l,v,c in items]]
        t=Table(data,colWidths=[cw]*n)
        t.setStyle(TableStyle([('BOX',(0,0),(-1,-1),0.5,colors.HexColor('#e0e0e0')),
            ('INNERGRID',(0,0),(-1,-1),0.5,colors.HexColor('#e0e0e0')),
            ('BACKGROUND',(0,0),(-1,-1),RL_LGREY),('TOPPADDING',(0,0),(-1,-1),14),('BOTTOMPADDING',(0,0),(-1,-1),14)]))
        return t

    def section_hdr(label):
        t=Table([[Paragraph(f'<font color="white"><b>{label}</b></font>',
            PS('sh',fontSize=11,textColor=colors.white,fontName='Helvetica-Bold'))]],colWidths=[PAGE_W])
        t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),RL_GREEN),
            ('TOPPADDING',(0,0),(-1,-1),10),('BOTTOMPADDING',(0,0),(-1,-1),10),('LEFTPADDING',(0,0),(-1,-1),14)]))
        return t

    def side_by_side(a,b,wa=9.2,wb=8.3):
        t=Table([[a,b]],colWidths=[wa*cm,wb*cm])
        t.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),0),('RIGHTPADDING',(0,0),(-1,-1),0)]))
        return t

    story=[]; total=bk['total'] or 0; veg=bk['veg'] or 0; nonveg=bk['nonveg'] or 0; guests=bk['guests'] or 0

    # COVER
    story+=[Spacer(1,1.8*cm),Paragraph('IntelliMess',sTitle),Paragraph('Weekly Operations Report',sSub),
            Spacer(1,0.3*cm),HRFlowable(width='100%',thickness=2.5,color=RL_GREEN,spaceAfter=12),
            Paragraph(f"Period: <b>{week_ago.strftime('%d %b %Y')}</b> to <b>{now.strftime('%d %b %Y')}</b>",sSub),
            Paragraph(f"Generated on {now.strftime('%d %b %Y at %I:%M %p')}",sSmall),Spacer(1,0.9*cm)]
    story.append(kpi_row([('Total Bookings',str(total),CLR_GREEN),('Veg',str(veg),'#388e3c'),
        ('Non-Veg',str(nonveg),CLR_RED),('Guest Meals',str(guests),CLR_BLUE),('Avg Rating',f'{overall_avg}/5',CLR_ORANGE)]))
    if daily:
        dlabels=[r['bdate'].strftime('%a %d %b') if hasattr(r['bdate'],'strftime') else str(r['bdate']) for r in daily]
        story+=[Spacer(1,0.7*cm),_trend(dlabels,[r['cnt'] for r in daily])]
    story.append(PageBreak())

    # BOOKINGS
    story+=[section_hdr('1.  Booking Summary'),Spacer(1,0.5*cm)]
    if meal_bk and food_bk:
        ml=[r['meal'] for r in meal_bk]; mv=[r['cnt'] for r in meal_bk]; mc=[MEAL_COLORS.get(m,'#888') for m in ml]
        fl=[r['food_type'] for r in food_bk]; fv=[r['cnt'] for r in food_bk]; fc=['#4CAF50' if 'Veg' in l else '#ef5350' for l in fl]
        story.append(side_by_side(_bar(ml,mv,mc,'Bookings by Meal',w=8.5,h=6.2),_donut(fl,fv,fc,'Veg vs Non-Veg',w=7.8,h=6.2)))
    if meal_bk:
        mtbl=[['Meal','Bookings','Share']]
        for r in meal_bk: mtbl.append([r['meal'],str(r['cnt']),f"{round(r['cnt']/total*100)}%" if total else '-'])
        story+=[Spacer(1,0.3*cm),Paragraph('Meal Breakdown',sH2),tbl(mtbl,[7*cm,4*cm,3.5*cm])]
    story.append(PageBreak())

    # RATINGS
    story+=[section_hdr('2.  Dish Ratings & Satisfaction'),Spacer(1,0.5*cm)]
    if dish_rows:
        dn=[d['dish_name'] for d in dish_rows]
        da=[round(float(d['avg_r']),2) if d['avg_r'] else 0 for d in dish_rows]
        dc=[CLR_GREEN if v>=4 else (CLR_ORANGE if v>=3 else CLR_RED) for v in da]
        story.append(_hbar(dn,da,dc,'Dish Ratings',w=16,h=max(5,len(dn)*1.05)))
    if rdist and meal_sat:
        rv=[{str(r['rating']):r['cnt'] for r in rdist}.get(str(i),0) for i in range(1,6)]
        ms_l=[r['meal'] for r in meal_sat]; ms_v=[round(float(r['avg_r']),2) for r in meal_sat]
        ms_c=[MEAL_COLORS.get(m,'#888') for m in ms_l]
        story+=[Spacer(1,0.3*cm),side_by_side(_bar(['1*','2*','3*','4*','5*'],rv,RATING_COLORS,'Rating Distribution',ylabel='Responses',w=8.5,h=5.8),_hbar(ms_l,ms_v,ms_c,'Satisfaction by Meal',w=8,h=5.8))]
    if dish_rows:
        best=dish_rows[0]; worst=dish_rows[-1]
        rtbl=[['Dish','Avg Rating','Reviews','Status']]
        for d in dish_rows:
            avg=round(float(d['avg_r']),2) if d['avg_r'] else 0
            s='Best' if d==best else ('Attention' if d==worst else ('Good' if avg>=3.5 else 'Low'))
            rtbl.append([d['dish_name'],f"{avg}/5",str(d['reviews']),s])
        story+=[Spacer(1,0.3*cm),Paragraph('Dish Details',sH2),tbl(rtbl,[7*cm,3*cm,3*cm,3.5*cm],accent=1)]
        story.append(Paragraph(f"<b>Top:</b> {best['dish_name']} - {round(float(best['avg_r']),2)}/5 from {best['reviews']} review(s).",sNote))
        if worst!=best: story.append(Paragraph(f"<b>Needs Attention:</b> {worst['dish_name']} - {round(float(worst['avg_r']),2)}/5.",sNote))
    story.append(PageBreak())

    # SENTIMENT
    story+=[section_hdr('3.  Comment Sentiment Analysis'),Spacer(1,0.5*cm)]
    has_c=[d for d in dsentiment if d['total']>0]
    if has_c:
        story.append(_sent_stack([d['name'] for d in has_c],[d['pos_pct'] for d in has_c],[d['neg_pct'] for d in has_c],[d['neu_pct'] for d in has_c],w=16,h=max(5,len(has_c)*.95)))
        stbl=[['Dish','Comments','Pos%','Neg%','Verdict','Top Complaint']]
        for d in has_c:
            c=(d['top_neg'][:40]+'...') if d['top_neg'] and len(d['top_neg'])>40 else (d['top_neg'] or '-')
            stbl.append([d['name'],str(d['total']),f"{d['pos_pct']}%",f"{d['neg_pct']}%",d['label'],c])
        story+=[Spacer(1,0.4*cm),Paragraph('Sentiment Detail',sH2),tbl(stbl,[3.5*cm,2*cm,1.8*cm,1.8*cm,3.2*cm,5.2*cm])]
    else:
        story.append(Paragraph('No comments this week.',sBody))
    story.append(PageBreak())

    # POLLS
    story+=[section_hdr('4.  Poll Results & Winners'),Spacer(1,0.5*cm)]
    if poll_rows:
        pq=[(p['question'][:22]+'...' if len(p['question'])>22 else p['question']) for p in poll_rows]
        pv=[p['votes'] for p in poll_rows]; pc=[MEAL_COLORS.get(p['meal'],'#888') for p in poll_rows]
        if any(v>0 for v in pv): story.append(_bar(pq,pv,pc,'Votes per Poll',ylabel='Votes',w=16,h=max(5,len(poll_rows)*1.2)))
        ptbl=[['Poll Question','Meal','Date','Winner Dish','Votes']]
        for p in poll_rows:
            ds=p['poll_date'].strftime('%d %b') if hasattr(p['poll_date'],'strftime') else str(p['poll_date'])
            q=(p['question'][:35]+'...') if len(p['question'])>35 else p['question']
            ptbl.append([q,p['meal'],ds,p['winner_dish'] or 'Open',str(p['votes'])])
        story+=[Spacer(1,0.4*cm),Paragraph('Poll Summary',sH2),tbl(ptbl,[6*cm,2.5*cm,2*cm,4*cm,2*cm])]
    else:
        story.append(Paragraph('No polls this week.',sBody))
    story.append(PageBreak())

    # SUGGESTIONS
    story+=[section_hdr('5.  Student Dish Suggestions'),Spacer(1,0.5*cm)]
    if top_suggestions:
        sq=[(s['dish_name'][:18]+'...' if len(s['dish_name'])>18 else s['dish_name']) for s in top_suggestions]
        sv=[s['votes'] for s in top_suggestions]; sc=[MEAL_COLORS.get(s['meal'],'#888') for s in top_suggestions]
        if any(v>0 for v in sv): story.append(_bar(sq,sv,sc,'Top Suggested Dishes by Votes',ylabel='Votes',w=16,h=max(5,len(sq)*1.1)))
        sug_tbl=[['Dish','Meal','Votes','Reason']]
        for s in top_suggestions:
            reason=(s['reason'][:40]+'...') if s['reason'] and len(s['reason'])>40 else (s['reason'] or '-')
            sug_tbl.append([s['dish_name'],s['meal'],str(s['votes']),reason])
        story+=[Spacer(1,0.4*cm),Paragraph('Top Requests',sH2),tbl(sug_tbl,[5*cm,3*cm,2*cm,7.5*cm])]
        story.append(Paragraph('Consider adding high-vote suggestions to upcoming menus or creating polls around them.',sNote))
    else:
        story.append(Paragraph('No suggestions yet.',sBody))

    story+=[Spacer(1,1*cm),HRFlowable(width='100%',thickness=0.5,color=colors.HexColor('#e0e0e0'),spaceAfter=4),
            Paragraph(f'IntelliMess Weekly Report - {now.strftime("%d %b %Y")} - Confidential',sSmall)]

    doc.build(story)
    buf.seek(0)
    filename = f"IntelliMess_Report_{now.strftime('%Y-%m-%d')}.pdf"
    return Response(buf, mimetype='application/pdf',
                    headers={'Content-Disposition': f'attachment; filename={filename}'})



# ================================================================
# ----------------  ADMIN MENU MANAGEMENT  -----------------------
# ================================================================

@app.route('/admin/menu')
def admin_menu():
    if session.get('role') != 'admin':
        return redirect('/login')
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True, buffered=True)

    days  = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']
    meals = ['Breakfast','Lunch','Snacks','Dinner']

    # Build full weekly menu grid
    menu_grid = {d: {m: [] for m in meals} for d in days}
    cursor.execute("""
        SELECT wm.id as menu_id, wm.day_of_week, wm.meal,
               d.id as dish_id, d.dish_name
        FROM weekly_menu wm
        LEFT JOIN menu_items mi ON wm.id = mi.weekly_menu_id
        LEFT JOIN dishes d ON mi.dish_id = d.id
        ORDER BY wm.day_of_week, wm.meal
    """)
    for row in cursor.fetchall():
        day, meal = row['day_of_week'], row['meal']
        if day in menu_grid and meal in menu_grid[day]:
            if row['dish_name']:
                menu_grid[day][meal].append({
                    'dish_id':   row['dish_id'],
                    'dish_name': row['dish_name'],
                    'menu_id':   row['menu_id'],
                })

    # All dishes for dropdown
    cursor.execute("SELECT id, dish_name FROM dishes ORDER BY dish_name")
    all_dishes = cursor.fetchall() or []

    cursor.close()
    conn.close()
    return render_template("admin_menu.html",
        menu_grid=menu_grid, days=days, meals=meals, all_dishes=all_dishes)


@app.route('/admin/menu/add', methods=['POST'])
def admin_menu_add():
    if session.get('role') != 'admin':
        return redirect('/login')
    day       = request.form['day']
    meal      = request.form['meal']
    dish_name = request.form.get('new_dish_name', '').strip()
    dish_id   = request.form.get('existing_dish_id', '')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True, buffered=True)

    # Use existing dish or create new one
    if dish_id:
        did = int(dish_id)
    elif dish_name:
        cursor2 = conn.cursor()
        cursor.execute("SELECT id FROM dishes WHERE dish_name=%s", (dish_name,))
        ex = cursor.fetchone()
        if ex:
            did = ex['id']
        else:
            cursor2.execute("INSERT INTO dishes (dish_name) VALUES (%s)", (dish_name,))
            conn.commit()
            did = cursor2.lastrowid
        cursor2.close()
    else:
        cursor.close(); conn.close()
        return redirect('/admin/menu')

    # Get or create weekly_menu row
    cursor.execute("SELECT id FROM weekly_menu WHERE day_of_week=%s AND meal=%s", (day, meal))
    wm = cursor.fetchone()
    cursor3 = conn.cursor()
    if wm:
        menu_id = wm['id']
    else:
        cursor3.execute("INSERT INTO weekly_menu (day_of_week, meal) VALUES (%s,%s)", (day, meal))
        conn.commit()
        menu_id = cursor3.lastrowid

    # Add dish if not already in that slot
    cursor.execute("SELECT 1 FROM menu_items WHERE weekly_menu_id=%s AND dish_id=%s", (menu_id, did))
    if not cursor.fetchone():
        cursor3.execute("INSERT INTO menu_items (weekly_menu_id, dish_id) VALUES (%s,%s)", (menu_id, did))
        conn.commit()

    cursor3.close(); cursor.close(); conn.close()
    return redirect('/admin/menu')


@app.route('/admin/menu/remove', methods=['POST'])
def admin_menu_remove():
    if session.get('role') != 'admin':
        return redirect('/login')
    menu_id = request.form['menu_id']
    dish_id = request.form['dish_id']
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM menu_items WHERE weekly_menu_id=%s AND dish_id=%s", (menu_id, dish_id))
    conn.commit()
    cursor.close(); conn.close()
    return redirect('/admin/menu')




# ================================================================
# --------  GAMIFICATION: STREAKS & BADGES  ----------------------
# ================================================================

BADGES = {
    'first_bite':    {'icon': '🌱', 'name': 'First Bite',     'desc': 'Gave your first feedback',          'color': '#66bb6a'},
    'on_a_roll':     {'icon': '🔥', 'name': 'On a Roll',      'desc': '3-day feedback streak',             'color': '#ff7043'},
    'week_warrior':  {'icon': '⭐', 'name': 'Week Warrior',   'desc': '7-day feedback streak',             'color': '#ffd600'},
    'fortnight':     {'icon': '🏅', 'name': 'Fortnight Pro',  'desc': '14-day feedback streak',            'color': '#ab47bc'},
    'monthly_hero':  {'icon': '👑', 'name': 'Monthly Hero',   'desc': '30-day feedback streak',            'color': '#f9a825'},
    'critic':        {'icon': '🎯', 'name': 'Food Critic',    'desc': '10 total feedback submissions',     'color': '#1976d2'},
    'connoisseur':   {'icon': '🍽️', 'name': 'Connoisseur',   'desc': '25 total feedback submissions',     'color': '#00897b'},
    'mess_legend':   {'icon': '🏆', 'name': 'Mess Legend',    'desc': '50 total feedback submissions',     'color': '#e65100'},
    'five_star':     {'icon': '💫', 'name': 'Five Star',      'desc': 'Gave 5 stars 5 times',              'color': '#ffd600'},
    'honest_critic': {'icon': '📝', 'name': 'Honest Critic',  'desc': 'Gave a 1-star rating (brave!)',     'color': '#78909c'},
}

def update_streak_and_badges(user_id, conn):
    """Recalculate streak, update user_streaks, award new badges. Call after every feedback submit."""
    cursor = conn.cursor(dictionary=True, buffered=True)

    # Get all distinct feedback dates for this user, ordered ascending
    cursor.execute("""
        SELECT DISTINCT feedback_date FROM feedback
        WHERE user_id = %s ORDER BY feedback_date ASC
    """, (user_id,))
    rows = cursor.fetchall()
    dates = [r['feedback_date'] for r in rows]

    total_feedbacks = 0
    cursor.execute("SELECT COUNT(*) as c FROM feedback WHERE user_id=%s", (user_id,))
    total_feedbacks = cursor.fetchone()['c']

    cursor.execute("SELECT AVG(rating) as a, SUM(CASE WHEN rating=5 THEN 1 ELSE 0 END) as fives, SUM(CASE WHEN rating=1 THEN 1 ELSE 0 END) as ones FROM feedback WHERE user_id=%s", (user_id,))
    rating_row = cursor.fetchone()
    avg_r  = round(float(rating_row['a']), 2) if rating_row['a'] else 0
    fives  = rating_row['fives'] or 0
    ones   = rating_row['ones']  or 0

    # Calculate current streak (working backwards from today)
    from datetime import date as dt_date, timedelta as td
    today = dt_date.today()
    current_streak = 0
    check = today
    date_set = set(dates)
    # if no feedback today, check from yesterday
    if check not in date_set:
        check = today - td(days=1)
    while check in date_set:
        current_streak += 1
        check = check - td(days=1)

    # Calculate longest streak
    longest = 0
    run = 1
    for i in range(1, len(dates)):
        if (dates[i] - dates[i-1]).days == 1:
            run += 1
            longest = max(longest, run)
        else:
            run = 1
    longest = max(longest, run, current_streak)

    last_date = dates[-1] if dates else None

    # Upsert into user_streaks
    cursor2 = conn.cursor()
    cursor2.execute("""
        INSERT INTO user_streaks (user_id, current_streak, longest_streak,
            last_feedback_date, total_feedbacks, avg_rating_given)
        VALUES (%s,%s,%s,%s,%s,%s)
        ON DUPLICATE KEY UPDATE
            current_streak=VALUES(current_streak),
            longest_streak=VALUES(longest_streak),
            last_feedback_date=VALUES(last_feedback_date),
            total_feedbacks=VALUES(total_feedbacks),
            avg_rating_given=VALUES(avg_rating_given)
    """, (user_id, current_streak, longest, last_date, total_feedbacks, avg_r))

    # Determine which badges this user has earned
    earned = set()
    if total_feedbacks >= 1:  earned.add('first_bite')
    if current_streak >= 3:   earned.add('on_a_roll')
    if current_streak >= 7:   earned.add('week_warrior')
    if current_streak >= 14:  earned.add('fortnight')
    if current_streak >= 30:  earned.add('monthly_hero')
    if total_feedbacks >= 10: earned.add('critic')
    if total_feedbacks >= 25: earned.add('connoisseur')
    if total_feedbacks >= 50: earned.add('mess_legend')
    if fives >= 5:            earned.add('five_star')
    if ones >= 1:             earned.add('honest_critic')

    # Insert newly earned badges (ignore duplicates)
    for badge_key in earned:
        cursor2.execute("""
            INSERT IGNORE INTO user_badges (user_id, badge_key) VALUES (%s,%s)
        """, (user_id, badge_key))

    conn.commit()
    cursor.close(); cursor2.close()


@app.route('/achievements')
def achievements():
    if 'user_id' not in session or session['role'] != 'student':
        return redirect('/login')
    user_id = session['user_id']
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True, buffered=True)

    # Get this user's streak data
    cursor.execute("SELECT * FROM user_streaks WHERE user_id=%s", (user_id,))
    streak_data = cursor.fetchone() or {
        'current_streak': 0, 'longest_streak': 0,
        'total_feedbacks': 0, 'avg_rating_given': 0,
        'last_feedback_date': None
    }

    # Get earned badges
    cursor.execute("SELECT badge_key, awarded_at FROM user_badges WHERE user_id=%s ORDER BY awarded_at", (user_id,))
    earned_raw = {r['badge_key']: r['awarded_at'] for r in cursor.fetchall()}

    # Build badge list: earned + locked
    all_badges = []
    for key, info in BADGES.items():
        all_badges.append({**info, 'key': key,
            'earned': key in earned_raw,
            'awarded_at': earned_raw.get(key)
        })

    # Leaderboard: top 10 by current streak, then total feedbacks
    cursor.execute("""
        SELECT u.username, us.current_streak, us.longest_streak,
               us.total_feedbacks, us.avg_rating_given,
               (SELECT COUNT(*) FROM user_badges ub WHERE ub.user_id=u.id) as badge_count,
               us.user_id
        FROM user_streaks us JOIN users u ON us.user_id=u.id
        WHERE u.role='student'
        ORDER BY us.current_streak DESC, us.total_feedbacks DESC
        LIMIT 10
    """)
    leaderboard = cursor.fetchall() or []

    # My rank
    cursor.execute("""
        SELECT COUNT(*)+1 as rank FROM user_streaks us JOIN users u ON us.user_id=u.id
        WHERE u.role='student'
        AND (us.current_streak > (SELECT COALESCE(current_streak,0) FROM user_streaks WHERE user_id=%s)
        OR (us.current_streak = (SELECT COALESCE(current_streak,0) FROM user_streaks WHERE user_id=%s)
            AND us.total_feedbacks > (SELECT COALESCE(total_feedbacks,0) FROM user_streaks WHERE user_id=%s)))
    """, (user_id, user_id, user_id))
    rank_row = cursor.fetchone()
    my_rank = rank_row['rank'] if rank_row else '—'

    # Build last-7-days heatmap data
    from datetime import date as dt_date, timedelta as dt_td
    today_d = dt_date.today()
    feedback_dates_raw = []
    cursor2 = conn.cursor(dictionary=True, buffered=True)
    cursor2.execute("SELECT DISTINCT feedback_date FROM feedback WHERE user_id=%s", (user_id,))
    feedback_dates_raw = {r['feedback_date'] for r in cursor2.fetchall()}
    cursor2.close()

    last_7_days = []
    for i in range(6, -1, -1):
        d = today_d - dt_td(days=i)
        last_7_days.append({
            'label':    d.strftime('%A %d %b'),
            'short':    d.strftime('%a')[:2],
            'done':     d in feedback_dates_raw,
            'is_today': d == today_d,
        })

    cursor.close(); conn.close()
    return render_template('achievements.html',
        username=session.get('username',''),
        streak=streak_data, badges=all_badges,
        leaderboard=leaderboard, my_rank=my_rank,
        user_id=user_id, BADGES=BADGES,
        last_7_days=last_7_days)


# ================================================================
# --------  DISH SUGGESTIONS  ------------------------------------
# ================================================================

@app.route('/suggestions')
def suggestions():
    if 'user_id' not in session or session['role'] != 'student':
        return redirect('/login')
    user_id = session['user_id']
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True, buffered=True)

    # All pending/noted suggestions sorted by votes desc
    cursor.execute("""
        SELECT ds.id, ds.dish_name, ds.meal, ds.reason, ds.votes,
               ds.status, ds.submitted_at, u.username,
               (SELECT 1 FROM suggestion_votes sv
                WHERE sv.suggestion_id=ds.id AND sv.user_id=%s) as user_voted,
               (ds.user_id = %s) as is_mine
        FROM dish_suggestions ds
        JOIN users u ON ds.user_id = u.id
        WHERE ds.status != 'declined'
        ORDER BY ds.votes DESC, ds.submitted_at DESC
    """, (user_id, user_id))
    suggestions = cursor.fetchall() or []

    # Student's own suggestions (all statuses)
    cursor.execute("""
        SELECT id, dish_name, meal, reason, votes, status, submitted_at
        FROM dish_suggestions WHERE user_id=%s ORDER BY submitted_at DESC
    """, (user_id,))
    my_suggestions = cursor.fetchall() or []

    cursor.close(); conn.close()
    return render_template("suggestions.html",
        suggestions=suggestions, my_suggestions=my_suggestions,
        username=session.get('username',''))


@app.route('/suggestions/submit', methods=['POST'])
def submit_suggestion():
    if 'user_id' not in session or session['role'] != 'student':
        return redirect('/login')
    user_id   = session['user_id']
    dish_name = request.form.get('dish_name','').strip()
    meal      = request.form.get('meal','')
    reason    = request.form.get('reason','').strip()

    if not dish_name or meal not in ('Breakfast','Lunch','Snacks','Dinner'):
        return redirect('/suggestions')

    conn = get_db_connection()
    cursor = conn.cursor()
    # Prevent duplicate suggestions from same student
    cursor.execute("""
        SELECT id FROM dish_suggestions
        WHERE user_id=%s AND LOWER(dish_name)=LOWER(%s) AND meal=%s
    """, (user_id, dish_name, meal))
    if not cursor.fetchone():
        cursor.execute("""
            INSERT INTO dish_suggestions (user_id, dish_name, meal, reason)
            VALUES (%s,%s,%s,%s)
        """, (user_id, dish_name, meal, reason or None))
        conn.commit()
    cursor.close(); conn.close()
    return redirect('/suggestions')


@app.route('/suggestions/upvote/<int:suggestion_id>', methods=['POST'])
def upvote_suggestion(suggestion_id):
    if 'user_id' not in session or session['role'] != 'student':
        return redirect('/login')
    user_id = session['user_id']
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True, buffered=True)

    # Check not their own suggestion
    cursor.execute("SELECT user_id FROM dish_suggestions WHERE id=%s", (suggestion_id,))
    row = cursor.fetchone()
    if not row or row['user_id'] == user_id:
        cursor.close(); conn.close()
        return redirect('/suggestions')

    # Insert vote (ignore if already voted due to UNIQUE constraint)
    try:
        c2 = conn.cursor()
        c2.execute("INSERT IGNORE INTO suggestion_votes (suggestion_id, user_id) VALUES (%s,%s)",
                   (suggestion_id, user_id))
        if c2.rowcount:
            c2.execute("UPDATE dish_suggestions SET votes=votes+1 WHERE id=%s", (suggestion_id,))
        conn.commit()
        c2.close()
    except Exception:
        pass
    cursor.close(); conn.close()
    return redirect('/suggestions')


# ── ADMIN views ──
@app.route('/admin/suggestions')
def admin_suggestions():
    if session.get('role') != 'admin':
        return redirect('/login')
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True, buffered=True)
    cursor.execute("""
        SELECT ds.id, ds.dish_name, ds.meal, ds.reason, ds.votes,
               ds.status, ds.submitted_at, u.username
        FROM dish_suggestions ds
        JOIN users u ON ds.user_id = u.id
        ORDER BY ds.votes DESC, ds.submitted_at DESC
    """)
    suggestions = cursor.fetchall() or []
    # Group counts
    pending = sum(1 for s in suggestions if s['status']=='pending')
    noted   = sum(1 for s in suggestions if s['status']=='noted')
    cursor.close(); conn.close()
    return render_template("admin_suggestions.html",
        suggestions=suggestions, pending=pending, noted=noted)


@app.route('/admin/suggestions/status', methods=['POST'])
def admin_suggestion_status():
    if session.get('role') != 'admin':
        return redirect('/login')
    suggestion_id = request.form['suggestion_id']
    status        = request.form['status']
    if status not in ('pending','noted','declined'):
        return redirect('/admin/suggestions')
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE dish_suggestions SET status=%s WHERE id=%s", (status, suggestion_id))
    conn.commit()
    cursor.close(); conn.close()
    return redirect('/admin/suggestions')

# ================================================================
# --------  DEMAND FORECASTING  (scikit-learn) -------------------
# ================================================================
@app.route('/admin/forecast')
def admin_forecast():
    if session.get('role') != 'admin':
        return redirect('/login')

    import numpy as np
    from sklearn.ensemble import GradientBoostingRegressor
    from sklearn.preprocessing import LabelEncoder
    from sklearn.model_selection import cross_val_score
    from sklearn.metrics import mean_absolute_error

    conn   = get_db_connection()
    cursor = conn.cursor(dictionary=True, buffered=True)
    now    = datetime.now()
    today  = now.date()
    meals  = ['Breakfast', 'Lunch', 'Snacks', 'Dinner']
    MEAL_ENC = {m: i for i, m in enumerate(meals)}

    # ── 1. Pull all historical booking rows ──────────────────────
    cursor.execute("""
        SELECT booking_date,
               meal,
               COUNT(*) + COALESCE(SUM(guest_count), 0) AS headcount
        FROM bookings
        WHERE booking_date < CURDATE()
        GROUP BY booking_date, meal
        ORDER BY booking_date
    """)
    raw = cursor.fetchall() or []

    # ── 2. Build feature matrix ──────────────────────────────────
    # Features per (date, meal):
    #   0  day_of_week       0=Mon … 6=Sun
    #   1  meal_encoded      0=Breakfast … 3=Dinner
    #   2  week_of_year      1-53
    #   3  month             1-12
    #   4  is_weekend        0/1
    #   5  lag_7             headcount same meal 7 days ago
    #   6  lag_14            headcount same meal 14 days ago
    #   7  rolling_4w_avg    avg headcount this meal, past 4 same-DOW

    # Build lookup: (date, meal) -> headcount
    from collections import defaultdict
    hist_lookup = {}
    for r in raw:
        hist_lookup[(r['booking_date'], r['meal'])] = int(r['headcount'])

    def get_hc(date, meal, default=0):
        return hist_lookup.get((date, meal), default)

    def rolling_dow_avg(date, meal, weeks=4):
        vals = [get_hc(date - timedelta(days=7*w), meal)
                for w in range(1, weeks+1)
                if (date - timedelta(days=7*w), meal) in hist_lookup]
        return round(sum(vals) / len(vals), 2) if vals else 0.0

    X, y = [], []
    for r in raw:
        d    = r['booking_date']
        meal = r['meal']
        hc   = int(r['headcount'])
        feat = [
            d.weekday(),
            MEAL_ENC[meal],
            d.isocalendar()[1],   # week of year
            d.month,
            1 if d.weekday() >= 5 else 0,
            get_hc(d - timedelta(days=7),  meal),
            get_hc(d - timedelta(days=14), meal),
            rolling_dow_avg(d, meal),
        ]
        X.append(feat)
        y.append(hc)

    X = np.array(X, dtype=float)
    y = np.array(y, dtype=float)

    # ── 3. Train Gradient Boosting model ─────────────────────────
    fallback_mode = False
    model_info = {}

    if len(X) >= 8:   # need at least a few rows to train
        model = GradientBoostingRegressor(
            n_estimators=200,
            learning_rate=0.08,
            max_depth=4,
            subsample=0.85,
            min_samples_leaf=2,
            random_state=42,
        )
        model.fit(X, y)

        # Cross-validated MAE (how many meals off on average)
        if len(X) >= 5:
            cv_scores = cross_val_score(model, X, y,
                                        scoring='neg_mean_absolute_error',
                                        cv=min(5, len(X)))
            mae = round(-cv_scores.mean(), 1)
            r2  = round(model.score(X, y), 3)
        else:
            preds = model.predict(X)
            mae = round(mean_absolute_error(y, preds), 1)
            r2  = round(model.score(X, y), 3)

        # Feature importances
        feat_names = ['Day of Week','Meal','Week #','Month',
                      'Is Weekend','Lag 7d','Lag 14d','4-week avg']
        importances = sorted(zip(feat_names, model.feature_importances_),
                             key=lambda x: x[1], reverse=True)
        model_info = {
            'mae': mae, 'r2': r2,
            'n_samples': len(X),
            'importances': [(n, round(v*100, 1)) for n, v in importances[:5]],
        }
    else:
        fallback_mode = True

    # ── 4. Generate 7-day forecast ───────────────────────────────
    forecast = []
    day_names = ['Mon','Tue','Wed','Thu','Fri','Sat','Sun']

    for offset in range(1, 8):
        fdate = today + timedelta(days=offset)
        dow   = fdate.weekday()

        # Firm bookings already in system for that date
        cursor.execute("""
            SELECT meal, COUNT(*) + COALESCE(SUM(guest_count),0) as booked
            FROM bookings WHERE booking_date=%s GROUP BY meal
        """, (fdate,))
        booked_map = {r['meal']: int(r['booked']) for r in cursor.fetchall()}

        meals_forecast = []
        for meal in meals:
            booked = booked_map.get(meal, 0)

            if fallback_mode:
                # No enough data — use simple DOW average
                hist_vals = [get_hc(fdate - timedelta(days=7*w), meal)
                             for w in range(1, 5)
                             if (fdate - timedelta(days=7*w), meal) in hist_lookup]
                ml_pred = round(sum(hist_vals)/len(hist_vals)) if hist_vals else booked
                ci_low = ci_high = ml_pred
                confidence = 'low'
            else:
                feat = np.array([[
                    dow,
                    MEAL_ENC[meal],
                    fdate.isocalendar()[1],
                    fdate.month,
                    1 if dow >= 5 else 0,
                    get_hc(fdate - timedelta(days=7),  meal),
                    get_hc(fdate - timedelta(days=14), meal),
                    rolling_dow_avg(fdate, meal),
                ]], dtype=float)

                ml_pred = max(0, round(float(model.predict(feat)[0])))

                # Confidence interval: ±1 MAE, expanded for further-out days
                margin = mae * (1 + offset * 0.08)
                ci_low  = max(0, round(ml_pred - margin))
                ci_high = round(ml_pred + margin)

                # Blend: weight firm bookings more when close
                if offset == 1:
                    w_booked = 0.65
                elif offset <= 3:
                    w_booked = 0.35
                else:
                    w_booked = 0.10

                if booked > 0:
                    ml_pred = round(booked * w_booked + ml_pred * (1 - w_booked))
                    ci_low  = max(0, round(ci_low  * (1 - w_booked) + booked * w_booked * 0.85))
                    ci_high = round(ci_high * (1 - w_booked) + booked * w_booked * 1.15)

                confidence = 'high' if offset <= 3 else ('medium' if offset <= 5 else 'low')

            # vs same meal last week
            last_week_count = get_hc(fdate - timedelta(days=7), meal) or None
            trend = ('up'   if last_week_count and ml_pred > last_week_count else
                     'down' if last_week_count and ml_pred < last_week_count else 'flat')

            meals_forecast.append({
                'meal':           meal,
                'booked':         booked,
                'predicted':      ml_pred,
                'ci_low':         ci_low,
                'ci_high':        ci_high,
                'suggested_prep': round(ci_high * 1.10),
                'confidence':     confidence,
                'last_week':      last_week_count,
                'trend':          trend,
            })

        forecast.append({
            'date':            fdate,
            'label':           fdate.strftime('%a %d %b'),
            'dow_label':       day_names[dow],
            'meals':           meals_forecast,
            'total_predicted': sum(m['predicted'] for m in meals_forecast),
            'total_ci_low':    sum(m['ci_low']    for m in meals_forecast),
            'total_ci_high':   sum(m['ci_high']   for m in meals_forecast),
            'is_tomorrow':     offset == 1,
        })

    # ── 5. Summary stats ─────────────────────────────────────────
    week_total_predicted = sum(d['total_predicted'] for d in forecast)
    busiest_day          = max(forecast, key=lambda d: d['total_predicted'])
    all_meals_flat       = [m for d in forecast for m in d['meals']]
    busiest_meal_row     = max(all_meals_flat, key=lambda m: m['predicted'])

    # Historical daily for chart (last 28 days)
    cursor.execute("""
        SELECT booking_date,
               SUM(COALESCE(guest_count,0) + 1) as headcount
        FROM bookings
        WHERE booking_date >= CURDATE() - INTERVAL 28 DAY
          AND booking_date < CURDATE()
        GROUP BY booking_date ORDER BY booking_date
    """)
    historical_daily = cursor.fetchall() or []

    cursor.close(); conn.close()

    return render_template('admin_forecast.html',
        forecast=forecast,
        week_total_predicted=week_total_predicted,
        busiest_day=busiest_day,
        busiest_meal=busiest_meal_row,
        historical_daily=historical_daily,
        model_info=model_info,
        fallback_mode=fallback_mode,
        today=today,
    )


# ================================================================
# --------  ADMIN SEPARATE SUB-PAGES  ----------------------------
# ================================================================

def _get_dish_stats_and_sentiment():
    """Shared helper — returns dish_stats with sentiment, overall avg."""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True, buffered=True)
    cursor.execute("""
        SELECT d.dish_name, AVG(f.rating) as avg_rating,
               COUNT(f.id) as total_reviews,
               GROUP_CONCAT(f.comment SEPARATOR '||||') as all_comments
        FROM feedback f JOIN dishes d ON f.dish_id = d.id
        GROUP BY d.dish_name ORDER BY avg_rating DESC
    """)
    raw = cursor.fetchall() or []
    cursor.execute("SELECT AVG(rating) as overall FROM feedback")
    ov = cursor.fetchone()
    overall = round(float(ov['overall']), 2) if ov and ov['overall'] else 0
    cursor.close(); conn.close()

    dish_stats = []
    for dish in raw:
        comments = [c.strip() for c in (dish['all_comments'] or '').split('||||') if c.strip()]
        pos = neg = neu = 0
        notable_positive = []
        notable_negative = []
        for c in comments:
            sentiment, score = analyze_sentiment(c)
            if sentiment == 'Positive':
                pos += 1
                if len(notable_positive) < 2: notable_positive.append(c)
            elif sentiment == 'Negative':
                neg += 1
                if len(notable_negative) < 2: notable_negative.append(c)
            else:
                neu += 1
        total_c = pos + neg + neu
        sp = {
            'positive': round(pos/total_c*100) if total_c else 0,
            'negative': round(neg/total_c*100) if total_c else 0,
            'neutral':  round(neu/total_c*100) if total_c else 0,
        }
        if total_c == 0: label = 'No comments'
        elif pos >= neg and pos >= neu: label = 'Mostly Positive'
        elif neg >= pos and neg >= neu: label = 'Needs Improvement'
        else: label = 'Mixed'
        dish_stats.append({
            'dish_name': dish['dish_name'], 'avg_rating': dish['avg_rating'],
            'total_reviews': dish['total_reviews'], 'sentiment': label,
            'sentiment_pct': sp, 'notable_positive': notable_positive,
            'notable_negative': notable_negative, 'comment_count': total_c,
        })
    return dish_stats, overall


@app.route('/admin/analytics')
def admin_analytics():
    if session.get('role') != 'admin':
        return redirect('/login')
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True, buffered=True)

    cursor.execute("""
        SELECT DATE(booking_date) as bdate, COUNT(*) as count FROM bookings
        WHERE booking_date >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
        GROUP BY DATE(booking_date) ORDER BY bdate ASC
    """)
    booking_trend = cursor.fetchall() or []

    cursor.execute("SELECT meal, COUNT(*) as count FROM bookings GROUP BY meal")
    meal_stats = cursor.fetchall() or []

    cursor.execute("SELECT food_type, COUNT(*) as count FROM bookings GROUP BY food_type")
    food_stats = cursor.fetchall() or []

    cursor.execute("SELECT rating, COUNT(*) as count FROM feedback GROUP BY rating ORDER BY rating ASC")
    rating_dist = {str(r['rating']): r['count'] for r in cursor.fetchall()}

    cursor.execute("""
        SELECT b.meal, AVG(f.rating) as avg_rating, COUNT(f.id) as total
        FROM feedback f JOIN bookings b ON f.booking_id = b.id
        GROUP BY b.meal ORDER BY avg_rating DESC
    """)
    meal_satisfaction = cursor.fetchall() or []

    cursor.execute("SELECT COUNT(*) as total FROM bookings")
    total_bk = cursor.fetchone()['total'] or 1
    cursor.execute("SELECT COUNT(DISTINCT booking_id) as fb FROM feedback")
    fb_bk = cursor.fetchone()['fb'] or 0
    feedback_rate = round(fb_bk / total_bk * 100, 1)

    cursor.close(); conn.close()
    dish_stats, overall = _get_dish_stats_and_sentiment()

    return render_template("admin_analytics.html",
        booking_trend=booking_trend, meal_stats=meal_stats,
        food_stats=food_stats, rating_dist=rating_dist,
        meal_satisfaction=meal_satisfaction, feedback_rate=feedback_rate,
        dish_stats=dish_stats, overall=overall)


@app.route('/admin/bookings')
def admin_bookings():
    if session.get('role') != 'admin':
        return redirect('/login')
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True, buffered=True)
    cursor.execute("""
        SELECT b.*, u.username, u.roll_no
        FROM bookings b JOIN users u ON b.user_id = u.id
        ORDER BY b.booking_date DESC, b.booking_time DESC
    """)
    bookings = cursor.fetchall() or []
    cursor.close(); conn.close()
    return render_template("admin_bookings.html", bookings=bookings)


@app.route('/admin/sentiment')
def admin_sentiment():
    if session.get('role') != 'admin':
        return redirect('/login')
    dish_stats, overall = _get_dish_stats_and_sentiment()
    return render_template("admin_sentiment.html", dish_stats=dish_stats, overall=overall)


@app.route('/admin/heatmap')
def admin_heatmap():
    if session.get('role') != 'admin':
        return redirect('/login')
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True, buffered=True)
    cursor.execute("""
        SELECT DAYNAME(booking_date) as day_name, meal, COUNT(*) as count
        FROM bookings GROUP BY DAYNAME(booking_date), meal
    """)
    days_order  = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']
    meals_order = ['Breakfast','Lunch','Snacks','Dinner']
    heatmap = {d: {m: 0 for m in meals_order} for d in days_order}
    heatmap_max = 1
    for row in cursor.fetchall():
        d, m, c = row['day_name'], row['meal'], row['count']
        if d in heatmap and m in heatmap[d]:
            heatmap[d][m] = c
            if c > heatmap_max: heatmap_max = c

    # Comeback suggestions
    cursor.execute("""
        SELECT d.dish_name, AVG(f.rating) as avg_rating, MAX(b.booking_date) as last_served
        FROM feedback f JOIN dishes d ON f.dish_id = d.id JOIN bookings b ON f.booking_id = b.id
        GROUP BY d.dish_name
        HAVING avg_rating >= 4.0 AND MAX(b.booking_date) <= DATE_SUB(CURDATE(), INTERVAL 14 DAY)
        ORDER BY avg_rating DESC
    """)
    comeback_dishes = cursor.fetchall() or []
    cursor.close(); conn.close()

    return render_template("admin_heatmap.html",
        heatmap=heatmap, heatmap_max=heatmap_max,
        days_order=days_order, meals_order=meals_order,
        comeback_dishes=comeback_dishes)


# ---------------- RUN ----------------
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)

