# Campus Exchange

A web app where BTH students lend and borrow everyday items – textbooks,
calculators, tools, games – instead of everyone buying their own.

Built as my individual project in the Software Engineering Project course
(PA1414) at Blekinge Institute of Technology, based on requirements from a
customer and delivered in sprints with demos.

## Features
- Sign up with a BTH email, verified with a code sent by email
- List items with photo, description, category and loan period
- Browse and search available items
- Request to borrow – the owner accepts or rejects
- One active loan per item; other requests are rejected automatically
- Extend loans, recall items, mark them as returned or as giveaways
- "My loans" overview of everything you borrow and lend
- Notifications for new requests and overdue items
- Two-way reviews and ratings to build trust between users
- Password reset via emailed code

## Tech stack
Python · Flask · Flask-SQLAlchemy (SQLite) · Flask-Login · Flask-Mail · HTML/CSS

## Getting started
Requires Python 3.9+ and a Gmail account with an App Password.

```bash
git clone https://github.com/MohamedK040/campus-exchange.git
cd campus-exchange
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Create a `.env` file in the project root:
```
SECRET_KEY=any-long-random-string
MAIL_USERNAME=your-gmail@gmail.com
MAIL_PASSWORD=your-16-character-app-password
```

Run `python app.py` and open http://127.0.0.1:5001.
The database is created automatically on first run.

## License
MIT
