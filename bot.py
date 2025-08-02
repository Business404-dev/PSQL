# bot.py
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from config import BOT_TOKEN, SUPPORT_AGENTS
from db import (
    init_db, create_ticket, add_message, get_ticket,
    list_tickets, set_status, assign_ticket
)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# démarrage : init DB
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.reply("👋 Bienvenue sur le support. Tape /newticket pour créer un ticket.")

# Création de ticket (simple séquence)
user_states = {}  # temporaire : {user_id: {"stage": ..., "subject": ...}}

@dp.message(Command("newticket"))
async def cmd_newticket(message: types.Message):
    user_states[message.from_user.id] = {"stage": "await_subject"}
    await message.reply("📝 Quel est le sujet de votre problème ?")

@dp.message()
async def handle_sequence(message: types.Message):
    uid = message.from_user.id
    state = user_states.get(uid)
    if not state:
        return  # pas dans une séquence
    if state["stage"] == "await_subject":
        subject = message.text.strip()
        state["subject"] = subject
        state["stage"] = "await_description"
        await message.reply("Décris ton problème en détail :")
    elif state["stage"] == "await_description":
        description = message.text.strip()
        subject = state.get("subject", "Sans sujet")
        ticket_id = await create_ticket(
            user_id=message.from_user.id,
            username=message.from_user.username or "",
            subject=subject,
            description=description
        )
        await message.reply(f"✅ Ton ticket a été créé. Numéro : #{ticket_id}")
        # Notifier les agents
        for agent in SUPPORT_AGENTS:
            try:
                await bot.send_message(
                    agent,
                    f"🆕 Nouveau ticket #{ticket_id}\n"
                    f"De: @{message.from_user.username or message.from_user.full_name}\n"
                    f"Sujet: {subject}\n"
                    f"Description: {description[:200]}..."
                )
            except Exception:
                pass
        user_states.pop(uid, None)

# Commandes agents

@dp.message(Command("list_tickets"))
async def cmd_list_tickets(message: types.Message):
    if message.from_user.id not in SUPPORT_AGENTS:
        return
    tickets = await list_tickets()
    if not tickets:
        await message.reply("Aucun ticket trouvé.")
        return
    lines = []
    for t in tickets:
        tid = t["id"]
        subj = t["subject"]
        status = t["status"]
        assigned = t["assigned_to"] or "—"
        lines.append(f"#{tid} | {subj} | statut: {status} | assigné à: {assigned}")
    await message.reply("🎫 Tickets existants :\n" + "\n".join(lines))

@dp.message(Command("view_ticket"))
async def cmd_view_ticket(message: types.Message):
    if message.from_user.id not in SUPPORT_AGENTS:
        return
    parts = message.text.strip().split()
    if len(parts) < 2 or not parts[1].isdigit():
        await message.reply("Usage: /view_ticket <id>")
        return
    tid = int(parts[1])
    result = await get_ticket(tid)
    if not result:
        await message.reply("Ticket introuvable.")
        return
    ticket, messages = result
    resp = (
        f"🎫 Ticket #{ticket['id']}\n"
        f"Sujet: {ticket['subject']}\n"
        f"Description initiale: {ticket['description']}\n"
        f"Statut: {ticket['status']}\n"
        f"Assigné à: {ticket['assigned_to'] or '—'}\n"
        f"Utilisateur: @{ticket['username']} ({ticket['user_id']})\n"
        f"Créé: {ticket['created_at']}\n"
        f"Dernière mise à jour: {ticket['updated_at']}\n\n"
        f"--- Historique ---\n"
    )
    for m in messages:
        sender = m["sender_name"] or ""
        content = m["content"]
        timestamp = m["timestamp"]
        resp += f"[{timestamp}] {sender}: {content}\n"
    await message.reply(resp)

@dp.message(Command("assign"))
async def cmd_assign(message: types.Message):
    if message.from_user.id not in SUPPORT_AGENTS:
        return
    parts = message.text.strip().split()
    if len(parts) < 3 or not parts[1].isdigit() or not parts[2].isdigit():
        await message.reply("Usage: /assign <ticket_id> <agent_user_id>")
        return
    tid = int(parts[1])
    agent_id = int(parts[2])
    await assign_ticket(tid, agent_id)
    await message.reply(f"Ticket #{tid} assigné à {agent_id}.")

@dp.message(Command("set_status"))
async def cmd_set_status(message: types.Message):
    if message.from_user.id not in SUPPORT_AGENTS:
        return
    parts = message.text.strip().split()
    if len(parts) < 3 or not parts[1].isdigit():
        await message.reply("Usage: /set_status <ticket_id> <statut>")
        return
    tid = int(parts[1])
    status = parts[2].lower()
    valid = ["ouvert", "en_cours", "resolu", "ferme"]
    if status not in valid:
        await message.reply(f"Statuts valides: {', '.join(valid)}")
        return
    await set_status(tid, status)
    await message.reply(f"Statut de #{tid} mis à {status}.")

# Réponse à un ticket via #<id> message
@dp.message()
async def catch_all(message: types.Message):
    if not message.text:
        return
    if message.from_user.id not in SUPPORT_AGENTS:
        return
    if message.text.strip().startswith("#"):
        parts = message.text.strip().split(" ", 1)
        if len(parts) < 2:
            return
        ticket_ref = parts[0][1:]
        if not ticket_ref.isdigit():
            return
        ticket_id = int(ticket_ref)
        result = await get_ticket(ticket_id)
        if not result:
            await message.reply("Ticket introuvable.")
            return
        # Ajouter message
        content = parts[1]
        await add_message(ticket_id, message.from_user.id, message.from_user.username or "", content)
        ticket, _ = result
        user_id = ticket["user_id"]
        await bot.send_message(user_id,
            f"✉️ Réponse sur ton ticket #{ticket_id} :\n{content}"
        )
        await message.reply(f"Message ajouté au ticket #{ticket_id}.")

async def main():
    await init_db()
    print("🛠️  Base initialisée, démarrage du bot...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
