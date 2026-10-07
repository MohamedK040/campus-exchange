# PA1414 Software Engineering Project HT26

## Project Description

**Project Name:** Campus Exchange

**Customer Name:** Henry Edison

**Student Full Name:** Mohamed Kdimate

## Project Aim and Objectives

Campus Exchange is a web application that makes it easy for students to lend and
borrow things from each other. Students often own items they only need
occasionally — textbooks, calculators, tools, games, sports equipment, kitchen
equipment — while other students need exactly those things for a short period.
Instead of everyone buying their own, Campus Exchange lets students share.

Objectives:

- Let students offer items they are willing to lend to other students.
- Let students browse and search for items offered by others.
- Let students request to borrow an item, which the owner can accept or reject.
- Keep track of who currently holds an item and when it is due back.
- Give students an overview of what they are currently borrowing and lending.
- Build trust between users through reviews and ratings.

## User Personas

| Name | Characteristics | Needs and Expectations | How will they use the system? |
|------|-----------------|------------------------|-------------------------------|
| Anna, 22 (the Lender) | BTH student, owns tools and kitchen equipment that mostly sit unused. Comfortable with everyday apps. | Wants to lend out items without hassle and keep track of who has what, so nothing gets lost. | Lists her items, reviews incoming borrow requests, and accepts or rejects them. Marks items as returned. |
| Björn, 20 (the Borrower) | New student on a tight budget. Basic technical skills. | Needs course literature and a calculator for a short period without buying them. Wants to quickly find something available nearby. | Browses and searches for items, sends borrow requests, and sees what he is currently borrowing and when to return it. |
| Cecilia, 24 (the Occasional User) | BTH student who both lends and borrows now and then. Average technical skills. | Wants the exchange to be simple and to feel safe lending to and borrowing from people she can trust. | Occasionally lists an item or borrows one, and checks other users' reviews before lending. |

## Software Requirements

### Functional Requirements

- Users can register an account using their BTH email address.
- Registration is verified with a numeric code sent to the BTH email; only BTH email addresses are accepted.
- Users can log in and log out.
- Users can list an item they want to lend, with an image, description, category, and loan period (start and end date).
- Users can browse and search for available items.
- Users can send a request to borrow an available item.
- The item owner can accept or reject a borrow request.
- The owner sets the loan period and can extend it.
- The owner can recall (ask back) an item.
- When an item is lent out, further requests for it are automatically rejected.
- The system keeps track of who currently holds an item and its expected return date.
- Users can see the items they are currently borrowing and lending.
- Users can confirm, with a confirmation button, that an item has been returned.
- The owner can mark an item as a giveaway if they no longer want it back.
- The system notifies users on the website about new requests and overdue items, and sends reminders.
- Users can leave reviews and ratings for each other, so others can see how trustworthy a user is.

### Non-Functional Requirements

- The application is web-based and usable from an ordinary web browser.
- All data is stored persistently in a database.
- The system should support around 5000 users.
- Only BTH students (verified school email) can register and use the system.
- User data is handled securely (for example, passwords are never stored in plain text).
- The interface should be simple and easy to use.

## How to Install and Run

### Requirements

- Python 3.9 or newer
- A Gmail account with an App Password (used to send password-reset codes)

### Steps

1. Clone the repository:

```
   git clone https://github.com/dipt-pa1414-ht26/pa1414-caex-hed-mokd23.git
   cd pa1414-caex-hed-mokd23
```

2. Create and activate a virtual environment:

```
   python -m venv .venv
   source .venv/bin/activate      # macOS / Linux
   .venv\Scripts\activate         # Windows
```

3. Install the dependencies:

```
   pip install -r requirements.txt
```

4. Create a file named `.env` in the project root with your Gmail credentials (used to email password-reset codes):

```
   MAIL_USERNAME=your-gmail@gmail.com
   MAIL_PASSWORD=your-16-character-app-password
```

5. Start the application:

```
   python app.py
```

6. Open http://127.0.0.1:5000 in your browser.

The database (`campus_exchange.db`) is created automatically the first time you run the app, so there is no separate setup step.

## Your Backlog

Your backlog lives in two places, working together:

### 1. GitHub Issues (the content)

For every user story, feature, and task, create a GitHub Issue with a clear title and description. Use the issue template provided in this repository (see `.github/ISSUE_TEMPLATE/`).

Write them in this order:
1. All **user stories** first (format: *"As [a user], I want [action] so that [goal]"*)
2. Then all **features**
3. Then all **tasks**

### 2. Project Board (the backlog itself)

Add every Issue to a Project board. The board is your backlog, not the issue text.

Your repository does not come with a board already set up — see **[PROJECT_BOARD.md](PROJECT_BOARD.md)** for step-by-step instructions on creating your board and setting up the required fields (Priority, Estimated Effort, Sprint). 

You'll need a working board by the end of Sprint 1, as Status Report 3 requires it.

---

## Development

From Week 38 onward:
- Set up your development environment and start development.
- You're free to organise your code however works best for you — for example, using `src/` and `docs/` folders, or any other structure. There's no required folder layout; 
- At the end of each sprint, your work will be demonstrated to the customer at that sprint's Demo
- Keep this README as the one place that always explains how to install and run your project.


Your repository must remain **Private** for the entire course. This protects your customer's requirements and your own work.

---

## Documenting Your Project

Once Sprint 2 begins, add a **User Manual** section to this README, covering:
- **Installing** — what's needed to set up your project locally (dependencies, environment, etc.)
- **Running** — how to start/execute the application