from werkzeug.security import check_password_hash, generate_password_hash

from db import get_connection

# Dummy hash used to reduce timing differences when the email is not found
DUMMY_HASH = generate_password_hash("dummy-password-for-timing")


def login_technician(technician_email, password):

    # 1. Validate inputs
    if not technician_email or not technician_email.strip():
        raise ValueError("Invalid email or password.")

    if not password:
        raise ValueError("Invalid email or password.")

    # 2. Normalize email
    technician_email = technician_email.strip().lower()

    conn = get_connection()

    try:
        cur = conn.cursor()

        # 3. Look up technician
        cur.execute("""
            SELECT technician_email, password_hash
            FROM ds_02
            WHERE technician_email = %s
        """, (technician_email,))

        row = cur.fetchone()

        cur.close()

        # 4. Technician not found: run a dummy check, then fail
        if row is None:
            check_password_hash(DUMMY_HASH, password)
            raise ValueError("Invalid email or password.")

        # 5. Compare submitted password with stored hash
        stored_hash = row[1]

        if not check_password_hash(stored_hash, password):
            raise ValueError("Invalid email or password.")

        # 6. Successful login
        return {
            "technician_email": row[0]
        }

    finally:
        conn.close()