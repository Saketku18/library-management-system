# 📚 Library Management System

A web-based **Library Management System** built using **Python Flask** and **SQLite**.  
This system allows you to manage books, members, borrowing, returns, and fines through a user-friendly web interface.

---

## 🚀 Features

- Add, view, and manage books
- Add and manage members
- Borrow and return books
- Automatic fine calculation (₹5 per overdue day)
- Real-time dashboard statistics:
  - Total books
  - Total members
  - Borrowed books
  - Overdue books
- SQLite database for storage
- REST-style API architecture

---

## 🛠 Tech Stack

- **Backend:** Python (Flask)
- **Database:** SQLite
- **Frontend:** HTML, CSS, JavaScript
- **Tools:** Git, GitHub

---

## ⚙️ Setup Instructions

### 1️⃣ Clone the Repository
```bash
git clone https://github.com/Saketku18/library-management-system.git
cd library-management-system
```

---

### 2️⃣ Install Dependencies
Make sure Python is installed.

Install Flask:

```bash
pip install flask
```

---

### 3️⃣ Run the Application

```bash
python app.py
```

---

### 4️⃣ Open in Browser

Visit:

```
http://localhost:5000
```

---

## 📂 Project Structure

```
library-management-system/
│
├── app.py         # Flask application (Backend + Frontend)
├── .gitignore     # Files ignored by Git
└── README.md      # Documentation
```

---

## 🗃 Database

The database file `library.db` is automatically created when the application runs.

Tables:
- `books`
- `members`
- `transactions`

⚠️ Database file is ignored in Git to protect user data.

---

## 🔐 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/books | Get all books |
| POST | /api/books | Add book |
| GET | /api/members | Get members |
| POST | /api/members | Add member |
| POST | /api/borrow | Borrow book |
| POST | /api/return | Return book |
| GET | /api/stats | Dashboard stats |

---

## ✅ Example API Request (Add Member)

PowerShell Command:
```powershell
Invoke-RestMethod -Uri "http://localhost:5000/api/members" `
-Method POST `
-Headers @{ "Content-Type" = "application/json" } `
-Body '{ "name": "Neha", "email": "neha@gmail.com", "phone": "9876500000", "address": "Delhi" }'
```

---

## 📄 License

This project is for educational use.

---

## 👨‍💻 Author

**Saket Kumar**  
GitHub: https://github.com/Saketku18

---

## ⭐ Support

If you find this project useful, give it a ⭐ on GitHub!
