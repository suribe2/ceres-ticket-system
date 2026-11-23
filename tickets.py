import secrets
import string
from psycopg2 import errors

from db import get_connection

ALPHABET = string.ascii_uppercase + string.digits
ID_LENGTH = 12
MAX_ATTEMPTS = 5
VALID_PRIORITIES = ("Low", "Medium", "High")


def generate_ticket_id():
    return ''.join(
        secrets.choice(ALPHABET)
        for _ in range(ID_LENGTH)
    )


def create_ticket(employee_email, priority, equipment, description):
    # Validate inputs
    if not employee_email or not employee_email.strip():
        raise ValueError("Employee email is required.")

    if not priority or priority.strip() not in VALID_PRIORITIES:
        raise ValueError("Priority must be Low, Medium, or High.")

    if not equipment or not equipment.strip():
        raise ValueError("Equipment is required.")

    if not description or not description.strip():
        raise ValueError("Description is required.")

    conn = get_connection()

    try:
        for _ in range(MAX_ATTEMPTS):
            ticket_id = generate_ticket_id()

            try:
                with conn.cursor() as cur:
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
                        employee_email.strip(),
                        priority.strip(),
                        equipment.strip(),
                        description.strip()
                    ))

                conn.commit()
                return ticket_id

            except errors.UniqueViolation:
                conn.rollback()
                continue

        raise RuntimeError(
            "Unable to generate a unique ticket ID. Please try again later."
        )

    finally:
        conn.close()