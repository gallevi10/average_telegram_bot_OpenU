# Average Bot - Telegram Bot for GPA Calculation
# Author: Gal Levi
# Date: February 2025
# License: MIT
# Version: 2.0
# Description: This file contains the main logic of the bot.
# This bot helps students from the Open University to calculate their accurate GPA.

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove
from telegram.ext import (Application, CommandHandler, MessageHandler,
                          CallbackQueryHandler, filters, ConversationHandler, CallbackContext)
import logging
import time
from utils import *
from db import *

# logs for debugging
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


async def start(update: Update, context: CallbackContext) -> int:
    """Starts the conversation with the user."""

    user_id = update.message.chat_id  # gets the user's id
    ACTIVE_USERS[user_id] = time.time()  # adds the user to the active users dictionary
    context.user_data["user_id"] = user_id # stores the user's id in the context

    keyboard_change_degree = [[  # creates inline buttons for the user to choose if he studies an exact sciences degree
        InlineKeyboardButton("החלף סוג תואר", callback_data="change_degree"),
    ]]

    reply_markup_change_degree = InlineKeyboardMarkup(keyboard_change_degree)

    # gets if the user studies an exact sciences degree, returns -1 if the user has not chosen yet
    exact_science_indication = get_exact_science(user_id)
    if exact_science_indication != -1:  # if the user has already chosen if he studies an exact sciences degree
        user_logger.info(f"User {user_id} restarted the bot.")
        context.user_data["grades"] = []
        if exact_science_indication == 1:  # if the user studies an exact sciences degree
            await update.message.reply_text(EXACT_ACKNOWLEDGEMENT, reply_markup=reply_markup_change_degree)
        else:
            await update.message.reply_text(NOT_EXACT_ACKNOWLEDGEMENT, reply_markup=reply_markup_change_degree)
        await update.message.reply_text(GRADE_PROMPT, reply_markup=load_grades_buttons())
        return ENTER_GRADE


    user_logger.info(f"User {user_id} started using the bot. Total active users: {len(ACTIVE_USERS)}")

    await update.message.reply_text(START_TEXT) # sends the welcome message
    # asks the user if he studies an exact sciences degree
    await update.message.reply_text(EXACT_SCIENCES_QUESTION, reply_markup=degree_yes_or_no_buttons())
    return ASK_DEGREE


async def ask_degree(update: Update, context: CallbackContext) -> int:
    """Handles the user's response about studying an exact sciences degree."""
    query = update.callback_query
    await query.answer()  # acknowledges the user's response

    is_exact_science = (query.data == "degree_yes") # either True or False
    user_logger.info(f"User {context.user_data['user_id']} successfully chose his degree type.") # logs the user's action
    update_exact_science(context.user_data["user_id"], is_exact_science)  # updates the user's choice in the database
    context.user_data["grades"] = []  # creates an empty list to store the user's grades

    await query.message.reply_text(GRADE_PROMPT, reply_markup=load_grades_buttons()) # prompts the user to enter his grades
    return ENTER_GRADE


