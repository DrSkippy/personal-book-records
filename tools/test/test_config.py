import json
import os
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'book_service'))

BASE_CONFIG = {
    "username": "user",
    "password": "pass",
    "database": "book_collection",
    "host": "localhost",
    "port": 5432,
    "isbn_com": {"url_isbn": "https://example.com/{}", "key": "isbn-key"},
    "api_key": "file-api-key",
    "ai_agent": {
        "chat_host": "http://file-chat-host:11434",
        "chat_model": "file-chat-model",
        "embed_host": "http://file-embed-host:1234",
        "embed_model": "file-embed-model",
        "embed_api_key": "file-embed-key",
        "embed_dimensions": 512,
    },
}


class TestConfig(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
        json.dump(BASE_CONFIG, self.tmp)
        self.tmp.close()
        self.env_patcher = patch.dict(os.environ, {"BOOKDB_CONFIG": self.tmp.name}, clear=False)
        self.env_patcher.start()

        global config
        from booksdb import config

    def tearDown(self):
        self.env_patcher.stop()
        os.unlink(self.tmp.name)

    def test_ai_agent_values_from_file(self):
        config.read_json_configuration()
        self.assertEqual(config.EMBED_HOST, "http://file-embed-host:1234")
        self.assertEqual(config.EMBED_MODEL, "file-embed-model")
        self.assertEqual(config.EMBED_API_KEY, "file-embed-key")
        self.assertEqual(config.EMBED_DIMENSIONS, 512)

    @patch.dict(os.environ, {
        "AI_EMBED_HOST": "http://env-embed-host:9999",
        "AI_EMBED_MODEL": "env-embed-model",
        "AI_EMBED_API_KEY": "env-embed-key",
        "AI_EMBED_DIMENSIONS": "1024",
    })
    def test_ai_agent_env_vars_override_file(self):
        config.read_json_configuration()
        self.assertEqual(config.EMBED_HOST, "http://env-embed-host:9999")
        self.assertEqual(config.EMBED_MODEL, "env-embed-model")
        self.assertEqual(config.EMBED_API_KEY, "env-embed-key")
        self.assertEqual(config.EMBED_DIMENSIONS, 1024)

    def test_embed_dimensions_defaults_when_absent(self):
        cfg = dict(BASE_CONFIG)
        cfg["ai_agent"] = {}
        with open(self.tmp.name, "w") as f:
            json.dump(cfg, f)
        config.read_json_configuration()
        self.assertIsNone(config.EMBED_HOST)
        self.assertIsNone(config.EMBED_MODEL)
        self.assertEqual(config.EMBED_DIMENSIONS, 768)

    def test_chat_values_from_file(self):
        config.read_json_configuration()
        self.assertEqual(config.CHAT_HOST, "http://file-chat-host:11434")
        self.assertEqual(config.CHAT_MODEL, "file-chat-model")
        self.assertIsNone(config.CHAT_API_KEY)

    @patch.dict(os.environ, {
        "AI_CHAT_HOST": "http://env-chat-host:9999",
        "AI_CHAT_MODEL": "env-chat-model",
        "AI_CHAT_API_KEY": "env-chat-key",
    })
    def test_chat_env_vars_override_file(self):
        config.read_json_configuration()
        self.assertEqual(config.CHAT_HOST, "http://env-chat-host:9999")
        self.assertEqual(config.CHAT_MODEL, "env-chat-model")
        self.assertEqual(config.CHAT_API_KEY, "env-chat-key")

    def test_chat_values_none_when_absent(self):
        cfg = dict(BASE_CONFIG)
        cfg["ai_agent"] = {}
        with open(self.tmp.name, "w") as f:
            json.dump(cfg, f)
        config.read_json_configuration()
        self.assertIsNone(config.CHAT_HOST)
        self.assertIsNone(config.CHAT_MODEL)
        self.assertIsNone(config.CHAT_API_KEY)


if __name__ == '__main__':
    unittest.main()
