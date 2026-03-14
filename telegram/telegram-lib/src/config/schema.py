"""
Configuration schema for Synchromessotron.

Configuration is expressed as a YAML file.  Example:

  sync_state:
    collection: sync_state
    document: last_sync

  sync_pairs:
    - source:
        messenger: telegram
        account_id: "+1234567890"
        credentials_ref: TELEGRAM_SESSION
      target:
        messenger: vk
        account_id: "123456789"
        credentials_ref: VK_TOKEN
      write_strategy: repost   # or "forward"

    - source:
        messenger: vk
        account_id: "123456789"
        credentials_ref: VK_TOKEN
      target:
        messenger: telegram
        account_id: "+1234567890"
        credentials_ref: TELEGRAM_SESSION
      write_strategy: forward
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class AccountConfig(BaseModel):
    messenger: str
    account_id: str
    credentials_ref: str


class SyncPairConfig(BaseModel):
    source: AccountConfig
    target: AccountConfig
    write_strategy: str = "repost"


class SyncStateConfig(BaseModel):
    collection: str = "sync_state"
    document: str = "last_sync"


class AppConfig(BaseModel):
    sync_state: SyncStateConfig = Field(default_factory=SyncStateConfig)
    sync_pairs: list[SyncPairConfig]
