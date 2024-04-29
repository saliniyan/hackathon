from flask import Flask, render_template, request, g, redirect, url_for, session
import sqlite3


application = Flask(__name__)
application.config['DATABASE'] = 'site.db'
application.secret_key = "hello"

mail = "saliniyanp02@gmail.com"

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(application.config['DATABASE'])
        db.row_factory = sqlite3.Row  # Access rows as dictionaries
    return db

def close_db(e=None):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

@application.teardown_appcontext
def teardown_db(e=None):
    close_db()

house_info = {
    1: {
        'rooms': 3,
        'adults': 2,
        'children': 1,
        'description': "NATURAL VIEW",
        'url': "https://saliniyan.github.io/images/room.jpeg"
    },

    2: {
        'rooms': 4,
        'adults': 3,
        'children': 2,
        'description': "HOTEL NEAR",
        'url': "https://saliniyan.github.io/images/room.jpeg"
    },
    3: {
        'rooms': 2,
        'adults': 1,
        'children': 0,
        'description': "PARKING LOT",
        'url': "https://saliniyan.github.io/images/room.jpeg"
    }
}

def create_tables():
    with application.app_context():
        db = get_db()
        cursor = db.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reservations (
                User varchar(50),
                id INTEGER PRIMARY KEY,
                check_in DATE NOT NULL,
                check_out DATE NOT NULL,
                House_NO INTEGER NOT NULL,
                status varchar(50),
                FOREIGN KEY (House_NO) REFERENCES houses(id)
            );
        ''')
        db.commit()

@application.route('/')
def index():
    return render_template('login.html')

@application.route('/authenticate', methods=['POST'])
def authenticate():
    username = request.form['username']
    password = request.form['password']

    if username == 's' and password == '123':
        session['username'] = username
        return redirect(url_for('index1'))  # Redirect to index1 route
    elif username == 'b' and password == '456':
        session['username'] = username
        return redirect(url_for('admin_panel'))  # Redirect to admin_panel route
    else:
        return "Invalid credentials"

@application.route('/index1')
def index1():
    if 'username' in session and session['username'] == 's':
        return render_template('index1.html')
    else:
        return redirect(url_for('index'))

@application.route('/submit', methods=['POST'])
def submit():
    check_in = request.form['check_in']
    check_out = request.form['check_out']
    rooms_needed = int(request.form['rooms'])

    if not check_in or not check_out or rooms_needed <= 0:
        return "Invalid input. Please fill in all fields correctly."

    db = get_db()
    cursor = db.cursor()

    available_houses = []
    for house_id, info in house_info.items():
        if info['rooms'] >= rooms_needed:
            available_houses.append(house_id)

    available_results = []
    for house_id in available_houses:
        cursor.execute('''
            SELECT COUNT(*) FROM reservations
            WHERE House_NO = ? AND
            (check_in BETWEEN ? AND ? OR check_out BETWEEN ? AND ?) AND
            status != 'rejected';  -- Exclude bookings with status 'rejected'
        ''', (house_id, check_in, check_out, check_in, check_out))
        booking_count = cursor.fetchone()[0]
        if booking_count == 0:
            house_description = house_info[house_id]['description']
            house_url = house_info[house_id]['url']
            available_results.append({
                'house_id': house_id,
                'rooms': house_info[house_id]['rooms'],
                'description': house_description,
                'url': house_url
            })


    if available_results:
        return render_template('available_houses.html', available_results=available_results)
    else:
        return "Sorry, no houses are available for your requested dates or rooms."

@application.route('/book', methods=['POST'])
def book():
    house_id = request.form['house_id']
    check_in = request.form['check_in']
    check_out = request.form['check_out']

    if not house_id or not check_in or not check_out:
        return "Invalid input. Please fill in all fields correctly."

    db = get_db()
    cursor = db.cursor()
    status = "pending"

    cursor.execute('''
        INSERT INTO reservations (check_in, check_out, House_NO, status, User)
        VALUES (?, ?, ?, ?, ?);
    ''', (check_in, check_out, house_id, status, mail))

    db.commit()

    success_message = "Your Request was successfully sent to admin"

    return render_template('success.html', success_message=success_message)

@application.route('/admin', methods=['GET', 'POST'])
def admin_panel():
    if request.method == 'GET':
        db = get_db()
        cursor = db.cursor()
        cursor.execute('''
            SELECT * FROM reservations WHERE status = 'pending';
        ''')
        pending_bookings = cursor.fetchall()
        
        return render_template('admin_panel.html', pending_bookings=pending_bookings)
    elif request.method == 'POST':
        booking_id = request.form['booking_id']
        action = request.form['action']

        if action == 'accept':
            db = get_db()
            cursor = db.cursor()
            cursor.execute('''
                UPDATE reservations SET status = 'accepted' WHERE id = ?;
            ''', (booking_id,))
            db.commit()
        elif action == 'reject':
            db = get_db()
            cursor = db.cursor()
            cursor.execute('''
                UPDATE reservations SET status = 'rejected' WHERE id = ?;
            ''', (booking_id,))
            db.commit()

        return redirect(url_for('admin_panel'))

if __name__ == '__main__':
    create_tables()
    application.run(debug=True)
