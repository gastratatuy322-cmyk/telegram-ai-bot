import os 
from dotenv import load_dotenv
import asyncio
from aiogram import Bot, Dispatcher, types
from openai import AsyncOpenAI
from aiogram.filters import CommandStart, Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, BufferedInputFile, BotCommand, MenuButtonCommands
from ddgs import DDGS
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
# Import custom AI detection module
from detec import check_AI_score
from file_maker import create_excel_table, create_presentation, create_word_doc
from security import check_promt_security, build_safe_messages
# Load environment variables and initialize OpenRouter AI client
load_dotenv()
ai_key = os.getenv("OPENROUTER_API_KEY")
client = AsyncOpenAI(base_url="https://openrouter.ai/api/v1",
                api_key=ai_key)
# Initialize Telegram Bot and Dispatcher
bot_token = os.getenv("BOT_TOKEN")
bot = Bot(token=bot_token)
dp = Dispatcher()
# Create inline keyboard for selecting output format
def get_format_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
           InlineKeyboardButton(text="💬 Text(Текст)", callback_data="fmt_text"),
           InlineKeyboardButton(text="📄 Document(Документ)", callback_data="fmt_doc")
        ],
        [
            InlineKeyboardButton(text="📊 Table(Таблица)", callback_data="fmt_excel"),
            InlineKeyboardButton(text="📽 Presentation(Презентация)", callback_data="fmt_ppt")
        ]
    ])
    return keyboard
# Create inline keyboard for selecting presentation slide count
def get_slides_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
               InlineKeyboardButton(text="5 Slides(Слайдов)", callback_data="slides_5"),
               InlineKeyboardButton(text="8 Slides(Слайдов)", callback_data="slides_8")
            ],
            [
                InlineKeyboardButton(text="12 Slides(Слайдов)", callback_data="slides_12"),
                InlineKeyboardButton(text="15 Slides(Слайдов)", callback_data="slides_15")
            ]    
    ])
    return keyboard

# Create inline keyboard with Approve and Regenerate buttons
def get_action_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [
        InlineKeyboardButton(text="✅ Approve(Одобрить)", callback_data="approve"),
        InlineKeyboardButton(text="🔄 Redo(Переделать)", callback_data="regenerate")
    ]
])
    return keyboard
# Handle the command
@dp.message(Command("info"))
async def info_command(message: types.message):
    text = (
        "ℹ️ <b>About the bot:</b>\n\n"
        "I am a multi-agent AI assistant that searches the internet for relevant information, "
        "writes structured content and checks the text for human-likeness (using an AI detector)"
        "and collects the finished files.\n\n"
        "📌 <b>Available formats:</b>\n"
        "• 💬Standard text with a check option and a rewrite button\n"
        "• 📄 Document Word (.docx)\n"
        "• 📊 Table Excel (.xlsx)\n"
        "• 📽 Presentation PowerPoint (.pptx) with images, spanning 5-15 slides\n\n"
        "⚠️ <i>Tip: always check the facts and formatting before submitting your work.</i>"
        )
    await message.answer(text, parse_mode="HTML")
@dp.message(Command("privacy"))
async def privacy_command(message: types.message):
    text = (
        "🔒 <b>Privacy Policy:</b>\n\n"
        "1. <b>Without saving to disk:</b> all documents, spreadsheets, and presentations are being collected "
        "exclusively in RAM (RAM) and are instantly deleted as soon as they are sent to your chat.\n"
        "2. <b>Message history:</b> The bot does not maintain a database of your requests and does not share them with third parties..\n"
        "3. <b>External API:</b> The text of your query is temporarily transmitted to a search engine and to language models."
        "solely for the purpose of generating the current response."
    )
    await message.answer(text, parse_mode="HTML")
@dp.message(CommandStart())
async def start_handler(message: types.Message):
    await message.answer(
        "👋 <b>Hi! I am a multi-agent AI assistant..</b>\n\n"
        "Just write me any topic or question - I will find the latest information on the Internet, "
        "I will prepare the text, check it to ensure it sounds natural (human-like), and put together the final file..\n\n"
        "📌 <b>Available commands:</b>\n"
        "/start — Restart the bot\n"
        "/info — More details on features and formats\n"
        "/privacy — Privacy Policy\n\n"
        "✍️ <i>Write your first topic right now!</i>"
    )
