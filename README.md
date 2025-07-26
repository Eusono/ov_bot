# ov_bot

A Discord bot built for the RuneScape clan **Odin's Valhalla**, with features tailored for community management, RuneScape chat enhancements, and clan banking tools.

---

## 🧠 Features

- 🔐 **Role-Based Command Permissions**
  - Restrict admin commands to specific role IDs
- 💬 **Welcome Messaging**
  - Auto-messages users entering designated channels like `#the-door`
- 💰 **Clan Bank System**
  - `/clanbank add`, `/clanbank remove`, and logging via JSON-backed storage
- 🔀 **Random Commands**
  - Fun utilities like dice rolls, random number generators, etc.
- ⚙️ **Admin Utilities**
  - Channel control, announcements, and more (restricted to certain roles)

---

## 🗂️ Project Structure

```
ov_bot/
├── ov_bot.py               # Entry point
├── config.py               # Bot configuration (ignored in git)
├── example.config.py       # Sample config to copy/edit
├── clan_bank.json          # JSON data store for clan banking
├── reminders.json          # (Reserved) for scheduled reminders
├── cogs/                   # All feature modules
│   ├── admin.py
│   ├── example.py
│   ├── randoms.py
│   └── rs3_finances.py
└── utils/
    └── permissions.py      # Role checking helpers
```

---

## 🛠️ Setup

### 1. Clone the Repository

```bash
git clone git@github.com:Eusono/ov_bot.git
cd ov_bot
```

### 2. Create a Virtual Environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

> If no `requirements.txt` exists yet, install:
```bash
pip install -U discord.py
```

### 4. Configure the Bot

Copy the config example:
```bash
cp example.config.py config.py
```

Edit `config.py` to include your:
- Bot token
- Guild/server ID
- Channel and role IDs for permissions
- File paths for data

---

## 🚀 Running the Bot

From the project root:

```bash
source .venv/bin/activate
python ov_bot.py
```

Or use systemd like on the production server:
```ini
[Service]
WorkingDirectory=/opt/ovbot
ExecStart=/opt/ovbot/.venv/bin/python /opt/ovbot/ov_bot.py
Restart=always
```

---

## 🧾 Notes

- Secrets and config values are stored in `config.py`, which is excluded via `.gitignore`
- Persistent data is saved to `clan_bank.json`
- Make sure all role and channel IDs in `config.py` match your Discord server

---

## 📜 License

This project is licensed under the [MIT License](LICENSE).

---

## 🙌 Credits

Created and maintained by @Eusono
Built with ❤️ for the Odin's Valhalla community.
