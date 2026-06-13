#!/usr/bin/env python3
"""
Centralized Telegram Bot for Homelab Platform

Commands:
  /help       — Show available commands
  /me         — Show bot info and status
  /resume     — Get latest resume/CV
  /deploy     — Deploy a service (future)
  /backup     — Trigger backup (future)
  /expenses   — View expenses (future)
  /notion     — Notion integration (future)
  /github     — GitHub integration (future)
  /health     — Cluster health status (future)
  /status     — System status (future)

Features:
  • Hourly heartbeat (silent, no notification)
  • Service notifications via /api/notify
  • Startup notification on bot launch
"""

import os
import logging
import asyncio
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

# Global notification queue (will be set by bot thread)
notification_queue: Optional[asyncio.Queue] = None


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
• /me - Show bot info and status
• /k8s_report - Get cluster health report
• /resume - Get your resume/CV (latest version)

*Features:*
• 🫀 Hourly heartbeat (automatic)
• 📨 Service notifications
• 🔔 Startup notification

*Coming Soon:*
• /deploy - Deploy a service
• /backup - Trigger system backup
• /expenses - View expense tracking
• /notion - Notion integration
• /github - GitHub notifications
• /health - Cluster health report
• /status - System status overview

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

Need help? Type /help again or use /me for bot status.
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


async def me_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /me command - show bot info"""
    if not update.message:
        return

    import socket
    from datetime import datetime, timezone

    hostname = socket.gethostname()
    uptime = datetime.now(timezone.utc).isoformat()

    info_text = f"""
🤖 *Homelab Bot Information*

*Hostname:* `{hostname}`
*Status:* Running ✅
*Started:* {uptime}

*Features:*
• 📨 Notifications from services
• 📊 Cluster health reports
• 💼 Resume delivery
• 🔔 Hourly heartbeat

*API Port:* 9999
*Chat ID:* `{TELEGRAM_CHAT_ID[:10]}...`

Use /help for more commands.
"""
    await update.message.reply_text(info_text, parse_mode="Markdown")


async def k8s_report_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /k8s_report command - show cluster health report"""
    if not update.message:
        return

    from datetime import datetime, timezone

    logger.info("Cluster health report requested")

    try:
        report_text = """
📊 *Kubernetes Cluster Health Report*

_Note: Detailed reports are generated weekly via the k8s-health-report CronJob (Sundays 06:00 UTC)_

*Quick Status:*
• Use the web dashboard for real-time monitoring
• Check ArgoCD for application deployment status
• View pod logs with: `kubectl logs -n home -f <pod-name>`

*Common Issues:*
• Pod not starting? → Check events: `kubectl describe pod -n home <pod-name>`
• Service unreachable? → Verify service exists: `kubectl get svc -n home`
• High resource usage? → Check limits: `kubectl top nodes/pods -n home`

*Next Scheduled Report:*
_Sunday 06:00 UTC (via k8s-health-report CronJob)_

For immediate cluster diagnostics, contact cluster admin or check the detailed weekly reports.
"""
        await update.message.reply_text(report_text, parse_mode="Markdown")

    except Exception as e:
        logger.error(f"Failed to send report: {e}")
        await update.message.reply_text(
            f"❌ Failed to send report: {e}",
            parse_mode="Markdown"
        )


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
        if notification_queue is None:
            raise HTTPException(status_code=503, detail="Bot not ready")

        notification_data = {
            "chat_id": chat_id,
            "text": formatted_message,
            "service": notification.service
        }
        assert notification_queue is not None
        notification_queue.put_nowait(notification_data)
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


async def hourly_heartbeat(application):
    """Send hourly heartbeat without notifying (silent background task)"""
    from datetime import datetime, timezone

    while True:
        try:
            await asyncio.sleep(3600)  # 1 hour
            timestamp = datetime.now(timezone.utc).isoformat()
            message = f"🫀 *Heartbeat*\n\nBot is alive at {timestamp}"

            await application.bot.send_message(
                chat_id=TELEGRAM_CHAT_ID,
                text=message,
                parse_mode="Markdown"
            )
            logger.info(f"Hourly heartbeat sent at {timestamp}")
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Failed to send hourly heartbeat: {e}")


async def process_notification_queue(application, queue: asyncio.Queue):
    """Process notifications from the queue in the bot's event loop"""
    while True:
        try:
            # Wait for notification (non-blocking in event loop)
            notification = await queue.get()
            try:
                msg = await application.bot.send_message(
                    chat_id=notification["chat_id"],
                    text=notification["text"],
                    parse_mode="Markdown"
                )
                logger.info(f"Notification sent from {notification['service']} (message_id={msg.message_id})")
            except Exception as e:
                logger.error(f"Failed to send notification from {notification['service']}: {e}")
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Error processing notification queue: {e}")


async def run_bot():
    """Run the Telegram bot"""
    global notification_queue
    logger.info("Starting Telegram bot...")

    if not TELEGRAM_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN environment variable is required")
        return

    # Create notification queue in this event loop
    notification_queue = asyncio.Queue()

    # Create bot application
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("resume", resume_command))
    application.add_handler(CommandHandler("me", me_command))
    application.add_handler(CommandHandler("k8s_report", k8s_report_command))

    # Handle unknown commands
    application.add_handler(MessageHandler(filters.COMMAND, unknown_command))

    # Handle regular messages
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )

    # Start bot
    await application.initialize()
    await application.start()

    # Send startup notification
    try:
        startup_msg = "🟢 Bot is online and ready to receive commands"
        await application.bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=startup_msg,
            parse_mode="Markdown"
        )
        logger.info("Startup notification sent")
    except Exception as e:
        logger.error(f"Failed to send startup notification: {e}")

    # Start background tasks
    queue_task = asyncio.create_task(process_notification_queue(application, notification_queue))
    heartbeat_task = asyncio.create_task(hourly_heartbeat(application))

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
        heartbeat_task.cancel()
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
