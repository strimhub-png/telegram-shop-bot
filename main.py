import telebot
from telebot import types
import urllib.parse

# બોટ અને એડમિન સેટિંગ્સ
API_TOKEN = '8630081492:AAGUD27F5mIgE6GB-TlfLOfQFDQaLFohtZw'
bot = telebot.TeleBot(API_TOKEN)

ADMIN_UPI_ID = "chintanlimbachiya491-1@okicici"
ADMIN_ID = 5714243957  # તમારી Telegram ID

products = {}
orders = {}
user_states = {}

# /start કમાન્ડ
@bot.message_handler(commands=['start'])
def start_command(message):
    user_id = message.from_user.id
    args = message.text.split()

    # જો લિંક પર ક્લિક કરીને પ્રોડક્ટ જોવા આવ્યા હોય
    if len(args) > 1:
        prod_id = args[1]
        if prod_id in products:
            prod = products[prod_id]
            caption = (
                f"📦 **{prod['name']}**\n\n"
                f"💰 **કિંમત:** ₹{prod['price']}\n"
                f"🛡️ **100% Instant Delivery**\n\n"
                f"👉 નીચેનો QR કોડ સ્કેન કરીને ₹{prod['price']} પેમેન્ટ કરો.\n"
                f"પેમેન્ટ થઈ જાય એટલે નીચે **'✅ Verify Payment'** બટન દબાવો."
            )
            
            # Dynamic UPI QR Code
            upi_url = f"upi://pay?pa={ADMIN_UPI_ID}&pn=Store&am={prod['price']}&cu=INR"
            qr_api = f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={urllib.parse.quote(upi_url)}"
            
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("✅ Verify Payment", callback_data=f"verify_{prod_id}"))
            
            bot.send_photo(message.chat.id, qr_api, caption=caption, parse_mode="Markdown", reply_markup=markup)
            return
        else:
            bot.reply_to(message, "❌ પ્રોડક્ટ મળ્યો નથી અથવા લિંક એક્સપાયર થઈ ગઈ છે.")
            return

    # એડમિન મેનૂ (ફક્ત તમને જ દેખાશે)
    if user_id == ADMIN_ID:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.row("➕ નવી પ્રોડક્ટ ઉમેરો", "📋 બધી પ્રોડક્ટ્સ")
        bot.send_message(message.chat.id, "👋 વેલકમ એડમિન! નીચેનામાંથી પસંદ કરો:", reply_markup=markup)
    else:
        bot.send_message(message.chat.id, "👋 હેલો! પ્રોડક્ટ ખરીદવા માટે મળેલી ડાયરેક્ટ પ્રોડક્ટ લિંક પર ક્લિક કરો.")

# નવી પ્રોડક્ટ એડ કરવાની પ્રોસેસ
@bot.message_handler(func=lambda msg: msg.text == "➕ નવી પ્રોડક્ટ ઉમેરો")
def add_product_step1(message):
    if message.from_user.id != ADMIN_ID:
        return
    user_states[message.chat.id] = {'step': 'name'}
    bot.send_message(message.chat.id, "📝 પ્રોડક્ટનું નામ લખો:")

@bot.message_handler(func=lambda msg: msg.chat.id in user_states)
def handle_product_steps(message):
    state = user_states[message.chat.id]
    step = state.get('step')

    if step == 'name':
        state['name'] = message.text
        state['step'] = 'price'
        bot.send_message(message.chat.id, "💰 કિંમત લખો (ફક્ત આંકડો, દા.ત. 49 અથવા 199):")
    
    elif step == 'price':
        state['price'] = message.text
        state['step'] = 'link'
        bot.send_message(message.chat.id, "🔗 ડિલિવરી માટેની ફાઈલ અથવા Google Drive લિંક મોકલો:")
    
    elif step == 'link':
        state['link'] = message.text
        prod_id = f"item_{len(products) + 1}"
        products[prod_id] = {
            'name': state['name'],
            'price': state['price'],
            'link': state['link']
        }
        del user_states[message.chat.id]
        
        bot_username = bot.get_me().username
        share_url = f"https://t.me/{bot_username}?start={prod_id}"
        
        bot.send_message(
            message.chat.id,
            f"✅ **પ્રોડક્ટ સફળતાપૂર્વક બની ગઈ!**\n\n"
            f"📌 **નામ:** {state['name']}\n"
            f"💵 **કિંમત:** ₹{state['price']}\n\n"
            f"🔗 **શેરિંગ લિંક:**\n`{share_url}`\n\n"
            f"👉 આ લિંક જેને મોકલશો તેને સીધો QR કોડ મળશે!",
            parse_mode="Markdown"
        )

