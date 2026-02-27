from flask import Flask, render_template, request, redirect, session
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
    cursor.execute("""
        SELECT id, meal, food_type, booking_date FROM bookings
        WHERE user_id = %s AND booking_date <= %s
    """, (user_id, today))
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
        feedback_data.append({"booking_id": booking_id, "meal": meal, "dishes": dishes})
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

    cursor.execute("""
        SELECT d.dish_name, AVG(f.rating) as avg_rating FROM feedback f
        JOIN dishes d ON f.dish_id = d.id GROUP BY d.dish_name ORDER BY avg_rating DESC
    """)
    dish_stats = cursor.fetchall() or []
    most_liked = dish_stats[0] if dish_stats else None
    least_liked = dish_stats[-1] if dish_stats else None

    cursor.execute("SELECT AVG(rating) as overall FROM feedback")
    overall_row = cursor.fetchone()
    overall = overall_row['overall'] if overall_row and overall_row['overall'] else 0

    cursor.execute("SELECT meal, COUNT(*) as count FROM bookings GROUP BY meal")
    meal_stats = cursor.fetchall() or []

    cursor.execute("SELECT food_type, COUNT(*) as count FROM bookings GROUP BY food_type")
    food_stats = cursor.fetchall() or []

    cursor.execute("SELECT COUNT(*) as cnt FROM polls WHERE status='open'")
    open_polls_count = cursor.fetchone()['cnt']

    cursor.close()
    conn.close()

    return render_template("admin.html",
        bookings=bookings, dish_stats=dish_stats,
        most_liked=most_liked, least_liked=least_liked,
        overall=overall, next_meal=next_meal, next_meal_date=today_date,
        next_meal_count=next_meal_count, student_count=student_count,
        total_guests=total_guests, veg_count=veg_count, nonveg_count=nonveg_count,
        meal_stats=meal_stats, food_stats=food_stats,
        open_polls_count=open_polls_count
    )

# ---------------- RUN ----------------
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
