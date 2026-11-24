import os
import logging

import psycopg2
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_wtf.csrf import CSRFProtect

from tickets import (
    create_ticket,
    lookup_status,
    get_all_tickets,
    get_ticket_by_id,
    update_ticket,
    get_hardware_report,
)
from auth import login_technician


load_dotenv()

app = Flask(__name__)

# Load secret key for session signing and CSRF protection
secret_key = os.getenv("SECRET_KEY")

if not secret_key:
    raise RuntimeError("SECRET_KEY must be configured in .env")

app.config["SECRET_KEY"] = secret_key
app.config["PERMANENT_SESSION_LIFETIME"] = 1800

# Enable global CSRF protection across all POST forms
CSRFProtect(app)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Employee ticket submission route (FR-01, FR-02)
@app.route("/submit-ticket", methods=["GET", "POST"])
def submit_ticket():
    form_data = {
        "employee_email": "",
        "priority": "",
        "equipment": "",
        "description": ""
    }

    if request.method == "POST":
        form_data = {
            "employee_email": request.form.get("employee_email", "").strip(),
            "priority": request.form.get("priority", "").strip(),
            "equipment": request.form.get("equipment", "").strip(),
            "description": request.form.get("description", "").strip()
        }

        try:
            ticket_id = create_ticket(
                employee_email=form_data["employee_email"],
                priority=form_data["priority"],
                equipment=form_data["equipment"],
                description=form_data["description"]
            )

            session["ticket_id"] = ticket_id

            return redirect(url_for("ticket_confirmation"))

        except ValueError as error:
            flash(str(error), "error")

        except (psycopg2.Error, RuntimeError):
            logger.exception("Ticket submission failed")
            flash(
                "Something went wrong. Please try again later.",
                "error"
            )

    return render_template(
        "submit_ticket.html",
        form_data=form_data
    )


# Ticket submission confirmation screen
@app.route("/ticket-confirmation", methods=["GET"])
def ticket_confirmation():
    ticket_id = session.pop("ticket_id", None)

    if not ticket_id:
        return redirect(url_for("submit_ticket"))

    return render_template(
        "ticket_confirmation.html",
        ticket_id=ticket_id
    )


# Employee ticket status lookup form (FR-03)
@app.route("/lookup-status", methods=["GET", "POST"])
def lookup_ticket_status():
    form_data = {
        "employee_email": "",
        "ticket_id": ""
    }

    if request.method == "POST":
        form_data = {
            "employee_email": request.form.get("employee_email", "").strip(),
            "ticket_id": request.form.get("ticket_id", "").strip()
        }

        session["lookup_email"] = form_data["employee_email"]
        session["lookup_ticket_id"] = form_data["ticket_id"]

        return redirect(url_for("status_result"))

    return render_template(
        "lookup_status.html",
        form_data=form_data
    )


# Employee ticket status lookup result screen
@app.route("/status-result", methods=["GET"])
def status_result():
    employee_email = session.pop("lookup_email", None)
    ticket_id = session.pop("lookup_ticket_id", None)

    if not employee_email or not ticket_id:
        return redirect(url_for("lookup_ticket_status"))

    try:
        result = lookup_status(employee_email, ticket_id)

    except ValueError as error:
        flash(str(error), "error")
        return redirect(url_for("lookup_ticket_status"))

    except psycopg2.Error:
        logger.exception("Ticket status lookup failed")
        flash("Something went wrong. Please try again later.", "error")
        return redirect(url_for("lookup_ticket_status"))

    return render_template(
        "status_result.html",
        ticket_id=result["ticket_id"],
        status=result["status"]
    )


# Technician authentication route (FR-04)
@app.route("/technician-login", methods=["GET", "POST"])
def technician_login():
    form_data = {"technician_email": ""}

    if request.method == "POST":
        form_data["technician_email"] = request.form.get(
            "technician_email", ""
        ).strip()

        password = request.form.get("password", "")

        try:
            technician = login_technician(
                technician_email=form_data["technician_email"],
                password=password
            )

            # Reset session before storing authenticated technician email
            session.clear()
            session.permanent = True

            session["technician_email"] = technician["technician_email"]

            return redirect(url_for("dashboard"))

        except ValueError:
            flash("Invalid email or password.", "error")

        except psycopg2.Error:
            logger.exception("Technician login failed")
            flash(
                "Something went wrong. Please try again later.",
                "error"
            )

    return render_template(
        "technician_login.html",
        form_data=form_data
    )


# Technician ticket queue dashboard with status and priority filtering (FR-05)
@app.route("/dashboard", methods=["GET"])
def dashboard():
    technician_email = session.get("technician_email")

    # Require authenticated technician session
    if not technician_email:
        return redirect(url_for("technician_login"))

    status_filter = request.args.get("status", "").strip()
    priority_filter = request.args.get("priority", "").strip()

    try:
        tickets = get_all_tickets(
            status_filter=status_filter,
            priority_filter=priority_filter
        )
    except psycopg2.Error:
        logger.exception("Failed to load dashboard tickets")
        flash("Unable to load tickets right now.", "error")
        tickets = []

    return render_template(
        "dashboard.html",
        technician_email=technician_email,
        tickets=tickets,
        status_filter=status_filter,
        priority_filter=priority_filter
    )


# Individual ticket detail view and status/internal note update route (FR-06, FR-11)
@app.route("/ticket/<ticket_id>", methods=["GET", "POST"])
def ticket_detail(ticket_id):
    technician_email = session.get("technician_email")

    # Require authenticated technician session
    if not technician_email:
        return redirect(url_for("technician_login"))

    # Handle technician status and internal note updates
    if request.method == "POST":
        new_status = request.form.get("status", "").strip()
        internal_note = request.form.get("internal_note", "")

        try:
            update_ticket(ticket_id, new_status, internal_note)
            flash("Ticket updated successfully.", "success")
            return redirect(url_for("ticket_detail", ticket_id=ticket_id))

        except ValueError as error:
            flash(str(error), "error")

        except psycopg2.Error:
            logger.exception("Failed to update ticket")
            flash("Something went wrong while updating the ticket.", "error")

    # Fetch current ticket details for display
    try:
        ticket = get_ticket_by_id(ticket_id)
    except psycopg2.Error:
        logger.exception("Failed to load ticket details")
        flash("Unable to load ticket details.", "error")
        return redirect(url_for("dashboard"))

    if not ticket:
        flash("Ticket not found.", "error")
        return redirect(url_for("dashboard"))

    return render_template(
        "ticket_detail.html",
        technician_email=technician_email,
        ticket=ticket
    )


# Hardware equipment summary report route (FR-07 to FR-09)
@app.route("/hardware-report", methods=["GET"])
def hardware_report():
    technician_email = session.get("technician_email")

    # Require authenticated technician session
    if not technician_email:
        return redirect(url_for("technician_login"))

    try:
        report_rows = get_hardware_report()
    except psycopg2.Error:
        logger.exception("Failed to generate hardware report")
        flash("Unable to generate hardware report.", "error")
        report_rows = []

    return render_template(
        "hardware_report.html",
        technician_email=technician_email,
        report_rows=report_rows
    )


# Technician logout route
@app.route("/logout", methods=["POST"])
def logout():
    session.clear()

    return redirect(url_for("technician_login"))


if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=os.getenv("APP_ENV") == "development"
    )
