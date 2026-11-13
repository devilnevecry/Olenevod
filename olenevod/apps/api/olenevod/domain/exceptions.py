"""Доменные исключения (чистые, без I/O и фреймворков)."""

from typing import Any


class DomainError(Exception):
    """Базовое доменное исключение."""

    code: str = "domain_error"

    def __init__(self, message: str, code: str | None = None, extra: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.code = code or self.code
        self.extra = extra or {}


class OutOfStock(DomainError):
    """Недостаточно остатка для резерва/отгрузки."""

    code = "out_of_stock"

    def __init__(self, variant_id: str, available: int, requested: int) -> None:
        super().__init__(
            f"Not enough stock for variant {variant_id}: available {available}, requested {requested}",
            extra={"variant_id": variant_id, "available": available, "requested": requested},
        )


class InvalidTransition(DomainError):
    """Недопустимый переход статуса (заказ, резерв, перемещение)."""

    code = "invalid_transition"

    def __init__(self, entity: str, from_status: str, to_status: str) -> None:
        super().__init__(
            f"Invalid transition for {entity}: {from_status} -> {to_status}",
            extra={"entity": entity, "from_status": from_status, "to_status": to_status},
        )


class CityAccessDenied(DomainError):
    """Доступ к данным другого города запрещён."""

    code = "city_access_denied"

    def __init__(self, city_id: str) -> None:
        super().__init__(f"Access to city {city_id} is denied", extra={"city_id": city_id})


class NotFound(DomainError):
    """Запись не найдена."""

    code = "not_found"

    def __init__(self, entity: str, ident: Any) -> None:
        super().__init__(f"{entity} not found: {ident}", extra={"entity": entity, "id": ident})


class AlreadyExists(DomainError):
    """Запись с таким ключом уже существует."""

    code = "already_exists"

    def __init__(self, entity: str, ident: Any) -> None:
        super().__init__(f"{entity} already exists: {ident}", extra={"entity": entity, "id": ident})
