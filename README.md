# 📊 Average Bot - Telegram GPA Calculator for Open University

**Average Bot** is a Telegram bot designed to help students at the Open University of Israel calculate their weighted GPA easily.  
It is especially tailored for exact sciences degrees, supporting advanced course weighting and grade management.

---

## 🚀 Features

- 🎓 Weighted GPA calculation based on course type (regular/advanced)
- ✍️ Add, delete, and view grades before calculation
- 📝 Add an optional description for each grade (e.g., "Linear Algebra")
- 💾 Save and load both recent and saved grades
- 🧠 Support for students in exact sciences degrees
- 💬 Feedback system: users can send feedback to the developer
- 📢 Admin tools: private message or broadcast to all users
- 🗂 Separate logs for user activity and feedback
- 🧪 Robust error handling and session state management

---

## 🛠️ Installation

### Prerequisites
- Python 3.8+
- Telegram Bot Token (from [@BotFather](https://t.me/BotFather))
- Telegram user ID for admin access

### Steps

1️⃣ Clone the repository:

```bash
git clone https://github.com/gallevi10/average_telegram_bot_OpenU.git
cd average_telegram_bot_OpenU
```

2️⃣ Install dependencies:

```bash
pip install -r requirements.txt
```

3️⃣ Set environment variables:

- On Linux/macOS:
```bash
export BOT_TOKEN="<your telegram bot token>"
export ADMIN_TELEGRAM_ID="<your telegram user ID>"
```

- On Windows (PowerShell):
```powershell
$env:BOT_TOKEN="<your telegram bot token>"
$env:ADMIN_TELEGRAM_ID="<your telegram user ID>"
```

4️⃣ Run the bot:

```bash
python average_bot.py
```

---

## 📖 Usage

1. Start the bot with the `/start` command in Telegram.
2. The bot will ask if you are studying an **exact sciences** degree.
3. Enter grades in the following format:

```
90 5
85 4
Object Oriented Programming 95 4
```

4. Specify if the courses are regular or advanced.
5. You can add more grades, delete by index, or click "finished" to compute the GPA.
6. After calculation, choose whether to save your grades.
7. Use `/feedback` to send feedback to the developer.

---

## 🔧 Project Structure

```
Average-Bot/
├── average_bot.py        # Main bot logic
├── db.py                 # SQLite database operations
├── utils.py              # Helper functions, constants, logging
├── requirements.txt      # Dependencies
├── README.md             # Project documentation
├── bot_users.log         # User activity logs
├── feedbacks.log         # User feedback logs
└── data/
    └── database.db       # SQLite database file
```

---

## 🧩 Dependencies

- `python-telegram-bot`
- `asyncio`
- `httpx`
- `See full list in requirements.txt.`

---

## 📜 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

## ✉️ Contact

For issues, suggestions, or feature requests, feel free to email: **gallevi1902@gmail.com**

---

Enjoy using **Average Bot**! 🚀🎓
