"""Telegram bot for private dilution alerts (Opción Privada)."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import Optional

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)

from config import get_settings
from db.database import Database
from pipeline import ScanPipeline
from rag.rag_engine import RAGEngine
from scanners.company_facts import CompanyFactsClient
from scanners.dilution_scanner import DilutionScanner
from scanners.rss_monitor import RSSMonitor

logger = logging.getLogger(__name__)


def _fmt_money(amount: Optional[float]) -> str:
    if amount is None:
        return "N/A"
    if amount >= 1_000_000_000:
        return f"${amount / 1_000_000_000:.2f}B"
    if amount >= 1_000_000:
        return f"${amount / 1_000_000:.2f}M"
    return f"${amount:,.0f}"


def _risk_emoji(level: Optional[str]) -> str:
    if not level:
        return "⚪"
    u = str(level).upper()
    if u in {"HIGH", "CRITICAL"}:
        return "🔴 HIGH"
    if u in {"MEDIUM", "MED"}:
        return "🟡 MED"
    return "🟢 LOW"


def format_alert_message(filing: dict) -> str:
    """Format dilution alert for Telegram."""
    ticker = filing.get("ticker") or filing.get("cik", "?")
    form = filing.get("form_type", "?")
    amount = filing.get("shelf_amount_usd")
    dilution = filing.get("dilution_percentage")
    dil_str = f"{dilution:.1f}%" if dilution is not None else "N/A"
    risk = _risk_emoji(filing.get("risk_level"))
    atm = "✅" if filing.get("has_atm") else "❌"
    ratchet = "✅" if filing.get("has_full_ratchet") else "❌"
    prefunded = "✅" if filing.get("has_prefunded_warrants") else "❌"
    url = filing.get("filing_url") or filing.get("source_url") or ""

    return (
        f"🔥 *DILUCIÓN DETECTADA*\n"
        f"Ticker: `{ticker}`\n"
        f"Form: {form}\n"
        f"Amount: {_fmt_money(amount)}\n"
        f"Dilución estimada: {dil_str} {risk}\n"
        f"Cláusulas: ATM {atm} | Full Ratchet {ratchet} | Pre-Funded Warrants {prefunded}\n"
        f"Filing: {url}"
    )


class TelegramBot:
    """Async Telegram bot for SEC dilution monitoring."""

    def __init__(self) -> None:
        self.settings = get_settings()
        if not self.settings.telegram_bot_token:
            raise ValueError("TELEGRAM_BOT_TOKEN is required for Telegram mode.")
        self.db = Database()
        self.db.init()
        self.facts = CompanyFactsClient()
        self.pipeline = ScanPipeline()
        self.scanner = DilutionScanner()
        self._rss_task: Optional[asyncio.Task] = None

    async def cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        text = (
            "👋 *SEC Dilution Tracker Bot*\n\n"
            "Comandos disponibles:\n"
            "/scan TICKER — escanear dilución\n"
            "/alerts — alertas últimas 24h\n"
            "/watch TICKER — añadir a watchlist\n"
            "/unwatch TICKER — quitar de watchlist\n"
            "/watchlist — ver watchlist\n"
            "/top — top 10 dilución\n"
            "/ask TICKER pregunta — RAG sobre filing\n"
            "/monitor — scan diario manual\n"
            "/status — estado del bot"
        )
        await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

    async def cmd_scan(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not context.args:
            await update.message.reply_text("Uso: /scan TICKER")
            return
        ticker = context.args[0].upper()
        await update.message.reply_text(f"⏳ Escaneando `{ticker}`...", parse_mode=ParseMode.MARKDOWN)
        try:
            result = await asyncio.to_thread(
                self.pipeline.scan_ticker, ticker, run_rag=False
            )
            lines = [f"✅ *{ticker}* — {result.filings_processed} filings"]
            for f in result.filings[:5]:
                pct = f"{f.dilution_percentage:.1f}%" if f.dilution_percentage else "N/A"
                lines.append(f"• {f.form_type} | Dilución: {pct} | {_risk_emoji(f.risk_level.value if f.risk_level else None)}")
                if f.source_url:
                    self.db.save_dilution_alert(f)
            await update.message.reply_text("\n".join(lines), parse_mode=ParseMode.MARKDOWN)
        except Exception as exc:
            await update.message.reply_text(f"❌ Error: {exc}")

    async def cmd_alerts(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        alerts = self.db.get_recent_alerts(hours=24, limit=20)
        if not alerts:
            await update.message.reply_text("Sin alertas en las últimas 24h.")
            return
        for alert in alerts[:10]:
            await update.message.reply_text(
                format_alert_message(alert),
                parse_mode=ParseMode.MARKDOWN,
                disable_web_page_preview=True,
            )

    async def cmd_watch(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not context.args:
            await update.message.reply_text("Uso: /watch TICKER")
            return
        ticker = context.args[0].upper()
        cik = self.facts.resolve_cik_from_ticker(ticker)
        if not cik:
            await update.message.reply_text(f"❌ No se encontró CIK para `{ticker}`", parse_mode=ParseMode.MARKDOWN)
            return
        chat_id = update.effective_chat.id
        if self.db.add_watchlist(chat_id, cik, ticker):
            await update.message.reply_text(f"✅ `{ticker}` añadido a watchlist", parse_mode=ParseMode.MARKDOWN)
        else:
            await update.message.reply_text(f"`{ticker}` ya está en watchlist", parse_mode=ParseMode.MARKDOWN)

    async def cmd_unwatch(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not context.args:
            await update.message.reply_text("Uso: /unwatch TICKER")
            return
        ticker = context.args[0].upper()
        if self.db.remove_watchlist(update.effective_chat.id, ticker):
            await update.message.reply_text(f"✅ `{ticker}` eliminado", parse_mode=ParseMode.MARKDOWN)
        else:
            await update.message.reply_text(f"`{ticker}` no estaba en watchlist", parse_mode=ParseMode.MARKDOWN)

    async def cmd_watchlist(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        items = self.db.get_watchlist(update.effective_chat.id)
        if not items:
            await update.message.reply_text("Watchlist vacía. Usa /watch TICKER")
            return
        lines = ["📋 *Watchlist:*"]
        for item in items:
            lines.append(f"• `{item['ticker']}` (CIK {item['cik']})")
        await update.message.reply_text("\n".join(lines), parse_mode=ParseMode.MARKDOWN)

    async def cmd_top(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        top = self.db.get_top(limit=10)
        if not top:
            await update.message.reply_text("No hay datos de dilución aún.")
            return
        lines = ["🔥 *Top 10 Dilución:*"]
        for i, row in enumerate(top, 1):
            t = row.get("ticker") or row.get("cik")
            pct = row.get("dilution_percentage")
            pct_s = f"{pct:.1f}%" if pct is not None else "N/A"
            lines.append(f"{i}. `{t}` — {pct_s} ({row.get('form_type', '?')})")
        await update.message.reply_text("\n".join(lines), parse_mode=ParseMode.MARKDOWN)

    async def cmd_ask(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if len(context.args) < 2:
            await update.message.reply_text("Uso: /ask TICKER tu pregunta aquí")
            return
        ticker = context.args[0].upper()
        question = " ".join(context.args[1:])
        await update.message.reply_text(f"🤖 Analizando `{ticker}`...", parse_mode=ParseMode.MARKDOWN)
        try:
            engine = RAGEngine()
            response = await asyncio.to_thread(
                engine.query_ticker, ticker, question=question
            )
            cik = self.facts.resolve_cik_from_ticker(ticker) or ""
            self.db.save_rag_analysis(cik, "", question, response)
            answer = response.answer[:4000]
            await update.message.reply_text(f"*Respuesta:*\n{answer}", parse_mode=ParseMode.MARKDOWN)
        except Exception as exc:
            await update.message.reply_text(f"❌ {exc}")

    async def cmd_monitor(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        await update.message.reply_text("⏳ Ejecutando scan diario SEC...")
        try:
            filings = await asyncio.to_thread(self.scanner.scan_date)
            count = 0
            for f in filings:
                from datetime import date as date_cls
                from models import FilingDilution, RiskLevel
                alert = FilingDilution(
                    accession_number=f.file_path.split("/")[-1].replace(".txt", "")[:20] or f"cik-{f.cik}-{f.filed_date}",
                    cik=f.cik,
                    ticker=None,
                    form_type=f.form_type,
                    filed_date=f.filed_date,
                    source_url=f.filing_url,
                    risk_level=RiskLevel.HIGH if "S-3" in f.form_type or "424B" in f.form_type else RiskLevel.MEDIUM,
                    summary=f.company_name,
                )
                self.db.save_dilution_alert(alert)
                count += 1
            self.db.set_bot_state("last_scan", datetime.utcnow().isoformat())
            await update.message.reply_text(f"✅ Scan completo: {count} filings críticos detectados")
        except Exception as exc:
            await update.message.reply_text(f"❌ Error en scan: {exc}")

    async def cmd_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        stats = self.db.stats()
        last_scan = self.db.get_bot_state("last_scan") or "never"
        text = (
            f"🟢 *Bot Status*\n"
            f"Mode: `{stats.get('mode', '?')}`\n"
            f"Private: `{stats.get('private_mode', '?')}`\n"
            f"Filings: {stats.get('filings', stats.get('total_filings', 0))}\n"
            f"Companies: {stats.get('companies', stats.get('total_companies', 0))}\n"
            f"Last scan: {last_scan}\n"
            f"RSS daemon: {'running' if self._rss_task and not self._rss_task.done() else 'stopped'}"
        )
        await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

    async def _on_rss_alert(self, alert, app: Application) -> None:
        """Notify watchlist users when RSS detects critical filing."""
        from models import FilingDilution, RiskLevel
        filing = FilingDilution(
            accession_number=alert.accession_number,
            cik=alert.cik,
            ticker=None,
            form_type=alert.form_type,
            filed_date=datetime.utcnow().date(),
            source_url=alert.filing_url,
            summary=alert.summary,
            risk_level=RiskLevel.HIGH,
        )
        self.db.save_dilution_alert(filing)
        msg = format_alert_message(filing.model_dump())
        watchers = self.db.get_watchers_for_ticker(alert.company_name[:4].upper())
        for chat_id in watchers:
            try:
                await app.bot.send_message(chat_id=chat_id, text=msg, parse_mode=ParseMode.MARKDOWN)
            except Exception as exc:
                logger.error("Failed to notify chat %s: %s", chat_id, exc)

    async def _rss_loop(self, app: Application) -> None:
        monitor = RSSMonitor()
        interval = self.settings.rss_poll_interval_seconds
        while True:
            try:
                alerts = await asyncio.to_thread(monitor.poll_once)
                for alert in alerts:
                    await self._on_rss_alert(alert, app)
                    logger.info("RSS alert processed: %s %s", alert.form_type, alert.company_name)
            except Exception as exc:
                logger.error("RSS loop error: %s", exc)
            await asyncio.sleep(interval)

    def run(self, daemon: bool = False) -> None:
        """Start bot (blocking)."""

        async def post_init(application: Application) -> None:
            if daemon:
                self._rss_task = asyncio.create_task(self._rss_loop(application))
                logger.info("RSS daemon started")

        app = (
            Application.builder()
            .token(self.settings.telegram_bot_token)
            .post_init(post_init)
            .build()
        )
        app.add_handler(CommandHandler("start", self.cmd_start))
        app.add_handler(CommandHandler("scan", self.cmd_scan))
        app.add_handler(CommandHandler("alerts", self.cmd_alerts))
        app.add_handler(CommandHandler("watch", self.cmd_watch))
        app.add_handler(CommandHandler("unwatch", self.cmd_unwatch))
        app.add_handler(CommandHandler("watchlist", self.cmd_watchlist))
        app.add_handler(CommandHandler("top", self.cmd_top))
        app.add_handler(CommandHandler("ask", self.cmd_ask))
        app.add_handler(CommandHandler("monitor", self.cmd_monitor))
        app.add_handler(CommandHandler("status", self.cmd_status))
        logger.info("Telegram bot starting (daemon=%s)", daemon)
        app.run_polling(allowed_updates=Update.ALL_TYPES)


def run_telegram_bot(daemon: bool = False) -> None:
    TelegramBot().run(daemon=daemon)
