
import os
import random
from datetime import datetime, timedelta

import psycopg2
from psycopg2 import sql
from psycopg2.extras import execute_values


# -----------------------------------------
# DATABASE CONFIGURATION
# -----------------------------------------

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "5432")),
    "dbname": os.getenv("DB_NAME", "security_analytics"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD"),
}




USERS = [f"user_{i:03d}" for i in range(1, 51)]

IPS = [
    "192.168.1.100",
    "192.168.1.101",
    "10.0.0.50",
    "10.0.0.51",
    "172.16.0.10",
    "203.0.113.42",
    "198.51.100.7",
    "203.0.113.99",
    None,
    "",
]

EVENT_TYPES = [
    "LOGIN",
    "login",
    "Login",
    "LOGOUT",
    "logout",
    "FAILED_LOGIN",
    "failed_login",
    "Failed_Login",
    "PASSWORD_CHANGE",
    "MFA_CHALLENGE",
]

STATUSES = [
    "success",
    "SUCCESS",
    "failure",
    "FAILURE",
    "Success",
    "Failure",
]

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
    "curl/7.88.1",
    "python-requests/2.31.0",
    None,
]


# CREATE DATABASE


def create_database():

    config = {**DB_CONFIG, "dbname": "postgres"}

    conn = psycopg2.connect(**config)
    conn.autocommit = True

    try:
        with conn.cursor() as cur:

            cur.execute(
                "SELECT 1 FROM pg_database WHERE datname = %s",
                (DB_CONFIG["dbname"],),
            )

            if not cur.fetchone():

                cur.execute(
                    sql.SQL("CREATE DATABASE {}").format(
                        sql.Identifier(DB_CONFIG["dbname"])
                    )
                )

                print(f"Created database: {DB_CONFIG['dbname']}")

            else:
                print(f"Database {DB_CONFIG['dbname']} already exists")

    finally:
        conn.close()


# CREATE RAW TABLE


def create_tables(conn):

    with conn.cursor() as cur:

        cur.execute("CREATE SCHEMA IF NOT EXISTS raw")

        # Reset table for reproducible development runs
        cur.execute("DROP TABLE IF EXISTS raw.auth_events")

        cur.execute(
            """
            CREATE TABLE raw.auth_events (
                id SERIAL PRIMARY KEY,
                event_timestamp TEXT,
                user_id TEXT,
                event_type TEXT,
                ip_address TEXT,
                status TEXT,
                user_agent TEXT
            )
            """
        )

    conn.commit()

    print("Created raw.auth_events table")



# GENERATE SYNTHETIC EVENTS


def generate_events(num_events=500):

    events = []

    base_time = datetime(2026, 8, 20, 0, 0, 0)

    # Generate random authentication events
    for _ in range(num_events):

        ts = base_time + timedelta(
            seconds=random.randint(0, 7 * 24 * 3600)
        )

        format_choice = random.random()

        if format_choice < 0.30:
            ts_str = ts.strftime("%m/%d/%Y %H:%M:%S")

        elif format_choice < 0.65:
            ts_str = ts.isoformat()

        else:
            ts_str = ts.strftime("%Y-%m-%d %H:%M:%S")

        events.append(
            (
                ts_str,
                random.choice(USERS),
                random.choice(EVENT_TYPES),
                random.choice(IPS),
                random.choice(STATUSES),
                random.choice(USER_AGENTS),
            )
        )

   

    attacker_ip = "203.0.113.42"
    target_user = "user_001"

    brute_start = base_time + timedelta(days=3, hours=2)

    for i in range(20):

        ts = brute_start + timedelta(seconds=i * 5)

        ts_str = ts.strftime("%Y-%m-%d %H:%M:%S")

        events.append(
            (
                ts_str,
                target_user,
                "FAILED_LOGIN",
                attacker_ip,
                "failure",
                "python-requests/2.31.0",
            )
        )

    # INJECT DUPLICATE EVENTS


    # Snapshot original events so duplicates are selected
    # from the generated dataset
    original_events = events.copy()

    for _ in range(15):
        events.append(random.choice(original_events))

    random.shuffle(events)

    return events



def load_events(conn, events):

    with conn.cursor() as cur:

        execute_values(
            cur,
            """
            INSERT INTO raw.auth_events (
                event_timestamp,
                user_id,
                event_type,
                ip_address,
                status,
                user_agent
            )
            VALUES %s
            """,
            events,
        )

    conn.commit()

    print(f"Loaded {len(events)} events into raw.auth_events")




def main():

    create_database()

    with psycopg2.connect(**DB_CONFIG) as conn:

        create_tables(conn)

        events = generate_events(500)

        load_events(conn, events)

    print("Security analytics pipeline completed successfully!")


if __name__ == "__main__":
    main()
