import os
import logging

import psycopg2
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_wtf.csrf import CSRFProtect

from tickets import create_ticket, lookup_status


load_dotenv()

app = Flask(__name__)

secret_key = os.getenv("SECRET_KEY")

if not secret_key:
    raise RuntimeError("SECRET_KEY must be configured in .env")

app.config["SECRET_KEY"] = secret_key
app.config["PERMANENT_SESSION_LIFETIME"] = 1800

CSRFProtect(app)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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


@app.route("/ticket-confirmation", methods=["GET"])
def ticket_confirmation():
    ticket_id = session.pop("ticket_id", None)

    if not ticket_id:
        return redirect(url_for("submit_ticket"))

    return render_template(
        "ticket_confirmation.html",
        ticket_id=ticket_id
    )


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

        try:
            # Validate by running the lookup once, then store only the inputs
            lookup_status(
                employee_email=form_data["employee_email"],
                ticket_id=form_data["ticket_id"]
            )

            session["lookup_email"] = form_data["employee_email"]
            session["lookup_ticket_id"] = form_data["ticket_id"]

            return redirect(url_for("status_result"))

        except ValueError as error:
            flash(str(error), "error")

        except psycopg2.Error:
            logger.exception("Ticket status lookup failed")
            flash(
                "Something went wrong. Please try again later.",
                "error"
            )

    return render_template(
        "lookup_status.html",
        form_data=form_data
    )


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


if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=os.getenv("APP_ENV") == "development"
    )