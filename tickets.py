
import secrets
import string
import psycopg2

from db import get_connection

ALPHABET = string.ascii_uppercase + string.digits
ID_LENGTH = 12
MAX_ATTEMPTS = 5


# Generate a random ticket ID
def generate_ticket_id():
    return ''.join(
        secrets.choice(ALPHABET)
        for _ in range(ID_LENGTH)
    )


# Create a new ticket
def create_ticket(employee_email, priority, equipment, description):

    # Validate inputs
    if not employee_email or not employee_email.strip():
        raise ValueError("Employee email is required.")

    if not priority or not priority.strip():
        raise ValueError("Priority is required.")

    if not equipment or not equipment.strip():
        raise ValueError("Equipment is required.")

    if not description or not description.strip():
        raise ValueError("Description is required.")

    # Normalize inputs
    employee_email = employee_email.strip().lower()
    priority = priority.strip()
    equipment = equipment.strip()
    description = description.strip()

    conn = get_connection()

    try:
        for attempt in range(MAX_ATTEMPTS):

            ticket_id = generate_ticket_id()

            try:
                cur = conn.cursor()

                cur.execute("""
                    INSERT INTO ds_01 (
                        ticket_id,
                        employee_email,
                        priority,
                        equipment,
                        description
                    )
                    VALUES (%s, %s, %s, %s, %s)
                """, (
                    ticket_id,
                    employee_email,
                    priority,
                    equipment,
                    description
                ))

                conn.commit()
                cur.close()

                return ticket_id

            except psycopg2.errors.UniqueViolation:
                conn.rollback()
                cur.close()
                continue

        raise RuntimeError(
            "Unable to generate a unique ticket ID. Please try again later."
        )

    finally:
        conn.close()


# Look up ticket status
def lookup_status(employee_email, ticket_id):

    # Validate inputs
    if not employee_email or not employee_email.strip():
        raise ValueError("Employee email is required.")

    if not ticket_id or not ticket_id.strip():
        raise ValueError("Ticket ID is required.")

    # Normalize inputs
    employee_email = employee_email.strip().lower()
    ticket_id = ticket_id.strip().upper()

    conn = get_connection()

    try:
        cur = conn.cursor()

        cur.execute("""
            SELECT ticket_id, status
            FROM ds_01
            WHERE employee_email = %s
            AND ticket_id = %s
        """, (employee_email, ticket_id))

        row = cur.fetchone()

        cur.close()

        if row:
            return {
                "ticket_id": row[0],
                "status": row[1]
            }

        raise ValueError("Incorrect email or ticket ID.")

    finally:
        conn.close()
