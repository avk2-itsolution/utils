class BitrixObjectException(Exception):
    pass


class NotFoundObject(BitrixObjectException):
    pass


class MultipleObjectsReturned(BitrixObjectException):
    pass
