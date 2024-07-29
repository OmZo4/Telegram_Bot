from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
import logging
import os
from datetime import datetime

# Replace 'YOUR_TOKEN_HERE' with your bot's token
TOKEN = 'YOUR_TOKEN_HERE'

# Initialize variables
SCHEDULE = "Today's schedule is not available yet."
PREDICTIONS_FILE = 'predictions.txt'
RESULTS_FILE = 'results.txt'
POINTS_FILE = 'points.txt'
REGISTERED_USERS_FILE = 'registered_users.txt'

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

def load_registered_users():
    registered_users = []
    if not os.path.exists(REGISTERED_USERS_FILE):
        return []
    with open(REGISTERED_USERS_FILE, 'r') as file:
        for line in file:
            user_id = line.strip()
            registered_users.append(int(user_id))
        return  registered_users

REGISTERED_USERS = load_registered_users()

async def euro(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        'Welcome to the EURO 2024 Prediction Bot! '
        'Use /predict to submit your game predictions.\n'
        'Prediction format: /predict <team1> <score1>-<score2> / <team2> <score3>-<score4> / ...\n\n'
        'Example: /predict TeamA 2-1 / TeamB 1-1\n\n'
        'For a list of available commands, use /help.\n\n'
        f'{SCHEDULE}'
    )
    logger.info(f"User {update.message.from_user.userid} started the bot.")

