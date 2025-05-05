#Izveidots ar MI
from pathlib import Path
from flask import Flask, render_template, request, redirect, session, flash
import sqlite3

app = Flask(__name__)
app.secret_key = 'carsdf_is_a_sigma'

# Database helper
def get_db_connection():
    db = Path(__file__).parent/"tickets.db"
    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    return conn

# Form
@app.route('/')
def show_new_tickets():
    conn = get_db_connection()
    tickets = conn.execute('SELECT * FROM NewTickets').fetchall()
    categories = conn.execute('SELECT * FROM Categories').fetchall()
    conn.close()
    return render_template('submit.html', tickets=tickets, categories=categories)

# New tickets view (ADMIN)
@app.route('/admin/new_tickets')
def admin_new_tickets():
    if not session.get('admin'):
        return redirect('/admin_login')

    conn = get_db_connection()
    tickets = conn.execute(
        '''SELECT nt.*, c.name as category_name
           FROM NewTickets nt
           LEFT JOIN Categories c ON nt.category_id = c.id'''
    ).fetchall()
    conn.close()

    return render_template('new_tickets.html', tickets=tickets)



# Login route
@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        admin = conn.execute(
            'SELECT * FROM Admins WHERE username = ? AND password = ?',
            (username, password)
        ).fetchone()
        conn.close()

        if admin:
            session.clear()
            session['admin'] = True
            return redirect('/admin')
        else:
            flash('Invalid admin credentials.')
            return redirect('/admin_login')

    return render_template('admin_login.html')


@app.route('/admin/new_tickets', methods=['POST'])
def view_all_new_tickets():
    if not session.get('admin'):
        return redirect('/admin_login')

    conn = get_db_connection()
    tickets = conn.execute('SELECT * FROM NewTickets').fetchall()
    conn.close()
    return render_template('admin_new_tickets.html', tickets=tickets)

@app.route('/mark_ticket_taken/<int:ticket_id>', methods=['POST'])
def mark_ticket_taken(ticket_id):
    if not session.get('admin'):
        return redirect('/admin_login')

    conn = get_db_connection()
    ticket = conn.execute('SELECT * FROM NewTickets WHERE id = ?', (ticket_id,)).fetchone()

    if ticket:
        conn.execute('''
            INSERT INTO TakenTickets (id, name, ticket_title, ticket_issue, email, category_id)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            ticket['id'], ticket['name'], ticket['ticket_title'],
            ticket['ticket_issue'], ticket['email'], ticket['category_id']
        ))
        conn.execute('DELETE FROM NewTickets WHERE id = ?', (ticket_id,))

    conn.commit()
    conn.close()
    return redirect('/admin/new_tickets')

# Logout route
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# Admin dashboard
@app.route('/admin')
def admin_dashboard():
    if not session.get('admin'):
        return redirect('/adnin_login')

    conn = get_db_connection()
    new_count = conn.execute('SELECT COUNT(*) FROM NewTickets').fetchone()[0]
    taken_count = conn.execute('SELECT COUNT(*) FROM TakenTickets').fetchone()[0]
    completed_count = conn.execute('SELECT COUNT(*) FROM CompletedTickets').fetchone()[0]

    categories = conn.execute('SELECT * FROM Categories').fetchall()
    category_stats = []
    for category in categories:
        cat_id = category['id']
        new = conn.execute('SELECT COUNT(*) FROM NewTickets WHERE category_id = ?', (cat_id,)).fetchone()[0]
        taken = conn.execute('SELECT COUNT(*) FROM TakenTickets WHERE category_id = ?', (cat_id,)).fetchone()[0]
        completed = conn.execute('SELECT COUNT(*) FROM CompletedTickets WHERE category_id = ?', (cat_id,)).fetchone()[0]
        category_stats.append({
            'name': category['name'],
            'new': new,
            'taken': taken,
            'completed': completed
        })

    conn.close()
    return render_template('admin_dashboard.html',
                           new_count=new_count,
                           taken_count=taken_count,
                           completed_count=completed_count,
                           category_stats=category_stats)


# Taken Tickets view
@app.route('/admin/taken_tickets')
def admin_taken_tickets():
    if not session.get('admin'):
        return redirect('/admin_login')

    conn = get_db_connection()
    tickets = conn.execute(
        '''SELECT tt.*, c.name as category_name
           FROM TakenTickets tt
           LEFT JOIN Categories c ON tt.category_id = c.id'''
    ).fetchall()
    conn.close()

    return render_template('taken_tickets.html', tickets=tickets)



# Mark a ticket as completed
@app.route('/complete_ticket/<int:ticket_id>', methods=['POST'])
def complete_ticket(ticket_id):
    if not session.get('admin'):
        return redirect('/admin_login')

    conn = get_db_connection()
    ticket = conn.execute('SELECT * FROM TakenTickets WHERE id = ?', (ticket_id,)).fetchone()

    if ticket:
        conn.execute('''
            INSERT INTO CompletedTickets (id, name, ticket_title, ticket_issue, email, category_id)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            ticket['id'], ticket['name'], ticket['ticket_title'],
            ticket['ticket_issue'], ticket['email'], ticket['category_id']
        ))
        conn.execute('DELETE FROM TakenTickets WHERE id = ?', (ticket_id,))

    conn.commit()
    conn.close()
    return redirect('/admin/taken_tickets')  

