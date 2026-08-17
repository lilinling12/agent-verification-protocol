from __future__ import annotations

import sys
import types
import unittest
from unittest.mock import patch

from avp_ref import __version__
from avp_ref import http_server


class _FakeFastAPI:
    def __init__(self, *, title: str, version: str) -> None:
        self.title = title
        self.version = version

    @staticmethod
    def get(_path: str):
        return lambda function: function

    @staticmethod
    def post(_path: str):
        return lambda function: function


class _FakeHTTPException(Exception):
    def __init__(self, status_code: int, detail: object | None = None) -> None:
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail


class HTTPServerMetadataTest(unittest.TestCase):
    def test_application_version_matches_distribution_version(self) -> None:
        fastapi = types.ModuleType("fastapi")
        fastapi.FastAPI = _FakeFastAPI
        fastapi.HTTPException = _FakeHTTPException

        with patch.dict(sys.modules, {"fastapi": fastapi}):
            app = http_server.create_app()

        self.assertEqual(__version__, app.version)


if __name__ == "__main__":
    unittest.main()