# બધી પ્રોડક્ટ્સ જોવી
@bot.message_handler(func=lambda msg: msg.text == "📋 બધી પ્રોડક્ટ્સ")
def list_products(message):
    if message.from_user.id != ADMIN_ID:
        return
    if not products:
        bot.send_message(message.chat.id, "હજુ સુધી કોઈ પ્રોડક્ટ ઉમેરી નથી.")
        return
    
    bot_username = bot.get_me().username
    text = "📋 **તમારી એક્ટિવ પ્રોડક્ટ્સ:**\n\n"
    for pid, pdata in products.items():
        text += f"• **{pdata['name']}** (₹{pdata['price']})\n🔗 લિંક: https://t.me/{bot_username}?start={pid}\n\n"
    bot.send_message(message.chat.id, text, parse_mode="Markdown")

# પેમેન્ટ વેરિફિકેશન
@bot.callback_query_handler(func=lambda call: call.data.startswith('verify_'))
def verify_clicked(call):
    prod_id = call.data.split('_')[1]
    orders[call.message.chat.id] = prod_id
    bot.send_message(call.message.chat.id, "📸 કૃપા કરીને પેમેન્ટનો સ્ક્રીનશોટ અથવા UTR નંબર અહીં મોકલો:")

# એડમિનને પ્રૂફ મોકલવું
@bot.message_handler(content_types=['photo', 'text'], func=lambda msg: msg.chat.id in orders)
def forward_to_admin(message):
    prod_id = orders[message.chat.id]
    prod = products.get(prod_id)
    user = message.from_user

    admin_markup = types.InlineKeyboardMarkup()
    admin_markup.add(
        types.InlineKeyboardButton("✅ Confirm & Send Link", callback_data=f"approve_{message.chat.id}_{prod_id}"),
        types.InlineKeyboardButton("❌ Reject", callback_data=f"reject_{message.chat.id}")
    )

    info_text = (
        f"🔔 **નવું પેમેન્ટ પ્રૂફ મળ્યું!**\n\n"
        f"📦 પ્રોડક્ટ: {prod['name']}\n"
        f"💵 રકમ: ₹{prod['price']}\n"
        f"👤 યુઝર: @{user.username} (ID: `{user.id}`)"
    )
    
    if message.photo:
        bot.send_photo(ADMIN_ID, message.photo[-1].file_id, caption=info_text, reply_markup=admin_markup, parse_mode="Markdown")
    else:
        bot.send_message(ADMIN_ID, f"{info_text}\n\n📝 UTR: {message.text}", reply_markup=admin_markup, parse_mode="Markdown")

    bot.send_message(message.chat.id, "⏳ તમારું પેમેન્ટ વેરિફાય થઈ રહ્યું છે, એડમિન કન્ફર્મ કરશે એટલે તરત લિંક મળી જશે.")
    del orders[message.chat.id]

# એડમિન Approve / Reject કરે ત્યારે
@bot.callback_query_handler(func=lambda call: call.data.startswith('approve_') or call.data.startswith('reject_'))
def handle_approval(call):
    data = call.data.split('_')
    action = data[0]
    user_chat_id = int(data[1])

    if action == 'approve':
        prod_id = data[2]
        prod = products.get(prod_id)
        bot.send_message(
            user_chat_id,
            f"🎉 **પેમેન્ટ કન્ફર્મ થઈ ગયું છે!**\n\n"
            f"📦 તમારી પ્રોડક્ટ: **{prod['name']}**\n\n"
            f"📥 **ડાઉનલોડ લિંક:**\n👉 {prod['link']}",
            parse_mode="Markdown"
        )
        bot.edit_message_caption("✅ આ ઓર્ડર Approve કરી દીધો છે અને લિંક મોકલી દેવાઈ છે.", chat_id=call.message.chat.id, message_id=call.message.message_id)
    else:
        bot.send_message(user_chat_id, "❌ તમારું પેમેન્ટ વેરિફાય થયું નથી. જો પૈસા કપાઈ ગયા હોય તો એડમિનનો સંપર્ક કરો.")
        bot.edit_message_caption("❌ Reject કરવામાં આવ્યું.", chat_id=call.message.chat.id, message_id=call.message.message_id)

bot.infinity_polling()
