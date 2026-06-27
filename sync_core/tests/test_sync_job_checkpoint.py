from __future__ import annotations

import unittest

from utils.sync_core.dto import ExternalKey, Payload, Projection, SyncItemState, SyncItemStatus, TargetUpsertResult
from utils.sync_core.errors import TemporaryError
from utils.sync_core.sync_job import SyncJob


class DummySource:
    def __init__(self, count: int):
        self.count = count
        self.last_checkpoint: str | None = None

    def fetch(self, since_token):
        def _iter():
            for i in range(1, self.count + 1):
                self.last_checkpoint = f"cp-{i}"
                yield ExternalKey(system="sys", key=str(i)), Payload(data=f"item-{i}", version=str(i))

        return _iter(), lambda: self.last_checkpoint

    def validate(self, key, payload):
        return None


class DummyMapper:
    def validate(self, key, payload):
        return None

    def map(self, key, payload):
        return Projection(kind="kind", data=payload.data)


class DummyTarget:
    def __init__(self, fail_on: str | None = None):
        self.fail_on = fail_on

    def validate(self, key, projection):
        return None

    def upsert(self, key, projection, binding=None, version=None):
        if key.key == self.fail_on:
            raise TemporaryError("temp fail")
        return TargetUpsertResult.completed(f"internal-{key.key}")


class DummyDeferredTarget:
    def validate(self, key, projection):
        return None

    def upsert(self, key, projection, binding=None, version=None):
        return TargetUpsertResult.deferred(command_id=int(key.key))


class DummyStateStore:
    def __init__(self):
        self.saved_checkpoints: list[str] = []
        self.item_states: dict[str, SyncItemState] = {}

    def get_checkpoint(self, stream):
        return None

    def save_checkpoint(self, stream, token):
        self.saved_checkpoints.append(token)

    def bind(self, key, internal_id, version):
        return None

    def get_binding(self, key):
        return None

    def iter_bindings(self, system):
        return []

    def validate_binding(self, key, binding):
        return None

    def get_item_state(self, key):
        return self.item_states.get(key.key)

    def save_item_state(self, state):
        self.item_states[state.key.key] = state


class DummyLogger:
    def on_skipped(self, key, reason):
        return None

    def on_created(self, key, internal_id):
        return None

    def on_updated(self, key, internal_id):
        return None

    def on_error(self, key, exc):
        return None


class SyncJobCheckpointTest(unittest.TestCase):
    def test_deferred_checkpoint_saved_in_batches(self):
        state = DummyStateStore()
        job = SyncJob(
            stream="s",
            source=DummySource(count=5),
            mapper=DummyMapper(),
            target=DummyTarget(),
            state=state,
            logger=DummyLogger(),
            checkpoint_save_every=3,
        )

        job.run()

        self.assertEqual(state.saved_checkpoints, ["cp-3", "cp-5", "cp-5"])

    def test_retryable_temp_error_blocks_checkpoint(self):
        state = DummyStateStore()
        job = SyncJob(
            stream="s",
            source=DummySource(count=2),
            mapper=DummyMapper(),
            target=DummyTarget(fail_on="2"),
            state=state,
            logger=DummyLogger(),
            checkpoint_save_every=1,
        )

        result = job.run()

        self.assertEqual(state.saved_checkpoints, ["cp-1"])
        self.assertEqual(result.failed, 1)
        saved_state = state.item_states["2"]
        self.assertEqual(saved_state.status, SyncItemStatus.TEMP_ERROR)
        self.assertEqual(saved_state.attempts, 1)

    def test_deferred_item_becomes_pending_and_blocks_checkpoint(self):
        state = DummyStateStore()
        job = SyncJob(
            stream="s",
            source=DummySource(count=2),
            mapper=DummyMapper(),
            target=DummyDeferredTarget(),
            state=state,
            logger=DummyLogger(),
            checkpoint_save_every=1,
        )

        result = job.run()

        self.assertEqual(state.saved_checkpoints, [])
        self.assertEqual(result.pending, 2)
        self.assertEqual(result.skipped, 0)
        self.assertEqual(state.item_states["1"].status, SyncItemStatus.PENDING)
        self.assertEqual(state.item_states["2"].status, SyncItemStatus.PENDING)


if __name__ == "__main__":
    unittest.main()
