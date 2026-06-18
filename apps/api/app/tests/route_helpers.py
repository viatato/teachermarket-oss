from collections.abc import Iterator
from typing import Any

from fastapi.routing import APIRoute


def iter_application_routes(app: Any) -> Iterator[Any]:
    for route in app.routes:
        if isinstance(route, APIRoute):
            yield route
            continue

        effective_candidates = getattr(route, "effective_candidates", None)
        if callable(effective_candidates):
            yield from effective_candidates()


def route_for_endpoint(app: Any, endpoint: Any) -> Any:
    return next(
        route
        for route in iter_application_routes(app)
        if getattr(route, "endpoint", None) is endpoint
    )


def route_dependency_calls(route: Any) -> set[Any]:
    dependant = getattr(route, "dependant")
    return {dependency.call for dependency in dependant.dependencies}
