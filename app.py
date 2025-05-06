#Izveidots ar MI
from pathlib import Path
from flask import Flask, render_template, request, redirect, url_for, session, flash
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

#New Ticket View for admins
@app.route('/admin/new_tickets', methods=['POST'])
def view_all_new_tickets():
    if not session.get('admin'):
        return redirect('/admin_login')

    conn = get_db_connection()
    tickets = conn.execute('SELECT * FROM NewTickets').fetchall()
    conn.close()
    return render_template('admin_new_tickets.html', tickets=tickets)
#Mark ticket taken
@app.route('/mark_ticket_taken/<int:ticket_id>', methods=['POST'])
def mark_ticket_taken(ticket_id):
    if not session.get('admin'):
        return redirect('/admin_login')

    conn = get_db_connection()

    # Fetch the ticket from the NewTickets table
    ticket = conn.execute('SELECT * FROM NewTickets WHERE id = ?', (ticket_id,)).fetchone()

    if ticket:
        # Insert the ticket into the TakenTickets table
        conn.execute('''
            INSERT INTO TakenTickets (id, name, ticket_title, ticket_issue, email, category_id)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            ticket['id'], ticket['name'], ticket['ticket_title'],
            ticket['ticket_issue'], ticket['email'], ticket['category_id']
        ))

        # Update the 'is_taken' value to 1 for the current ticket
        conn.execute('UPDATE NewTickets SET is_taken = 1 WHERE id = ?', (ticket_id,))

        # Delete all tickets in NewTickets where is_taken = 1
        conn.execute('DELETE FROM NewTickets WHERE is_taken = 1')

    conn.commit()
    conn.close()

    return redirect('/admin/new_tickets')

@app.route('/mark_ticket_completed/<int:ticket_id>', methods=['POST'])
def mark_ticket_completed(ticket_id):
    if not session.get('admin'):
        return redirect('/admin_login')

    conn = get_db_connection()

    # Fetch the ticket from the TakenTickets table
    ticket = conn.execute('SELECT * FROM TakenTickets WHERE id = ?', (ticket_id,)).fetchone()

    if ticket:
        # Mark the ticket as completed by setting is_completed to 1
        conn.execute('UPDATE TakenTickets SET is_finished = 1 WHERE id = ?', (ticket_id,))

        # Insert the ticket into the CompletedTickets table
        conn.execute('''
            INSERT INTO CompletedTickets (id, name, ticket_title, ticket_issue, email, category_id)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            ticket['id'], ticket['name'], ticket['ticket_title'],
            ticket['ticket_issue'], ticket['email'], ticket['category_id']
        ))

        # Delete the ticket from TakenTickets since it's now completed
        conn.execute('DELETE FROM TakenTickets WHERE id = ?', (ticket_id,))

    conn.commit()
    conn.close()

    return redirect('/admin/completed_tickets')



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
    user_email = session.get('user')
    is_admin = session.get('admin')

    if not user_email and not is_admin:
        return redirect('/user_login')

    conn = get_db_connection()

    if is_admin:
        # Admins can delete by ID from any table
        for table in ['NewTickets', 'TakenTickets', 'CompletedTickets']:
            conn.execute(f'DELETE FROM {table} WHERE id = ?', (ticket_id,))
    else:
        # Users can delete only their own tickets by email
        for table in ['NewTickets', 'TakenTickets', 'CompletedTickets']:
            conn.execute(f'DELETE FROM {table} WHERE id = ? AND email = ?', (ticket_id, user_email))

    conn.commit()
    conn.close()

    return redirect('/my_tickets') if user_email else redirect('/admin/new_tickets')




#Ticket submission form
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
    user_email = session.get('user')
    
    if not user_email:
        return redirect('/user_login')

    conn = get_db_connection()

    tickets_new = conn.execute('''
        SELECT t.*, c.name AS category_name
        FROM NewTickets t
        LEFT JOIN Categories c ON t.category_id = c.id
        WHERE t.email = ?
    ''', (user_email,)).fetchall()

    tickets_taken = conn.execute('''
        SELECT t.*, c.name AS category_name
        FROM TakenTickets t
        LEFT JOIN Categories c ON t.category_id = c.id
        WHERE t.email = ?
    ''', (user_email,)).fetchall()

    tickets_completed = conn.execute('''
        SELECT t.*, c.name AS category_name
        FROM CompletedTickets t
        LEFT JOIN Categories c ON t.category_id = c.id
        WHERE t.email = ?
    ''', (user_email,)).fetchall()


    print(f"Tickets for {user_email}:")
    print(f"New tickets: {tickets_new}")
    print(f"Taken tickets: {tickets_taken}")
    print(f"Completed tickets: {tickets_completed}")
    
    conn.close()

    return render_template('my_tickets.html', tickets_new=tickets_new, tickets_taken=tickets_taken, tickets_completed=tickets_completed)



#LOGIN TO SEE YOUR OWN TICKETS
@app.route('/user_login', methods=['GET', 'POST'])
def user_login():
    if request.method == 'POST':
        email = request.form['email'].strip().lower()

        conn = get_db_connection()

        exists_in_new = conn.execute('SELECT 1 FROM NewTickets WHERE email = ?', (email,)).fetchone()
        exists_in_taken = conn.execute('SELECT 1 FROM TakenTickets WHERE email = ?', (email,)).fetchone()
        exists_in_completed = conn.execute('SELECT 1 FROM CompletedTickets WHERE email = ?', (email,)).fetchone()

        conn.close()

        if exists_in_new or exists_in_taken or exists_in_completed:
            session['user'] = email
            return redirect('/my_tickets')
        else:
            flash('Email not found in the system.')
    
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