async def predict(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id

    if user_id not in REGISTERED_USERS:
        await update.message.reply_text("You are not authorized to submit predictions. Please register first.")
        logger.warning(f"Unauthorized prediction attempt by {user_id}.")
        return

    # Split the arguments by '/'
    predictions_raw = ' '.join(context.args).split(' / ')

    predictions = []
    for prediction in predictions_raw:
        parts = prediction.split()
        if len(parts) != 2:
            await update.message.reply_text(
                'Incorrect format. Please use: /predict <team1> <score1>-<score2> / <team2> <score3>-<score4> ...\n\n'
                f'{SCHEDULE}'
            )
            return

        team, score = parts
        score1, score2 = score.split('-')

        # Validate that scores are integers
        if not (score1.isdigit() and score2.isdigit()):
            await update.message.reply_text(
                'Invalid scores. Please provide integer values for scores. Format: /predict <team1> <score1>-<score2> / <team2> <score3>-<score4> ...\n\n'
                f'{SCHEDULE}'
            )
            return

        predictions.append(f'{team}: {score1}-{score2}')

    # Check if the user has already made a prediction today
    # if has_already_predicted_today(str(user_id)):
    #     await update.message.reply_text(
    #         'You have already made a prediction today. Please try again tomorrow.\n\n'
    #         f'{SCHEDULE}'
    #     )
    #     user_id
    #     return

    # Save the predictions to a file
    with open(PREDICTIONS_FILE, 'a') as file:
        for prediction in predictions:
            file.write(f'{user_id}: {prediction} on {datetime.now().date()}\n')

    await update.message.reply_text(
        f'Thank you! Your predictions have been recorded:\n' +
        '\n'.join(predictions) +
        f'\n\n{SCHEDULE}'
    )
    logger.info(f"Predictions recorded for user {user_id}: {predictions}")

async def schedule(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(SCHEDULE)
    logger.info(f"User {update.message.from_user.id} requested the schedule.")

async def result(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if len(context.args) != 3:
        await update.message.reply_text('Incorrect format. Please use: /result <team1> <team2> <score1>-<score2>')
        return

    team1, team2, result = context.args
    score1, score2 = result.split('-')

    if not (score1.isdigit() and score2.isdigit()):
        await update.message.reply_text('Invalid scores. Please provide integer values for scores. Format: /result <team1> <team2> <score1>-<score2>')
        return

    match_result = f'{team1} vs {team2}: {score1}-{score2}'

    # Save the result to a file
    with open(RESULTS_FILE, 'a') as file:
        file.write(f'{match_result} on {datetime.now().date()}\n')

    await update.message.reply_text(f'Result recorded: {match_result}')
    logger.info(f"Result recorded: {match_result}")

    # Update points based on the new result
    update_points(team1, team2, int(score1), int(score2))

async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not os.path.exists(POINTS_FILE):
        await update.message.reply_text('No leaderboard available yet.')
        return

    with open(POINTS_FILE, 'r') as file:
        lines = file.readlines()

    if not lines:
        await update.message.reply_text('No leaderboard available yet.')
        return

    leaderboard_text = "Leaderboard:\n"
    for line in lines:
        leaderboard_text += line

    await update.message.reply_text(leaderboard_text)
    logger.info(f"User {update.message.from_user.id} requested the leaderboard.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    help_text = (
        'Available commands:\n'
        '/id - Display your user ID.\n'
        '/euro - Display the welcome message and schedule.\n'
        '/predict - Submit your game predictions. Format: /predict <team1> <score1>-<score2> / <team2> <score3>-<score4> / ...\n'
        '/schedule - Display today\'s matches schedule.\n'
        '/result - Record the results of matches. Format: /result <team1> <team2> <score1>-<score2>\n'
        '/leaderboard - Display the points leaderboard.\n'
        '/register - Register yourself to submit predictions.\n'
        '/help - Display this help message.\n'
    )
    await update.message.reply_text(help_text)
    logger.info(f"User {update.message.from_user.id} requested help.")

async def register(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    if user_id in REGISTERED_USERS:
        await update.message.reply_text("You are already registered.")
        logger.info(f"User {user_id} attempted to register again.")
        return

    with open(REGISTERED_USERS_FILE, 'a') as file:
        file.write(f'{user_id}\n')
        file.flush()

    REGISTERED_USERS.append(user_id)
    await update.message.reply_text("You have been registered successfully.")
    logger.info(f"User {user_id} has been registered.")

def update_points(team1: str, team2: str, score1: int, score2: int) -> None:
    # Read predictions
    if not os.path.exists(PREDICTIONS_FILE):
        return

    with open(PREDICTIONS_FILE, 'r') as file:
        lines = file.readlines()
        print(lines)

    user_points = {}
    if os.path.exists(POINTS_FILE):
        with open(POINTS_FILE, 'r') as file:
            user_points = {line.split(': ')[0]: int(line.split(': ')[1].strip()) for line in file}

    for line in lines:
        parts = line.strip().split(': ')
        if len(parts) < 3:
            continue  # Skip lines that don't have enough parts

        user_id = parts[0]
        team_prediction = parts[1]
        prediction = parts[2]

        # Extract the score part correctly
        score_part = prediction.split(': ')[-1].split(' ')[0]  # Get the first part before " on "
        predicted_score1, predicted_score2 = map(int, score_part.split('-'))

        if team_prediction == team1 or team_prediction == team2:
            points = calculate_points(score1, score2, predicted_score1, predicted_score2)

            if user_id in user_points:
                user_points[user_id] += points
            else:
                user_points[user_id] = points

    with open(POINTS_FILE, 'w') as file:
        for user, points in user_points.items():
            file.write(f'{user}: {points}\n')


def calculate_points(actual_score1: int, actual_score2: int, predicted_score1: int, predicted_score2: int) -> int:
    points = 0
    print("Calculating point")
    if (actual_score1 > actual_score2 and predicted_score1 > predicted_score2) or \
       (actual_score1 < actual_score2 and predicted_score1 < predicted_score2) or \
       (actual_score1 == actual_score2 and predicted_score1 == predicted_score2):
        points += 1  # Correct W/D/L prediction

    if actual_score1 == predicted_score1 and actual_score2 == predicted_score2:
        points += 1  # Correct exact score prediction

    return points

def has_already_predicted_today(user_id: int) -> bool:
    if not os.path.exists(PREDICTIONS_FILE):
        return False

    today_date = datetime.now().date()
    with open(PREDICTIONS_FILE, 'r') as file:
        lines = file.readlines()

    for line in lines:
        if line.startswith(user_id):
            _, date_str = line.rsplit(' on ', 1)
            date = datetime.strptime(date_str.strip(), '%Y-%m-%d').date()
            if date == today_date:
                return True

    return False

async def id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id in REGISTERED_USERS:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f'Your ID is {user_id}')
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="You are not registered.")



if __name__ == '__main__':
        # Create the Application
    SCHEDULE = """
    Today's Matches:
    1. Abdou vs Chedly - 18:00
    2. Omar vs Mohamed - 21:00
    """

    # Ensure predictions and points files exist
    if not os.path.exists(PREDICTIONS_FILE):
        with open(PREDICTIONS_FILE, 'w') as file:
            file.write('')

    if not os.path.exists(POINTS_FILE):
        with open(POINTS_FILE, 'w') as file:
            file.write('')

    if not os.path.exists(REGISTERED_USERS_FILE):
        with open(REGISTERED_USERS_FILE, 'w') as file:
            file.write('')

    application = ApplicationBuilder().token(TOKEN).build()

    # Register the handlers
    application.add_handler(CommandHandler("euro", euro))
    application.add_handler(CommandHandler("id", id))
    application.add_handler(CommandHandler("predict", predict))
    application.add_handler(CommandHandler("schedule", schedule))
    application.add_handler(CommandHandler("result", result))
    application.add_handler(CommandHandler("leaderboard", leaderboard))
    application.add_handler(CommandHandler("register", register))
    application.add_handler(CommandHandler("help", help_command))
    application.run_polling()

