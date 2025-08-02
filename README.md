# Bot Telegram Service Client (Tickets) – MVP

## Fonctionnalités
- Création de ticket par utilisateur (`/newticket`)
- Statuts (ouvert, en_cours, resolu, ferme)
- Assignation manuelle d’un agent
- Historique des échanges
- Réponse via `#<id> message`
- Notifications aux agents

## Installation locale (test)
1. Copier `.env.example` en `.env` et remplir :
   ```env
   BOT_TOKEN=ton_token
   SUPPORT_AGENTS=123456789
   DATABASE_URL=postgresql://...

   venv\Scripts\activate.bat

    python.exe -m pip install --upgrade pip
pip install -r requirements.txt

Microsoft Visual C++ 14.0 