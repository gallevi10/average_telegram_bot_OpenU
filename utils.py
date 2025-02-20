# Average Bot - Telegram Bot for GPA Calculation
# Author: Gal Levi
# Date: February 2025
# License: MIT
# Version: 2.0
# Description: This file contains the constants and functions that are used by the bot's logic.

from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackContext
import os

# constants for the bot's messages
START_TEXT = "🎓 שלום! אני יודע לחשב ממוצע באוניברסיטה הפתוחה.\nאשמח לעזור לך לחשב את הממוצע שלך."
EXACT_SCIENCES_QUESTION = "❓ האם אתה לומד תואר במדעים מדויקים (כגון מתמטיקה, מדעי המחשב וכו')?"
COURSE_TYPE_QUESTION_SHORT = "❓ האם הקורס הוא רגיל או מתקדם?"
COURSE_TYPE_QUESTION_LONG = "❓ האם הקורסים הם רגילים או מתקדמים?"
GRADE_PROMPT = ("📌 אנא הכנס ציונים ונק\"ז בפורמט הבא:\n"
                "<ציון 60-100> <נק\"ז 1-8>\n"
                "(קודם ציון ואז נק\"ז).\n"
                "למשל:\n"
                "90 5\n"
                "או:\n"
                "90 5\n"
                "80 4\n"
                "70 3\n"
                "...\n"
                "לאחר מכן בחר את סוג הקורסים.\n"
                "או טען ציונים שנשמרו.")
GRADE_OR_CREDITS_ERROR = "❌ קלט שגוי! עלייך להכניס ציון מ60 עד 100 ונק\"ז מ1 עד 8 בלבד."
FORMAT_ERROR = "❌ קלט שגוי! אנא הכנס ציון ונק\"ז בפורמט הנכון (למשל 5 90)."
ADD_GRADE = ("📌 הכנס ציונים נוספים ולאחר מכן בחר את סוג הקורסים או טען ציונים שנשמרו וצרף אותם לקיימים.\n"
             "למחיקת ציונים לפי אינדקס לחץ 'מחק ציונים לפי אינדקס'.\n"
             "לסיום לחץ 'סיימתי'.\n\n")
END_TEXT = "🚫 השיחה הסתיימה. אם תרצה להתחיל מחדש, הקלד או לחץ על /start."
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
UNKNOWN_COMMAND = "❌ פקודה לא ידועה. הפקודה היחידה שנתמכת היא /start."
UNKNOWN_TEXT_BEFORE_START = "❌ עלייך להתחיל את השיחה קודם על ידי הקלדה או לחיצה על /start."

# constants for the states of the conversation
ASK_DEGREE, ENTER_GRADE, CHOOSE_COURSE_TYPE, DELETE_GRADE, SAVE_GRADES = range(5)

ADVANCED_COURSE = 1.5 # the weight of an advanced course
TOKEN = os.getenv("BOT_TOKEN") # gets the bot's token from the environment variables
ACTIVE_USERS = {} # a dictionary to store the active users


# functions for the bot's logic
def check_grade_and_credit(grades : list) -> bool:
    """Checks if the user's input is a valid score."""
    for grade, credit in grades: # iterates over the user's grades
        if not (60 <= grade <= 100 and 1 <= credit <= 8):
            return False
    return True


def get_history(context: CallbackContext) -> str:
    """Returns the user's grades history."""
    history = "הציונים שהוזנו עד כה:\n"
    # iterates over the user's grades and adds them to the history
    for i, (grade, credit, is_advanced) in enumerate(context.user_data["grades"], start=1):
        if is_advanced: # if the course is advanced
            history += f"{i}. ציון: {int(grade)}, נק\"ז: {int(credit)} (מתקדם)\n"
        else: # if the course is regular
            history += f"{i}. ציון: {int(grade)}, נק\"ז: {int(credit)} (רגיל)\n"

    return history

def get_grades_input(grades_input : str) -> list:
    """Parses the user's input into a list of grades."""
    return [tuple(map(float, grade.split())) for grade in grades_input.split("\n") if grade]

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

def pack_grades(grades : list) -> str:
    """Packs a list of grades into a string."""
    output = ""
    for grade in grades:
        output += f"{grade[0]} {grade[1]} {grade[2]}\n"

    return output

def unpack_grades(grades : str) -> list:
    """Unpacks a string of grades into a list."""
    output = []
    for grade in grades.split("\n"):
        if not grade:
            continue
        grade_split = grade.split()
        output.append([float(grade_split[0]), float(grade_split[1]), grade_split[2] == "True"])

    return output
