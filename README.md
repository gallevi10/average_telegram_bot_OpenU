# 📊 Average Bot - Telegram Open University GPA Calculator

Welcome to **Average Bot**, a Telegram bot designed to help students at the Open University calculate their weighted GPA effortlessly.
This bot is particularly useful for students in **exact sciences** (e.g., Computer Science, Mathematics, etc.) where advanced courses carry extra weight.

---

## 🚀 Features

- 📌 Supports both **regular** and **advanced** courses.
- 📊 Calculates a **weighted GPA** based on course types.
- 🏫 Designed specifically for **Open University** students.
- 📝 Supports adding, deleting, and listing grades before calculation.
- 💾 Remembers user inputs within a session.

---

## 🛠️ Installation

### Prerequisites
Ensure you have **Python 3.8+** installed. You also need a **Telegram Bot Token**, which you can obtain by chatting with [BotFather](https://t.me/BotFather).

### Steps

1️⃣ Clone the repository:

```sh
git clone https://github.com/gallevi10/average_telegram_bot_OpenU
cd average_telegram_bot_OpenU
```

2️⃣ Install dependencies:

```sh
pip install -r requirements.txt
```

3️⃣ Set up the environment variable for your **Telegram Bot Token**:

- On **Linux/macOS**:
  ```sh
  export BOT_TOKEN="<your telegram bot token>"
  ```

- On **Windows** (PowerShell):
  ```powershell
  $env:BOT_TOKEN="<your telegram bot token>"
  ```

4️⃣ Run the bot:

```sh
python average_bot.py
```

---

## 📖 Usage

1. Start the bot by sending `/start` in Telegram.
2. The bot will ask if you are studying an **exact sciences** degree.
3. Enter grades and credit points in the format:  
   ```
   <grade (1-100)> <credits (1-8)>
   ```
   Example: `90 5`
4. If you are an exact sciences student, specify if the course is **regular** or **advanced**.
5. Add more grades or type `/end` to get your final GPA.

---

## 🔧 Project Structure

```
Average-Bot/
│── average_bot.py        # Main bot script
│── requirements.txt      # Dependencies
│── README.md             # Project documentation (this file)
```

---

## 🛠 Dependencies

This bot relies on:

- `python-telegram-bot`
- `httpx`
- `urllib3`
- See full list in `requirements.txt`.

---

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🤝 Contributing

Contributions are welcome! Feel free to fork the repository and submit a pull request.

---

## 📞 Contact

For any issues or feature requests, open an issue on GitHub or contact me at **gallevi1902@gmail.com**.

---

Enjoy using **Average Bot**! 🚀
