# Average Bot - Telegram Bot for GPA Calculation
# Author: Gal Levi
# Date: May 2025
# License: MIT
# Version: 3.0
# Description: This file contains the constants and functions that are used by the bot's logic.

from telegram import InlineKeyboardMarkup, InlineKeyboardButton, Bot
from telegram.ext import CallbackContext
import os
import asyncio
import logging

# constants for the states of the conversation
(ASK_DEGREE, ENTER_GRADE, CHOOSE_COURSE_TYPE,
 DELETE_GRADE, SAVE_GRADES, WRITE_FEEDBACK,
 WRITE_BROADCAST_MSG, GET_ID_FOR_PRIVATE_MESSAGE, WRITE_PRIVATE_MSG) = range(9)

# constants for the bot's logic
ADVANCED_COURSE = 1.5 # the weight of an advanced course
TOKEN = os.getenv("BOT_TOKEN") # the token for the bot
ADMIN_ID = int(os.getenv("ADMIN_TELEGRAM_ID")) # the id of the admin
ACTIVE_USERS = {} # a dictionary to store the active users
SLEEP_TIME = 0.1 # the time to sleep between sending broadcast messages
MAX_DESC_LENGTH = 25 # the maximum length of the description

# constants for the bot's messages
START_TEXT = "🎓 שלום! אני יודע לחשב ממוצע באוניברסיטה הפתוחה.\nאשמח לעזור לך לחשב את הממוצע שלך."
EXACT_SCIENCES_QUESTION = "❓ האם אתה לומד תואר במדעים מדויקים (כגון מתמטיקה, מדעי המחשב וכו')?"
COURSE_TYPE_QUESTION_SHORT = "❓ האם הקורס הוא רגיל או מתקדם?"
COURSE_TYPE_QUESTION_LONG = "❓ האם הקורסים הם רגילים או מתקדמים?"
GRADE_PROMPT = ("📌 אנא הכנס ציונים בפורמט הבא:\n"
                "<תיאור> <ציון> <נק\"ז>\n"
                "(צריך להכניס קודם תיאור(אופציונלי), ציון ואז נק\"ז).\n"
                "למשל:\n"
                "90 5\n"
                "או:\n"
                "90 5\n"
                "80 4\n"
                "72 4\n"
                "...\n"
                "או:\n"
                "\u200Eתיאור כלשהו 95 4\n"
                "...\n"
                "לאחר מכן בחר את סוג הקורסים.\n"
                "או טען ציונים שנשמרו.")
GRADE_OR_CREDITS_RANGE_ERROR = "❌ קלט שגוי! עלייך להכניס ציון מ60 עד 100 ונק\"ז מ1 עד 8 בלבד. אנא נסה שוב."
GRADE_OR_CREDITS_INTEGER_ERROR = "❌ קלט שגוי! עלייך להכניס ציון ונק\"ז כמספרים שלמים בלבד. אנא נסה שוב."
FORMAT_ERROR = ("❌ קלט שגוי! אנא הכנס ציון ונק\"ז בפורמט הנכון.\n"
                "למשל:\n"
                "90 5\n"
                "או:\n"
                "\u200Eתיאור כלשהו 90 5\n")
ADD_GRADE = ("📌 הכנס ציונים נוספים ולאחר מכן בחר את סוג הקורסים או טען ציונים שנשמרו וצרף אותם לקיימים.\n"
             "למחיקת ציונים לפי אינדקס לחץ 'מחק ציונים לפי אינדקס'.\n"
             "לסיום לחץ 'סיימתי'.\n\n")
END_TEXT = ("🚫 השיחה הסתיימה. אם תרצה להתחיל מחדש, הקלד או לחץ על /start."
            "\n✍️ אם ברצונך לכתוב פידבק או המלצה לשיפור אנא הקלד או לחץ על /feedback")
