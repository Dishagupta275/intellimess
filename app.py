from flask import Flask, render_template, request
import mysql.connector
import os
from datetime import datetime



app = Flask(__name__)

# Database connection function
def get_db_connection():
    return mysql.connector.connect(
        host=os.environ.get("DB_HOST", "localhost"),
        user=os.environ.get("DB_USER", "root"),
        password=os.environ.get("DB_PASSWORD", "8121"),
        database=os.environ.get("DB_NAME", "intellimess")
    )

# Student booking page
@app.route('/')
def home():
    return render_template("booking.html")

from datetime import datetime, timedelta

@app.route('/book', methods=['POST'])
def book():
    name = request.form['name']
    meal = request.form['meal']
    food_type = request.form['food_type']
    date_str = request.form['date']

    now = datetime.now()
    today = now.date()
    tomorrow = today + timedelta(days=1)

    # Convert string to date
    booking_date = datetime.strptime(date_str, "%Y-%m-%d").date()

    # Allow only today or tomorrow
    if booking_date not in [today, tomorrow]:
        return "Booking allowed only for today or tomorrow."

    # Meal times
    meal_times = {
        "Breakfast": 8,
        "Lunch": 13,
        "Dinner": 20
    }

    meal_hour = meal_times[meal]

    # Meal datetime
    meal_datetime = datetime.combine(
        booking_date,
        datetime.min.time()
    ).replace(hour=meal_hour)

    # Booking closing logic
    if meal == "Breakfast":
        # Fixed closing at 6 AM
        closing_time = datetime.combine(
            booking_date,
            datetime.min.time()
        ).replace(hour=6)
    else:
        # 4 hours before meal
        closing_time = meal_datetime - timedelta(hours=4)

    # Conditions
    if now >= meal_datetime:
        return f"{meal} time has already passed. Booking not allowed."

    if now >= closing_time:
        return f"Booking for {meal} is closed."

    # Save booking
    current_time = now.strftime("%H:%M:%S")

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO bookings
        (name, meal, food_type, booking_date, booking_time)
        VALUES (%s, %s, %s, %s, %s)""",
        (name, meal, food_type, booking_date, current_time)
    )
    conn.commit()
    cursor.close()
    conn.close()

    return f"Booking successful for {name} - {meal} ({food_type})"
# Admin dashboard to view bookings with filtering
@app.route('/admin')
def admin():
    # Get filter parameters
    filter_date = request.args.get('date', '')
    filter_meal = request.args.get('meal', '')
    filter_food_type = request.args.get('food_type', '')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Build query with filters
    query = "SELECT * FROM bookings WHERE 1=1"
    params = []
    
    if filter_date:
        query += " AND booking_date = %s"
        params.append(filter_date)
    
    if filter_meal:
        query += " AND meal = %s"
        params.append(filter_meal)
    
    if filter_food_type:
        query += " AND food_type = %s"
        params.append(filter_food_type)
    
    # Order by booking_date and booking_time descending
    query += " ORDER BY booking_date DESC, booking_time DESC"
    
    cursor.execute(query, params)
    bookings = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template("admin.html", bookings=bookings)

# Run the app (deployment-ready)
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)