#DELETE TICKET FUNCTION
@app.route('/delete_ticket/<int:ticket_id>', methods=['POST'])
def delete_ticket(ticket_id):
    if not session.get('admin'):
        return redirect('/admin_login')

    conn = get_db_connection()

    # Deletes from all three - at least one will be found and deleted.
    conn.execute('DELETE FROM NewTickets WHERE id = ?', (ticket_id,))
    conn.execute('DELETE FROM TakenTickets WHERE id = ?', (ticket_id,))
    conn.execute('DELETE FROM CompletedTickets WHERE id = ?', (ticket_id,))

    conn.commit()
    conn.close()
    return redirect(request.referrer or '/admin')



@app.route('/submit_ticket', methods=['GET', 'POST'])
def submit_ticket():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        title = request.form['ticket_title']
        issue = request.form['ticket_issue']
        category_id = request.form['category_id']

        conn = get_db_connection()
        conn.execute('''
            INSERT INTO NewTickets (name, ticket_title, ticket_issue, email, is_taken, category_id)
            VALUES (?, ?, ?, ?, 0, ?)
        ''', (name, title, issue, email, category_id))
        conn.commit()
        conn.close()

        flash('Ticket submitted successfully!')
        return redirect('/')

    # For GET: Show the form with categories
    conn = get_db_connection()
    categories = conn.execute('SELECT * FROM Categories').fetchall()
    conn.close()
    return render_template('submit.html', categories=categories)

#Check your own tickets
@app.route('/my_tickets')
def my_tickets():
    user_email = session.get('user_email')
    if not user_email:
        flash('Please log in with your email to view your tickets.')
        return redirect('/user_login')

    conn = get_db_connection()

    # New tickets
    new_tickets = conn.execute(
        '''SELECT nt.*, c.name AS category_name
           FROM NewTickets nt
           LEFT JOIN Categories c ON nt.category_id = c.id
           WHERE nt.email = ?''',
        (user_email,)
    ).fetchall()

    # Taken tickets
    taken_tickets = conn.execute(
        '''SELECT tt.*, c.name AS category_name
           FROM TakenTickets tt
           LEFT JOIN Categories c ON tt.category_id = c.id
           WHERE tt.email = ?''',
        (user_email,)
    ).fetchall()

    # Completed tickets
    completed_tickets = conn.execute(
        '''SELECT ct.*, c.name AS category_name
           FROM CompletedTickets ct
           LEFT JOIN Categories c ON ct.category_id = c.id
           WHERE ct.email = ?''',
        (user_email,)
    ).fetchall()

    conn.close()

    return render_template('my_tickets.html',
                           new_tickets=new_tickets,
                           taken_tickets=taken_tickets,
                           completed_tickets=completed_tickets)

#LOGIN TO SEE YOUR OWN TICKETS
@app.route('/user_login', methods=['GET', 'POST'])
def user_login():
    if request.method == 'POST':
        email = request.form['email']
        # Optionally: check that this email actually exists in the DB
        session.clear()
        session['user_email'] = email
        return redirect('/my_tickets')
    return render_template('user_login.html')

#COMPLETED TICKETS (ADMIN)
@app.route('/admin/completed_tickets')
def admin_completed_tickets():
    if not session.get('admin'):
        return redirect('/admin_login')

    conn = get_db_connection()
    tickets = conn.execute(
        '''SELECT ct.*, c.name as category_name
           FROM CompletedTickets ct
           LEFT JOIN Categories c ON ct.category_id = c.id'''
    ).fetchall()
    conn.close()

    return render_template('completed_tickets.html', tickets=tickets)



if __name__ == '__main__':
    app.run(debug=True)
