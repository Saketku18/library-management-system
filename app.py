from flask import Flask, render_template_string, request, jsonify
import sqlite3
from datetime import datetime, date, timedelta

app = Flask(__name__)

# ===================== DB HELPERS =====================

DB_NAME = "library.db"

def get_db():
    return sqlite3.connect(DB_NAME)

def init_db():
    conn = get_db()
    c = conn.cursor()

    # 1. Branch
    c.execute("""
        CREATE TABLE IF NOT EXISTS branch (
            branch_id INTEGER PRIMARY KEY AUTOINCREMENT,
            manager_id INTEGER,
            branch_address TEXT,
            contact_no TEXT
        )
    """)

    # 2. Employee
    c.execute("""
        CREATE TABLE IF NOT EXISTS employee (
            emp_id INTEGER PRIMARY KEY AUTOINCREMENT,
            emp_name TEXT,
            position TEXT,
            salary REAL,
            branch_id INTEGER
        )
    """)

    # 3. Books
    c.execute("""
        CREATE TABLE IF NOT EXISTS books (
            isbn TEXT PRIMARY KEY,
            book_title TEXT,
            category TEXT,
            rental_price REAL,
            status TEXT DEFAULT 'yes',
            author TEXT,
            publisher TEXT
        )
    """)

    # 4. Members
    c.execute("""
        CREATE TABLE IF NOT EXISTS members (
            member_id INTEGER PRIMARY KEY AUTOINCREMENT,
            member_name TEXT,
            member_address TEXT,
            reg_date DATE DEFAULT CURRENT_DATE
        )
    """)

    # 5. Issued_Status
    c.execute("""
        CREATE TABLE IF NOT EXISTS issued_status (
            issued_id INTEGER PRIMARY KEY AUTOINCREMENT,
            issued_member_id INTEGER,
            issued_book_name TEXT,
            issued_date DATE,
            issued_book_isbn TEXT,
            issued_emp_id INTEGER
        )
    """)

    # 6. Return_Status
    c.execute("""
        CREATE TABLE IF NOT EXISTS return_status (
            return_id INTEGER PRIMARY KEY AUTOINCREMENT,
            issued_id INTEGER,
            return_book_name TEXT,
            return_date DATE,
            return_book_isbn TEXT
        )
    """)

    conn.commit()
    conn.close()

# ===================== STATS API =====================

@app.route("/api/stats")
def api_stats():
    conn = get_db()
    c = conn.cursor()

    def count(table):
        return c.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]

    stats = {
        "branch":   count("branch"),
        "employee": count("employee"),
        "books":    count("books"),
        "members":  count("members"),
        "issued":   count("issued_status"),
        "returns":  count("return_status")
    }
    conn.close()
    return jsonify(stats)

# ===================== TABLE VIEW API =====================

@app.route("/api/table/<name>")
def api_table(name):
    conn = get_db()
    c = conn.cursor()

    mapping = {
        "branch":   "branch",
        "employee": "employee",
        "books":    "books",
        "members":  "members",
        "issued":   "issued_status",
        "returns":  "return_status"
    }

    table = mapping.get(name)
    if not table:
        conn.close()
        return jsonify([])

    c.execute(f"SELECT * FROM {table}")
    rows = c.fetchall()
    cols = [col[0] for col in c.description]
    conn.close()

    data = [dict(zip(cols, r)) for r in rows]
    return jsonify(data)

# ===================== ADD / ISSUE / RETURN APIs =====================

@app.route("/api/add/branch", methods=["POST"])
def api_add_branch():
    data = request.json
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        INSERT INTO branch (manager_id, branch_address, contact_no)
        VALUES (?, ?, ?)
    """, (data["manager_id"], data["branch_address"], data["contact_no"]))
    conn.commit()
    conn.close()
    return jsonify(success=True, message="Branch added")

@app.route("/api/add/employee", methods=["POST"])
def api_add_employee():
    data = request.json
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        INSERT INTO employee (emp_name, position, salary, branch_id)
        VALUES (?, ?, ?, ?)
    """, (data["emp_name"], data["position"], data["salary"], data["branch_id"]))
    conn.commit()
    conn.close()
    return jsonify(success=True, message="Employee added")