async def receive_grade(update: Update, context: CallbackContext) -> int:
    """Receives the user's grade and credits."""
    if update.callback_query:  # if the user clicked an inline button
        query = update.callback_query
        if query.data == "finished": # if the user finished entering grades
            await query.answer(COMPUTING_GRADE)
            return await calculate_average(update, context)
        elif query.data == "delete": # if the user wants to delete a grade
            keyboard = [[
                InlineKeyboardButton("חזור להזנת ציונים", callback_data="go_back"),
            ]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.message.reply_text(DELETE_GRADE_PROMPT, reply_markup=reply_markup)
            await query.answer(WAITING_FOR_INDICES)
            return DELETE_GRADE
        elif query.data == "change_degree": # if the user wants to change his degree type
            user_logger.info(f"User {context.user_data['user_id']} decided to change his degree type.")
            await query.message.reply_text(EXACT_SCIENCES_QUESTION, reply_markup=degree_yes_or_no_buttons())
            await query.answer(WAITING_FOR_DEGREE_TYPE)
            return ASK_DEGREE
        elif query.data == "load_last_grades" or "load_saved_grades": # if the user wants to load his grades
            if query.data == "load_last_grades":
                loaded = get_last_grades(context.user_data["user_id"]) # loads the user's last grades
            else:
                loaded = get_saved_grades(context.user_data["user_id"]) # loads the user's saved grades
            if loaded: # if the user has grades saved
                context.user_data["grades"] += loaded
                await query.answer(SUCCESSFULLY_LOADED_GRADES) # lets the user know the grades were loaded successfully
                grades_typed = get_history(context)
                await query.message.reply_text(ADD_GRADE + grades_typed, reply_markup=add_grades_buttons())
                user_logger.info(f"User {context.user_data['user_id']} loaded his grades successfully.")
            else: # if the user does not have last grades
                await query.message.reply_text(LOAD_GRADES_ERROR)
                user_logger.info(f"User {context.user_data['user_id']} tried to load grades but has none.")
            return ENTER_GRADE

    text = update.message.text.strip()  # gets the user's grade and credits
    try:
        context.user_data["curr_grades"] = get_grades_input(text)  # parses the user's input into a list of grades
        if not check_grade_and_credit(context.user_data["curr_grades"]):  # checks if the user's grade and credits are valid
            await update.message.reply_text(GRADE_OR_CREDITS_ERROR)
            user_logger.info(f"User {context.user_data['user_id']} entered grades or credits out of range.")
            return ENTER_GRADE
        user_logger.info(f"User {context.user_data['user_id']} entered grades successfully.")
        return await choose_course_type(update, context) # asks the user if the courses are advanced or regular
    except ValueError:  # if the user's input is not in the correct format
        await update.message.reply_text(FORMAT_ERROR)
        user_logger.info(f"User {context.user_data['user_id']} entered grades in the wrong format.")
        return ENTER_GRADE


async def choose_course_type(update: Update, context: CallbackContext) -> int:
    """Asks the user if the course is advanced or regular using inline buttons - exact sciences student."""

    if len(context.user_data["curr_grades"]) == 1:  # if the user entered more than one grade
        keyboard = [[  # creates inline buttons for the user to choose the course type
            InlineKeyboardButton("מתקדם", callback_data="advanced"),
            InlineKeyboardButton("רגיל", callback_data="regular")
        ]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(COURSE_TYPE_QUESTION_SHORT, reply_markup=reply_markup)
    else:  # if the user entered only one grade
        keyboard = [[  # creates inline buttons for the user to choose the course type
            InlineKeyboardButton("מתקדמים", callback_data="advanced"),
            InlineKeyboardButton("רגילים", callback_data="regular")
        ]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(COURSE_TYPE_QUESTION_LONG, reply_markup=reply_markup)

    return CHOOSE_COURSE_TYPE


async def receive_course_type(update: Update, context: CallbackContext) -> int:
    """Receives the user's course type from inline buttons - exact sciences student."""
    query = update.callback_query
    await query.answer(SUCCESSFULLY_ADDED_GRADES) # acknowledges the user's response

    course_type = query.data  # either "advanced" or "regular"
    user_logger.info(f"User {context.user_data['user_id']} chose the courses type successfully.")

    context.user_data["grades"] += [(grade, credit, course_type == "advanced") for grade, credit in context.user_data["curr_grades"]]

    grades_typed = get_history(context)
    await query.message.reply_text(ADD_GRADE + grades_typed, reply_markup=add_grades_buttons())
    return ENTER_GRADE


async def delete_grade(update: Update, context: CallbackContext) -> int:
    """Deletes a grade the user entered by index."""
    if update.callback_query:  # if the user clicked an inline button
        query = update.callback_query
        if query.data == "go_back":
            user_logger.info(f"User {context.user_data['user_id']} decided to go back to entering grades.")
            await query.answer(GOING_BACK_TO_GRADES_INPUT)
            grades_typed = get_history(context)
            await query.message.reply_text(ADD_GRADE + grades_typed, reply_markup=add_grades_buttons())
            return ENTER_GRADE

    text = update.message.text.strip()  # gets the user's index to delete
    try:
        indices = list(map(int, text.split()))  # parses the user's input into a list of indices
        # checks if the user entered indices that are not exist
        wrong_indices = [index for index in indices if index < 1 or index > len(context.user_data["grades"])]
        if wrong_indices:  # if the list of wrong indices is not empty
            await update.message.reply_text("❌ האינדקסים הבאים לא תואמים לאף ציון:"
                                            "\n" + " ".join(map(str, wrong_indices))
                                            + "\n"
                                            "אנא הכנס אינדקסים בטווח 1-" + str(len(context.user_data["grades"])))
            user_logger.info(f"User {context.user_data['user_id']} entered not matching index.")
            return DELETE_GRADE

        ind_set = set(indices) # creates a set of the indices to check for duplicates
        if len(ind_set) != len(indices):  # checks if the user entered the same index more than once
            await update.message.reply_text(DUPLICATE_INDICES_ERROR)
            return DELETE_GRADE # asks the user to enter the indices again

        indices.sort(reverse=True)  # sorts the indices in reverse order in order to delete them correctly
        for index in indices:  # iterates over the user's indices after validation
            context.user_data["grades"].pop(index - 1)  # deletes the grade by index

        user_logger.info(f"User {context.user_data['user_id']} deleted grades successfully.")
        await update.message.reply_text(SUCCESSFULLY_DELETED_GRADE)
        if len(context.user_data["grades"]) == 0:  # if the user deleted all the grades
            # prompts the user to enter a new grade from the beginning
            await update.message.reply_text(GRADE_PROMPT, reply_markup=load_grades_buttons())
        else:
            grades_typed = get_history(context)
            await update.message.reply_text(ADD_GRADE + grades_typed, reply_markup=add_grades_buttons())
        return ENTER_GRADE
    except ValueError:
        await update.message.reply_text(WRONG_NUMBER_ERROR)
        user_logger.info(f"User {context.user_data['user_id']} entered non-numeric index.")
        return DELETE_GRADE


async def calculate_average(update: Update, context: CallbackContext) -> int:
    """Calculates the weighted average of the user's grades."""
    query = update.callback_query
    await query.answer()
    user_id = context.user_data["user_id"]

    grades = context.user_data["grades"]  # gets the user's grades
    is_exact = get_exact_science(user_id)  # gets if the user studies an exact sciences degree

    # calculates the total weighted grades
    total_weighted = sum(grade * credits * (ADVANCED_COURSE if is_exact and is_advanced else 1) for grade, credits, is_advanced in grades)
    # calculates the total credits
    total_credits = sum(credits * (ADVANCED_COURSE if is_exact and is_advanced else 1) for _, credits, is_advanced in grades)
    weighted_avg = total_weighted / total_credits  # calculates the weighted average

    await query.message.reply_text(f"🎓 הממוצע המשוקלל שלך הוא: {weighted_avg:.2f}", reply_markup=ReplyKeyboardRemove())
    user_logger.info(f"User {user_id} calculated his average successfully.") # logs the user's action

    update_last_grades(user_id, grades)  # updates the user's last grades in the database

    saved_grades = get_saved_grades(user_id)
    if saved_grades == grades:  # if the current grades are already in the database
        return await end(query, context)

    # asks the user if he wants to save his current grades
    keyboard = [[
        InlineKeyboardButton("אין צורך", callback_data="dont_save_grades"),
        InlineKeyboardButton("כן", callback_data="save_grades"),
    ]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    if not saved_grades:  # if the user does not have saved grades
        await query.message.reply_text(NOT_EXISTS_SAVED_GRADES_PROMPT, reply_markup=reply_markup)
    else:  # if the user has saved grades
        await query.message.reply_text(EXISTS_SAVED_GRADES_PROMPT, reply_markup=reply_markup)
    return SAVE_GRADES

async def save_grades_button_handler(update: Update, context: CallbackContext) -> int:
    """Handles the user's choice to save his grades."""
    query = update.callback_query
    if query.data == "save_grades":  # if the user wants to save his grades
        user_logger.info(f"User {context.user_data['user_id']} chose to save his grades.")
        user_id = context.user_data["user_id"]
        grades = context.user_data["grades"]
        update_saved_grades(user_id, grades)  # saves the user's grades in the database
        await query.answer(SUCCESSFULLY_SAVED_GRADES)
    else:
        user_logger.info(f"User {context.user_data['user_id']} chose not to save his grades.")
        await query.answer(SUCCESSFULLY_NOT_SAVED_GRADES)

    return await end(query, context)

async def end(update: Update, context: CallbackContext) -> int:
    """Ends the conversation with the user."""
    if update.message:  # if the user typed /end
        await update.message.reply_text(END_TEXT, reply_markup=ReplyKeyboardRemove())
    else:  # if the user clicked the "finished" button
        await update.callback_query.message.reply_text(END_TEXT, reply_markup=ReplyKeyboardRemove())

    user_id = context.user_data["user_id"]
    if user_id in ACTIVE_USERS:  # removes the user from the active users dictionary
        del ACTIVE_USERS[user_id]

    user_logger.info(f"User {user_id} exited the bot. Total active users: {len(ACTIVE_USERS)}")
    return ConversationHandler.END  # ends the conversation

async def unknown_command_handler(update: Update, context: CallbackContext) -> None:
    """Handles unknown commands."""
    await update.message.reply_text(UNKNOWN_COMMAND)
    user_logger.info(f"User {update.message.chat_id} entered an unknown command.")

async def unknown_text_before_start_handler(update: Update, context: CallbackContext) -> None:
    """Handles text before starting the conversation."""
    await update.message.reply_text(UNKNOWN_TEXT_BEFORE_START)
    user_logger.info(f"User {update.message.chat_id} entered text before starting the conversation.")


def main():
    """Main function to run the bot."""
    app = Application.builder().token(TOKEN).build()
    setup_database() # creates the database if it does not exist

    # creates a conversation handler
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("start", start), # starts the conversation
            MessageHandler(filters.COMMAND, unknown_command_handler), # handles unknown commands
            MessageHandler(filters.TEXT, unknown_text_before_start_handler), # handles text before starting
        ],
        states={
            # state to ask the user if he studies an exact sciences degree
            ASK_DEGREE: [CallbackQueryHandler(ask_degree, pattern="^(degree_yes|degree_no)$")],
            ENTER_GRADE: [ # state to enter the user's grades
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_grade),
                CallbackQueryHandler(receive_grade, pattern="^finished$"),
                CallbackQueryHandler(receive_grade, pattern="^delete$"),
                CallbackQueryHandler(receive_grade, pattern="^change_degree$"),
                CallbackQueryHandler(receive_grade, pattern="^load_last_grades$"),
                CallbackQueryHandler(receive_grade, pattern="^load_saved_grades$"),
            ],
            # state to choose the course type
            CHOOSE_COURSE_TYPE: [CallbackQueryHandler(receive_course_type, pattern="^(advanced|regular)$")],
            SAVE_GRADES: [ # state to save the user's grades
                CallbackQueryHandler(save_grades_button_handler, pattern="^save_grades$"),
                CallbackQueryHandler(save_grades_button_handler, pattern="^dont_save_grades$")
            ],
            DELETE_GRADE: [ # state to delete a grade
                MessageHandler(filters.TEXT & ~filters.COMMAND, delete_grade),
                CallbackQueryHandler(delete_grade, pattern="^go_back$"),
                CallbackQueryHandler(receive_grade, pattern="^finished$") # if the user regrets and wants to finish
            ],
        },
        fallbacks=[
            CommandHandler("end", end), # ends the conversation
            CommandHandler("start", start), # starts the conversation from any state
            MessageHandler(filters.COMMAND, unknown_command_handler), # handles unknown commands
        ]
    )

    app.add_handler(conv_handler)
    app.run_polling()


if __name__ == '__main__':
    main()