# Handle format selection and run the 4-agent generation pipeline
@dp.callback_query(lambda c: c.data and (c.data.startswith("fmt_")) or c.data.startswith("slides_"))
async def format_choice_callback(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    user_data = await state.get_data()
# Prevent concurrent requests while generation is in progress
    if user_data.get("is_busy"):
        await callback.answer("⏳ Wait for the current generation to finish!", show_alert=True)
        return
    topic = user_data.get("topic")
    chosen_format = callback.data
    if not topic: return
    if chosen_format == "fmt_ppt":
        await callback.message.edit_text("Select the number of slides for the presentation:",                         
        reply_markup=get_slides_keyboard())
        return
    slides_count = "5"
    if chosen_format.startswith("slides_"):
        slides_count = chosen_format.split("_")[1]
        chosen_format = "fmt_ppt"
    await state.update_data(last_format=chosen_format, last_slides=slides_count)
    await state.update_data(is_busy=True)
    try:
    # Agent 1 (Researcher): Search the web for real-time facts and sources
            await callback.message.edit_text("🔍 Searching for information online (Agent 1)...")
            context_text = ""
            sources_list = ""
    # Detect user's region based on Telegram interface language
            try:
                lang = (callback.from_user.language_code or "en").lower()
                exceptions = {"uk": "ua-uk", "en": "us-en", "ja": "jp-ja"}
                ddg_region = exceptions.get(lang, f"{lang}-{lang}")
                search_results = DDGS().text(topic, region=ddg_region, max_results=5)    
            except Exception as search_err:
                print(f"Search warning: {search_err}")
                search_results = []
            for item in search_results:
                context_text += f"{item['title']}: {item['body']}\n"
                sources_list += f"{item['title']}: {item['href']}\n"  
    # Agent 2 (Writer): Generate the initial draft based on user's topic
            wrait_promt = ("You are a professional writer and content creator"
                    "Write a detailed, well-structured, and informative text based on the user's topic."
                    "Always reply in the exact same language that the user used in their message."
                    f" User's locale/region code: {ddg_region}. Adapt currency, laws,"
                    "and local context to this region while answering strictly in the language of the user's request."
                    "If the search results are short or empty, use your own encyclopedic knowledge to complete all slides")
            if chosen_format == "fmt_excel":
                 wrait_promt += " Format the entire output strictly as a CSV table separated by semicolons (;)."
                 " Do not use markdown blocks."
            elif chosen_format == "fmt_ppt":
                 wrait_promt += f" Create a detailed presentation with exactly {slides_count} slides." 
                 "Separate EVERY slide strictly with '===SLIDE==='. Write the slide title on the first line," 
                 "followed by 3-5 detailed bullet points."
    # Wrap user topic in XML tags to prevent prompt injection
            safe_messages = build_safe_messages(wrait_promt, topic)
            response2 = await client.chat.completions.create(
            model="openrouter/free",
            messages=safe_messages)        
            draft_text = response2.choices[0].message.content
            await callback.message.edit_text("Editing text (Agent 2)")
            if chosen_format in ["fmt_text", "fmt_doc"]:
    # Agent 3 (Editor): Rewrite the draft to sound more natural and human-like
                response3 = await client.chat.completions.create(
                    model="openrouter/free",
                    messages=[
                            {"role": "system", "content": "You are an experienced human editor."
                            "Rewrite the provided text to make it sound completely natural,"
                            "engaging, and written by a real person. Remove robotic phrasing,"
                            "AI cliches, and repetitive structures while keeping all key facts and structure."
                            " Always reply in the exact same language as the provided text."},
                            {"role": "user", "content": draft_text}
                            ])
                final_tecst = response3.choices[0].message.content
            else:
                final_tecst = draft_text
            # Agent 4 (Local AI Detector): Calculate human-likeness score mathematically
            await callback.message.edit_text("🕵️ Checking AI probability...")
            ai_score = check_AI_score(final_tecst)
            if chosen_format == "fmt_text":
                full_answer = f"{final_tecst}\n\n📊 AI Probability: {ai_score}%\n\n🔗 Sources:\n{sources_list}"
                if len(full_answer) > 4000:
                    full_answer = full_answer[:3950] + "\n\n... (text shortened to fit the limit Telegram)"
                await callback.message.edit_text(full_answer, reply_markup=get_action_keyboard())
            elif chosen_format == "fmt_doc":
                file_stream = create_word_doc(topic, final_tecst, sources_list)
                await callback.message.delete()
                await callback.message.answer_document(BufferedInputFile(file_stream.read(), filename="document.docx"), 
                                                       caption=f"📊 AI Probability: {ai_score}%",  
                                                       reply_markup=get_action_keyboard())
            elif chosen_format == "fmt_excel":
                file_stream = create_excel_table(topic, final_tecst, sources_list)
                await callback.message.delete()
                await callback.message.answer_document(BufferedInputFile(file_stream.read(), filename="table.xlsx"), 
                                                       caption=f"📊 AI Probability: {ai_score}%", 
                                                        reply_markup=get_action_keyboard())
            elif chosen_format == "fmt_ppt":
                file_stream = create_presentation(topic, final_tecst, sources_list)
                await callback.message.delete()
                await callback.message.answer_document(BufferedInputFile(file_stream.read(), filename="presentation.pptx"), 
                                                       caption=f"📊 AI Probability: {ai_score}%", 
                                                       reply_markup=get_action_keyboard())
    # Catch API or network errors to prevent the bot from crashing
    except Exception as e:
            print(f"Erorr API: {e}")
            await callback.message.answer("An error occurred when requesting AI, try again.")
    finally:
        await state.update_data(is_busy=False)
# Handle incoming text messages and run the multi-agent pipeline
@dp.message()
async def echo_handler(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    if user_data.get("is_busy"):
        await message.answer("⏳ Hold on, I’m still working on your previous request!")
        return
    # Ignore non-text messages (stickers, photos, voice, etc.)
    if not message.text:
        await message.answer("I still understand only the message")
        return
    # Run security firewall check on incoming topic
    status_msg = await message.answer("🛡️ Checking the request...")
    is_safe, result_text = await check_promt_security(client, "openrouter/free", message.text)
    if not is_safe:
        await status_msg.edit_text(result_text)
        return
    await state.update_data(topic=result_text)
    await status_msg.edit_text("In what format should the response be prepared?", reply_markup=get_format_keyboard())
    return 
# Handle the "Approve" button click
@dp.callback_query(lambda c: c.data == "approve")
async def approve_callback(callback: types.CallbackQuery):
    await callback.answer("The text has been approved!")
    await callback.message.edit_reply_markup(reply_markup=None)
    (await callback.message.answer
    ("Great! The work has been approved."))
# Handle the "Regenerate" button click (reset format for files or re-run Editor for text)
@dp.callback_query(lambda c: c.data == "regenerate")
async def regenerate_callback(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    if not callback.message.text:
        user_data = await state.get_data()
        topic = user_data.get("topic")
        if not topic:
            await callback.message.answer("The topic is outdated; please submit your request again.")
            return
        await callback.message.delete()
        await callback.message.answer(f"Reworking the theme: <b>{topic}</b>\nSelect a format:", 
                                    reply_markup=get_format_keyboard(), parse_mode="HTML")
        return
    if callback.message.text:
        old_text = callback.message.text
        clean_old_text = old_text.split("\n\n📊")[0]
        sources_part = "\n\n🔗" + old_text.split("\n\n🔗")[1] if "\n\n🔗" in old_text else ""
        await callback.message.edit_text("🔄 Regenerating text...")
        await state.update_data(is_busy=True)
        try:
            response4 = await client.chat.completions.create(
                model="openrouter/free",
                messages=[
                    {"role": "system", "content": "You are an experienced human editor."
                            "Rewrite the provided text to make it sound completely natural,"
                            "engaging, and written by a real person. Remove robotic phrasing,"
                            "AI cliches, and repetitive structures while keeping all key facts and structure."
                            " Always reply in the exact same language as the provided text."},
                    {"role": "user", "content": clean_old_text}
                ])
            new_text = response4.choices[0].message.content
            await callback.message.edit_text("🕵️ Checking AI probability...")
            new_score = check_AI_score(new_text)
            final_regenerated = f"{new_text}\n\n📊 AI Probability: {new_score}%{sources_part}"
            await callback.message.edit_text(final_regenerated,
            reply_markup=get_action_keyboard())
            if len(final_regenerated) > 4000:
                final_regenerated = final_regenerated[:3950] + "\n\n... (text shortened to fit the limit Telegram)"
        except Exception as e:
            print(f"Error API: {e}")
            await callback.message.edit_text("An error occurred while reworking the text, please try again.")
        finally:
                await state.update_data(is_busy=False)
# Configure bot commands menu in Telegram UI
async def set_bot_commands(bot: Bot):
    commands = [
        BotCommand(command="start", description="Start the bot"),
        BotCommand(command="info", description="On possibilities and formats"),
        BotCommand(command="privacy", description="Privacy Policy"),
    ]
    await bot.set_my_commands(commands)
    await bot.set_chat_menu_button(menu_button=MenuButtonCommands())
# Start polling updates from Telegram servers
async def main():
    print("Bot started!")
    await set_bot_commands(bot)
    await dp.start_polling(bot)
if __name__ == "__main__":
    asyncio.run(main())