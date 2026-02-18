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
    cursor.execute(
        "SELECT * FROM users WHERE username=%s AND password=%s",
        (username, password)
    )
    user = cursor.fetchone()
    cursor.close()
    conn.close()

    if user:
        session['user_id'] = user['id']
        session['role'] = user['role']

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
    return render_template("student.html")

# ---------------- MENU (NEXT 4 MEALS) ----------------
@app.route('/menu')
def menu():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    meal_times = [
        ("Breakfast", "07:30"),
        ("Lunch", "11:45"),
        ("Snacks", "16:30"),
        ("Dinner", "19:30")
    ]

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
            SELECT d.dish_name
            FROM weekly_menu wm
            JOIN menu_items mi ON wm.id = mi.weekly_menu_id
            JOIN dishes d ON mi.dish_id = d.id
            WHERE wm.day_of_week = %s AND wm.meal = %s
        """, (day, meal))

        dishes = [row['dish_name'] for row in cursor.fetchall()]
        menu_data.append({
            "day": day,
            "meal": meal,
            "dishes": dishes
        })

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

    now = datetime.now()
    today = now.date()
    tomorrow = today + timedelta(days=1)
    booking_date = datetime.strptime(date_str, "%Y-%m-%d").date()

    if booking_date not in [today, tomorrow]:
        return "Booking allowed only for today or tomorrow."

    meal_times = {
        "Breakfast": 8,
        "Lunch": 13,
        "Dinner": 20
    }

    meal_hour = meal_times[meal]
    meal_datetime = datetime.combine(booking_date, datetime.min.time()).replace(hour=meal_hour)

    if meal == "Breakfast":
        closing_time = meal_datetime.replace(hour=6)
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
        INSERT INTO bookings
        (user_id, meal, food_type, booking_date, booking_time)
        VALUES (%s, %s, %s, %s, %s)
    """, (user_id, meal, food_type, booking_date, current_time))
    conn.commit()
    cursor.close()
    conn.close()

    return "Booking successful"

# ---------------- FEEDBACK ----------------
@app.route('/feedback')
def feedback():
    if 'user_id' not in session:
        return redirect('/login')

    user_id = session['user_id']
    now = datetime.now()
    today = now.date()
    current_day = now.strftime('%A')

    meal_times = {
        "Breakfast": 7,
        "Lunch": 12,
        "Snacks": 16,
        "Dinner": 19
    }

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT meal, food_type
        FROM bookings
        WHERE user_id = %s AND booking_date = %s
    """, (user_id, today))

    bookings = cursor.fetchall()
    feedback_data = {}

    for booking in bookings:
        meal = booking['meal']
        food_type = booking['food_type']

        meal_hour = meal_times[meal]
        meal_time = datetime.combine(today, datetime.min.time()).replace(hour=meal_hour)

        if now < meal_time:
            continue

        if food_type == "Veg":
            cursor.execute("""
                SELECT d.id, d.dish_name
                FROM dishes d
                JOIN menu_items mi ON d.id = mi.dish_id
                JOIN weekly_menu wm ON wm.id = mi.weekly_menu_id
                WHERE wm.day_of_week = %s AND wm.meal = %s
                AND d.dish_name NOT LIKE '%Chicken%'
                AND d.dish_name NOT LIKE '%Egg%'
            """, (current_day, meal))
        else:
            cursor.execute("""
                SELECT d.id, d.dish_name
                FROM dishes d
                JOIN menu_items mi ON d.id = mi.dish_id
                JOIN weekly_menu wm ON wm.id = mi.weekly_menu_id
                WHERE wm.day_of_week = %s AND wm.meal = %s
                AND d.dish_name NOT LIKE '%Paneer%'
            """, (current_day, meal))

        feedback_data[meal] = cursor.fetchall()

    cursor.close()
    conn.close()

    if not feedback_data:
        return "No completed meals available for feedback."

    return render_template("feedback.html", feedback_data=feedback_data)

@app.route('/submit_feedback', methods=['POST'])
def submit_feedback():
    if 'user_id' not in session:
        return redirect('/login')

    user_id = session['user_id']
    feedback_date = datetime.now().date()

    conn = get_db_connection()
    cursor = conn.cursor()

    for key in request.form:
        if key.startswith("rating_"):
            dish_id = key.split("_")[1]
            rating = request.form[key]
            comment = request.form.get(f"comment_{dish_id}", "")

            cursor.execute("""
                INSERT INTO feedback
                (user_id, dish_id, rating, comment, feedback_date)
                VALUES (%s, %s, %s, %s, %s)
            """, (user_id, dish_id, rating, comment, feedback_date))

    conn.commit()
    cursor.close()
    conn.close()

    return "Feedback submitted successfully"

# ---------------- ADMIN ----------------
@app.route('/admin')
def admin():
    if 'user_id' not in session or session['role'] != 'admin':
        return redirect('/login')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM bookings")
    bookings = cursor.fetchall()

    cursor.execute("""
        SELECT f.rating, d.dish_name, u.username
        FROM feedback f
        JOIN dishes d ON f.dish_id = d.id
        JOIN users u ON f.user_id = u.id
    """)
    feedback = cursor.fetchall()

    cursor.execute("""
        SELECT d.dish_name, AVG(f.rating) as avg_rating
        FROM feedback f
        JOIN dishes d ON f.dish_id = d.id
        GROUP BY d.dish_name
        ORDER BY avg_rating DESC
    """)
    dish_stats = cursor.fetchall()

    most_liked = dish_stats[0] if dish_stats else None
    least_liked = dish_stats[-1] if dish_stats else None

    cursor.execute("SELECT AVG(rating) as overall FROM feedback")
    overall = cursor.fetchone()

    cursor.close()
    conn.close()

    return render_template(
        "admin.html",
        bookings=bookings,
        feedback=feedback,
        dish_stats=dish_stats,
        most_liked=most_liked,
        least_liked=least_liked,
        overall=overall
    )

# ---------------- RUN ----------------
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)