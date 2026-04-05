<div align="center">

# 📚 Book Inventory System

### A Digital Book Inventory Management System built with Python & Django

[![Python](https://img.shields.io/badge/Python-100%25-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-Web_Framework-092E20?style=flat-square&logo=django&logoColor=white)](https://www.djangoproject.com/)
[![SQLite](https://img.shields.io/badge/Database-SQLite-003B57?style=flat-square&logo=sqlite&logoColor=white)](https://www.sqlite.org/)
[![License](https://img.shields.io/badge/License-MIT-22c55e?style=flat-square)](LICENSE)

</div>

---

## 📖 About

**Book Inventory System** is a group university project that implements a fully functional digital book inventory management application using **Python** and **Django**. It supports complete CRUD operations, author-based filtering, UML design diagrams, and URL-based testing — all backed by a lightweight SQLite database.

---

## ✨ Features

- 📋 **Full CRUD** — Create, Read, Update, and Delete book records
- 🔍 **Filter by Author** — Quickly search and filter the inventory by author name
- 🗂️ **Student & Inventory Apps** — Modular Django app structure separating concerns
- 🧪 **URL-Based Testing** — Endpoint testing built into the project workflow
- 📐 **UML Diagrams** — Includes design documentation with UML class/sequence diagrams
- 🗄️ **SQLite Database** — Zero-config local database included (`db.sqlite3`)

---

## 🏗️ Tech Stack
Language       Python
Framework      Django
Database       SQLite3
Architecture   MVT (Model-View-Template)
Testing        Django URL-based testing

---

## 📁 Project Structure
book-inventory-system/
├── helloworld/          # Initial Django app / project config
├── inventory/           # Core inventory app (models, views, URLs, templates)
├── student/             # Student-related app
├── manage.py            # Django management CLI
├── db.sqlite3           # SQLite database
└── .gitignore

---

## ⚙️ Getting Started

### Prerequisites

- Python `>=3.8`
- pip

### 1. Clone the Repository
```bash
git clone https://github.com/kaiffarooqui970/book-inventory-system.git
cd book-inventory-system
```

### 2. Create a Virtual Environment
```bash
python -m venv venv
source venv/bin/activate        # macOS/Linux
venv\Scripts\activate           # Windows
```

### 3. Install Dependencies
```bash
pip install django
```

### 4. Apply Migrations
```bash
python manage.py migrate
```

### 5. Run the Development Server
```bash
python manage.py runserver
```

Then open your browser at **http://127.0.0.1:8000**

---

## 🧪 Testing

Django's built-in test runner can be used to run URL-based tests:
```bash
python manage.py test
```

---

## 🗺️ Key URLs

| Route | Description |
|---|---|
| `/` | Home / landing page |
| `/inventory/` | View all books |
| `/inventory/add/` | Add a new book |
| `/inventory/<id>/edit/` | Edit a book record |
| `/inventory/<id>/delete/` | Delete a book record |
| `/inventory/?author=<name>` | Filter books by author |

---

## 📐 UML Diagrams

UML class and sequence diagrams are included as part of the project documentation to illustrate the system design and data flow between components.

---

## 👥 Contributors

This is a **group project** developed collaboratively.

- [kaiffarooqui970](https://github.com/kaiffarooqui970)

---

## 📄 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

<div align="center">

Built with ❤️ using Python & Django

⭐ Star this repo if you found it useful!

</div>
