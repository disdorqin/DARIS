"""Telegram bot that invokes the ARISE email agent on AgentCore."""

import os
import json
import logging
import re
import boto3
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("arise-telegram")

# Config
BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
ALLOWED_USERNAME = "abekek"
AGENT_ARN = os.environ.get("AGENT_ARN",
    "arn:aws:bedrock-agentcore:us-west-2:436776987862:runtime/arise_email-prFvYN2bd3")
AWS_REGION = os.environ.get("AWS_REGION", "us-west-2")
AWS_PROFILE = os.environ.get("AWS_PROFILE", "abekek")


def get_bedrock_client():
    session = boto3.Session(profile_name=AWS_PROFILE, region_name=AWS_REGION)
    return session.client("bedrock-agentcore")


def invoke_agent(task: str) -> str:
    """Send task to AgentCore and extract response text."""
    client = get_bedrock_client()

    response = client.invoke_agent_runtime(
        agentRuntimeArn=AGENT_ARN,
        payload=json.dumps({
            "jsonrpc": "2.0",
            "method": "message/send",
            "id": "tg-1",
            "params": {
                "message": {
                    "role": "user",
                    "parts": [{"kind": "text", "text": task}],
                    "messageId": "tg-msg-1",
                }
            }
        }),
    )

    body = response["response"].read().decode("utf-8")
    data = json.loads(body)
    result = data.get("result", {})

    # Extract text from artifacts (streamed as many small chunks)
    texts = []
    for artifact in result.get("artifacts", []):
        for part in artifact.get("parts", []):
            if part.get("kind") == "text":
                texts.append(part["text"])

    if texts:
        # Chunks are split mid-word, just concatenate
        return "".join(texts).strip()

    # Fallback: check history for agent messages
    for item in result.get("history", []):
        if item.get("role") == "agent":
            for part in item.get("parts", []):
                if part.get("kind") == "text":
                    texts.append(part["text"])

    if texts:
        return "".join(texts)

    return "Agent completed but returned no text response."


def format_for_telegram(text: str) -> str:
    """Convert markdown to Telegram HTML."""
    # Escape HTML special chars first (but not our own tags)
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    # Headers → bold
    text = re.sub(r'^#{1,3}\s+(.+)$', r'<b>\1</b>', text, flags=re.MULTILINE)

    # **bold** → <b>bold</b>
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)

    # *italic* → <i>italic</i>  (but not inside bold tags)
    text = re.sub(r'(?<!\*)\*([^*]+?)\*(?!\*)', r'<i>\1</i>', text)

    # `code` → <code>code</code>
    text = re.sub(r'`([^`]+?)`', r'<code>\1</code>', text)

    # --- → empty line
    text = re.sub(r'^---+$', '', text, flags=re.MULTILINE)

    # Clean up extra blank lines
    text = re.sub(r'\n{3,}', '\n\n', text)

    return text.strip()


def is_authorized(update: Update) -> bool:
    username = update.effective_user.username
    return username == ALLOWED_USERNAME


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update):
        await update.message.reply_text("Not authorized.")
        return
    await update.message.reply_text(
        "ARISE Email Agent\n\n"
        "Send me a message and I'll check your emails.\n\n"
        "Examples:\n"
        "- Read my latest 5 emails and list action items\n"
        "- Check my inbox for anything urgent today\n"
        "- Any emails about meetings this week?"
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update):
        await update.message.reply_text("Not authorized.")
        return

    task = update.message.text
    logger.info(f"Task from @{update.effective_user.username}: {task}")

    # Send "typing" indicator
    await update.message.chat.send_action("typing")

    try:
        result = invoke_agent(task)
        result = format_for_telegram(result)
        # Telegram has a 4096 char limit per message
        chunks = [result[i:i+4000] for i in range(0, len(result), 4000)] if len(result) > 4000 else [result]
        for chunk in chunks:
            await update.message.reply_text(chunk, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Error: {e}")
        await update.message.reply_text(f"Error invoking agent: {str(e)[:500]}")


def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("Telegram bot starting...")
    app.run_polling()


if __name__ == "__main__":
    main()
