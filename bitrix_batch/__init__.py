__all__ = [
    "BitrixBatchCommand",
    "process_pending_bitrix_batch_commands",
]


def __getattr__(name):
    if name in {"BitrixBatchCommand", "process_pending_bitrix_batch_commands"}:
        from .models import BitrixBatchCommand
        from .runner import process_pending_bitrix_batch_commands

        exports = {
            "BitrixBatchCommand": BitrixBatchCommand,
            "process_pending_bitrix_batch_commands": process_pending_bitrix_batch_commands,
        }
        return exports[name]
    raise AttributeError(name)
