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
    return render_template("student.html", username=session.get('username', ''))

# ---------------- MENU ----------------
@app.route('/menu')
def menu():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    meal_times = [("Breakfast","07:30"),("Lunch","11:45"),("Snacks","16:30"),("Dinner","19:30")]
    now = datetime.now()
    today = now.strftime("%A")
    current_time = now.strftime("%H:%M")
    next_meals = []
    day_index = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
    start_day = day_index.index(today)
    i = 0
    while len(next_meals) < 4:
        day = day_index[(start_day + i) % 7]
        for meal, time in meal_times:
            if i == 0 and time <= current_time:
                continue
            next_meals.append((day, meal))
            if len(next_meals) == 4:
                break
        i += 1
    menu_data = []
    for day, meal in next_meals:
        cursor.execute("""
            SELECT d.dish_name FROM weekly_menu wm
            JOIN menu_items mi ON wm.id = mi.weekly_menu_id
            JOIN dishes d ON mi.dish_id = d.id
            WHERE wm.day_of_week = %s AND wm.meal = %s
        """, (day, meal))
        dishes = [row['dish_name'] for row in cursor.fetchall()]
        menu_data.append({"day": day, "meal": meal, "dishes": dishes})
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
    cursor.close()
    conn.close()
    return redirect('/student')

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

    # Find the winning option
    cursor.execute("""
        SELECT po.id as option_id, po.option_text,
               p.meal, p.poll_date, COUNT(pv.id) as vote_count
        FROM poll_options po
        LEFT JOIN poll_votes pv ON po.id = pv.option_id
        JOIN polls p ON p.id = po.poll_id
        WHERE po.poll_id = %s
        GROUP BY po.id
        ORDER BY vote_count DESC
        LIMIT 1
    """, (poll_id,))
    winner = cursor.fetchone()

    # Add winning dish to menu if it exists and has votes
    if winner and winner['vote_count'] > 0:
        poll_date = winner['poll_date']
        # Get day name from poll_date
        if isinstance(poll_date, str):
            from datetime import datetime as dt
            poll_date = dt.strptime(poll_date, '%Y-%m-%d').date()
        day_name = poll_date.strftime('%A')
        meal = winner['meal']
        dish_name = winner['option_text']

        # Insert dish if not already in dishes table
        cursor2 = conn.cursor(dictionary=True, buffered=True)
        cursor2.execute("SELECT id FROM dishes WHERE dish_name = %s", (dish_name,))
        existing_dish = cursor2.fetchone()
        if existing_dish:
            dish_id = existing_dish['id']
        else:
            cursor3 = conn.cursor()
            cursor3.execute("INSERT INTO dishes (dish_name) VALUES (%s)", (dish_name,))
            conn.commit()
            dish_id = cursor3.lastrowid
            cursor3.close()

        # Find or create weekly_menu entry for that day+meal
        cursor2.execute("""
            SELECT id FROM weekly_menu WHERE day_of_week = %s AND meal = %s
        """, (day_name, meal))
        menu_entry = cursor2.fetchone()
        if menu_entry:
            menu_id = menu_entry['id']
        else:
            cursor3 = conn.cursor()
            cursor3.execute("INSERT INTO weekly_menu (day_of_week, meal) VALUES (%s, %s)", (day_name, meal))
            conn.commit()
            menu_id = cursor3.lastrowid
            cursor3.close()

        # Add dish to menu_items if not already there
        cursor2.execute("""
            SELECT 1 FROM menu_items WHERE weekly_menu_id = %s AND dish_id = %s
        """, (menu_id, dish_id))
        if not cursor2.fetchone():
            cursor3 = conn.cursor()
            cursor3.execute("INSERT INTO menu_items (weekly_menu_id, dish_id) VALUES (%s, %s)", (menu_id, dish_id))
            conn.commit()
            cursor3.close()

        cursor2.close()

        # Save winner info on poll for display
        cursor4 = conn.cursor()
        cursor4.execute("UPDATE polls SET status='closed', winner_dish=%s WHERE id=%s", (dish_name, poll_id))
        conn.commit()
        cursor4.close()
    else:
        cursor5 = conn.cursor()
        cursor5.execute("UPDATE polls SET status='closed' WHERE id=%s", (poll_id,))
        conn.commit()
        cursor5.close()

    cursor.close()
    conn.close()
    return redirect('/admin/polls')

