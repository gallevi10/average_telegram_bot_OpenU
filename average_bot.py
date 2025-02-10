# Average Bot - Telegram Bot for GPA Calculation
# Author: Gal Levi
# Date: February 2025
# License: MIT
# Description: A bot that assists students in calculating their university GPA.


from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove
from telegram.ext import (Application, CommandHandler, MessageHandler,
                          CallbackQueryHandler, filters, ConversationHandler, CallbackContext)
import logging
import os

# logs for debugging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# constants for the bot's messages
START_TEXT = "🎓 שלום! אני יודע לחשב ממוצע באוניברסיטה הפתוחה.\nאשמח לעזור לך לחשב את הממוצע שלך."
EXACT_SCIENCES_QUESTION = "❓ האם אתה לומד תואר במדעים מדויקים (כגון מתמטיקה, מדעי המחשב וכו')?"
COURSE_TYPE_QUESTION = "📌 האם הקורס הוא מתקדם או רגיל?"
GRADE_PROMPT = "📌 אנא הכנס ציון ונק\"ז בפורמט הבא: \n<ציון 60-100> <נק\"ז 1-8> \n(קודם ציון ואז נק\"ז, למשל 5 90)."
GRADE_OR_CREDITS_ERROR = "❌ קלט שגוי! עלייך להכניס ציון מ60 עד 100 ונק\"ז מ1 עד 8 בלבד."
FORMAT_ERROR = "❌ קלט שגוי! אנא הכנס ציון ונק\"ז בפורמט הנכון (למשל 5 90)."
ADD_GRADE = "📌 הכנס ציון נוסף או לחץ 'סיימתי' לסיום.\n"
NO_GRADES_ERROR = "❌ לא הוזנו ציונים."
END_TEXT = "🚫 השיחה הסתיימה. אם תרצה להתחיל מחדש, הקלד/לחץ על /start."
DELETE_GRADE_PROMPT = "📌 הכנס את מספר האינדקס של הציון שברצונך למחוק."
WRONG_INDEX_ERROR = "❌ האינדקס לא תואם לציון. אנא נסה שוב."
WRONG_NUMBER_ERROR = "❌ מספר לא תקין. אנא נסה שוב."

# constants for the states of the conversation
ASK_DEGREE, ENTER_GRADE, CHOOSE_COURSE_TYPE, DELETE_GRADE = range(4)

ADVANCED_COURSE = 1.5  # the weight of an advanced course


