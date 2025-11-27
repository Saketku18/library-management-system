from flask import Flask, render_template_string, request, jsonify
import sqlite3
from datetime import datetime, timedelta

app = Flask(__name__)

HTML = '''<!DOCTYPE html>
<html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Library Management</title><style>
*{margin:0;padding:0;box-sizing:border-box}body{font-family:Arial,sans-serif;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);min-height:100vh;padding:20px}
.container{max-width:1200px;margin:0 auto}header{background:#fff;padding:25px;border-radius:12px;box-shadow:0 5px 20px rgba(0,0,0,.2);margin-bottom:20px;text-align:center}
h1{color:#667eea;font-size:2em}.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:15px;margin-bottom:20px}
.stat-card{background:#fff;padding:20px;border-radius:10px;box-shadow:0 3px 10px rgba(0,0,0,.1);text-align:center}.stat-number{font-size:2em;font-weight:bold;color:#667eea}
.stat-label{color:#666;font-size:.85em;margin-top:5px}.main{display:grid;grid-template-columns:200px 1fr;gap:20px}
.sidebar{background:#fff;padding:15px;border-radius:10px;box-shadow:0 3px 10px rgba(0,0,0,.1);height:fit-content}
.nav-btn{width:100%;padding:12px;margin-bottom:8px;border:none;background:#f0f0f0;border-radius:6px;cursor:pointer;text-align:left;transition:all .3s}
.nav-btn:hover,.nav-btn.active{background:#667eea;color:#fff}.content{background:#fff;padding:25px;border-radius:10px;box-shadow:0 3px 10px rgba(0,0,0,.1)}
.section{display:none}.section.active{display:block}.form-group{margin-bottom:15px}label{display:block;margin-bottom:5px;font-weight:500}
input,select{width:100%;padding:10px;border:2px solid #e0e0e0;border-radius:6px;font-size:1em}input:focus,select:focus{outline:none;border-color:#667eea}
.btn{padding:10px 25px;border:none;border-radius:6px;cursor:pointer;font-size:1em;transition:all .3s}.btn-primary{background:#667eea;color:#fff}
.btn-primary:hover{background:#5568d3}table{width:100%;border-collapse:collapse;margin-top:15px}th,td{padding:12px;text-align:left;border-bottom:1px solid #e0e0e0}
th{background:#f8f9fa;color:#667eea;font-weight:600}tr:hover{background:#f8f9fa}.badge{padding:4px 10px;border-radius:15px;font-size:.85em}
.badge-success{background:#d4edda;color:#155724}.badge-danger{background:#f8d7da;color:#721c24}.alert{padding:12px;border-radius:6px;margin-bottom:15px}
.alert-success{background:#d4edda;color:#155724}.alert-error{background:#f8d7da;color:#721c24}
@media (max-width:768px){.main{grid-template-columns:1fr}.stats{grid-template-columns:1fr 1fr}}
</style></head><body>
<div class="container"><header><h1>📚 Library Management System</h1></header>
<div class="stats">
<div class="stat-card"><div class="stat-number" id="totalBooks">0</div><div class="stat-label">Total Books</div></div>
<div class="stat-card"><div class="stat-number" id="totalMembers">0</div><div class="stat-label">Members</div></div>
<div class="stat-card"><div class="stat-number" id="borrowed">0</div><div class="stat-label">Borrowed</div></div>
<div class="stat-card"><div class="stat-number" id="overdue">0</div><div class="stat-label">Overdue</div></div>
</div>
<div class="main"><div class="sidebar">
<button class="nav-btn active" onclick="showSection('books')">📖 Books</button>
<button class="nav-btn" onclick="showSection('addBook')">➕ Add Book</button>
<button class="nav-btn" onclick="showSection('members')">👥 Members</button>
<button class="nav-btn" onclick="showSection('addMember')">➕ Add Member</button>
<button class="nav-btn" onclick="showSection('borrow')">📤 Borrow</button>
<button class="nav-btn" onclick="showSection('return')">📥 Return</button>
</div>
<div class="content">
<div id="books" class="section active"><h2>All Books</h2><table><thead><tr><th>ID</th><th>Title</th><th>Author</th><th>ISBN</th><th>Available</th></tr></thead>
<tbody id="booksTable"></tbody></table></div>
<div id="addBook" class="section"><h2>Add New Book</h2><div id="bookAlert"></div><form onsubmit="addBook(event)">
<div class="form-group"><label>Title *</label><input type="text" id="bookTitle" required></div>
<div class="form-group"><label>Author *</label><input type="text" id="bookAuthor" required></div>
<div class="form-group"><label>ISBN *</label><input type="text" id="bookISBN" required></div>
<div class="form-group"><label>Year *</label><input type="number" id="bookYear" required></div>
<div class="form-group"><label>Category *</label><input type="text" id="bookCategory" required></div>
<div class="form-group"><label>Copies *</label><input type="number" id="bookCopies" value="1" required></div>
<button type="submit" class="btn btn-primary">Add Book</button></form></div>
<div id="members" class="section"><h2>All Members</h2><table><thead><tr><th>ID</th><th>Name</th><th>Email</th><th>Phone</th><th>Status</th></tr></thead>
<tbody id="membersTable"></tbody></table></div>
<div id="addMember" class="section"><h2>Add New Member</h2><div id="memberAlert"></div><form onsubmit="addMember(event)">
<div class="form-group"><label>Name *</label><input type="text" id="memberName" required></div>
<div class="form-group"><label>Email *</label><input type="email" id="memberEmail" required></div>
<div class="form-group"><label>Phone *</label><input type="tel" id="memberPhone" required></div>
<div class="form-group"><label>Address</label><input type="text" id="memberAddress"></div>
<button type="submit" class="btn btn-primary">Add Member</button></form></div>
<div id="borrow" class="section"><h2>Borrow a Book</h2><div id="borrowAlert"></div><form onsubmit="borrowBook(event)">
<div class="form-group"><label>Member ID *</label><input type="number" id="borrowMember" required></div>
<div class="form-group"><label>Book ID *</label><input type="number" id="borrowBookId" required></div>
<div class="form-group"><label>Days *</label><input type="number" id="borrowDays" value="14" required></div>
<button type="submit" class="btn btn-primary">Borrow Book</button></form></div>
<div id="return" class="section"><h2>Return a Book</h2><div id="returnAlert"></div><form onsubmit="returnBook(event)">
<div class="form-group"><label>Transaction ID *</label><input type="number" id="returnTransaction" required></div>
<button type="submit" class="btn btn-primary">Return Book</button></form></div>
</div></div></div>
<script>
function showSection(id){document.querySelectorAll('.section').forEach(s=>s.classList.remove('active'));
document.querySelectorAll('.nav-btn').forEach(b=>b.classList.remove('active'));
document.getElementById(id).classList.add('active');event.target.classList.add('active');}
async function loadStats(){const r=await fetch('/api/stats');const d=await r.json();
document.getElementById('totalBooks').textContent=d.total_book_titles||0;
document.getElementById('totalMembers').textContent=d.active_members||0;
document.getElementById('borrowed').textContent=d.borrowed_books||0;
document.getElementById('overdue').textContent=d.overdue_books||0;}
async function loadBooks(){const r=await fetch('/api/books');const d=await r.json();
document.getElementById('booksTable').innerHTML=d.map(b=>`<tr><td>${b[0]}</td><td>${b[1]}</td><td>${b[2]}</td><td>${b[3]}</td>
<td><span class="badge ${b[7]>0?'badge-success':'badge-danger'}">${b[7]}/${b[6]}</span></td></tr>`).join('');}
async function loadMembers(){const r=await fetch('/api/members');const d=await r.json();
document.getElementById('membersTable').innerHTML=d.map(m=>`<tr><td>${m[0]}</td><td>${m[1]}</td><td>${m[2]}</td><td>${m[3]}</td>
<td><span class="badge badge-success">${m[6]}</span></td></tr>`).join('');}
async function addBook(e){e.preventDefault();const data={title:document.getElementById('bookTitle').value,
author:document.getElementById('bookAuthor').value,isbn:document.getElementById('bookISBN').value,
year:document.getElementById('bookYear').value,category:document.getElementById('bookCategory').value,
copies:document.getElementById('bookCopies').value};
const r=await fetch('/api/books',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)});
const res=await r.json();document.getElementById('bookAlert').innerHTML=
`<div class="alert ${res.success?'alert-success':'alert-error'}">${res.message}</div>`;
if(res.success){e.target.reset();loadBooks();loadStats();}setTimeout(()=>document.getElementById('bookAlert').innerHTML='',3000);}
async function addMember(e){e.preventDefault();const data={name:document.getElementById('memberName').value,
email:document.getElementById('memberEmail').value,phone:document.getElementById('memberPhone').value,
address:document.getElementById('memberAddress').value};
const r=await fetch('/api/members',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)});
const res=await r.json();document.getElementById('memberAlert').innerHTML=
`<div class="alert ${res.success?'alert-success':'alert-error'}">${res.message}</div>`;
if(res.success){e.target.reset();loadMembers();loadStats();}setTimeout(()=>document.getElementById('memberAlert').innerHTML='',3000);}
async function borrowBook(e){e.preventDefault();const data={book_id:document.getElementById('borrowBookId').value,
member_id:document.getElementById('borrowMember').value,days:document.getElementById('borrowDays').value};
const r=await fetch('/api/borrow',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)});
const res=await r.json();document.getElementById('borrowAlert').innerHTML=
`<div class="alert ${res.success?'alert-success':'alert-error'}">${res.message}</div>`;
if(res.success){e.target.reset();loadBooks();loadStats();}setTimeout(()=>document.getElementById('borrowAlert').innerHTML='',3000);}
async function returnBook(e){e.preventDefault();const data={transaction_id:document.getElementById('returnTransaction').value};
const r=await fetch('/api/return',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)});
const res=await r.json();document.getElementById('returnAlert').innerHTML=
`<div class="alert ${res.success?'alert-success':'alert-error'}">${res.message}</div>`;
if(res.success){e.target.reset();loadBooks();loadStats();}setTimeout(()=>document.getElementById('returnAlert').innerHTML='',3000);}
window.onload=()=>{loadStats();loadBooks();loadMembers();};
</script></body></html>'''

