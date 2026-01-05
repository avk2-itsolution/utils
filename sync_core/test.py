from django.db import models

from telephony.functions.helpers import get_token
from utils.sync_core.interfaces.mapper import Mapper
from utils.sync_core.interfaces.source import Source
from utils.sync_core.interfaces.state_store import StateStore
from utils.sync_core.interfaces.target import Target
from utils.sync_core.sync_job import SyncJob


class SyncBindingModel(models.Model):
    system = models.CharField(max_length=64)
    ext_key = models.CharField(max_length=255, db_index=True)
    internal_id = models.CharField(max_length=64)
    version = models.CharField(max_length=128, null=True, blank=True)

    class Meta:
        unique_together = (("system", "ext_key"),)


class SyncCheckpointModel(models.Model):
    stream = models.CharField(max_length=128, unique=True)
    token = models.CharField(max_length=256)

# sync_core/state_store.py
from typing import Optional

from utils.sync_core.dto import ExternalKey, Binding, SyncResult


class DjangoStateStore(StateStore):
    def get_checkpoint(self, stream: str) -> Optional[str]:
        obj = SyncCheckpointModel.objects.filter(stream=stream).first()
        return obj.token if obj else None

    def save_checkpoint(self, stream: str, token: str) -> None:
        SyncCheckpointModel.objects.update_or_create(
            stream=stream,
            defaults={"token": token},
        )

    def bind(self, key: ExternalKey, internal_id: str, version: Optional[str]) -> None:
        SyncBindingModel.objects.update_or_create(
            system=key.system,
            ext_key=key.key,
            defaults={"internal_id": internal_id, "version": version},
        )

    def get_binding(self, key: ExternalKey) -> Optional[Binding]:
        obj = (
            SyncBindingModel.objects
            .filter(system=key.system, ext_key=key.key)
            .only("internal_id", "version")
            .first()
        )
        if not obj:
            return None
        return Binding(internal_id=obj.internal_id, version=obj.version)

# sync_core/sources/tickets_api_source.py
from typing import Iterable, Optional
import requests

from utils.sync_core.dto.dto import ExternalKey, Payload


class TicketsApiSource(Source):
    """Читает тикеты из внешнего API постранично."""

    def __init__(self, base_url: str, api_key: str, system_code: str = "tickets_api"):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.system_code = system_code

    def fetch(self, since_token: Optional[str]) -> Iterable[tuple[ExternalKey, Payload]]:
        params = {}
        if since_token:
            params["since"] = since_token

        next_page: Optional[str] = f"{self.base_url}/tickets"
        while next_page:
            resp = requests.get(
                next_page,
                headers={"Authorization": f"Bearer {self.api_key}"},
                params=params,
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json()
            for item in data["results"]:
                key = ExternalKey(system=self.system_code, key=str(item["id"]))
                payload = Payload(
                    data=item,
                    version=item.get("updated_at"),  # или хеш
                )
                yield key, payload
            next_page = data.get("next")
            params = {}  # для next обычно параметры уже закодированы в URL


# sync_core/mappers/ticket_to_activity.py
from utils.sync_core.dto.dto import ExternalKey, Payload, Projection


class TicketToActivityMapper(Mapper):
    """Маппинг тикета во внутреннюю проекцию дела Bitrix."""

    def map(self, key: ExternalKey, payload: Payload) -> Projection:
        d = payload.data
        return Projection(
            kind="activity",
            fields={
                "OWNER_TYPE_ID": 2,                # 2 = Сделка
                "OWNER_ID": d["deal_id"],          # ожидаем, что API отдаёт это поле
                "TYPE_ID": 4,                      # условный тип дела
                "SUBJECT": d["title"],
                "DESCRIPTION": d.get("description", ""),
                "DESCRIPTION_TYPE": 1,             # text
                "RESPONSIBLE_ID": d["responsible_bx_id"],
                "DEADLINE": d["deadline_iso"],     # ISO-строка
            },
        )


# sync_core/targets/bx_activity_target.py
from django.utils import timezone

from utils.sync_core.dto.dto import ExternalKey, Projection


class BxActivityTarget(Target):
    """Создаёт/обновляет дела в Bitrix24 по проекциям."""

    def __init__(self, but):
        self.but = but  # BitrixUserToken

    def upsert(self, key: ExternalKey, projection: Projection) -> str:
        assert projection.kind == "activity"
        fields = dict(projection.fields)

        fields.setdefault("RESPONSIBLE_ID", 1)
        fields.setdefault("DEADLINE", timezone.now().isoformat())
        fields["UF_EXTERNAL_KEY"] = f"{key.system}:{key.key}"

        existing = self.but.call_api_method(
            "crm.activity.list",
            {
                "filter": {"UF_EXTERNAL_KEY": fields["UF_EXTERNAL_KEY"]},
                "select": ["ID"],
            },
        )
        if existing and existing.get("total", 0) > 0:
            act_id = existing["result"][0]["ID"]
            self.but.call_api_method(
                "crm.activity.update", {"id": act_id, "fields": fields}
            )
            return str(act_id)

        created = self.but.call_api_method(
            "crm.activity.add", {"fields": fields}
        )
        return str(created["result"])


def sync_tickets_to_bx_activities() -> SyncResult:
    but = get_token()
    source = TicketsApiSource(
        base_url="https://external.example.com/api",
        api_key="SECRET",
        system_code="tickets_api",
    )
    mapper = TicketToActivityMapper()
    target = BxActivityTarget(but)
    state = DjangoStateStore()

    job = SyncJob(
        stream="tickets_api->bx.activity",
        source=source,
        mapper=mapper,
        target=target,
        state=state,
    )
    return job.run()
