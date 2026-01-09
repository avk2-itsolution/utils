from typing import Optional, Iterable

from .dto import SyncResult, Binding, Projection, ExternalKey, Payload, SyncItemState, SyncItemStatus
from .errors import SyncError, TemporaryError, PermanentError, TemporarySourceError, PermanentSourceError
from .interfaces import Source, Mapper, Target, StateStore, SyncLogger


class SyncJob:
    # https://chatgpt.com/c/690e4884-b0e0-832e-8bdd-0296f3498a42
    def __init__(self, stream: str, source: Source, mapper: Mapper, target: Target,
                 state: StateStore, logger: SyncLogger, max_attempts: int = 3):
        self.stream = stream          # имя потока синка, для чекпоинта
        self.source = source          # откуда читаем внешние данные
        self.mapper = mapper          # чем преобразуем во внутреннюю проекцию
        self.target = target          # куда пишем (Bitrix/БД)
        self.state = state            # “память синхронизации” (чекпоинты и биндинги)
        self.logger = logger          # логирование событий синка
        self.max_attempts = max_attempts
        self._last_fetch_checkpoint: Optional[str] = None

    def run(self) -> SyncResult:
        checkpoint: Optional[str] = self.state.get_checkpoint(self.stream)
        sync_result = SyncResult()
        has_retryable_temp_errors = False  # есть ли что ретраить

        items: Iterable[tuple[ExternalKey, Payload]] = self._iter_source_items(checkpoint)
        for key, payload in items:
            stored_state: Optional[SyncItemState] = self.state.get_item_state(key)
            prev_state: Optional[SyncItemState] = (
                stored_state
                if stored_state is not None and stored_state.version == payload.version
                else None
            )

            if prev_state is not None:  # не трогаем PERM_ERROR и превышенные попытки
                if prev_state.status is SyncItemStatus.PERM_ERROR:
                    self.logger.on_skipped(key, "perm_error")
                    sync_result = sync_result.inc(skipped=1)
                    continue
                if prev_state.status is SyncItemStatus.TEMP_ERROR and prev_state.attempts >= self.max_attempts:
                    self.logger.on_skipped(key, "max_attempts")
                    sync_result = sync_result.inc(skipped=1)
                    continue

            try:
                sync_result = self._process_item(
                    key=key, payload=payload, prev_state=prev_state, sync_result=sync_result)

            except TemporaryError as exc:
                # посчитаем попытку и решим, нужен ли ещё ретрай
                attempts_before = prev_state.attempts if prev_state else 0
                attempts_after = attempts_before + 1
                if attempts_after < self.max_attempts:
                    has_retryable_temp_errors = True

                self._save_failed_state(
                    key=key, payload=payload, prev_state=prev_state, status=SyncItemStatus.TEMP_ERROR, exc=exc)
                sync_result = sync_result.inc(failed=1)
                self.logger.on_error(key, exc)
                continue

            except PermanentError as exc:
                self._save_failed_state(
                    key=key, payload=payload, prev_state=prev_state, status=SyncItemStatus.PERM_ERROR, exc=exc)
                sync_result = sync_result.inc(failed=1)
                self.logger.on_error(key, exc)
                continue

            except SyncError as exc:
                # todo должно отличаться от PermanentError
                self._save_failed_state(
                    key=key, payload=payload, prev_state=prev_state, status=SyncItemStatus.PERM_ERROR, exc=exc)
                sync_result = sync_result.inc(failed=1)
                self.logger.on_error(key, exc)
                continue

        # чекпоинт двигаем только если не осталось TEMP_ERROR с незакрытыми ретраями
        if self._last_fetch_checkpoint is not None and not has_retryable_temp_errors:
            self.state.save_checkpoint(self.stream, self._last_fetch_checkpoint)
        return sync_result

    def _process_item(
            self, *,
            key: ExternalKey,
            payload: Payload,
            prev_state: Optional[SyncItemState],
            sync_result: SyncResult,
    ) -> SyncResult:
        self.source.validate(key, payload)  # 1. техническая проверка сырья

        bound: Optional[Binding] = self.state.get_binding(key)
        if bound:
            self.state.validate_binding(key, bound)  # проверка консистентности StateStore

        if bound and bound.is_up_to_date_for(payload):
            self.logger.on_skipped(key, "same_version")
            self._save_success_state(key, payload, prev_state)
            return sync_result.inc(skipped=1)

        self.mapper.validate(key, payload)  # 2. бизнес-валидация входных данных
        projection: Projection = self.mapper.map(key, payload)  # строим проекцию под целевую систему
        self.target.validate(key, projection)  # 3. валидация перед записью в приёмник
        internal_id = self.target.upsert(key, projection, binding=bound)  # создаём/обновляем сущность в целевой системе
        self.state.bind(key, internal_id, payload.version)  # сохраняем связь ExternalKey ↔ internal_id, version

        self._save_success_state(key, payload, prev_state)

        if bound:
            self.logger.on_updated(key, internal_id)
            return sync_result.inc(updated=1)
        else:
            self.logger.on_created(key, internal_id)
            return sync_result.inc(created=1)

    def _save_success_state(self, key: ExternalKey, payload: Payload, prev_state: Optional[SyncItemState]) -> None:
        attempts = (prev_state.attempts + 1) if prev_state else 1
        self.state.save_item_state(
            SyncItemState(
                key=key,
                version=payload.version,
                status=SyncItemStatus.SUCCESS,
                attempts=attempts,
                last_error=None,
            )
        )

    def _save_failed_state(
        self,
        *,
        key: ExternalKey,
        payload: Payload,
        prev_state: Optional[SyncItemState],
        status: SyncItemStatus,
        exc: Exception,
    ) -> None:
        attempts = (prev_state.attempts + 1) if prev_state else 1
        self.state.save_item_state(
            SyncItemState(
                key=key,
                version=payload.version,
                status=status,
                attempts=attempts,
                last_error=str(exc),
            )
        )

    def _iter_source_items(self, checkpoint: Optional[str]) -> Iterable[tuple[ExternalKey, Payload]]:
        """Обёртка над source.fetch с обработкой ошибок источника."""
        try:
            items, new_checkpoint = self.source.fetch(checkpoint)  # новый контракт
            self._last_fetch_checkpoint = new_checkpoint          # запоминаем чекпоинт
            yield from items                                      # остаёмся генератором
        except (TemporarySourceError, PermanentSourceError) as exc:
            self._log_fetch_error(exc)
            raise

    def _log_fetch_error(self, exc: SyncError) -> None:
        """Логируем ошибку на уровне fetch без конкретного элемента."""
        error_key = ExternalKey(system=self.stream, key="__fetch__")
        self.logger.on_error(error_key, exc)
