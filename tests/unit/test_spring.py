"""Test spring module."""
from unittest.mock import PropertyMock

import pytest
import requests

from config.spring import ConfigClient, config_client, create_config_client

# from tests.unit.test_oauth2 import ResponseMock


class ResponseMock:
    CONFIG = {
        "health": {"config": {"enabled": False}},
        "spring": {
            "cloud": {
                "consul": {
                    "discovery": {
                        "health-check-interval": "10s",
                        "health-check-path": "/manage/health",
                        "instance-id": "pecas-textos:${random.value}",
                        "prefer-ip-address": True,
                        "register-health-check": True,
                    },
                    "host": "discovery",
                    "port": 8500,
                }
            }
        },
    }

    def __init__(self, code=200, ok=True, headers={}):
        self.status_code = code
        self.ok = ok
        self.headers = {"Content-Type": "application/json"}

    def json(self):
        return self.CONFIG


class TestConfigClient:
    CONFIG_EXAMPLE = {
        "health": {"config": {"enabled": False}},
        "spring": {
            "cloud": {
                "consul": {
                    "discovery": {
                        "health-check-interval": "10s",
                        "health-check-path": "/manage/health",
                        "instance-id": "pecas-textos:${random.value}",
                        "prefer-ip-address": True,
                        "register-health-check": True,
                    },
                    "host": "discovery",
                    "port": 8500,
                }
            }
        },
    }

    @pytest.fixture
    def client(self):
        return ConfigClient(app_name="test_app")

    def test_get_config_failed(self, client):
        """SystemExit will be raises because fail_fast it's True by default."""
        with pytest.raises(SystemExit):
            client.get_config()

    def test_get_config(self, client, monkeypatch):
        monkeypatch.setattr(requests, "get", ResponseMock)
        client.get_config()
        assert isinstance(client.config, dict)

    def test_get_config_response_failed(self, client, monkeypatch):
        monkeypatch.setattr(requests, "get", ResponseMock(code=404, ok=False))
        with pytest.raises(SystemExit):
            client.get_config()

    def test_config_property(self, client):
        assert isinstance(client.config, dict)

    def test_default_url_property(self, client):
        assert isinstance(client.url, str)
        assert client.url == "http://localhost:8888/master/test_app-development"

    def test_custom_url_property(self):
        client = ConfigClient(
            app_name="test_app", url="{address}/{branch}/{profile}-{app_name}.yaml"
        )
        assert client.url == "http://localhost:8888/master/development-test_app.yaml"

    def test_decorator_failed(self, client):
        @config_client()
        def inner(c=None):
            assert isinstance(c, ConfigClient)

        with pytest.raises(SystemExit):
            inner()

    def test_decorator(self, client, monkeypatch):
        monkeypatch.setattr(requests, "get", ResponseMock)

        @config_client()
        def inner(c=None):
            assert isinstance(c, ConfigClient)

        inner()

    def test_fail_fast_disabled(self):
        client = ConfigClient(app_name="test_app", fail_fast=False)
        with pytest.raises(ConnectionError):
            client.get_config()

    def test_create_config_client_with_singleton(self, monkeypatch):
        monkeypatch.setattr(requests, "get", ResponseMock)
        client1 = create_config_client()
        client2 = create_config_client()
        assert id(client1) == id(client2)

    def test_get_keys(self, client):
        type(client)._config = PropertyMock(return_value=self.CONFIG_EXAMPLE)
        assert client.get_keys() == self.CONFIG_EXAMPLE.keys()

    def test_get_attribute(self, client):
        type(client)._config = PropertyMock(return_value=self.CONFIG_EXAMPLE)
        response = client.get_attribute("spring.cloud.consul.host")
        assert response is not None
        assert response == "discovery"
