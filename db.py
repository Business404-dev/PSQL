# db.py
import asyncpg
import datetime
from config import DATABASE_URL

async def get_conn():
    return await asyncpg.connect(DATABASE_URL)

async def init_db():
    conn = await get_conn()
    await conn.execute("""
    CREATE TABLE IF NOT EXISTS tickets (
        id SERIAL PRIMARY KEY,
        user_id BIGINT NOT NULL,
        username TEXT,
        subject TEXT,
        description TEXT,
        status TEXT DEFAULT 'ouvert',
        assigned_to BIGINT,
        created_at TIMESTAMP,
        updated_at TIMESTAMP
    );
    """)
    await conn.execute("""
    CREATE TABLE IF NOT EXISTS messages (
        id SERIAL PRIMARY KEY,
        ticket_id INTEGER NOT NULL REFERENCES tickets(id) ON DELETE CASCADE,
        sender_id BIGINT,
        sender_name TEXT,
        content TEXT,
        timestamp TIMESTAMP
    );
    """)
    await conn.close()

async def create_ticket(user_id, username, subject, description):
    now = datetime.datetime.utcnow()
    conn = await get_conn()
    ticket = await conn.fetchrow(
        """
        INSERT INTO tickets (user_id, username, subject, description, created_at, updated_at)
        VALUES ($1,$2,$3,$4,$5,$5)
        RETURNING id
        """,
        user_id, username, subject, description, now
    )
    ticket_id = ticket["id"]
    await conn.execute(
        """
        INSERT INTO messages (ticket_id, sender_id, sender_name, content, timestamp)
        VALUES ($1,$2,$3,$4,$5)
        """,
        ticket_id, user_id, username, description, now
    )
    await conn.close()
    return ticket_id

async def add_message(ticket_id, sender_id, sender_name, content):
    now = datetime.datetime.utcnow()
    conn = await get_conn()
    await conn.execute(
        """
        INSERT INTO messages (ticket_id, sender_id, sender_name, content, timestamp)
        VALUES ($1,$2,$3,$4,$5)
        """,
        ticket_id, sender_id, sender_name, content, now
    )
    await conn.execute(
        "UPDATE tickets SET updated_at = $1 WHERE id = $2",
        now, ticket_id
    )
    await conn.close()

async def get_ticket(ticket_id):
    conn = await get_conn()
    ticket = await conn.fetchrow("SELECT * FROM tickets WHERE id = $1", ticket_id)
    if not ticket:
        await conn.close()
        return None
    messages = await conn.fetch(
        "SELECT sender_name, content, timestamp FROM messages WHERE ticket_id = $1 ORDER BY timestamp ASC",
        ticket_id
    )
    await conn.close()
    return ticket, messages

async def list_tickets(status=None):
    conn = await get_conn()
    if status:
        tickets = await conn.fetch("SELECT * FROM tickets WHERE status = $1 ORDER BY updated_at DESC", status)
    else:
        tickets = await conn.fetch("SELECT * FROM tickets ORDER BY updated_at DESC")
    await conn.close()
    return tickets

async def set_status(ticket_id, status):
    now = datetime.datetime.utcnow()
    conn = await get_conn()
    await conn.execute(
        "UPDATE tickets SET status = $1, updated_at = $2 WHERE id = $3",
        status, now, ticket_id
    )
    await conn.close()

async def assign_ticket(ticket_id, agent_id):
    now = datetime.datetime.utcnow()
    conn = await get_conn()
    await conn.execute(
        "UPDATE tickets SET assigned_to = $1, updated_at = $2 WHERE id = $3",
        agent_id, now, ticket_id
    )
    await conn.close()