DELETE_GRADE_PROMPT = "📌 הכנס את מספרי האינדקס של הציונים שברצונך למחוק\n(למשל 3 2 1)."
WRONG_INDEX_ERROR = "❌ האינדקס לא תואם לציון. אנא נסה שוב."
WRONG_NUMBER_ERROR = "❌ מספר לא תקין. אנא נסה שוב."
EXACT_ACKNOWLEDGEMENT = "📌 המערכת זיהתה שאתה לומד תואר במדעים מדויקים."
NOT_EXACT_ACKNOWLEDGEMENT = "📌 המערכת זיהתה שאתה לא לומד תואר במדעים מדויקים."
LOAD_GRADES_ERROR = "❌ אין ציונים שנשמרו. אנא הכנס ציונים חדשים."
SUCCESSFULLY_LOADED_GRADES = "✅ הציונים נטענו בהצלחה."
NOT_EXISTS_SAVED_GRADES_PROMPT = "❓ אין ציונים שנשמרו עדיין באופן יזום.\nהאם תרצה לשמור את הציונים הנוכחיים?"
EXISTS_SAVED_GRADES_PROMPT = "❓ האם תרצה לשמור את הציונים הנוכחיים?\n(השמירה תדרוס את השמירה הקודמת)"
SUCCESSFULLY_SAVED_GRADES = "✅ הציונים נשמרו בהצלחה."
SUCCESSFULLY_NOT_SAVED_GRADES = "✅ הציונים לא נשמרו."
SUCCESSFULLY_ADDED_GRADES = "✅ הציונים נוספו בהצלחה."
COMPUTING_GRADE = "🔄 מחשב ממוצע..."
SUCCESSFULLY_DELETED_GRADE = "✅ הציונים נמחקו בהצלחה."
WAITING_FOR_INDICES = "מחכה לאינדקסים..."
WAITING_FOR_DEGREE_TYPE = "מחכה לסוג התואר..."
GOING_BACK_TO_GRADES_INPUT = "🔙 חוזר להזנת ציונים..."
DUPLICATE_INDICES_ERROR = "❌ ישנם אינדקסים כפולים. אנא נסה שוב."
UNKNOWN_COMMAND = "❌ פקודה לא ידועה.\nהפקודות היחידות שנתמכות הן /start ו- /feedback."
UNKNOWN_TEXT_BEFORE_START = "❌ עלייך להתחיל את השיחה קודם על ידי הקלדה או לחיצה על /start."
NO_GRADES_ENTERED_FINISHED_PRESSED = "❌ אי אפשר לחשב ממוצע ללא ציונים. אנא הכנס ציונים קודם."
NO_GRADES_ENTERED_DELETE_PRESSED = "❌ אי אפשר למחוק ציונים כשאין ציונים. אנא הכנס ציונים קודם."
UNKNOWN_TEXT_IN_DEGREE_STATE = "❌ קלט לא צפוי, עלייך לבחור סוג תואר קודם."
UNKNOWN_TEXT_IN_COURSE_TYPE_STATE = "❌ קלט לא צפוי, עלייך לבחור סוג קורס קודם."
UNKNOWN_TEXT_IN_SAVE_GRADES_STATE = "❌ קלט לא צפוי, עלייך לבחור אם לשמור את הציונים קודם."
FEEDBACK_MSG = "✍️ אנא כתוב כעת את המשוב שלך."
FEEDBACK_ACKNOWLEDGEMENT = "✅ המשוב שלך נשמר במערכת בהצלחה, תודה רבה!"
FEEDBACK_EXIT = "❌ בחרת לא לכתוב פידבק."
BROADCAST_MSG = "📢 אנא כתוב את ההודעה שברצונך לשלוח לכל המשתמשים."
BROADCAST_ACKNOWLEDGEMENT = "✅ ההודעה נשלחה בהצלחה לכל המשתמשים."
ASK_ID_FOR_PRIVATE_MSG = "📩 אנא הכנס את מזהה המשתמש שברצונך לשלוח לו הודעה."
PRIVATE_MSG = "📩 אנא כתוב את ההודעה שברצונך לשלוח למשתמש."
SINGLE_ACKNOWLEDGEMENT = "✅ ההודעה נשלחה בהצלחה למשתמש."
ID_NOT_FOUND_ERROR = "❌ לא נמצא משתמש עם המזהה הזה במערכת.\nאנא נסה שוב."
WRONG_ID_ERROR = "❌ מזהה שגוי. אנא הכנס מזהה תקין."
WRONG_DESC_LENGTH_ERROR = f"❌ תיאור ארוך מדי. אנא הקלד תיאור עד {MAX_DESC_LENGTH} תווים."


# functions for the bot's logic
def check_input(grades : list) -> int:
    """Checks if the user's input is a valid score."""
    for desc, grade, credit in grades: # iterates over the user's grades
        if not (60 <= grade <= 100 and 1 <= credit <= 8): # checks if the grade and credit are in the valid range
            return 0
        if grade != int(grade) or credit != int(credit): # checks if the grade and credit are integers
            return -1
        if len(desc) > MAX_DESC_LENGTH: # checks if the description is too long
            return -2

    return 1


def get_history(context: CallbackContext) -> str:
    """Returns the user's grades history."""
    history = "הציונים שהוזנו עד כה:\n"
    # iterates over the user's grades and adds them to the history
    for i, (desc, grade, credit, is_advanced) in enumerate(context.user_data["grades"], start=1):
        if desc: # if there is a description
            desc = f"תיאור: {desc}, " # edit the description to include it in the history
        if is_advanced: # if the course is advanced
            history += f"{i}. {desc}ציון: {int(grade)}, נק\"ז: {int(credit)} (מתקדם)\n"
        else: # if the course is regular
            history += f"{i}. {desc}ציון: {int(grade)}, נק\"ז: {int(credit)} (רגיל)\n"

    return history


