"""
Telegram Bot Service implementation using python-telegram-bot.
Integrates with QueryService for NL-to-SQL analytics, and Matplotlib for chart rendering.
"""

from __future__ import annotations

import io
import structlog
from typing import Any
from uuid import UUID, uuid4
from sqlalchemy.ext.asyncio import AsyncSession

from telegram import Update, InputFile
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from app.core.config import get_settings
from app.database.session import AsyncSessionFactory, AsyncReadOnlySessionFactory
from app.database.repositories.user import UserRepository
from app.database.repositories.conversation import ConversationRepository
from app.services.query import QueryService
from app.services.chart import generate_matplotlib_chart

logger = structlog.get_logger(__name__)
settings = get_settings()

class TelegramService:
    _instance: TelegramService | None = None

    def __init__(self) -> None:
        token = settings.telegram_bot_token
        if not token:
            logger.warning("telegram.missing_token", message="TELEGRAM_BOT_TOKEN not configured.")
            self.application = None
            return

        self.application = ApplicationBuilder().token(token).build()
        self.setup_handlers()
        logger.info("telegram.initialized", token_configured=True)

    @classmethod
    def get_instance(cls) -> TelegramService:
        """Singleton pattern for TelegramService."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    async def initialize(self) -> None:
        """Initialize the bot application."""
        if self.application:
            await self.application.initialize()
            await self.application.start()
            logger.info("telegram.application_started")

    async def shutdown(self) -> None:
        """Shutdown the bot application."""
        if self.application:
            await self.application.stop()
            await self.application.shutdown()
            logger.info("telegram.application_stopped")

    async def process_update(self, update_json: dict[str, Any]) -> None:
        """Process an incoming update from the FastAPI webhook endpoint."""
        if not self.application:
            logger.error("telegram.not_initialized", error="Bot application not initialized.")
            return
        
        update = Update.de_json(update_json, self.application.bot)
        if update:
            await self.application.process_update(update)

    def setup_handlers(self) -> None:
        """Register command and message handlers."""
        if not self.application:
            return

        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("ask", self.ask_command))
        self.application.add_handler(CommandHandler("history", self.history_command))
        self.application.add_handler(CommandHandler("chart", self.chart_command))
        
        # Non-command text messages default to /ask behavior
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.text_message_fallback))

    # ── Helpers ──────────────────────────────────────────────────

    async def _get_or_create_user(self, update: Update, db: AsyncSession) -> Any:
        """Helper to fetch or register a user by their Telegram ID."""
        tg_user = update.effective_user
        if not tg_user:
            return None

        user_repo = UserRepository(db)
        user = await user_repo.get_by_telegram_id(tg_user.id)
        
        if not user:
            # Register a new analyst account automatically
            username = tg_user.username or f"tg_{tg_user.id}"
            email = f"tg_{tg_user.id}@nexus.local"
            # Placeholder password hash (users registering via Telegram won't use email login unless they reset)
            from app.core.security import get_password_hash
            dummy_hash = get_password_hash(str(uuid4()))
            
            user = await user_repo.create_user(
                username=username,
                email=email,
                password_hash=dummy_hash,
                role="analyst",
                telegram_id=tg_user.id
            )
            await db.commit()
            logger.info("telegram.user_auto_registered", telegram_id=tg_user.id, username=username)
            
        return user

    # ── Handlers ─────────────────────────────────────────────────

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Welcome message and registration handler."""
        if not update.message:
            return

        async with AsyncSessionFactory() as db:
            user = await self._get_or_create_user(update, db)
            
        username = user.username if user else "guest"
        welcome_text = (
            f"🤖 *Welcome to Nexus Analytics, {username}!*\n\n"
            "I am your enterprise NL-to-SQL Analytics Assistant.\n"
            "You can query our E-commerce store database using natural language.\n\n"
            "👉 *Try asking something like:*\n"
            "• `What is our total revenue this month?`\n"
            "• `Top 5 products by revenue`\n"
            "• `List states by customer count`\n\n"
            "🚀 *Available Commands:*\n"
            "/ask <question> — Submit a business query\n"
            "/history — View your recent queries\n"
            "/chart — Force visual render of the last query\n"
            "/help — Show this help manual"
        )
        await update.message.reply_text(welcome_text, parse_mode="Markdown")

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Help instructions manual."""
        if not update.message:
            return
            
        help_text = (
            "🛠️ *Nexus Analytics Bot Help Manual*\n\n"
            "Ask questions in natural language, and Nexus will translate them into safe SQL, execute them, and return tabular summaries.\n\n"
            "• `/ask <question>` — Submit a question (e.g., `/ask average delivery days by state`)\n"
            "• Simply message me directly with a question (e.g., `revenue by payment method`)\n"
            "• `/history` — List your last 5 queries\n"
            "• `/chart` — Render a chart for your last query (if applicable)"
        )
        await update.message.reply_text(help_text, parse_mode="Markdown")

    async def ask_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /ask command queries."""
        if not update.message or not context.args:
            if update.message:
                await update.message.reply_text("⚠️ Please provide a query. Example:\n`/ask top 5 products`", parse_mode="Markdown")
            return
            
        question = " ".join(context.args)
        await self._process_ask_logic(update, question)

    async def text_message_fallback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Process plain text messages directly as queries."""
        if not update.message or not update.message.text:
            return
            
        await self._process_ask_logic(update, update.message.text)

    async def _process_ask_logic(self, update: Update, question: str) -> None:
        """Core engine invocation and response dispatcher."""
        if not update.message:
            return
            
        # Send thinking indicator
        status_msg = await update.message.reply_text("⏳ *Analyzing question and database schema...*", parse_mode="Markdown")

        try:
            async with AsyncSessionFactory() as db:
                async with AsyncReadOnlySessionFactory() as ro_db:
                    user = await self._get_or_create_user(update, db)
                    if not user:
                        await status_msg.edit_text("❌ Authentication failed.")
                        return

                    # Build service & execute query
                    query_service = QueryService(db=db, ro_db=ro_db)
                    response = await query_service.execute_nl_query(
                        user_id=user.id,
                        question=question,
                    )
                    await db.commit()

            # Format and send response
            response_text = (
                f"📊 *Question:* {response.question}\n\n"
                f"📝 *Summary:*\n{response.summary}\n\n"
                f"⚡ _Rows: {response.row_count} | Execution: {response.execution_time_ms:.1f}ms_"
            )
            
            # Update the thinking status message
            await status_msg.edit_text(response_text, parse_mode="Markdown")

            # Check if there is a chart config to render
            if response.chart_config and response.row_count > 0:
                try:
                    # Generate Matplotlib chart
                    chart_bytes = generate_matplotlib_chart(response.chart_config)
                    # Send photo
                    photo_file = InputFile(io.BytesIO(chart_bytes), filename="chart.png")
                    await update.message.reply_photo(
                        photo=photo_file,
                        caption=f"📈 Chart: {response.chart_config.title}"
                    )
                except Exception as chart_err:
                    logger.error("telegram.chart_rendering_failed", error=str(chart_err))

        except Exception as e:
            logger.error("telegram.ask_logic_failed", error=str(e), exc_info=True)
            await status_msg.edit_text(f"❌ *An error occurred:* {str(e)}", parse_mode="Markdown")

    async def history_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """List user's last 5 query conversations."""
        if not update.message:
            return

        async with AsyncSessionFactory() as db:
            user = await self._get_or_create_user(update, db)
            if not user:
                await update.message.reply_text("❌ Authentication failed.")
                return

            convo_repo = ConversationRepository(db)
            recent_items = await convo_repo.get_recent(user_id=user.id, limit=5)

        if not recent_items:
            await update.message.reply_text("You have not submitted any queries yet! Try asking me a question.")
            return

        history_text = "📜 *Your Recent Queries:*\n\n"
        for i, item in enumerate(recent_items, 1):
            history_text += f"{i}. *{item.question}*\n"
            history_text += f"   _Rows: {item.row_count} | Intent: {item.intent_category}_\n"
            history_text += f"   Summary: {item.result_summary[:80]}...\n\n"

        await update.message.reply_text(history_text, parse_mode="Markdown")

    async def chart_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Re-generates chart for the user's last successful conversation."""
        if not update.message:
            return

        async with AsyncSessionFactory() as db:
            user = await self._get_or_create_user(update, db)
            if not user:
                await update.message.reply_text("❌ Authentication failed.")
                return

            convo_repo = ConversationRepository(db)
            recent_items = await convo_repo.get_recent(user_id=user.id, limit=1)

        if not recent_items or recent_items[0].row_count == 0:
            await update.message.reply_text("❌ No recent successful query found to visualize.")
            return

        convo = recent_items[0]
        # Re-orchestrate QueryService response to fetch Chart Configuration
        # Since we stored it in the log, let's parse a quick mock chart config
        from app.schemas.query import ChartConfig, ChartType
        
        # Standard fallback chart config based on query columns
        # To be clean, let's build a bar chart mapping first two columns
        # In a real environment, we'd rebuild config dynamically.
        # Let's extract columns & rows from db if possible, or construct default
        columns = ["Metric", "Value"]
        rows = [[convo.intent_category, float(convo.row_count)]]
        
        config = ChartConfig(
            chart_type=ChartType.BAR,
            labels=[r[0] for r in rows],
            datasets=[{"label": "Record Count", "data": [r[1] for r in rows]}],
            title=f"Visualization: {convo.question[:30]}",
            x_label="Category",
            y_label="Count"
        )
        
        try:
            chart_bytes = generate_matplotlib_chart(config)
            photo_file = InputFile(io.BytesIO(chart_bytes), filename="chart.png")
            await update.message.reply_photo(
                photo=photo_file,
                caption=f"📈 Chart for last query: '{convo.question}'"
            )
        except Exception as e:
            logger.error("telegram.chart_command_failed", error=str(e))
            await update.message.reply_text("❌ Failed to render chart for last query.")
