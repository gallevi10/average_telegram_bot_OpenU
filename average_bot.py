# Average Bot - Telegram Bot for GPA Calculation
# Author: Gal Levi
# Date: May 2025
# License: MIT
# Version: 3.0
# Description: This file contains the main logic for the bot.
# This bot helps students from the Open University to calculate their accurate GPA.

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove
from telegram.ext import (Application, CommandHandler, MessageHandler,
                          CallbackQueryHandler, filters, ConversationHandler, CallbackContext)
import time
from utils import *
from db import *


async def start(update: Update, context: CallbackContext) -> int:
    """Starts the conversation with the user."""
    user_id = update.message.chat_id  # gets the user's id
    # gets if the user studies an exact sciences degree, returns -1 if the user has not chosen yet
    exact_science_indication = await get_exact_science(user_id)
    # if the user restarted the bot before picking a degree type for the first time
    if user_id in ACTIVE_USERS and exact_science_indication == -1:
        log_user(user_id, "restarted the bot before picking a degree type for the first time.")
        await update.message.reply_text(EXACT_SCIENCES_QUESTION, reply_markup=degree_yes_or_no_buttons())
        return ASK_DEGREE

    keyboard_change_degree = [[  # creates inline buttons for the user to choose if he studies an exact sciences degree
        InlineKeyboardButton("החלף סוג תואר", callback_data="change_degree"),
    ]]

    reply_markup_change_degree = InlineKeyboardMarkup(keyboard_change_degree)

    if exact_science_indication != -1:  # if the user has already chosen if he studies an exact sciences degree
        if user_id in ACTIVE_USERS:  # if the user restarted the bot before finishing
            ACTIVE_USERS[user_id] = time.time() # updates the user's last active time
            log_user_and_active_users(user_id, "restarted the bot before finishing the conversation")
        else:  # if the user finished the last conversation
            ACTIVE_USERS[user_id] = time.time() # adds the user to the active users dictionary
            log_user_and_active_users(user_id, "restarted the bot")
            context.user_data["user_id"] = user_id  # stores the user's id in the context
        context.user_data["grades"] = []
        if exact_science_indication == 1:  # if the user studies an exact sciences degree
            await update.message.reply_text(EXACT_ACKNOWLEDGEMENT, reply_markup=reply_markup_change_degree)
        else:
            await update.message.reply_text(NOT_EXACT_ACKNOWLEDGEMENT, reply_markup=reply_markup_change_degree)
        await update.message.reply_text(GRADE_PROMPT, reply_markup=load_grades_buttons())
        return ENTER_GRADE

    ACTIVE_USERS[user_id] = time.time() # adds the user to the active users dictionary
    context.user_data["user_id"] = user_id # stores the user's id in the context
    log_user_and_active_users(user_id, "started the bot")
    await update.message.reply_text(START_TEXT) # sends the welcome message
    # asks the user if he studies an exact sciences degree
    await update.message.reply_text(EXACT_SCIENCES_QUESTION, reply_markup=degree_yes_or_no_buttons())
    return ASK_DEGREE


async def ask_degree(update: Update, context: CallbackContext) -> int:
    """Handles the user's response about studying an exact sciences degree."""
    query = update.callback_query
    await query.answer()  # acknowledges the user's response

    is_exact_science = (query.data == "degree_yes") # either True or False
    log_user(context.user_data["user_id"], "successfully chose his degree type")
    await update_exact_science(context.user_data["user_id"], is_exact_science)  # updates the user's choice in the database
    context.user_data["grades"] = []  # creates an empty list to store the user's grades

    await query.message.reply_text(GRADE_PROMPT, reply_markup=load_grades_buttons()) # prompts the user to enter his grades
    return ENTER_GRADE