@app.route("/api/add/book", methods=["POST"])
def api_add_book():
    data = request.json
    conn = get_db()
    c = conn.cursor()
    try:
        c.execute("""
            INSERT INTO books (isbn, book_title, category, rental_price, status, author, publisher)
            VALUES (?, ?, ?, ?, 'yes', ?, ?)
        """, (
            data["isbn"],
            data["book_title"],
            data["category"],
            data["rental_price"],
            data["author"],
            data["publisher"]
        ))
        conn.commit()
        conn.close()
        return jsonify(success=True, message="Book added")
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify(success=False, message="ISBN already exists")

@app.route("/api/add/member", methods=["POST"])
def api_add_member():
    data = request.json
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        INSERT INTO members (member_name, member_address)
        VALUES (?, ?)
    """, (data["member_name"], data["member_address"]))
    conn.commit()
    conn.close()
    return jsonify(success=True, message="Member added")

@app.route("/api/add/issue", methods=["POST"])
def api_add_issue():
    data = request.json
    conn = get_db()
    c = conn.cursor()

    # 1. check availability
    row = c.execute("SELECT status, book_title FROM books WHERE isbn = ?", (data["issued_book_isbn"],)).fetchone()
    if not row:
        conn.close()
        return jsonify(success=False, message="Book not found")
    status, title = row
    if status != "yes":
        conn.close()
        return jsonify(success=False, message="Book not available")

    issued_date = date.today().isoformat()
    c.execute("""
        INSERT INTO issued_status
        (issued_member_id, issued_book_name, issued_date, issued_book_isbn, issued_emp_id)
        VALUES (?, ?, ?, ?, ?)
    """, (
        data["issued_member_id"],
        title,
        issued_date,
        data["issued_book_isbn"],
        data["issued_emp_id"]
    ))
    c.execute("UPDATE books SET status = 'no' WHERE isbn = ?", (data["issued_book_isbn"],))
    conn.commit()
    conn.close()
    return jsonify(success=True, message="Book issued")

@app.route("/api/add/return", methods=["POST"])
def api_add_return():
    data = request.json
    issued_id = data["issued_id"]

    conn = get_db()
    c = conn.cursor()

    row = c.execute("""
        SELECT issued_book_name, issued_book_isbn, issued_date
        FROM issued_status
        WHERE issued_id = ?
    """, (issued_id,)).fetchone()

    if not row:
        conn.close()
        return jsonify(success=False, message="Invalid Issued ID")

    book_name, isbn, issued_date_str = row
    return_date = date.today().isoformat()

    c.execute("""
        INSERT INTO return_status
        (issued_id, return_book_name, return_date, return_book_isbn)
        VALUES (?, ?, ?, ?)
    """, (issued_id, book_name, return_date, isbn))

    c.execute("UPDATE books SET status = 'yes' WHERE isbn = ?", (isbn,))
    conn.commit()
    conn.close()
    return jsonify(success=True, message="Book returned")

# ===================== UI =====================

HTML = """
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>LibraFlow - Library Management System</title>
  <style>
    *{box-sizing:border-box;margin:0;padding:0}
    body{font-family:Arial,Helvetica,sans-serif;background:linear-gradient(135deg,#667eea,#764ba2);min-height:100vh;padding:20px}
    .wrapper{max-width:1200px;margin:0 auto}
    header{background:#fff;padding:18px;border-radius:16px;text-align:center;font-size:26px;font-weight:bold;color:#667eea;margin-bottom:18px}
    .stats{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-bottom:18px}
    .stat-card{background:#fff;border-radius:12px;padding:12px;text-align:center;cursor:pointer;box-shadow:0 3px 8px rgba(0,0,0,.1);transition:.2s}
    .stat-card:hover{transform:translateY(-2px);box-shadow:0 6px 14px rgba(0,0,0,.15)}
    .stat-title{font-size:14px;color:#555}
    .stat-number{font-size:22px;font-weight:bold;color:#333;margin-top:4px}
    .layout{display:grid;grid-template-columns:220px 1fr;gap:14px}
    .sidebar{background:#fff;border-radius:12px;padding:12px;box-shadow:0 3px 8px rgba(0,0,0,.1)}
    .nav-btn{width:100%;padding:10px;margin:5px 0;border:none;border-radius:8px;background:#f1f1f1;font-weight:600;cursor:pointer;transition:.2s}
    .nav-btn:hover{background:#e0e0ff}
    .content{background:#fff;border-radius:12px;padding:18px;box-shadow:0 3px 8px rgba(0,0,0,.1)}
    .form-section{display:none}
    .form-section.active{display:block}
    h2{margin-bottom:10px}
    input{width:100%;padding:8px;margin:4px 0 8px 0;border-radius:6px;border:1px solid #ccc}
    .btn-primary{padding:8px 16px;background:#667eea;color:#fff;border:none;border-radius:8px;cursor:pointer;margin-top:4px}
    .btn-primary:hover{background:#5562d3}
    #tableView{margin-top:18px;overflow-x:auto}
    table{width:100%;border-collapse:collapse;margin-top:8px}
    th,td{padding:8px;border-bottom:1px solid #eee;text-align:left;font-size:14px}
    th{background:#f6f6f6}
  </style>
</head>
<body>
<div class="wrapper">
  <header>📚 LibraFlow - Library Management System</header>

  <div class="stats">
    <div class="stat-card" onclick="loadTable('branch')">
      <div class="stat-title">Branches</div>
      <div class="stat-number" id="stat-branch">0</div>
    </div>
    <div class="stat-card" onclick="loadTable('employee')">
      <div class="stat-title">Employees</div>
      <div class="stat-number" id="stat-employee">0</div>
    </div>
    <div class="stat-card" onclick="loadTable('books')">
      <div class="stat-title">Books</div>
      <div class="stat-number" id="stat-books">0</div>
    </div>
    <div class="stat-card" onclick="loadTable('members')">
      <div class="stat-title">Members</div>
      <div class="stat-number" id="stat-members">0</div>
    </div>
    <div class="stat-card" onclick="loadTable('issued')">
      <div class="stat-title">Issued Records</div>
      <div class="stat-number" id="stat-issued">0</div>
    </div>
    <div class="stat-card" onclick="loadTable('returns')">
      <div class="stat-title">Return Records</div>
      <div class="stat-number" id="stat-returns">0</div>
    </div>
  </div>

  <div class="layout">
    <div class="sidebar">
      <button class="nav-btn" onclick="showForm('form-branch')">➕ Add Branch</button>
      <button class="nav-btn" onclick="showForm('form-employee')">➕ Add Employee</button>
      <button class="nav-btn" onclick="showForm('form-book')">➕ Add Book</button>
      <button class="nav-btn" onclick="showForm('form-member')">➕ Add Member</button>
      <button class="nav-btn" onclick="showForm('form-issue')">📤 Issue Book</button>
      <button class="nav-btn" onclick="showForm('form-return')">📥 Return Book</button>
    </div>

    <div class="content">
      <!-- Forms -->
      <div id="form-branch" class="form-section active">
        <h2>Add Branch</h2>
        <input id="branch-manager" placeholder="Manager ID">
        <input id="branch-address" placeholder="Branch Address">
        <input id="branch-contact" placeholder="Contact No">
        <button class="btn-primary" onclick="addBranch()">Add Branch</button>
      </div>

      <div id="form-employee" class="form-section">
        <h2>Add Employee</h2>
        <input id="emp-name" placeholder="Employee Name">
        <input id="emp-position" placeholder="Position">
        <input id="emp-salary" placeholder="Salary">
        <input id="emp-branch" placeholder="Branch ID">
        <button class="btn-primary" onclick="addEmployee()">Add Employee</button>
      </div>

      <div id="form-book" class="form-section">
        <h2>Add Book</h2>
        <input id="book-isbn" placeholder="ISBN">
        <input id="book-title" placeholder="Book Title">
        <input id="book-category" placeholder="Category">
        <input id="book-rental" placeholder="Rental Price">
        <input id="book-author" placeholder="Author">
        <input id="book-publisher" placeholder="Publisher">
        <button class="btn-primary" onclick="addBook()">Add Book</button>
      </div>

      <div id="form-member" class="form-section">
        <h2>Add Member</h2>
        <input id="member-name" placeholder="Member Name">
        <input id="member-address" placeholder="Member Address">
        <button class="btn-primary" onclick="addMember()">Add Member</button>
      </div>

      <div id="form-issue" class="form-section">
        <h2>Issue Book</h2>
        <input id="issue-member" placeholder="Member ID">
        <input id="issue-isbn" placeholder="Book ISBN">
        <input id="issue-emp" placeholder="Employee ID">
        <button class="btn-primary" onclick="issueBook()">Issue Book</button>
      </div>

      <div id="form-return" class="form-section">
        <h2>Return Book</h2>
        <input id="return-issued" placeholder="Issued ID">
        <button class="btn-primary" onclick="returnBook()">Return Book</button>
      </div>

      <!-- Table view area -->
      <div id="tableView"></div>
    </div>
  </div>
</div>

<script>
async function loadStats(){
  const res = await fetch('/api/stats');
  const d = await res.json();
  document.getElementById('stat-branch').textContent   = d.branch   || 0;
  document.getElementById('stat-employee').textContent = d.employee || 0;
  document.getElementById('stat-books').textContent    = d.books    || 0;
  document.getElementById('stat-members').textContent  = d.members  || 0;
  document.getElementById('stat-issued').textContent   = d.issued   || 0;
  document.getElementById('stat-returns').textContent  = d.returns  || 0;
}

function showForm(id){
  document.querySelectorAll('.form-section').forEach(f => f.classList.remove('active'));
  document.getElementById(id).classList.add('active');
  document.getElementById('tableView').innerHTML = "";  // clear table when switching forms
}

async function loadTable(name){

  // ✅ HIDE ALL FORMS WHEN TABLE OPENS
  document.querySelectorAll('.form-section')
    .forEach(f => f.classList.remove('active'));

  const res = await fetch('/api/table/' + name);
  const data = await res.json();
  const container = document.getElementById('tableView');

  if(!data || data.length === 0){
    container.innerHTML = "<h3>No records found</h3>";
    return;
  }
  const cols = Object.keys(data[0]);
  let displayName = {
  branch: "Branches",
  employee: "Employees",
  books: "Books",
  members: "Members",
  issued: "Issued Records",
  returned: "Return Records"
};
let html = "<h2>" + (displayName[name] || name) + "</h2>";

  html += "<table><thead><tr>";

  cols.forEach(c => html += "<th>" + c + "</th>");
  html += "</tr></thead><tbody>";

  data.forEach(row => {
    html += "<tr>";
    cols.forEach(c => html += "<td>" + (row[c]===null?'':row[c]) + "</td>");
    html += "</tr>";
  });

  html += "</tbody></table>";
  container.innerHTML = html;
}

async function addBranch(){
  const payload = {
    manager_id: document.getElementById('branch-manager').value,
    branch_address: document.getElementById('branch-address').value,
    contact_no: document.getElementById('branch-contact').value
  };
  await fetch('/api/add/branch',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});
  loadStats();
}

async function addEmployee(){
  const payload = {
    emp_name: document.getElementById('emp-name').value,
    position: document.getElementById('emp-position').value,
    salary: document.getElementById('emp-salary').value,
    branch_id: document.getElementById('emp-branch').value
  };
  await fetch('/api/add/employee',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});
  loadStats();
}

async function addBook(){
  const payload = {
    isbn: document.getElementById('book-isbn').value,
    book_title: document.getElementById('book-title').value,
    category: document.getElementById('book-category').value,
    rental_price: document.getElementById('book-rental').value,
    author: document.getElementById('book-author').value,
    publisher: document.getElementById('book-publisher').value
  };
  const res = await fetch('/api/add/book',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});
  const out = await res.json();
  alert(out.message);
  loadStats();
}

async function addMember(){
  const payload = {
    member_name: document.getElementById('member-name').value,
    member_address: document.getElementById('member-address').value
  };
  await fetch('/api/add/member',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});
  loadStats();
}

async function issueBook(){
  const payload = {
    issued_member_id: document.getElementById('issue-member').value,
    issued_book_isbn: document.getElementById('issue-isbn').value,
    issued_emp_id: document.getElementById('issue-emp').value
  };
  const res = await fetch('/api/add/issue',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});
  const out = await res.json();
  alert(out.message);
  loadStats();
}

async function returnBook(){
  const payload = {
    issued_id: document.getElementById('return-issued').value
  };
  const res = await fetch('/api/add/return',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});
  const out = await res.json();
  alert(out.message);
  loadStats();
}

// initial load
loadStats();
</script>

</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(HTML)

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