def get_grades_input(grades_input : str) -> list:
    """Parses the user's input into a list of grades."""
    output = []
    for line in grades_input.split("\n"):
        if not line:
            continue

        # clears the input from extra spaces
        line = ' '.join(line.split())

        # splits the line into description, grade, and credit
        after_split = line.rsplit(" ", 2)
        description = ""

        if len(after_split) <= 1:
            raise ValueError("Invalid input format")
        elif len(after_split) == 2: # if there is no description
            grade, credit = map(float, after_split)
        else:
            description, grade, credit = after_split[0], float(after_split[1]), float(after_split[2])
        output.append((description, grade, credit))

    return output


def add_grades_buttons() -> InlineKeyboardMarkup:
    """Creates inline buttons for the user to choose if he finished entering grades or wants to delete a grade."""
    keyboard = [
        [InlineKeyboardButton("טען ציונים אחרונים וצרף אותם לקיימים", callback_data="load_last_grades")],
        [InlineKeyboardButton("טען ציונים שמורים וצרף אותם לקיימים", callback_data="load_saved_grades")],
        [
            InlineKeyboardButton("סיימתי", callback_data="finished"),
            InlineKeyboardButton("מחק ציונים לפי אינדקס", callback_data="delete")
        ],
    ]
    return InlineKeyboardMarkup(keyboard)

def degree_yes_or_no_buttons() -> InlineKeyboardMarkup:
    """Creates inline buttons for the user to choose if he studies an exact sciences degree."""
    keyboard = [[
        InlineKeyboardButton("כן", callback_data="degree_yes"),
        InlineKeyboardButton("לא", callback_data="degree_no")
    ]]
    return InlineKeyboardMarkup(keyboard)

def load_grades_buttons() -> InlineKeyboardMarkup:
    """Creates an inline button for the user to load his last grades."""
    keyboard = [[
        InlineKeyboardButton("טען ציונים אחרונים", callback_data="load_last_grades"),
        InlineKeyboardButton("טען ציונים שמורים", callback_data="load_saved_grades")
    ]]
    return InlineKeyboardMarkup(keyboard)

# serialization and deserialization database functions
def pack_grades(grades : list) -> str:
    """Packs a list of grades into a string: <description>(optional) <grade> <credit> <is_advanced>."""
    output = ""
    for grade in grades:
        if grade[0]: # if the description is not empty
            output += f"{grade[0]} "
        output += f"{grade[1]} {grade[2]} {grade[3]}\n"

    return output

def unpack_grades(grades : str) -> list:
    """Unpacks a string of grades into a list of tuples: (description, grade, credit, is_advanced)."""
    output = []
    for line in grades.split("\n"):
        if not line:
            continue
        # splits the line into description, grade, credit, and is_advanced indicator
        after_split = line.rsplit(" ", 3)
        description = ""
        if len(after_split) == 3: # if there is no description
            grade, credit, is_advance = after_split
        else:
            description, grade, credit, is_advance = after_split

        output.append((description, float(grade), float(credit), is_advance == "True"))

    return output

def log_user(user_id: int, message: str) -> None:
    """Logs the user id and message to the user log file."""
    user_logger.info(f"User {user_id} {message}.")

def log_user_and_active_users(user_id: int, message: str) -> None:
    """Logs the user id, message and the total active users to the user log file."""
    user_logger.info(f"User {user_id} {message}. Total active users: {len(ACTIVE_USERS)}")

async def send_broadcast_message(text: str) -> int:
    """Sends a message to all users."""
    from db import get_all_users_ids
    bot = Bot(token=TOKEN)
    user_ids = await get_all_users_ids() # retrieves all user ids from the database
    successfully_sent = 0 # counter for the successfully sent messages
    for user_id in user_ids:
        try:
            await bot.send_message(chat_id=user_id, text=text)
            successfully_sent += 1
        except Exception as e:
            log_user(user_id, f"was unable to receive a message: {e}")
        await asyncio.sleep(SLEEP_TIME) # sleep for a second to avoid flooding the server

    return successfully_sent # returns the number of successfully sent messages

async def send_single_message(user_id: int, text: str) -> None:
    """Sends a message to specific user."""
    bot = Bot(token=TOKEN)
    try:
        await bot.send_message(chat_id=user_id, text=text)
    except Exception as e:
        log_user(user_id, f"was unable to receive a message: {e}")


# define the logging configuration
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# logs for the users
user_logger = logging.getLogger("user_logger")
user_handler = logging.FileHandler("bot_users.log")
user_formatter = logging.Formatter("%(asctime)s - %(message)s")
user_handler.setFormatter(user_formatter)
user_logger.addHandler(user_handler)
user_logger.setLevel(logging.INFO)

# logs for the feedbacks sent by the users
feedback_logger = logging.getLogger("feedback_logger")
feedback_handler = logging.FileHandler("feedbacks.log", encoding="utf-8")
feedback_formatter = logging.Formatter("%(asctime)s - %(message)s")
feedback_handler.setFormatter(feedback_formatter)
feedback_logger.addHandler(feedback_handler)
feedback_logger.setLevel(logging.INFO)