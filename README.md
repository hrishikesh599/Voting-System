# Voting System

A modern web-based voting management system built using **Flask**, **SQLite**, **HTML**, **CSS**, and **JavaScript**. The application allows administrators to create elections, manage candidates, collect votes, monitor live results, and export professional PDF reports.

---

## Features

### Admin Features

* Create and manage multiple classes/elections
* Add candidates to each class
* Set maximum voter limits
* Select the active class for voting
* Add new candidates after election creation
* Reset votes for a specific class
* Export election results

### Voting Features

* User-friendly voting interface
* One-click vote submission
* Real-time vote counting
* Automatic voter limit enforcement
* Live election monitoring

### Reporting Features

* Generate professional PDF reports
* Candidate-wise vote count
* Total votes cast summary
* Maximum voter capacity tracking
* Remaining voter calculation
* Export results for all classes

### User Interface

* Modern glassmorphism-inspired design
* Animated gradient backgrounds
* Responsive mobile-friendly layout
* Interactive buttons and hover effects
* Toast notifications for system feedback

---

## Technologies Used

* Python
* Flask
* Flask-SQLAlchemy
* SQLite
* HTML5
* CSS3
* JavaScript
* ReportLab
* Gunicorn

---

## Project Structure

```text
Voting-System/
│
├── app.py
├── requirements.txt
├── README.md
│
├── templates/
│   ├── dashboard.html
│   ├── admin.html
│   └── class_vote.html
│
├── static/
│   ├── style.css
│   └── assets/
│
├── data/
│   └── voting.db
│
└── exports/
```

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/hrishikesh599/voting-system.git
cd voting-system
```

### 2. Create a Virtual Environment

```bash
python -m venv venv
```

Activate it:

**Windows**

```bash
venv\Scripts\activate
```

**Linux / macOS**

```bash
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the Application

```bash
python app.py
```

The application will be available at:

```text
http://127.0.0.1:5000
```

---


## 👨‍💻 Author

**HRISHIKESH T HEMANTH**

Designed and developed as a modern digital voting solution for educational institutions.
