#!/usr/bin/env python3
"""
Centralized Telegram Bot for Homelab Platform

Commands:
  /help       — Show available commands
  /resume     — Get latest resume/CV
  /deploy     — Deploy a service (future)
  /backup     — Trigger backup (future)
  /expenses   — View expenses (future)
  /notion     — Notion integration (future)
  /github     — GitHub integration (future)
  /health     — Cluster health status (future)
  /status     — System status (future)

Notifications:
  Any service can POST to /api/notify to send messages
"""

import os
import logging
import asyncio
import queue
from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Get config from environment
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
API_PORT = int(os.getenv("API_PORT", "9999"))

# Queue for passing notifications from API to bot thread
notification_queue = queue.Queue()


# Pydantic models for API
class NotificationRequest(BaseModel):
    """Notification payload from other services"""

    message: str
    title: Optional[str] = None
    chat_id: Optional[str] = None  # Override default chat ID
    service: Optional[str] = None  # Service that sent the notification


# FastAPI app for notifications API
api_app = FastAPI(
    title="Telegram Bot API",
    description="Centralized notification API for homelab services",
)


# Telegram bot handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command"""
    if not update.message:
        return

    await update.message.reply_text(
        "👋 Welcome to Homelab Control Bot!\n\n" "Use /help to see available commands."
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help command - show all available commands"""
    if not update.message:
        return

    help_text = """
🤖 *Homelab Control Bot - Available Commands*

*Implemented:*
• /help - Show this help message
• /resume - Get your resume/CV (latest version)

*Coming Soon:*
• /deploy - Deploy a service
• /backup - Trigger system backup
• /expenses - View expense tracking
• /notion - Notion integration
• /github - GitHub notifications
• /health - Cluster health report
• /status - System status overview

*How it works:*
1. Use any command above
2. Bot responds with relevant information
3. Other services send notifications automatically

*For developers:*
Send notifications via HTTP POST:
```
POST /api/notify
Content-Type: application/json

{
  "title": "Backup Complete",
  "message": "Daily backup finished at 2024-06-13T10:30:00Z",
  "service": "backup-job"
}
```

Need help? Type /help again or check the docs.
"""
    await update.message.reply_text(help_text, parse_mode="Markdown")


async def resume_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /resume command - send resume/CV"""
    if not update.message or not update.effective_user:
        return

    logger.info(f"Resume requested by user {update.effective_user.id}")

    resume_text = """
📄 *Your Resume/CV*

*Name:* Your Name
*Title:* Software Engineer | Platform Engineering

*Summary:*
Lorem ipsum dolor sit amet, consectetur adipiscing elit.

*Experience:*
• Position 1 (Company A)
• Position 2 (Company B)

*Skills:*
• Python, Go, Kubernetes
• Cloud (GCP, AWS)
• DevOps, CI/CD

*Contact:*
📧 Email: your.email@example.com
🔗 GitHub: github.com/yourname
🔗 LinkedIn: linkedin.com/in/yourname

_Last updated: 2024-06-13_

💡 Tip: Use /deploy, /backup, /health for other actions.
"""

    await update.message.reply_text(resume_text, parse_mode="Markdown")
    if update.effective_user:
        logger.info(f"Resume sent to user {update.effective_user.id}")


async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle unknown commands"""
    if not update.message:
        return

    await update.message.reply_text(
        f"❌ Unknown command: {update.message.text}\n\n"
        "Use /help to see available commands."
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle regular messages"""
    if not update.message or not update.message.text or not update.effective_user:
        return

    logger.info(f"Message from {update.effective_user.username}: {update.message.text}")

    if update.message.text.startswith("/"):
        await unknown_command(update, context)
    else:
        # Echo back for debugging
        await update.message.reply_text(
            f"I received your message: {update.message.text[:50]}\n\n"
            "Use /help to see available commands."
        )


# API Endpoints
@api_app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "ok", "service": "telegram-bot"}


@api_app.post("/api/notify")
async def send_notification(notification: NotificationRequest):
    """
    Receive notification from other services and send via Telegram

    Example:
    POST /api/notify
    {
      "title": "Backup Complete",
      "message": "Daily backup finished successfully",
      "service": "backup-job"
    }
    """
    try:
        logger.info(f"Notification from {notification.service}: {notification.title}")

        # Format message
        chat_id = notification.chat_id or TELEGRAM_CHAT_ID

        if notification.title:
            formatted_message = f"*{notification.title}*\n\n{notification.message}"
        else:
            formatted_message = notification.message

        if notification.service:
            formatted_message += f"\n\n_From: {notification.service}_"

        # Queue message for bot thread to send (avoids event loop issues)
        notification_data = {
            "chat_id": chat_id,
            "text": formatted_message,
            "service": notification.service
        }
        notification_queue.put(notification_data)
        logger.info(f"Notification queued for delivery")

        return {"status": "queued", "message_id": None, "service": notification.service}

    except Exception as e:
        logger.error(f"Failed to queue notification: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_app.get("/api/commands")
async def get_commands():
    """List all available commands"""
    return {
        "commands": {
            "help": "Show available commands",
            "resume": "Get your resume/CV",
            "deploy": "Deploy a service (coming soon)",
            "backup": "Trigger backup (coming soon)",
            "expenses": "View expenses (coming soon)",
            "notion": "Notion integration (coming soon)",
            "github": "GitHub integration (coming soon)",
            "health": "Cluster health (coming soon)",
            "status": "System status (coming soon)",
        }
    }


async def process_notification_queue(application):
    """Process notifications from the queue in the bot's event loop"""
    while True:
        try:
            # Non-blocking check for notifications (timeout after 1 second)
            notification = notification_queue.get(timeout=1)
            try:
                msg = await application.bot.send_message(
                    chat_id=notification["chat_id"],
                    text=notification["text"],
                    parse_mode="Markdown"
                )
                logger.info(f"Notification sent from {notification['service']} (message_id={msg.message_id})")
            except Exception as e:
                logger.error(f"Failed to send notification from {notification['service']}: {e}")
        except queue.Empty:
            # Timeout, just continue
            pass
        except Exception as e:
            logger.error(f"Error processing notification queue: {e}")


async def run_bot():
    """Run the Telegram bot"""
    logger.info("Starting Telegram bot...")

    if not TELEGRAM_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN environment variable is required")
        return

    # Create bot application
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("resume", resume_command))

    # Handle unknown commands
    application.add_handler(MessageHandler(filters.COMMAND, unknown_command))

    # Handle regular messages
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )

    # Start bot
    await application.initialize()
    await application.start()

    # Start queue processor task
    queue_task = asyncio.create_task(process_notification_queue(application))

    if application.updater:
        await application.updater.start_polling(allowed_updates=Update.ALL_TYPES)
        logger.info("Bot is running and polling for updates")
    else:
        logger.error("Failed to initialize bot updater")

    # Keep running until interrupted
    try:
        await asyncio.Event().wait()
    except asyncio.CancelledError:
        logger.info("Bot shutting down")
        queue_task.cancel()
        await application.stop()
        await application.shutdown()


if __name__ == "__main__":
    import threading
    import time

    # Run bot in background thread with its own event loop
    def run_bot_thread():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(run_bot())
        except KeyboardInterrupt:
            pass
        finally:
            loop.close()

    bot_thread = threading.Thread(target=run_bot_thread, daemon=True)
    bot_thread.start()

    # Give bot thread time to initialize before starting API
    time.sleep(2)

    # Start FastAPI server in main thread
    logger.info(f"Starting API server on port {API_PORT}")
    uvicorn.run(api_app, host="0.0.0.0", port=API_PORT, log_level="info")