@app.route('/polls')
def polls():
    if 'user_id' not in session or session['role'] != 'student':
        return redirect('/login')
    user_id = session['user_id']
    now = datetime.now()
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True, buffered=True)

    # Auto-close expired polls and update menu with winner
    cursor.execute("""
        SELECT id FROM polls
        WHERE status='open'
        AND CONCAT(poll_date, ' ', closing_time) < %s
    """, (now.strftime('%Y-%m-%d %H:%M:%S'),))
    expired = cursor.fetchall()
    for ep in expired:
        # Trigger close logic by calling internally
        conn2 = get_db_connection()
        c2 = conn2.cursor(dictionary=True, buffered=True)
        c2.execute("""
            SELECT po.id as option_id, po.option_text,
                   p.meal, p.poll_date, COUNT(pv.id) as vote_count
            FROM poll_options po
            LEFT JOIN poll_votes pv ON po.id = pv.option_id
            JOIN polls p ON p.id = po.poll_id
            WHERE po.poll_id = %s
            GROUP BY po.id ORDER BY vote_count DESC LIMIT 1
        """, (ep['id'],))
        winner = c2.fetchone()
        if winner and winner['vote_count'] > 0:
            poll_date = winner['poll_date']
            if isinstance(poll_date, str):
                poll_date = datetime.strptime(poll_date, '%Y-%m-%d').date()
            day_name = poll_date.strftime('%A')
            meal = winner['meal']
            dish_name = winner['option_text']
            c2.execute("SELECT id FROM dishes WHERE dish_name=%s", (dish_name,))
            d = c2.fetchone()
            c3 = conn2.cursor()
            if d:
                dish_id = d['id']
            else:
                c3.execute("INSERT INTO dishes (dish_name) VALUES (%s)", (dish_name,))
                conn2.commit()
                dish_id = c3.lastrowid
            c2.execute("SELECT id FROM weekly_menu WHERE day_of_week=%s AND meal=%s", (day_name, meal))
            m = c2.fetchone()
            if m:
                menu_id = m['id']
            else:
                c3.execute("INSERT INTO weekly_menu (day_of_week, meal) VALUES (%s, %s)", (day_name, meal))
                conn2.commit()
                menu_id = c3.lastrowid
            c2.execute("SELECT 1 FROM menu_items WHERE weekly_menu_id=%s AND dish_id=%s", (menu_id, dish_id))
            if not c2.fetchone():
                c3.execute("INSERT INTO menu_items (weekly_menu_id, dish_id) VALUES (%s, %s)", (menu_id, dish_id))
            c3.execute("UPDATE polls SET status='closed', winner_dish=%s WHERE id=%s", (dish_name, ep['id']))
            conn2.commit()
            c3.close()
        else:
            c3 = conn2.cursor()
            c3.execute("UPDATE polls SET status='closed' WHERE id=%s", (ep['id'],))
            conn2.commit()
            c3.close()
        c2.close()
        conn2.close()

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

    # ---- DISH RATINGS + SENTIMENT ANALYSIS ----
    cursor.execute("""
        SELECT d.dish_name,
               AVG(f.rating) as avg_rating,
               COUNT(f.id) as total_reviews,
               GROUP_CONCAT(f.comment SEPARATOR '||||') as all_comments
        FROM feedback f
        JOIN dishes d ON f.dish_id = d.id
        GROUP BY d.dish_name
        ORDER BY avg_rating DESC
    """)
    raw_dish_stats = cursor.fetchall() or []

    dish_stats = []
    for dish in raw_dish_stats:
        comments_raw = dish['all_comments'] or ''
        comments = [c.strip() for c in comments_raw.split('||||') if c.strip()]
        pos = neg = neu = 0
        notable_positive = []
        notable_negative = []
        for c in comments:
            sentiment, score = analyze_sentiment(c)
            if sentiment == 'Positive':
                pos += 1
                if len(notable_positive) < 2:
                    notable_positive.append(c)
            elif sentiment == 'Negative':
                neg += 1
                if len(notable_negative) < 2:
                    notable_negative.append(c)
            else:
                neu += 1
        total_c = pos + neg + neu
        sentiment_pct = {
            'positive': round(pos / total_c * 100) if total_c else 0,
            'negative': round(neg / total_c * 100) if total_c else 0,
            'neutral': round(neu / total_c * 100) if total_c else 0,
        }
        # Overall label
        if total_c == 0:
            overall_sentiment = 'No comments'
        elif pos >= neg and pos >= neu:
            overall_sentiment = 'Mostly Positive'
        elif neg >= pos and neg >= neu:
            overall_sentiment = 'Needs Improvement'
        else:
            overall_sentiment = 'Mixed'

        dish_stats.append({
            'dish_name': dish['dish_name'],
            'avg_rating': dish['avg_rating'],
            'total_reviews': dish['total_reviews'],
            'sentiment': overall_sentiment,
            'sentiment_pct': sentiment_pct,
            'notable_positive': notable_positive,
            'notable_negative': notable_negative,
            'comment_count': total_c,
        })

    most_liked = dish_stats[0] if dish_stats else None
    least_liked = dish_stats[-1] if dish_stats else None

    cursor.execute("SELECT AVG(rating) as overall FROM feedback")
    overall_row = cursor.fetchone()
    overall = round(float(overall_row['overall']), 2) if overall_row and overall_row['overall'] else 0

    # ---- BOOKINGS OVER LAST 7 DAYS (trend chart) ----
    cursor.execute("""
        SELECT DATE(booking_date) as bdate, COUNT(*) as count
        FROM bookings
        WHERE booking_date >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
        GROUP BY DATE(booking_date)
        ORDER BY bdate ASC
    """)
    booking_trend = cursor.fetchall() or []

    # ---- MEAL-WISE BOOKINGS ----
    cursor.execute("SELECT meal, COUNT(*) as count FROM bookings GROUP BY meal")
    meal_stats = cursor.fetchall() or []

    # ---- VEG vs NONVEG ----
    cursor.execute("SELECT food_type, COUNT(*) as count FROM bookings GROUP BY food_type")
    food_stats = cursor.fetchall() or []

    # ---- RATING DISTRIBUTION (how many 1s, 2s, 3s, 4s, 5s) ----
    cursor.execute("""
        SELECT rating, COUNT(*) as count FROM feedback
        GROUP BY rating ORDER BY rating ASC
    """)
    rating_dist_raw = cursor.fetchall() or []
    rating_dist = {str(r['rating']): r['count'] for r in rating_dist_raw}

    # ---- MEAL SATISFACTION SCORES ----
    cursor.execute("""
        SELECT wm.meal, AVG(f.rating) as avg_rating, COUNT(f.id) as total
        FROM feedback f
        JOIN bookings b ON f.booking_id = b.id
        JOIN weekly_menu wm ON wm.meal = b.meal
        GROUP BY wm.meal
        ORDER BY avg_rating DESC
    """)
    meal_satisfaction = cursor.fetchall() or []

    # ---- FEEDBACK PARTICIPATION RATE ----
    cursor.execute("SELECT COUNT(*) as total FROM bookings")
    total_bookings = cursor.fetchone()['total'] or 1
    cursor.execute("SELECT COUNT(DISTINCT booking_id) as fb FROM feedback")
    total_feedback_bookings = cursor.fetchone()['fb'] or 0
    feedback_rate = round(total_feedback_bookings / total_bookings * 100, 1)

    cursor.execute("SELECT COUNT(*) as cnt FROM polls WHERE status='open'")
    open_polls_count = cursor.fetchone()['cnt']

    # ---- BOOKING HEATMAP (day x meal) ----
    cursor.execute("""
        SELECT DAYNAME(booking_date) as day_name, meal, COUNT(*) as count
        FROM bookings
        GROUP BY DAYNAME(booking_date), meal
    """)
    heatmap_raw = cursor.fetchall() or []
    days_order  = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']
    meals_order = ['Breakfast','Lunch','Snacks','Dinner']
    heatmap = {d: {m: 0 for m in meals_order} for d in days_order}
    heatmap_max = 1
    for row in heatmap_raw:
        d, m, c = row['day_name'], row['meal'], row['count']
        if d in heatmap and m in heatmap[d]:
            heatmap[d][m] = c
            if c > heatmap_max:
                heatmap_max = c

    # ---- DISH COMEBACK SUGGESTIONS ----
    # Dishes rated >= 4.0 avg but not served in last 14 days
    cursor.execute("""
        SELECT d.dish_name, AVG(f.rating) as avg_rating,
               MAX(b.booking_date) as last_served
        FROM feedback f
        JOIN dishes d ON f.dish_id = d.id
        JOIN bookings b ON f.booking_id = b.id
        GROUP BY d.dish_name
        HAVING avg_rating >= 4.0
           AND MAX(b.booking_date) <= DATE_SUB(CURDATE(), INTERVAL 14 DAY)
        ORDER BY avg_rating DESC
    """)
    comeback_dishes = cursor.fetchall() or []

    cursor.close()
    conn.close()

    return render_template("admin.html",
        bookings=bookings, dish_stats=dish_stats,
        most_liked=most_liked, least_liked=least_liked,
        overall=overall, next_meal=next_meal, next_meal_date=today_date,
        next_meal_count=next_meal_count, student_count=student_count,
        total_guests=total_guests, veg_count=veg_count, nonveg_count=nonveg_count,
        meal_stats=meal_stats, food_stats=food_stats,
        open_polls_count=open_polls_count,
        booking_trend=booking_trend,
        rating_dist=rating_dist,
        meal_satisfaction=meal_satisfaction,
        feedback_rate=feedback_rate,
        heatmap=heatmap, heatmap_max=heatmap_max,
        days_order=days_order, meals_order=meals_order,
        comeback_dishes=comeback_dishes
    )