def get_db():
    conn = sqlite3.connect('library.db')
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS books (
        book_id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, author TEXT NOT NULL,
        isbn TEXT UNIQUE NOT NULL, publication_year INTEGER, category TEXT,
        total_copies INTEGER DEFAULT 1, available_copies INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
    c.execute("""CREATE TABLE IF NOT EXISTS members (
        member_id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, email TEXT UNIQUE NOT NULL,
        phone TEXT, address TEXT, membership_date DATE DEFAULT CURRENT_DATE, status TEXT DEFAULT 'active')""")
    c.execute("""CREATE TABLE IF NOT EXISTS transactions (
        transaction_id INTEGER PRIMARY KEY AUTOINCREMENT, book_id INTEGER NOT NULL, member_id INTEGER NOT NULL,
        borrow_date DATE NOT NULL, due_date DATE NOT NULL, return_date DATE, fine_amount REAL DEFAULT 0,
        status TEXT DEFAULT 'borrowed', FOREIGN KEY (book_id) REFERENCES books(book_id),
        FOREIGN KEY (member_id) REFERENCES members(member_id))""")
    conn.commit()
    conn.close()

@app.route('/')
def index():
    return render_template_string(HTML)

@app.route('/api/stats')
def get_stats():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT COUNT(*), SUM(total_copies) FROM books")
    r = c.fetchone()
    stats = {'total_book_titles': r[0] or 0, 'total_book_copies': r[1] or 0}
    c.execute("SELECT COUNT(*) FROM members WHERE status='active'")
    stats['active_members'] = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM transactions WHERE status='borrowed'")
    stats['borrowed_books'] = c.fetchone()[0]
    today = datetime.now().date()
    c.execute("SELECT COUNT(*) FROM transactions WHERE status='borrowed' AND due_date<?", (today,))
    stats['overdue_books'] = c.fetchone()[0]
    conn.close()
    return jsonify(stats)

@app.route('/api/books')
def get_books():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM books")
    books = c.fetchall()
    conn.close()
    return jsonify(books)

@app.route('/api/books', methods=['POST'])
def add_book():
    data = request.json
    conn = get_db()
    c = conn.cursor()
    try:
        c.execute("""INSERT INTO books (title, author, isbn, publication_year, category, total_copies, available_copies)
            VALUES (?, ?, ?, ?, ?, ?, ?)""", (data['title'], data['author'], data['isbn'], 
            data['year'], data['category'], data['copies'], data['copies']))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Book added successfully!'})
    except:
        conn.close()
        return jsonify({'success': False, 'message': 'Error: ISBN already exists!'})

@app.route('/api/members')
def get_members():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM members")
    members = c.fetchall()
    conn.close()
    return jsonify(members)

@app.route('/api/members', methods=['POST'])
def add_member():
    data = request.json
    conn = get_db()
    c = conn.cursor()
    try:
        c.execute("INSERT INTO members (name, email, phone, address) VALUES (?, ?, ?, ?)",
            (data['name'], data['email'], data['phone'], data['address']))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Member added successfully!'})
    except:
        conn.close()
        return jsonify({'success': False, 'message': 'Error: Email already exists!'})

@app.route('/api/borrow', methods=['POST'])
def borrow_book():
    data = request.json
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT available_copies FROM books WHERE book_id=?", (data['book_id'],))
    r = c.fetchone()
    if not r or r[0] <= 0:
        conn.close()
        return jsonify({'success': False, 'message': 'Book not available!'})
    borrow_date = datetime.now().date()
    due_date = borrow_date + timedelta(days=int(data['days']))
    c.execute("INSERT INTO transactions (book_id, member_id, borrow_date, due_date) VALUES (?, ?, ?, ?)",
        (data['book_id'], data['member_id'], borrow_date, due_date))
    c.execute("UPDATE books SET available_copies=available_copies-1 WHERE book_id=?", (data['book_id'],))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'message': f'Book borrowed! Due: {due_date}'})

@app.route('/api/return', methods=['POST'])
def return_book():
    data = request.json
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT book_id, due_date, status FROM transactions WHERE transaction_id=?", (data['transaction_id'],))
    r = c.fetchone()
    if not r:
        conn.close()
        return jsonify({'success': False, 'message': 'Transaction not found!'})
    if r[2] == 'returned':
        conn.close()
        return jsonify({'success': False, 'message': 'Book already returned!'})
    return_date = datetime.now().date()
    due_date_obj = datetime.strptime(r[1], '%Y-%m-%d').date()
    days_overdue = (return_date - due_date_obj).days
    fine = max(0, days_overdue * 5)
    c.execute("UPDATE transactions SET return_date=?, fine_amount=?, status='returned' WHERE transaction_id=?",
        (return_date, fine, data['transaction_id']))
    c.execute("UPDATE books SET available_copies=available_copies+1 WHERE book_id=?", (r[0],))
    conn.commit()
    conn.close()
    msg = f'Book returned! Fine: ₹{fine}' if fine > 0 else 'Book returned successfully!'
    return jsonify({'success': True, 'message': msg})

if __name__ == '__main__':
    init_db()
    print("🚀 Server starting at http://localhost:5000")
    app.run(debug=True)