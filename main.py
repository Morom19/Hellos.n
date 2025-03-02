import telebot
import requests
import json
from datetime import datetime
from time import sleep

BOT_TOKEN = "8120696288:AAHKAmbnqSvIi0-_9m0Shulm7Z0-bMbcvGU"
OWNER_ID = 7661505696
DATA_FILE = "bot_data.json"

bot = telebot.TeleBot(BOT_TOKEN)

def load_data():
    try:
        with open(DATA_FILE, "r") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"allowed_users": [], "allowed_groups": []}

data = load_data()
allowed_users = set(data["allowed_users"])
allowed_groups = set(data["allowed_groups"])

def save_data():
    with open(DATA_FILE, "w") as file:
        json.dump({"allowed_users": list(allowed_users), "allowed_groups": list(allowed_groups)}, file)

def is_authorized(message):
    if message.chat.type in ['group', 'supergroup']:
        return message.chat.id in allowed_groups
    elif message.chat.type == 'private':
        return message.from_user.id == OWNER_ID or message.from_user.id in allowed_users
    return False

def format_timestamp(timestamp):
    try:
        return datetime.utcfromtimestamp(int(timestamp)).strftime('%Y-%m-%d %H:%M:%S')
    except:
        return "N/A"

def get_user_info(uid, region):
    try:
        url = f"https://ariiflexlabs-playerinfo.onrender.com/ff_info?uid={uid}&region={region}"
        response = requests.get(url)
        
        if response.status_code == 200:
            data = response.json()
            account = data.get("AccountInfo", {})
            guild = data.get("GuildInfo", {})
            pet = data.get("petInfo", {})
            social = data.get("socialinfo", {})

            formatted_info = f"""```
📱 ACCOUNT INFO
┌ 👤 Basic Account
├─ Name: {account.get('AccountName', 'N/A')}
├─ UID: {uid}
├─ Level: {account.get('AccountLevel', 'N/A')}
├─ Region: {account.get('AccountRegion', 'N/A')}
├─ Likes: {account.get('AccountLikes', 'N/A')}
├─ Created on: {format_timestamp(account.get('AccountCreateTime', 0))}
└─ Last Login: {format_timestamp(account.get('AccountLastLogin', 0))}

┌ 🎮 Game Stats
├─ Rank: {account.get('BrMaxRank', 'N/A')}
├─ Max Rank: {account.get('CsMaxRank', 'N/A')}
├─ Current Season: {account.get('AccountSeasonId', 'N/A')}
├─ Battle Points: {account.get('BrRankPoint', 'N/A')}
└─ Total Matches: {account.get('CsRankPoint', 'N/A')}

┌ 🛡️ Clan Info
├─ Clan Name: {guild.get('GuildName', 'N/A')}
├─ Clan Level: {guild.get('GuildLevel', 'N/A')}
├─ Members: {guild.get('GuildMember', 'N/A')}
└─ Max Capacity: {guild.get('GuildCapacity', 'N/A')}

┌ 🐾 Pet Info
├─ Name: {pet.get('name', 'N/A')}
├─ Level: {pet.get('level', 'N/A')}
├─ Experience: {pet.get('exp', 'N/A')}
└─ Selected Skill ID: {pet.get('selectedSkillId', 'N/A')}

┌ 🌐 Social Info
├─ Language: {social.get('AccountLanguage', 'N/A')}
├─ Game Mode Preference: {social.get('AccountPreferMode', 'N/A')}
├─ Rank Display: {account.get('ShowBrRank', 'N/A')}
└─ Signature: {social.get('AccountSignature', 'N/A')}```"""
            return formatted_info
        else:
            return "❌ Error: Could not retrieve data from the API."
    except Exception as e:
        return f"❌ Error occurred: {e}"

@bot.message_handler(commands=['ff'])
def fetch_player_info(message):
    if not is_authorized(message):
        bot.reply_to(message, "❌ You are not authorized to use this bot.")
        return
    
    try:
        args = message.text.split()
        if len(args) < 3:
            bot.reply_to(message, "❌ Usage: /ff <region> <uid>")
            return
        
        region, uid = args[1], args[2]

        loading_message = bot.reply_to(message, "⏳ Fetching player info...")

        info = get_user_info(uid, region)

        bot.edit_message_text(info, chat_id=loading_message.chat.id, message_id=loading_message.message_id, parse_mode='Markdown')
        
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {e}")

@bot.message_handler(commands=['start'])
def send_welcome(message):
    if is_authorized(message):
        bot.send_message(
            message.chat.id,
            "🚀 *How to Use Commands:*\n"
            "Simply type any command below followed by the required input.\n\n"
            "🔹 `/ff region <UID>` – Get full details of your account.\n"          
            "🔹 `/check <ID>` – Check if an account is banned.\n"
            "🔹 `/event <region>` – View the latest game events by region.",
            parse_mode="Markdown"
        )
    else:
        bot.reply_to(message, "❌ You are not authorized to use this bot.")
        