# ================================================================
# ----------------  WEEKLY PDF REPORT  ---------------------------
# ================================================================
@app.route('/admin/report')
def download_report():
    if session.get('role') != 'admin':
        return redirect('/login')

    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                    Table, TableStyle, HRFlowable, PageBreak)
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    import io

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True, buffered=True)
    now   = datetime.now()
    week_ago = now.date() - timedelta(days=7)

    # --- data collection ---
    cursor.execute("""
        SELECT COUNT(*) as total,
               SUM(CASE WHEN food_type='Veg' THEN 1 ELSE 0 END) as veg,
               SUM(CASE WHEN food_type='Non-Veg' THEN 1 ELSE 0 END) as nonveg,
               COALESCE(SUM(guest_count),0) as guests
        FROM bookings WHERE booking_date >= %s
    """, (week_ago,))
    bk = cursor.fetchone()

    cursor.execute("""
        SELECT meal, COUNT(*) as cnt FROM bookings
        WHERE booking_date >= %s GROUP BY meal ORDER BY cnt DESC
    """, (week_ago,))
    meal_bk = cursor.fetchall() or []

    cursor.execute("""
        SELECT d.dish_name, AVG(f.rating) as avg_r, COUNT(f.id) as reviews,
               GROUP_CONCAT(f.comment SEPARATOR '||||') as comments
        FROM feedback f JOIN dishes d ON f.dish_id=d.id
        JOIN bookings b ON f.booking_id=b.id
        WHERE b.booking_date >= %s
        GROUP BY d.dish_name ORDER BY avg_r DESC
    """, (week_ago,))
    dish_rows = cursor.fetchall() or []

    cursor.execute("""
        SELECT p.question, p.meal, p.poll_date, p.winner_dish,
               COUNT(DISTINCT pv.user_id) as votes
        FROM polls p LEFT JOIN poll_votes pv ON p.id=pv.poll_id
        WHERE p.poll_date >= %s
        GROUP BY p.id ORDER BY p.poll_date DESC
    """, (week_ago,))
    poll_rows = cursor.fetchall() or []

    cursor.execute("SELECT AVG(rating) as avg FROM feedback JOIN bookings b ON feedback.booking_id=b.id WHERE b.booking_date >= %s", (week_ago,))
    avg_row = cursor.fetchone()
    overall_avg = round(float(avg_row['avg']), 2) if avg_row and avg_row['avg'] else 0

    cursor.close()
    conn.close()

    # --- build PDF in memory ---
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            leftMargin=2*cm, rightMargin=2*cm,
                            topMargin=2*cm, bottomMargin=2*cm)

    GREEN  = colors.HexColor('#2e7d32')
    LGREEN = colors.HexColor('#e8f5e9')
    ORANGE = colors.HexColor('#e65100')
    RED    = colors.HexColor('#c62828')
    GREY   = colors.HexColor('#616161')
    LGREY  = colors.HexColor('#f5f5f5')
    WHITE  = colors.white

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('title', fontSize=22, textColor=GREEN,
                                  fontName='Helvetica-Bold', alignment=TA_CENTER, spaceAfter=4)
    sub_style   = ParagraphStyle('sub',   fontSize=11, textColor=GREY,
                                  alignment=TA_CENTER, spaceAfter=2)
    h1_style    = ParagraphStyle('h1',    fontSize=14, textColor=GREEN,
                                  fontName='Helvetica-Bold', spaceBefore=14, spaceAfter=6)
    h2_style    = ParagraphStyle('h2',    fontSize=11, textColor=GREY,
                                  fontName='Helvetica-Bold', spaceBefore=8, spaceAfter=4)
    body_style  = ParagraphStyle('body',  fontSize=10, textColor=colors.black,
                                  leading=15, spaceAfter=4)
    small_style = ParagraphStyle('small', fontSize=9,  textColor=GREY, spaceAfter=3)

    def make_table(data, col_widths, header_bg=LGREEN):
        t = Table(data, colWidths=col_widths)
        style = [
            ('BACKGROUND',  (0,0), (-1,0), header_bg),
            ('TEXTCOLOR',   (0,0), (-1,0), GREEN),
            ('FONTNAME',    (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE',    (0,0), (-1,0), 10),
            ('BOTTOMPADDING',(0,0),(-1,0), 8),
            ('TOPPADDING',  (0,0),(-1,0), 8),
            ('ROWBACKGROUNDS',(0,1),(-1,-1),[WHITE, LGREY]),
            ('FONTSIZE',    (0,1),(-1,-1), 9),
            ('TOPPADDING',  (0,1),(-1,-1), 6),
            ('BOTTOMPADDING',(0,1),(-1,-1),6),
            ('GRID',        (0,0),(-1,-1), 0.4, colors.HexColor('#e0e0e0')),
            ('ROUNDEDCORNERS', [4]),
        ]
        t.setStyle(TableStyle(style))
        return t

    story = []

    # ── Cover ──
    story.append(Spacer(1, 1.5*cm))
    story.append(Paragraph('IntelliMess', title_style))
    story.append(Paragraph('Weekly Operations Report', sub_style))
    story.append(Paragraph(
        f"Week of {week_ago.strftime('%d %b %Y')} – {now.strftime('%d %b %Y')}",
        sub_style))
    story.append(Paragraph(f"Generated on {now.strftime('%d %b %Y, %I:%M %p')}", small_style))
    story.append(HRFlowable(width='100%', thickness=1.5, color=GREEN, spaceAfter=16))

    # ── 1. Booking Summary ──
    story.append(Paragraph('1. Booking Summary', h1_style))
    total = bk['total'] or 0
    veg   = bk['veg']   or 0
    nonveg= bk['nonveg']or 0
    guests= bk['guests']or 0

    summary_data = [
        ['Metric', 'Value'],
        ['Total Bookings (this week)', str(total)],
        ['Vegetarian Bookings',        str(veg)],
        ['Non-Vegetarian Bookings',    str(nonveg)],
        ['Guest Meals Included',       str(guests)],
        ['Overall Avg Satisfaction',   f'{overall_avg} / 5'],
    ]
    story.append(make_table(summary_data, [10*cm, 5*cm]))
    story.append(Spacer(1, 0.4*cm))

    if meal_bk:
        story.append(Paragraph('Bookings by Meal', h2_style))
        meal_data = [['Meal', 'Bookings']] + [[r['meal'], str(r['cnt'])] for r in meal_bk]
        story.append(make_table(meal_data, [10*cm, 5*cm]))
    story.append(Spacer(1, 0.4*cm))

    # ── 2. Satisfaction & Ratings ──
    story.append(PageBreak())
    story.append(Paragraph('2. Dish Ratings & Satisfaction', h1_style))

    if dish_rows:
        rating_data = [['Dish', 'Avg Rating', 'Reviews']]
        for d in dish_rows:
            avg  = round(float(d['avg_r']), 2) if d['avg_r'] else 0
            stars = '★' * int(round(avg)) + '☆' * (5 - int(round(avg)))
            rating_data.append([d['dish_name'], f'{avg}  {stars}', str(d['reviews'])])
        story.append(make_table(rating_data, [8.5*cm, 4.5*cm, 2.5*cm]))

        if dish_rows:
            best  = dish_rows[0]
            worst = dish_rows[-1]
            story.append(Spacer(1, 0.3*cm))
            story.append(Paragraph(
                f"<b>Top Dish:</b> {best['dish_name']} ({round(float(best['avg_r']),2)}/5)",
                body_style))
            story.append(Paragraph(
                f"<b>Needs Attention:</b> {worst['dish_name']} ({round(float(worst['avg_r']),2)}/5)",
                body_style))
    else:
        story.append(Paragraph('No ratings recorded this week.', body_style))

    # ── 3. Sentiment Analysis ──
    story.append(Spacer(1, 0.5*cm))
    story.append(Paragraph('3. Comment Sentiment Analysis', h1_style))

    POSITIVE_WORDS = {'good','great','excellent','amazing','delicious','tasty','loved',
        'fantastic','wonderful','nice','perfect','enjoyed','fresh','hot','crispy',
        'yummy','best','awesome','superb','happy','satisfied','well','better','clean'}
    NEGATIVE_WORDS = {'bad','poor','terrible','awful','horrible','disgusting','cold',
        'stale','overcooked','undercooked','oily','bland','worst','hate','unhappy',
        'disappointed','tasteless','hard','burnt','raw','dirty','spicy','less',
        'not','never','complaint','issue','problem','delay','late','slow','waste'}

    def quick_sentiment(text):
        if not text: return 'Neutral'
        words = text.lower().split()
        p = sum(1 for w in words if w.strip('.,!?') in POSITIVE_WORDS)
        n = sum(1 for w in words if w.strip('.,!?') in NEGATIVE_WORDS)
        return 'Positive' if p > n else ('Negative' if n > p else 'Neutral')

    if dish_rows:
        sent_data = [['Dish', 'Sentiment', 'Top Comment']]
        for d in dish_rows:
            cmts = [c.strip() for c in (d['comments'] or '').split('||||') if c.strip()]
            if not cmts:
                sent_data.append([d['dish_name'], 'No comments', '—'])
                continue
            pos = sum(1 for c in cmts if quick_sentiment(c)=='Positive')
            neg = sum(1 for c in cmts if quick_sentiment(c)=='Negative')
            label = 'Mostly Positive' if pos > neg else ('Needs Improvement' if neg > pos else 'Mixed')
            top   = cmts[0][:60] + ('…' if len(cmts[0])>60 else '')
            sent_data.append([d['dish_name'], label, top])
        story.append(make_table(sent_data, [5*cm, 4*cm, 6.5*cm]))
    else:
        story.append(Paragraph('No comments recorded this week.', body_style))

    # ── 4. Poll Results ──
    story.append(PageBreak())
    story.append(Paragraph('4. Poll Results & Winners', h1_style))

    if poll_rows:
        poll_data = [['Question', 'Meal', 'Date', 'Winner Dish', 'Votes']]
        for p in poll_rows:
            winner = p['winner_dish'] or 'Poll open / no votes'
            date_str = p['poll_date'].strftime('%d %b') if hasattr(p['poll_date'],'strftime') else str(p['poll_date'])
            q = (p['question'][:40] + '…') if len(p['question'])>40 else p['question']
            poll_data.append([q, p['meal'], date_str, winner, str(p['votes'])])
        story.append(make_table(poll_data, [5.5*cm, 2.5*cm, 2*cm, 4*cm, 1.5*cm]))
    else:
        story.append(Paragraph('No polls conducted this week.', body_style))

    # ── Footer note ──
    story.append(Spacer(1, 1*cm))
    story.append(HRFlowable(width='100%', thickness=0.8, color=colors.HexColor('#e0e0e0')))
    story.append(Paragraph('Generated by IntelliMess · Confidential', small_style))

    doc.build(story)
    buf.seek(0)

    filename = f"IntelliMess_Report_{now.strftime('%Y-%m-%d')}.pdf"
    return Response(buf, mimetype='application/pdf',
                    headers={'Content-Disposition': f'attachment; filename={filename}'})


# ---------------- RUN ----------------
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
