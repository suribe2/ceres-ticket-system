import secrets
import string
import psycopg2

from db import get_connection

ALPHABET = string.ascii_uppercase + string.digits
ID_LENGTH = 12
MAX_ATTEMPTS = 5

VALID_STATUSES = ("Open", "Assigned", "Resolved")
VALID_PRIORITIES = ("Low", "Medium", "High")


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

                # Insert new ticket record into DS-01
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

        # Query ticket status matching employee email and ticket ID
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


# Retrieve all tickets for technician dashboard with optional status/priority filters (FR-05)
def get_all_tickets(status_filter=None, priority_filter=None):
    conn = get_connection()

    try:
        cur = conn.cursor()

        # Base query ordered by most recently submitted tickets
        query = """
            SELECT ticket_id, employee_email, created_at, status, priority, equipment
            FROM ds_01
            WHERE 1=1
        """
        params = []

        # Apply status filter if a valid status is selected
        if status_filter in VALID_STATUSES:
            query += " AND status = %s"
            params.append(status_filter)

        # Apply priority filter if a valid priority is selected
        if priority_filter in VALID_PRIORITIES:
            query += " AND priority = %s"
            params.append(priority_filter)

        query += " ORDER BY created_at DESC"

        cur.execute(query, tuple(params))
        rows = cur.fetchall()
        cur.close()

        return [
            {
                "ticket_id": row[0],
                "employee_email": row[1],
                "created_at": row[2],
                "status": row[3],
                "priority": row[4],
                "equipment": row[5],
            }
            for row in rows
        ]

    finally:
        conn.close()


# Retrieve full details for a single ticket by ticket ID (FR-06)
def get_ticket_by_id(ticket_id):
    ticket_id = ticket_id.strip().upper()
    conn = get_connection()

    try:
        cur = conn.cursor()

        cur.execute("""
            SELECT ticket_id, employee_email, created_at, status,
                   priority, equipment, description, internal_note
            FROM ds_01
            WHERE ticket_id = %s
        """, (ticket_id,))

        row = cur.fetchone()
        cur.close()

        if not row:
            return None

        return {
            "ticket_id": row[0],
            "employee_email": row[1],
            "created_at": row[2],
            "status": row[3],
            "priority": row[4],
            "equipment": row[5],
            "description": row[6],
            "internal_note": row[7] or "",
        }

    finally:
        conn.close()


# Update ticket status and internal technician note in DS-01 (FR-06, FR-11)
def update_ticket(ticket_id, status, internal_note):
    ticket_id = ticket_id.strip().upper()
    status = status.strip()

    # Validate status against allowed schema values
    if status not in VALID_STATUSES:
        raise ValueError("Invalid status selected.")

    note_value = internal_note.strip() if internal_note else None

    conn = get_connection()

    try:
        cur = conn.cursor()

        cur.execute("""
            UPDATE ds_01
            SET status = %s, internal_note = %s
            WHERE ticket_id = %s
        """, (status, note_value, ticket_id))

        if cur.rowcount == 0:
            conn.rollback()
            cur.close()
            raise ValueError("Ticket not found.")

        conn.commit()
        cur.close()

    finally:
        conn.close()


# Generate aggregated hardware ticket summary directly from DS-01 (FR-07 to FR-09)
def get_hardware_report():
    conn = get_connection()

    try:
        cur = conn.cursor()

        # Group tickets by equipment and count status and high-priority breakdowns
        cur.execute("""
            SELECT
                equipment,
                COUNT(*) AS total_tickets,
                COUNT(*) FILTER (WHERE status = 'Open') AS open_count,
                COUNT(*) FILTER (WHERE status = 'Assigned') AS assigned_count,
                COUNT(*) FILTER (WHERE status = 'Resolved') AS resolved_count,
                COUNT(*) FILTER (WHERE priority = 'High') AS high_priority_count
            FROM ds_01
            GROUP BY equipment
            ORDER BY total_tickets DESC, equipment ASC
        """)

        rows = cur.fetchall()
        cur.close()

        return [
            {
                "equipment": row[0],
                "total_tickets": row[1],
                "open_count": row[2],
                "assigned_count": row[3],
                "resolved_count": row[4],
                "high_priority_count": row[5],
            }
            for row in rows
        ]

    finally:
        conn.close()