@bot.message_handler(commands=['visit'])
def send_visit(message):
    if not is_authorized(message):
        bot.reply_to(message, "❌ You are not authorized to use this command.")
        return

    chat_id = message.chat.id
    user_id = message.from_user.id

    # تقسيم الرسالة والتحقق من وجود المعطيات
    args = message.text.split()
    if len(args) < 3:
        bot.send_message(chat_id, "❌ Use: /visit <region> <UID>", parse_mode="Markdown")
        return

    region = args[1]
    uid = args[2]
    key = "ARIFLEXLABS"

    # إرسال رسالة "⏳ Sending visit..."
    loading_message = bot.reply_to(message, "⏳ Sending visit...")

    # إرسال طلب الـ API
    url = f"https://ariflexlabs.publicvm.com/send_views?uid={uid}&server_name={region}&key={key}"

    try:
        # تحديد مهلة 60 ثانية
        response = requests.get(url, timeout=60)
        response.raise_for_status()  # التحقق من نجاح الطلب
    except requests.exceptions.Timeout:
        bot.edit_message_text("❌ Request timed out. Try again later.", chat_id=loading_message.chat.id, message_id=loading_message.message_id)
        return
    except requests.exceptions.RequestException as e:
        bot.edit_message_text(f"❌ Error: {e}", chat_id=loading_message.chat.id, message_id=loading_message.message_id)
        return

    if response.status_code == 200:
        try:
            data = response.json()
            views_sent = data.get("views_sent", "Unknown")
            remaining_requests = data.get("remaining_requests", "Unknown")

            success_message = f"✅ Visit sent successfully!\n📊 Views Sent: {views_sent}\n🔄 Remaining Requests: {remaining_requests}"
            bot.edit_message_text(success_message, chat_id=loading_message.chat.id, message_id=loading_message.message_id)
        except Exception as e:
            bot.edit_message_text(f"✅ Visit sent, but couldn't parse response.\nError: {e}", chat_id=loading_message.chat.id, message_id=loading_message.message_id)
    else:
        bot.edit_message_text(f"❌ Failed to send visit. Status Code: {response.status_code}\nResponse: {response.text}", chat_id=loading_message.chat.id, message_id=loading_message.message_id)

@bot.message_handler(commands=['event'])
def send_events(message):
    if not is_authorized(message):
        bot.reply_to(message, "❌ You are not authorized to use this bot.")
        return

    region = message.text.split(' ', 1)
    if len(region) < 2:
        bot.send_message(message.chat.id, "❌ Usage: /event <region>")
        return

    region = region[1]
    url = f'https://ff-event-nine.vercel.app/events?region={region}'
    fetching_msg = bot.send_message(message.chat.id, "⏳ Fetching events...")

    response = requests.get(url)

    if response.status_code == 200:
        try:
            events_data = response.json()
            events = events_data.get('events', [])
        except ValueError:
            bot.edit_message_text("🚫 Invalid JSON response.", message.chat.id, fetching_msg.message_id)
            return

        if events:
            media = []
            for event in events:
                image_url = event.get('src', None)
                if image_url:
                    media.append(telebot.types.InputMediaPhoto(image_url))

            batch_size = 10
            for i in range(0, len(media), batch_size):
                bot.send_media_group(message.chat.id, media[i:i + batch_size])

            bot.delete_message(message.chat.id, fetching_msg.message_id)

        else:
            bot.edit_message_text("❌ No events available.", message.chat.id, fetching_msg.message_id)
    else:
        bot.edit_message_text("❌ Error fetching events.", message.chat.id, fetching_msg.message_id)
        
@bot.message_handler(commands=['check'])
def check_ban_status(message):
    if not is_authorized(message):
        bot.reply_to(message, "❌ You are not authorized to use this bot.")
        return

    chat_id = message.chat.id
    args = message.text.split()

    if len(args) < 2:
        bot.send_message(chat_id, "❌ Usage: /check <ACCOUNT_ID>")
        return

    account_id = args[1]
    url = f"https://ffapi-gamma.vercel.app/api/ban_check/{account_id}"

    fetching_msg = bot.send_message(chat_id, "⏳ Checking ban status...")

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        try:
            data = response.json()
            is_banned = data.get("is_banned", 0)
            status_msg = f"💀 Account `{account_id}` is **banned**." if is_banned else f"🗿 Account `{account_id}` is **not banned**."
        except ValueError:
            status_msg = "🚫 Invalid API response format."

    except requests.RequestException as e:
        status_msg = f"❌ API request failed: {e}"

    bot.edit_message_text(status_msg, chat_id, fetching_msg.message_id, parse_mode="Markdown")
        