async def start(update: Update, context: CallbackContext) -> int:
    """Starts the conversation with the user."""
    keyboard = [[ # creates inline buttons for the user to choose if he studies an exact sciences degree
        InlineKeyboardButton("כן", callback_data="degree_yes"),
        InlineKeyboardButton("לא", callback_data="degree_no")
    ]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(START_TEXT)
    await update.message.reply_text(EXACT_SCIENCES_QUESTION, reply_markup=reply_markup)
    return ASK_DEGREE



async def ask_degree(update: Update, context: CallbackContext) -> int:
    """Handles the user's response about studying an exact sciences degree."""
    query = update.callback_query
    await query.answer() # acknowledges the user's response

    context.user_data["is_exact_sciences"] = (query.data == "degree_yes")
    context.user_data["grades"] = []  # creates an empty list to store the user's grades

    await query.message.reply_text(GRADE_PROMPT)
    return ENTER_GRADE


async def receive_grade(update: Update, context: CallbackContext) -> int:
    """Receives the user's grade and credits."""
    if update.callback_query: # if the user clicked an inline button
        query = update.callback_query
        await query.answer()
        if query.data == "finished":
            return await calculate_average(update, context)
        elif query.data == "delete":
            await query.message.reply_text(DELETE_GRADE_PROMPT)
            return DELETE_GRADE

    text = update.message.text.strip() # gets the user's grade and credits
    try:
        curr_grade, curr_credit = map(float, text.split())
        if not check_grade_and_credit(curr_grade, curr_credit): # checks if the user's grade and credits are valid
            await update.message.reply_text(GRADE_OR_CREDITS_ERROR)
            return ENTER_GRADE
        context.user_data["curr_grade"] = curr_grade
        context.user_data["curr_credit"] = curr_credit
        if context.user_data["is_exact_sciences"]: # if the user studies an exact sciences degree
            return await choose_course_type(update)

        return await insert_grade_not_exact(update, context) # if the user does not study an exact sciences degree
    except ValueError: # if the user's input is not in the correct format
        await update.message.reply_text(FORMAT_ERROR)
        return ENTER_GRADE


async def choose_course_type(update: Update) -> int:
    """Asks the user if the course is advanced or regular using inline buttons - exact sciences student."""
    keyboard = [[ # creates inline buttons for the user to choose the course type
        InlineKeyboardButton("מתקדם", callback_data="advanced"),
        InlineKeyboardButton("רגיל", callback_data="regular")
    ]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(COURSE_TYPE_QUESTION, reply_markup=reply_markup)
    return CHOOSE_COURSE_TYPE

async def insert_grade_not_exact(update: Update, context: CallbackContext) -> int:
    """Inserts the user's grade and credits - not exact sciences student."""

    # adds the user's grade and credits to the list of grades
    context.user_data["grades"].append((context.user_data["curr_grade"],
                                        context.user_data["curr_credit"],
                                        False))
    grades_typed = get_history(context)
    await update.message.reply_text(ADD_GRADE + grades_typed, reply_markup=delete_or_finish_buttons())
    return ENTER_GRADE

async def receive_course_type(update: Update, context: CallbackContext) -> int:
    """Receives the user's course type from inline buttons - exact sciences student."""
    query = update.callback_query
    await query.answer()

    course_type = query.data  # either "advanced" or "regular"
    curr_grade = context.user_data["curr_grade"]
    curr_credit = context.user_data["curr_credit"]

    context.user_data["grades"].append((curr_grade, curr_credit, (course_type == "advanced")))

    grades_typed = get_history(context)
    await query.message.reply_text(ADD_GRADE + grades_typed, reply_markup=delete_or_finish_buttons())
    return ENTER_GRADE

async def delete_grade(update: Update, context: CallbackContext) -> int:
    """Deletes a grade the user entered by index."""
    text = update.message.text.strip()  # gets the user's index to delete
    try:
        index = int(text)
        if index < 1 or index > len(context.user_data["grades"]): # checks if the index is valid
            await update.message.reply_text(WRONG_INDEX_ERROR)
            return DELETE_GRADE

        context.user_data["grades"].pop(index - 1) # deletes the grade by index
        if len(context.user_data["grades"]) == 0: # if the user deleted all the grades
            await update.message.reply_text(GRADE_PROMPT) # prompts the user to enter a new grade from the beginning
        else:
            grades_typed = get_history(context)
            await update.message.reply_text(ADD_GRADE + grades_typed, reply_markup=delete_or_finish_buttons())
        return ENTER_GRADE
    except ValueError:
        await update.message.reply_text(WRONG_NUMBER_ERROR)
        return DELETE_GRADE


async def calculate_average(update: Update, context: CallbackContext) -> int:
    """Calculates the weighted average of the user's grades."""
    query = update.callback_query
    await query.answer()

    grades = context.user_data["grades"] # gets the user's grades

    if not grades: # if the user did not enter any grades
        await query.message.reply_text(NO_GRADES_ERROR, reply_markup=ReplyKeyboardRemove())
        return await end(query)

    # calculates the total weighted grades
    total_weighted = sum(grade * credits * (ADVANCED_COURSE if is_advanced else 1) for grade, credits, is_advanced in grades)
    # calculates the total credits
    total_credits = sum(credits * (ADVANCED_COURSE if is_advanced else 1) for _, credits, is_advanced in grades)
    print(total_weighted, total_credits)
    weighted_avg = total_weighted / total_credits # calculates the weighted average
    await query.message.reply_text(f"🎓 הממוצע המשוקלל שלך הוא: {weighted_avg:.2f}", reply_markup=ReplyKeyboardRemove())
    return await end(query)

async def end(update: Update) -> int:
    """Ends the conversation with the user."""
    if update.message: # if the user typed /end
        await update.message.reply_text(END_TEXT, reply_markup=ReplyKeyboardRemove())
    else: # if the user clicked the "finished" button
        await update.callback_query.message.reply_text(END_TEXT, reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


# helper functions
def check_grade_and_credit(grade :float, credit :float) -> bool:
    """Checks if the user's input is a valid score."""
    return 60 <= grade <= 100 and 1 <= credit <= 8

def get_history(context: CallbackContext) -> str:
    """Returns the user's grades history."""
    history = "הציונים שהוזנו עד כה:\n"
    for i, (grade, credit, is_advanced) in enumerate(context.user_data["grades"], start=1):
        if context.user_data["is_exact_sciences"]:
            if is_advanced:
                history += f"{i}. ציון: {int(grade)}, נק\"ז: {int(credit)} (מתקדם)\n"
            else:
                history += f"{i}. ציון: {int(grade)}, נק\"ז: {int(credit)} (רגיל)\n"
        else:
            history += f"{i}. ציון: {int(grade)}, נק\"ז: {int(credit)}\n"

    return history

def delete_or_finish_buttons() -> InlineKeyboardMarkup:
    """Creates inline buttons for the user to choose if he finished entering grades or wants to delete a grade."""
    keyboard = [[
        InlineKeyboardButton("סיימתי", callback_data="finished"),
        InlineKeyboardButton("מחק ציון", callback_data="delete")
    ]]
    return InlineKeyboardMarkup(keyboard)


def main():
    """Main function to run the bot."""
    TOKEN = os.getenv("BOT_TOKEN")

    app = Application.builder().token(TOKEN).build()

    # creates a conversation handler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            ASK_DEGREE: [CallbackQueryHandler(ask_degree, pattern="^(degree_yes|degree_no)$")],
            ENTER_GRADE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_grade),
                CallbackQueryHandler(receive_grade, pattern="^finished$"),
                CallbackQueryHandler(receive_grade, pattern="^delete$")
            ],
            CHOOSE_COURSE_TYPE: [CallbackQueryHandler(receive_course_type, pattern="^(advanced|regular)$")],
            DELETE_GRADE: [MessageHandler(filters.TEXT & ~filters.COMMAND, delete_grade)],
        },
        fallbacks=[CommandHandler("end", end)],
    )

    app.add_handler(conv_handler)
    app.run_polling()


if __name__ == '__main__':
    main()