async def receive_grade(update: Update, context: CallbackContext) -> int:
    """Receives the user's grade and credits."""
    if update.callback_query:  # if the user clicked an inline button
        query = update.callback_query
        if query.data == "finished": # if the user finished entering grades
            if not context.user_data["grades"]: # if the user did not enter any grades
                await query.answer()
                await query.message.reply_text(NO_GRADES_ENTERED_FINISHED_PRESSED)
                log_user(context.user_data["user_id"], "tried to finish without entering grades")
                return ENTER_GRADE
            await query.answer(COMPUTING_GRADE)
            return await calculate_average(update, context)
        elif query.data == "delete": # if the user wants to delete a grade
            if not context.user_data["grades"]:
                await query.answer()
                await query.message.reply_text(NO_GRADES_ENTERED_DELETE_PRESSED)
                log_user(context.user_data["user_id"], "tried to delete grades without entering any")
                return ENTER_GRADE
            keyboard = [[
                InlineKeyboardButton("חזור להזנת ציונים", callback_data="go_back"),
            ]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.message.reply_text(DELETE_GRADE_PROMPT, reply_markup=reply_markup)
            await query.answer(WAITING_FOR_INDICES)
            return DELETE_GRADE
        elif query.data == "change_degree": # if the user wants to change his degree type
            log_user(context.user_data["user_id"], "decided to change his degree type")
            await query.message.reply_text(EXACT_SCIENCES_QUESTION, reply_markup=degree_yes_or_no_buttons())
            await query.answer(WAITING_FOR_DEGREE_TYPE)
            return ASK_DEGREE
        elif query.data in ["load_last_grades", "load_saved_grades"]: # if the user wants to load his grades
            if query.data == "load_last_grades":
                loaded = await get_last_grades(context.user_data["user_id"]) # loads the user's last grades
                log_user(context.user_data["user_id"], "tried to load his last grades")
            else:
                loaded = await get_saved_grades(context.user_data["user_id"]) # loads the user's saved grades
                log_user(context.user_data["user_id"], "tried to load his saved grades")
            if loaded: # if the user has grades saved
                context.user_data["grades"] += loaded
                await query.answer(SUCCESSFULLY_LOADED_GRADES) # lets the user know the grades were loaded successfully
                grades_typed = get_history(context)
                await query.message.reply_text(ADD_GRADE + grades_typed, reply_markup=add_grades_buttons())
                log_user(context.user_data["user_id"], "loaded his grades successfully")
            else: # if the user does not have last grades
                await query.message.reply_text(LOAD_GRADES_ERROR)
                log_user(context.user_data["user_id"], "tried to load grades but has none")
            return ENTER_GRADE

    text = update.message.text.strip()  # gets the user's input
    try:
        context.user_data["curr_grades"] = get_grades_input(text)  # parses the user's input into a list of grades
        valid_indicator = check_input(context.user_data["curr_grades"]) # valid indicator is 1 if the input is valid
        if valid_indicator < 1:  # if user's input is invalid
            if valid_indicator == 0:  # if the user entered a grade that is not in the range
                await update.message.reply_text(GRADE_OR_CREDITS_RANGE_ERROR)
                log_user(context.user_data["user_id"], "entered grades or credits out of range")
            elif valid_indicator == -1:  # if the user entered a grade or credit that is not an integer
                await update.message.reply_text(GRADE_OR_CREDITS_INTEGER_ERROR)
                log_user(context.user_data["user_id"], "entered non-integer grades")
            else: # if the user entered a description that is too long
                await update.message.reply_text(WRONG_DESC_LENGTH_ERROR)
                log_user(context.user_data["user_id"], "entered a too long description")
            return ENTER_GRADE
        log_user(context.user_data["user_id"], "entered grades successfully")
        return await choose_course_type(update, context) # asks the user if the courses are advanced or regular
    except ValueError:  # if the user's input is not in the correct format
        await update.message.reply_text(FORMAT_ERROR)
        log_user(context.user_data["user_id"], "entered grades in the wrong format")
        return ENTER_GRADE


async def choose_course_type(update: Update, context: CallbackContext) -> int:
    """Asks the user if the course is advanced or regular using inline buttons - exact sciences student."""

    advanced = "מתקדם"
    regular = "רגיל"
    msg = COURSE_TYPE_QUESTION_SHORT
    if len(context.user_data["curr_grades"]) > 1: # if the user entered more than one grade
        advanced = "מתקדמים"
        regular = "רגילים"
        msg = COURSE_TYPE_QUESTION_LONG

    # creates inline buttons for the user to choose the course type
    keyboard = [[  # creates inline buttons for the user to choose the course type
        InlineKeyboardButton(advanced, callback_data="advanced"),
        InlineKeyboardButton(regular, callback_data="regular")
    ]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(msg, reply_markup=reply_markup)

    return CHOOSE_COURSE_TYPE


async def receive_course_type(update: Update, context: CallbackContext) -> int:
    """Receives the user's course type from inline buttons - exact sciences student."""
    query = update.callback_query
    await query.answer(SUCCESSFULLY_ADDED_GRADES) # acknowledges the user's response

    course_type = query.data  # either "advanced" or "regular"
    log_user(context.user_data["user_id"], "chose the courses type successfully")
    context.user_data["grades"] += [(desc, grade, credit, course_type == "advanced")
                                    for desc, grade, credit in context.user_data["curr_grades"]]

    grades_typed = get_history(context)
    await query.message.reply_text(ADD_GRADE + grades_typed, reply_markup=add_grades_buttons())
    return ENTER_GRADE


async def delete_grade(update: Update, context: CallbackContext) -> int:
    """Deletes a grade the user entered by index."""
    if update.callback_query:  # if the user clicked an inline button
        query = update.callback_query
        if query.data == "go_back":
            log_user(context.user_data["user_id"], "decided to go back to entering grades")
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
                                            +"\n"
                                            "אנא הכנס אינדקסים בטווח 1-" + str(len(context.user_data["grades"])))
            log_user(context.user_data["user_id"], "entered not matching indices")
            return DELETE_GRADE

        ind_set = set(indices) # creates a set of the indices to check for duplicates
        if len(ind_set) != len(indices):  # checks if the user entered the same index more than once
            await update.message.reply_text(DUPLICATE_INDICES_ERROR)
            log_user(context.user_data["user_id"], "entered duplicate indices")
            return DELETE_GRADE # asks the user to enter the indices again

        indices.sort(reverse=True)  # sorts the indices in reverse order in order to delete them correctly
        for index in indices:  # iterates over the user's indices after validation
            context.user_data["grades"].pop(index - 1)  # deletes the grade by index

        log_user(context.user_data["user_id"], "deleted grades successfully")
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
        log_user(context.user_data["user_id"], "entered non-numeric index")
        return DELETE_GRADE


async def calculate_average(update: Update, context: CallbackContext) -> int:
    """Calculates the weighted average of the user's grades."""
    query = update.callback_query
    await query.answer()

    user_id = context.user_data["user_id"]
    grades = context.user_data["grades"]  # gets the user's grades
    is_exact = await get_exact_science(user_id)  # gets if the user studies an exact sciences degree

    # calculates the total weighted grades
    total_weighted = sum(grade * credits * (ADVANCED_COURSE if is_exact and is_advanced else 1) for _, grade, credits, is_advanced in grades)
    # calculates the total credits
    total_credits = sum(credits * (ADVANCED_COURSE if is_exact and is_advanced else 1) for _, _, credits, is_advanced in grades)
    weighted_avg = total_weighted / total_credits  # calculates the weighted average

    await query.message.reply_text(f"🎓 הממוצע המשוקלל שלך הוא: {weighted_avg:.2f}", reply_markup=ReplyKeyboardRemove())
    log_user(user_id, "calculated his average successfully")

    await update_last_grades(user_id, grades)  # updates the user's last grades in the database

    saved_grades = await get_saved_grades(user_id)
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
    else:
        await query.message.reply_text(EXISTS_SAVED_GRADES_PROMPT, reply_markup=reply_markup)
    return SAVE_GRADES

async def save_grades(update: Update, context: CallbackContext) -> int:
    """Handles the user's choice to save his grades."""
    query = update.callback_query
    user_id = context.user_data["user_id"]
    if query.data == "save_grades":  # if the user wants to save his grades
        grades = context.user_data["grades"]
        log_user(user_id, "chose to save his grades")
        await update_saved_grades(user_id, grades)  # saves the user's grades in the database
        await query.answer(SUCCESSFULLY_SAVED_GRADES)
    else:
        log_user(user_id, "chose not to save his grades")
        await query.answer(SUCCESSFULLY_NOT_SAVED_GRADES)

    return await end(query, context)

async def end(update: Update, context: CallbackContext) -> int:
    """Ends the conversation with the user."""
    if update.message:  # if the user typed /end or /feedback
        user_id = update.message.chat_id
        await update.message.reply_text(END_TEXT, reply_markup=ReplyKeyboardRemove())
    else:  # if the user clicked the "finished" button
        user_id = update.callback_query.message.chat_id
        await update.callback_query.message.reply_text(END_TEXT, reply_markup=ReplyKeyboardRemove())


    if user_id in ACTIVE_USERS:  # removes the user from the active users dictionary
        del ACTIVE_USERS[user_id]

    log_user_and_active_users(user_id, "exited the bot")
    return ConversationHandler.END  # ends the conversation


# handlers for the conversation states
async def unknown_command_handler(update: Update, context: CallbackContext) -> None:
    """Handles unknown commands."""
    await update.message.reply_text(UNKNOWN_COMMAND)
    log_user(update.message.chat_id, "entered an unknown command")

async def unknown_text_before_start_handler(update: Update, context: CallbackContext) -> None:
    """Handles text before starting the conversation."""
    await update.message.reply_text(UNKNOWN_TEXT_BEFORE_START)
    log_user(update.message.chat_id, "entered text before starting the conversation")

async def unknown_text_in_degree_state_handler(update: Update, context: CallbackContext) -> None:
    """Handles text in the degree state."""
    await update.message.reply_text(UNKNOWN_TEXT_IN_DEGREE_STATE)
    log_user(update.message.chat_id, "entered text in the degree state")


async def unknown_text_in_course_type_state_handler(update: Update, context: CallbackContext) -> None:
    """Handles text in the course type state."""
    await update.message.reply_text(UNKNOWN_TEXT_IN_COURSE_TYPE_STATE)
    log_user(update.message.chat_id, "entered text in the course type state")

async def unknown_text_in_save_grades_state_handler(update: Update, context: CallbackContext) -> None:
    """Handles text in the save grades state."""
    await update.message.reply_text(UNKNOWN_TEXT_IN_SAVE_GRADES_STATE)
    log_user(update.message.chat_id, "entered text in the save grades state")


async def start_broadcast_process(update: Update, context: CallbackContext) -> int:
    """Handles the admin's request to write a broadcast message."""
    user_id = update.message.chat_id
    log_user(user_id, "tried to write broadcast message")
    await update.message.reply_text(BROADCAST_MSG)
    return WRITE_BROADCAST_MSG

async def start_single_process(update: Update, context: CallbackContext) -> int:
    """Handles the admin's request to write a single message to a specific user."""
    user_id = update.message.chat_id
    log_user(user_id, "tried to write single message")
    await update.message.reply_text(ASK_ID_FOR_PRIVATE_MSG)
    return GET_ID_FOR_PRIVATE_MESSAGE

async def get_id_for_single_msg_handler(update: Update, context: CallbackContext) -> int:
    """Handles the admin's request to write a single message to a specific user."""
    user_id = update.message.chat_id
    try:
        target_user_id = int(update.message.text.strip())  # gets the user's id
        if not await user_exists(target_user_id):
            await update.message.reply_text(ID_NOT_FOUND_ERROR)
            log_user(user_id, "tried to send a message to a user that does not exist")
            return GET_ID_FOR_PRIVATE_MESSAGE
        context.user_data["target_user_id"] = target_user_id  # stores the user's id in the context
        await update.message.reply_text(PRIVATE_MSG)
        return WRITE_PRIVATE_MSG
    except ValueError:
        await update.message.reply_text(WRONG_ID_ERROR)
        return GET_ID_FOR_PRIVATE_MESSAGE

async def single_message_handler(update: Update, context: CallbackContext) -> None:
    """Handles the single message to a specific user."""
    user_id = update.message.chat_id
    target_user_id = context.user_data["target_user_id"]  # gets the target user's id
    private_message = update.message.text.strip()  # gets the admin's private message
    log_user(user_id, f"wrote a private message to user {target_user_id}: {private_message}")
    await send_single_message(target_user_id, private_message)  # sends the private message to the user
    await update.message.reply_text(SINGLE_ACKNOWLEDGEMENT)

async def broadcast_handler(update: Update, context: CallbackContext) -> None:
    """Handles the broadcast message."""
    user_id = update.message.chat_id
    broadcast_message = update.message.text.strip()  # gets the admin broadcast message
    log_user(user_id, f"wrote the broadcast message: {broadcast_message}")
    successfully_sent = await send_broadcast_message(broadcast_message)  # sends the broadcast message to all users
    await update.message.reply_text(f"✅ ההודעה נשלחה בהצלחה ל-{successfully_sent} משתמשים.")

async def start_feedback_process(update: Update, context: CallbackContext) -> int:
    """Handles the user's request to write feedback."""
    user_id = update.message.chat_id
    log_user(user_id, "started writing a feedback")
    keyboard = [[
        InlineKeyboardButton("אני לא מעוניין לכתוב פידבק", callback_data="exit_feedback"),
    ]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(FEEDBACK_MSG, reply_markup=reply_markup)
    return WRITE_FEEDBACK

async def feedback_handler(update: Update, context: CallbackContext) -> int:
    """Handles the user's feedback."""
    query = update.callback_query
    if query and query.data == "exit_feedback": # if the user does not want to write feedback
        user_id = query.message.chat_id
        await query.answer()
        await query.message.reply_text(FEEDBACK_EXIT)
        log_user(user_id, "exited the feedback process")
    else:
        user_id = update.message.chat_id
        feedback = update.message.text.strip()  # gets the user's feedback
        log_user(user_id, f"wrote a feedback")
        feedback_logger.info(f"User {user_id} wrote the feedback: {feedback}")
        await update.message.reply_text(FEEDBACK_ACKNOWLEDGEMENT)
    return await end(update, context)  # ends the conversation

def main():
    """Main function to run the bot."""
    app = Application.builder().token(TOKEN).build()
    setup_database() # creates the database if it does not exist

    # creates a conversation handler
    common_commands_and_unknown_command_handling = [
        CommandHandler("start", start),
        CommandHandler("feedback", start_feedback_process),
        CommandHandler("broadcast", start_broadcast_process, filters=filters.User(user_id=ADMIN_ID)),
        CommandHandler("single", start_single_process, filters=filters.User(user_id=ADMIN_ID)),
        MessageHandler(filters.COMMAND, unknown_command_handler),
    ]
    conv_handler = ConversationHandler(
        entry_points=common_commands_and_unknown_command_handling + [
            MessageHandler(filters.TEXT, unknown_text_before_start_handler), # handles text before starting
        ],
        states={
            # state to ask the user if he studies an exact sciences degree
            ASK_DEGREE: [
                CallbackQueryHandler(ask_degree, pattern="^(degree_yes|degree_no)$"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, unknown_text_in_degree_state_handler),
            ],
            ENTER_GRADE: [ # state to enter the user's grades
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_grade),
                CallbackQueryHandler(receive_grade, pattern="^finished$"),
                CallbackQueryHandler(receive_grade, pattern="^delete$"),
                CallbackQueryHandler(receive_grade, pattern="^change_degree$"),
                CallbackQueryHandler(receive_grade, pattern="^load_last_grades$"),
                CallbackQueryHandler(receive_grade, pattern="^load_saved_grades$"),
            ],
            # state to choose the course type
            CHOOSE_COURSE_TYPE: [
                CallbackQueryHandler(receive_course_type, pattern="^(advanced|regular)$"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, unknown_text_in_course_type_state_handler),
            ],
            SAVE_GRADES: [ # state to save the user's grades
                CallbackQueryHandler(save_grades, pattern="^save_grades$"),
                CallbackQueryHandler(save_grades, pattern="^dont_save_grades$"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, unknown_text_in_save_grades_state_handler),
            ],
            DELETE_GRADE: [ # state to delete a grade
                MessageHandler(filters.TEXT & ~filters.COMMAND, delete_grade),
                CallbackQueryHandler(delete_grade, pattern="^go_back$"),
                CallbackQueryHandler(receive_grade, pattern="^finished$") # if the user regrets and wants to finish
            ],
            WRITE_FEEDBACK: [ # state to write feedback
                MessageHandler(filters.TEXT & ~filters.COMMAND, feedback_handler),
                CallbackQueryHandler(feedback_handler, pattern="^exit_feedback$"),
            ],
            WRITE_BROADCAST_MSG: [ # state to write a broadcast message
                MessageHandler(filters.TEXT & ~filters.COMMAND, broadcast_handler),
            ],
            GET_ID_FOR_PRIVATE_MESSAGE: [ # state to get the user's id for a private message
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_id_for_single_msg_handler),
            ],
            WRITE_PRIVATE_MSG: [ # state to write a private message
                MessageHandler(filters.TEXT & ~filters.COMMAND, single_message_handler),
            ],
        },
        fallbacks=[
            CommandHandler("end", end), # ends the conversation
        ] + common_commands_and_unknown_command_handling
    )

    app.add_handler(conv_handler)
    app.run_polling()


if __name__ == '__main__':
    main()