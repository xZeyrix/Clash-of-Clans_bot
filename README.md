# 🏰 Clash of Clans Telegram Bot

> **A comprehensive Telegram bot for Clash of Clans clan management and community interaction**

[![License](https://img.shields.io/badge/License-Non--Commercial-red.svg)](LICENSES/NON-COMMERCIAL_SHORT.md)
[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![aiogram](https://img.shields.io/badge/aiogram-3.x-blue.svg)](https://docs.aiogram.dev/)

---

## 📖 Language / Язык

**[🇷🇺 Русская версия / Russian version →](README.ru.md)**

---

## 📄 License & Usage

This software is provided for **personal, educational, and Clash of Clans community purposes only**.  
**Commercial use is strictly prohibited** without written permission from the author (xZeyrix).

- 📋 **[Short License Summary](LICENSES/NON-COMMERCIAL_SHORT.md)** — Quick overview of what you can and cannot do
- 📜 **[Full License Terms](LICENSES/NON-COMMERCIAL_FULL.md)** — Complete legal documentation

---

## 📑 Table of Contents

- [Features](#-features)
- [Requirements](#-requirements)
- [Installation](#-installation)
- [Configuration](#️-configuration)
- [Usage](#-usage)
- [Bot Commands](#-bot-commands)
- [Project Structure](#-project-structure)
- [Contributing](#-contributing)
- [License](#-license)

---

## ✨ Features

### 🎮 Clash of Clans Integration
- **Clan Information** — Get detailed statistics about any clan by tag
- **War Monitoring** — Real-time war tracking with automatic notifications
- **War Status** — Current war information, stars, destruction percentage, time remaining
- **Automated Alerts** — Notifications at key war milestones (12h, 6h, 3h, 1h remaining)
- **Smertniki System** — Track players who haven't attacked in wars

### 💬 Chat Moderation
- **Anti-Spam Protection** — Configurable rate limiting (default: 10 messages per 60 seconds)
- **Anti-Profanity Filter** — Automatic detection and removal of inappropriate language
- **Ban System** — Temporary bans with admin review and unban functionality
- **User Whitelisting** — Admin and beta tester access control

### 🎤 Voice Message Processing
- **Speech-to-Text** — Convert voice messages to text using Groq AI (Whisper model)
- **Content Moderation** — Automatic profanity detection in voice messages
- **Duration Limits** — Supports messages up to 10 minutes
- **Processing Time Estimates** — Real-time conversion progress

### 👑 Administration Tools
- **Bot Pause/Resume** — Temporarily disable bot responses
- **Message Broadcasting** — Send announcements to clan chat
- **War Monitor Control** — Start, stop, and check monitoring status
- **Smertniki Management** — Add, remove, clear, and list war offenders
- **User Management** — Ban, kick, and unban users with button controls

### 📚 Clan Rules System
- **Interactive Rules Browser** — Navigate through clan rules with inline buttons
- **Categorized Rules** — Main rules, CWL, Clan Wars, Events, Raids, Roles, Penalties
- **Multi-page Support** — Easy navigation between rule sections

---

## 📋 Requirements

- **Python 3.10+**
- **Telegram Bot Token** (from [@BotFather](https://t.me/BotFather))
- **Clash of Clans API Credentials**:
  - Email/Password for development mode, **OR**
  - API Token for production ([developer.clashofclans.com](https://developer.clashofclans.com/))
- **Groq API Key** (for voice-to-text) — Get it from [console.groq.com](https://console.groq.com/)

### Python Dependencies

```bash
aiogram>=3.24.0
coc.py>=4.0.0
groq>=1.0.0
python-dotenv>=1.2.1
```

---

## 🚀 Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd Clash-of-Clans_bot
```

### 2. Create Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/MacOS
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install aiogram coc.py groq python-dotenv
```

### 4. Create Environment File

Create a `.env` file in the project root:

```env
# Telegram Configuration
TELEGRAM_BOT_TOKEN=your_bot_token_here
NOTIFICATION_CHAT_ID=your_main_chat_id
COMMUNICATION_CHAT_ID=your_talk_chat_id
DEV_NOTIFICATION_CHAT_ID=your_dev_chat_id

# Admin Configuration
ADMIN_USER_IDS=123456789,987654321
DEVELOPER_USER_ID=123456789

# Clash of Clans API
COC_EMAIL=your_coc_email@example.com
COC_PASSWORD=your_coc_password
COC_API_TOKEN=your_production_api_token
CLAN_TAG=#YOUR_CLAN_TAG

# Groq API (for voice recognition)
GROQ_API_KEY=your_groq_api_key
```

---

## ⚙️ Configuration

### Edit `config.py`

```python
# Development Mode
DEV_MODE = True  # Set to False for production deployment

# Admin IDs
ADMIN_IDS = [123456789]  # Your Telegram user IDs

# Moderation Settings
# Anti-spam: 10 messages per 60 seconds (configurable in main.py)
# Ban duration: 3600 seconds (1 hour)
```

### Customize Clan Rules

Edit rule texts in `data/texts.py`:
- `RULES_MAIN` — General clan rules
- `RULES_CWL` — Clan War League rules
- `RULES_CW` — Regular Clan War rules
- `RULES_EVENTS` — Event rules
- `RULES_RAIDS` — Capital Raids rules
- `RULES_ROLES` — Role descriptions
- `RULES_PENALTIES` — Penalty system

### Customize Ban Words

Edit profanity filters in `data/texts.py`:
- `BAN_WORDS` — Short banned words (exact match)
- `BAN_LONG` — Long banned phrases (substring match without spaces)
- `BAN_LIGHT` — Light warnings (no immediate ban)
- `BAN_TRIGGERS` — Trigger words for moderation

---

## 🎯 Usage

### Start the Bot

```bash
python main.py
```

### Development Mode vs Production

**Development Mode** (`DEV_MODE = True`):
- ✅ Uses email/password authentication for CoC API
- ✅ All messages go to dev chat
- ✅ Only dev ID can use the bot
- ✅ Useful for testing without affecting production

**Production Mode** (`DEV_MODE = False`):
- ✅ Uses API token for CoC API (more stable)
- ✅ Separate notification and communication chats
- ✅ Requires user whitelist (AllowedUsersMiddleware)
- ✅ Ready for deployment

### Adding Allowed Users (Production Mode)

When running in production, you need to whitelist users. Add their IDs to the allowed list or implement your whitelist logic in `utils/filters.py`.

---

## 🤖 Bot Commands

### 👤 User Commands

| Command | Description |
|---------|-------------|
| `/start` | Welcome message and help |
| `/help` | Display available commands |
| `/rules` | Browse clan rules (interactive) |
| `/smertniki` | Show list of war offenders |
| `/clan [tag]` | Get clan information (defaults to your clan) |
| `/war` | Current war status and statistics |
| `/getmyid` | Get your Telegram user ID |
| **Voice Messages** | Send voice → bot converts to text |

### 👑 Admin Commands

| Command | Description |
|---------|-------------|
| `/admin` | Show admin help |
| `/send <text>` | Broadcast message to clan chat |
| `/getchatid` | Get current chat ID |
| `/pause` | Pause bot (stops responding to users) |
| `/resume` | Resume bot operation |
| `/sm add <names>` | Add player(s) to smertniki list |
| `/sm rm <ids>` | Remove player(s) from smertniki list |
| `/sm list` | Show smertniki list with IDs |
| `/sm clear` | Clear entire smertniki list |
| `/mstart` | Start war monitoring |
| `/mstop` | Stop war monitoring |
| `/mstatus` | Check monitoring status |

---

## 📁 Project Structure

```
Clash-of-Clans_bot/
├── main.py                 # Bot entry point
├── config.py               # Configuration and environment variables
├── .env                    # Environment secrets (create this)
├── README.md               # English documentation
├── README.ru.md            # Russian documentation
├── LICENSES/               # License files
│   ├── NON-COMMERCIAL_SHORT.md
│   └── NON-COMMERCIAL_FULL.md
├── commands/               # Command implementations
│   ├── rules.py           # Clan rules navigation
│   ├── send.py            # Message broadcasting
│   └── smertniki.py       # War offenders management
├── data/                   # Data files and constants
│   ├── texts.py           # All text constants, rules, ban words
│   ├── bot_state.json     # Bot state persistence
│   └── smertniki.json     # War offenders database
├── development/            # Development tools
│   ├── betatesters.py     # Beta tester commands
│   └── dev.py             # Developer utilities
├── handlers/               # Message and command handlers
│   ├── user.py            # User command handlers
│   └── admin.py           # Admin command handlers
├── services/               # External API integrations
│   ├── groqapi.py         # Voice-to-text processing
│   └── coc/               # Clash of Clans API
│       ├── coc_api.py     # API authentication
│       ├── clan.py        # Clan information
│       ├── war.py         # War information
│       └── monitor.py     # War monitoring system
└── utils/                  # Utility modules
    ├── antimat.py         # Profanity filter middleware
    ├── antispam.py        # Anti-spam middleware
    ├── files.py           # File operations
    ├── filters.py         # Custom filters and middleware
    └── moderation.py      # Moderation system
```

---

## 🔧 Advanced Configuration

### War Monitoring

The war monitoring system automatically:
1. Detects when war starts (preparation phase)
2. Sends notifications when battle day begins
3. Tracks players who haven't attacked
4. Sends reminders at 12h, 6h, 3h, 1h remaining
5. Reports final results when war ends

**Configuration** (in `services/coc/monitor.py`):
- Check interval: 30 seconds
- Notification thresholds: 12h, 6h, 3h, 1h

### Moderation System

**Anti-Spam** (in `main.py`):
```python
antispam = AntiSpamMiddleware(
    moderation, 
    rate_limit=10,      # Max messages
    time_window=60      # Per 60 seconds
)
```

**Ban Duration** (in `main.py`):
```python
moderation = ModerationSystem(ban_time=3600)  # 1 hour in seconds
```

---

## 🤝 Contributing

This project is designed for personal and community use. If you want to contribute:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request
5. **Remember**: All modifications must comply with the non-commercial license

---

## ⚠️ Important Notes

- **Comply with Supercell ToS**: Make sure your bot usage doesn't violate [Supercell's Terms of Service](https://supercell.com/en/terms-of-service/)
- **API Rate Limits**: The Clash of Clans API has rate limits. The monitoring system is designed to respect them
- **Groq API Limits**: Free tier has usage limits for voice transcription
- **Bot Token Security**: Never commit your `.env` file or expose your bot token

---

## 📜 License

This project is licensed under the **Non-Commercial Clash of Clans Community License**.

- ✅ **Allowed**: Use, modify, and share for your Clash of Clans clan (non-commercial)
- ❌ **Prohibited**: Any commercial use, monetization, donations, advertisements

**Copyright (c) 2025-2026 xZeyrix**

For commercial use inquiries or permissions beyond this license, contact the copyright holder.

See [LICENSE](LICENSES/NON-COMMERCIAL_SHORT.md) for quick summary or [FULL LICENSE](LICENSES/NON-COMMERCIAL_FULL.md) for complete terms.

---

## 📞 Support

- **Issues**: Report bugs or request features (if repository has issues enabled)
- **Questions**: Refer to this documentation first
- **License Inquiries**: Contact copyright holder

---

<div align="center">

**Made with ❤️ for the Clash of Clans community**

🏰⚔️🛡️

[🔝 Back to Top](#-clash-of-clans-telegram-bot)

</div>