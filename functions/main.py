"""
Firebase Cloud Function entry point — scheduled sync job.

The scheduler cron expression is set in firebase.json under
``functions[].schedule``.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Logging — structured JSON format for Google Cloud Logging
# ---------------------------------------------------------------------------
import json
import logging

import firebase_admin
from firebase_admin import firestore_async
from firebase_functions import scheduler_fn

from src.config.loader import load_config
from src.core.interfaces import MessengerAccount
from src.core.orchestrator import SyncOrchestrator, SyncPair
from src.storage.firestore import FirestoreStateStorage


class _JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "severity": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
        }
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_entry)


_handler = logging.StreamHandler()
_handler.setFormatter(_JsonFormatter())
logging.basicConfig(handlers=[_handler], level=logging.INFO, force=True)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Firebase app initialisation (idempotent)
# ---------------------------------------------------------------------------
if not firebase_admin._apps:
    firebase_admin.initialize_app()


def _build_messenger(messenger_id: str, account_id: str, credentials_ref: str, write_strategy: str):
    """Instantiate the correct Reader / Writer for *messenger_id*.

    NOTE: This factory will be expanded after Human Checkpoint 1 once the
    concrete messenger libraries are confirmed.  Until then it raises for
    unknown messenger types so that misconfiguration is caught at startup.
    """
    if messenger_id == "telegram":
        from src.messengers.telegram.reader import TelegramReader
        from src.messengers.telegram.writer import TelegramWriter

        account = MessengerAccount(
            messenger_id=messenger_id,
            account_id=account_id,
            credentials_ref=credentials_ref,
        )
        return TelegramReader(), TelegramWriter(strategy=write_strategy), account

    if messenger_id == "vk":
        from src.messengers.vk.reader import VKReader
        from src.messengers.vk.writer import VKWriter

        account = MessengerAccount(
            messenger_id=messenger_id,
            account_id=account_id,
            credentials_ref=credentials_ref,
        )
        return VKReader(), VKWriter(strategy=write_strategy), account

    raise NotImplementedError(f"Unsupported messenger: {messenger_id!r}")


# ---------------------------------------------------------------------------
# Cloud Function
# ---------------------------------------------------------------------------

@scheduler_fn.on_schedule(schedule="every 5 minutes")
def sync(event: scheduler_fn.ScheduledEvent) -> None:
    """Scheduled entry point — runs the sync orchestrator."""
    import asyncio

    asyncio.run(_run_sync())


async def _run_sync() -> None:
    config = load_config()
    db = firestore_async.client()
    storage = FirestoreStateStorage(
        db,
        collection=config.sync_state.collection,
        document=config.sync_state.document,
    )

    pairs: list[SyncPair] = []
    for pair_cfg in config.sync_pairs:
        src_reader, _, src_account = _build_messenger(
            pair_cfg.source.messenger,
            pair_cfg.source.account_id,
            pair_cfg.source.credentials_ref,
            pair_cfg.write_strategy,
        )
        _, tgt_writer, tgt_account = _build_messenger(
            pair_cfg.target.messenger,
            pair_cfg.target.account_id,
            pair_cfg.target.credentials_ref,
            pair_cfg.write_strategy,
        )
        pairs.append(
            SyncPair(
                reader=src_reader,
                source_account=src_account,
                writer=tgt_writer,
                target_account=tgt_account,
            )
        )

    orchestrator = SyncOrchestrator(pairs)
    await orchestrator.run(storage)
