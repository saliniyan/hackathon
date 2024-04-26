from flask import Flask, render_template, request
import sqlite3

app = Flask(__name__)

conn = sqlite3.connect('site.db')
cursor = conn.cursor()

house_info = {
    1: {
        'rooms': 3,
        'adults': 2,
        'children': 1
    },
    2: {
        'rooms': 4,
        'adults': 3,
        'children': 2
    },
    3: {
        'rooms': 2,
        'adults': 1,
        'children': 0
    }
}

# Create reservations table if it doesn't exist
create_table_query = '''
CREATE TABLE IF NOT EXISTS reservations (
    id INTEGER PRIMARY KEY,
    check_in DATE NOT NULL,
    check_out DATE NOT NULL,
    rooms INTEGER NOT NULL,
    adults INTEGER NOT NULL,
    children INTEGER NOT NULL,
    House_NO INTEGER
);
'''
cursor.execute(create_table_query)

conn.commit()
conn.close()

# Routes
@app.route('/')
def index():
    return render_template('index1.html')

@app.route('/submit', methods=['POST'])
def submit():
    check_in = request.form['check_in']
    check_out = request.form['check_out']
    rooms_needed = int(request.form['rooms'])
    conn = sqlite3.connect('site.db')
    cursor = conn.cursor()

    available_houses = []
    for house_id, info in house_info.items():
        if info['rooms'] >= rooms_needed:
            available_houses.append(house_id)

    # Collect all available houses that are not booked for the requested dates
    available_results = []
    for house_id in available_houses:
        cursor.execute('''
            SELECT COUNT(*) FROM reservations
            WHERE House_NO = ? AND
            (check_in BETWEEN ? AND ? OR check_out BETWEEN ? AND ?);
        ''', (house_id, check_in, check_out, check_in, check_out))
        booking_count = cursor.fetchone()[0]
        if booking_count == 0:
            available_results.append(f"House {house_id} is available for your dates with {house_info[house_id]['rooms']} rooms.")

    # If available houses were found display them
    if available_results:
        return render_template('available_houses.html', available_results=available_results)
    else:
        return "Sorry, no houses are available for your requested dates or rooms."

if __name__ == '__main__':
    app.run(debug=True)
