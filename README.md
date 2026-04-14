# Graphical Authentication Prototype

A multifactor authentication system built with Flask and SQLite for my final year dissertation.

##  How It Works

Authentication is split into three stages:

1. **Graphical Password** — the user selects 4 images in a specific order from a randomised grid
2. **Recall Challenge** — the user is asked to recall specific images from their registered sequence (e.g. reverse order, 3rd image)
3. **OTP Verification** — a one-time passcode is generated and must be entered to complete login

## 🚀 Live Demo

[https://eshapatel11.pythonanywhere.com](https://eshapatel11.pythonanywhere.com)

##  Setup (Local)

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python init_db.py
python app.py
```

##  Built With

- Python / Flask
- SQLite
- bcrypt
