import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
from PIL import Image, ImageDraw, ImageFont

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# State definitions for Conversation
COMPANY_NAME, INDUSTRY = range(2)

# Helper function to get color palette based on industry
def get_industry_colors(industry: str):
    ind = industry.lower().strip()
    if any(x in ind for x in ["tech", "software", "digital", "crypto"]):
        return (26, 54, 93), (66, 153, 225), (247, 250, 252) # Deep Navy, Tech Blue, Light Gray
    elif any(x in ind for x in ["food", "cafe", "restaurant", "bake"]):
        return (123, 52, 30), (221, 107, 32), (255, 245, 240) # Teracotta, Warm Orange, Soft Cream
    elif any(x in ind for x in ["eco", "green", "nature", "plant", "farm"]):
        return (34, 84, 61), (72, 187, 120), (240, 253, 244) # Forest Green, Mint, Pale Leaf
    elif any(x in ind for x in ["fashion", "beauty", "glam", "luxury"]):
        return (26, 26, 26), (214, 158, 46), (255, 255, 255) # Obsidian Black, Dull Gold, Crisp White
    else:
        return (45, 55, 72), (113, 128, 150), (247, 250, 252) # Slate, Corporate Gray, Off-White

# Function to dynamically build the logo graphic asset
def create_brand_assets(name: str, industry: str):
    primary, secondary, background = get_industry_colors(industry)
    
    # 1. Base Canvas Layout (1200 x 800 Triple Mockup Display)
    canvas = Image.new("RGB", (1200, 800), (230, 235, 240))
    draw = ImageDraw.Draw(canvas)
    
    # --- PANEL 1: Corporate Letterhead / Signage Background (Left) ---
    draw.rectangle([0, 0, 400, 800], fill=background)
    # Simple procedurally drawn logo mark (Circle + Inner Diamond)
    draw.ellipse([150, 150, 250, 250], fill=primary)
    draw.polygon([(200, 170), (230, 200), (200, 230), (170, 200)], fill=secondary)
    draw.text((200, 300), name, fill=primary, anchor="mm", align="center")
    draw.text((200, 330), industry.upper(), fill=secondary, anchor="mm", align="center")
    
    # --- PANEL 2: Smartphone App Interface Mockup (Center) ---
    draw.rectangle([400, 0, 800, 800], fill=primary)
    # Draw Phone Silhouette
    draw.rectangle([480, 100, 720, 700], fill=(20, 20, 20), radius=30) # Phone body
    draw.rectangle([495, 115, 705, 685], fill=background, radius=15) # Phone screen
    # App Logo Screen Element
    draw.ellipse([570, 250, 630, 310], fill=secondary)
    draw.text((600, 360), name[:12], fill=primary, anchor="mm")
    # Fake UI Buttons
    draw.rectangle([520, 450, 680, 490], fill=primary, radius=8)
    draw.rectangle([520, 510, 680, 550], fill=(200, 200, 200), radius=8)

    # --- PANEL 3: Modern Business Card Mockup (Right) ---
    # Dark textured accent split
    draw.rectangle([800, 0, 1200, 800], fill=(40, 44, 52))
    # Horizontal Card Base
    card_box = [850, 280, 1150, 460]
    draw.rectangle(card_box, fill=background, radius=5)
    # Tiny logo on card
    draw.ellipse([880, 320, 910, 350], fill=primary)
    draw.text((930, 335), name[:15], fill=primary, anchor="lm")
    # Divider line
    draw.line([(880, 370), (1120, 370)], fill=secondary, width=2)
    # Dummy contact lines
    draw.rectangle([880, 395, 1000, 402], fill=secondary)
    draw.rectangle([880, 415, 960, 422], fill=secondary)

    # Save to disk temporarily
    output_path = "appy_pie_mockup.png"
    canvas.save(output_path, "PNG")
    return output_path

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "👋 Welcome to **Appy Pie Mockup Bot**!\n\n"
        "I can instantly generate native visual branding concepts and multi-surface mockups without any messy cloud weight.\n\n"
        "To get started, please tell me your **Company Name**:"
    )
    return COMPANY_NAME

async def receive_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['name'] = update.message.text
    await update.message.reply_text(
        f"Got it: *{update.message.text}*.\n\n"
        "Now, what **Industry** or business niche does this company belong to? (e.g., Tech, Food, Eco, Fashion)"
    )
    return INDUSTRY

async def receive_industry(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    name = context.user_data['name']
    industry = update.message.text
    
    status_msg = await update.message.reply_text("⚡ Processing vectors and rendering your multi-surface mockups...")
    
    try:
        # Generate the graphics asset procedurally via Pillow
        image_path = create_brand_assets(name, industry)
        
        # Send photo back to user
        await update.message.reply_photo(
            photo=open(image_path, 'rb'),
            caption=f"✨ **Branding Package for {name}**\n🏭 Industry: {industry}\n\n Here is your minimalist logo sign, mobile app application skin, and corporate business card mockup!"
        )
        
        # Clean up local file
        if os.path.exists(image_path):
            os.remove(image_path)
            
    except Exception as e:
        logger.error(f"Error drawing mockup assets: {e}")
        await update.message.reply_text("❌ Apologies, an unexpected styling error occurred while flattening the mockup sheets.")
    finally:
        await status_msg.delete()

    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Process cancelled. Type /start to begin a new brand layout creation.")
    return ConversationHandler.END

def main():
    # Retrieve the Token securely from Render Environment Variables
    TOKEN = os.getenv("TELEGRAM_TOKEN")
    if not TOKEN:
        logger.critical("TELEGRAM_TOKEN environment variable missing!")
        return

    application = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            COMPANY_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_name)],
            INDUSTRY: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_industry)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(conv_handler)
    
    # Run long polling approach
    application.run_polling()

if __name__ == '__main__':
    main()