@bot.message_handler(commands=['add'])
def add_user(message):
    # تجاهل الأمر إذا كان في مجموعة
    if message.chat.type != 'private':
        return  # لا يتم الرد على الإطلاق

    # التحقق من أن المستخدم هو المالك
    if message.from_user.id != OWNER_ID:
        bot.reply_to(message, "❌ أنت لست المالك.")
        return

    try:
        user_id = int(message.text.split()[1])
        if user_id not in allowed_users:
            allowed_users.add(user_id)
            save_data()
            bot.reply_to(message, f"✅ تمت إضافة المستخدم {user_id} بنجاح.")
        else:
            bot.reply_to(message, "❌ هذا المستخدم مصرح له بالفعل.")
    except (IndexError, ValueError):
        bot.reply_to(message, "❌ الرجاء إدخال معرف مستخدم صحيح.")
    except Exception as e:
        bot.reply_to(message, f"❌ حدث خطأ: {e}")

@bot.message_handler(commands=['elim'])
def remove_user(message):
    # تجاهل الأمر إذا كان في مجموعة
    if message.chat.type != 'private':
        return  # لا يتم الرد على الإطلاق

    # التحقق من أن المستخدم هو المالك
    if message.from_user.id != OWNER_ID:
        bot.reply_to(message, "❌ أنت لست المالك.")
        return

    try:
        user_id = int(message.text.split()[1])
        if user_id in allowed_users:
            allowed_users.remove(user_id)
            save_data()
            bot.reply_to(message, f"✅ تمت إزالة المستخدم {user_id} بنجاح.")
        else:
            bot.reply_to(message, "❌ هذا المستخدم غير موجود في القائمة.")
    except (IndexError, ValueError):
        bot.reply_to(message, "❌ الرجاء إدخال معرف مستخدم صحيح.")
    except Exception as e:
        bot.reply_to(message, f"❌ حدث خطأ: {e}")

@bot.message_handler(commands=['users'])
def list_users(message):
    # تجاهل الأمر إذا كان في مجموعة
    if message.chat.type != 'private':
        return  # لا يتم الرد على الإطلاق

    # التحقق من أن المستخدم هو المالك
    if message.from_user.id != OWNER_ID:
        bot.reply_to(message, "❌ أنت لست المالك.")
        return

    if allowed_users:
        users = "\n".join([str(user_id) for user_id in allowed_users])
        bot.reply_to(message, f"👥 المستخدمون المصرح لهم:\n{users}")
    else:
        bot.reply_to(message, "❌ لم تتم إضافة أي مستخدمين بعد.")

@bot.message_handler(commands=['addgroup'])
def add_group(message):
    # تجاهل الأمر إذا كان في مجموعة
    if message.chat.type != 'private':
        return  # لا يتم الرد على الإطلاق

    # التحقق من أن المستخدم هو المالك
    if message.from_user.id != OWNER_ID:
        bot.reply_to(message, "❌ أنت لست المالك.")
        return

    try:
        group_id = int(message.text.split()[1])
        allowed_groups.add(group_id)
        save_data()
        bot.send_message(group_id, "✅ تم تفعيل المجموعة بنجاح.")
        bot.reply_to(message, "✅ تمت إضافة المجموعة بنجاح.")
    except ValueError:
        bot.reply_to(message, "❌ الرجاء إدخال معرف مجموعة صحيح.")
    except Exception as e:
        bot.reply_to(message, f"❌ حدث خطأ: {e}")

@bot.message_handler(commands=['elimgroup'])
def remove_group(message):
    # تجاهل الأمر إذا كان في مجموعة
    if message.chat.type != 'private':
        return  # لا يتم الرد على الإطلاق

    # التحقق من أن المستخدم هو المالك
    if message.from_user.id != OWNER_ID:
        bot.reply_to(message, "❌ أنت لست المالك.")
        return

    try:
        group_id = int(message.text.split()[1])
        if group_id in allowed_groups:
            allowed_groups.remove(group_id)
            save_data()
            bot.reply_to(message, f"✅ تمت إزالة المجموعة {group_id} بنجاح.")
        else:
            bot.reply_to(message, "❌ هذه المجموعة غير موجودة في القائمة.")
    except ValueError:
        bot.reply_to(message, "❌ الرجاء إدخال معرف مجموعة صحيح.")
    except Exception as e:
        bot.reply_to(message, f"❌ حدث خطأ: {e}")

@bot.message_handler(commands=['groups'])
def list_groups(message):
    # تجاهل الأمر إذا كان في مجموعة
    if message.chat.type != 'private':
        return  # لا يتم الرد على الإطلاق

    # التحقق من أن المستخدم هو المالك
    if message.from_user.id != OWNER_ID:
        bot.reply_to(message, "❌ أنت لست المالك.")
        return

    if allowed_groups:
        groups = "\n".join([str(group_id) for group_id in allowed_groups])
        bot.reply_to(message, f"📋 المجموعات المصرح بها:\n{groups}")
    else:
        bot.reply_to(message, "❌ لم تتم إضافة أي مجموعات بعد.")
def main():
    while True:
        try:
            print("Bot started.......")
            bot.infinity_polling()
        except Exception as e:
            print(f"Error occurred: {e}")
            sleep(10)

if __name__ == "__main__":
    main()
