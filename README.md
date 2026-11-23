# ceres-ticket-system

# Ceres Solutions: IT Ticket Support System

A web application that lets employees submit IT support tickets and lets technicians manage them through a queue dashboard.

Developed for CEN4010, Fall 2026, under Professor Akbar.

## Team

- **Bruno Kaufmann**: Frontend
- **Sebastian Uribe**: Backend
- **Luke Abreu**: Project Management, QA & Integration

## Features

- Employee ticket submission with a unique, collision-free ticket ID
- Ticket status lookup by email and ticket ID
- Technician login with hashed passwords and timed sessions
- Ticket queue dashboard with filtering, status updates, and internal notes
- Ticket detail view
- Hardware reporting by equipment type

## Tech Stack

- **View:** HTML and CSS
- **Controller:** Python with Flask
- **Model:** PostgreSQL
- **Password hashing:** Werkzeug
- **Environment:** Docker

## Project Structure

```
ticket-system/
├── app.py
├── config.py
├── db.py
├── models/          # Data access for DS-01 to DS-04
├── routes/          # Controller logic, one file per module
├── utils/           # ID generator (ALG-01) and rate limiting
├── templates/       # HTML views
├── static/          # CSS and optional JS
├── schema.sql       # Table definitions
├── requirements.txt
├── Dockerfile
└── docker-compose.yml


## Setup

### Prerequisites

- [Git](https://git-scm.com/)
- [Docker](https://www.docker.com/) with at least 6GB of RAM allocated

### 1. Clone the repository

bash
git clone https://github.com/<your-username>/ceres-ticket-system.git
cd ceres-ticket-system


### 2. Create the environment file

Create a `.env` file in the project root. Do not commit this file.


POSTGRES_USER=<username>
POSTGRES_PASSWORD=<password>
POSTGRES_DB=<database_name>
SECRET_KEY=<random_string>


### 3. Start the application

bash
docker-compose up --build


### 4. Create the database tables

With the containers running, apply the schema:

bash
docker-compose exec db psql -U <username> -d <database_name> -f /schema.sql


### 5. Open the app

Go to [http://localhost:5000](http://localhost:5000) in your browser.

## Technician Accounts

Technician accounts are added manually to the Login Table (DS-02). Passwords must be hashed with Werkzeug before they are stored. Never insert plain-text passwords.

## Running Tests

Test cases are listed in Section 5 of the final deliverable. Run them manually in the browser and record results in Section 6.

## Team Workflow

- Do not push directly to `main`.
- Create a branch for each feature, for example `feature/submission-form`.
- Open a pull request and get one teammate's review before merging.
- Pull `main` before starting a new session.

## Known Limitations

- Automated email alerts and live chat are planned but not implemented.
- Only technicians can access the dashboard. Read-only roles are planned.
- Requires Docker with at least 6GB of RAM allocated.