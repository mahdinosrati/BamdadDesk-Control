from starlette.exceptions import HTTPException


class BodyLimit:
    """Enforce actual bytes even when Content-Length is absent or misleading."""
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        maximum = 200 * 1024 * 1024 if scope["path"] == "/api/releases" else 64 * 1024
        consumed = 0

        async def bounded_receive():
            nonlocal consumed
            message = await receive()
            if message["type"] == "http.request":
                consumed += len(message.get("body", b""))
                if consumed > maximum:
                    raise HTTPException(413, "Request too large")
            return message

        await self.app(scope, bounded_receive, send)
