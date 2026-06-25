"""
Shared pytest configuration.

server.py instantiates GAME and CHAT at module-import time. Both create
Agent objects which create a Groq client. We need to ensure:
1. GROQ_API_KEY env var is set so Groq doesn't raise on construction.
2. Groq's actual API calls are mocked so no real HTTP requests are made.

We set a dummy GROQ_API_KEY and patch groq.Groq at the package level so
the mock is in place before any module-level code in server.py runs.
"""

import os
import sys
from unittest.mock import MagicMock, patch

# Set a fake API key so the Groq client can be constructed without error.
# This must happen before any import of groq or agents.agent.
os.environ.setdefault("GROQ_API_KEY", "test-dummy-key-for-pytest")


def _make_groq_instance_mock(reply_text="Mocked LLM reply."):
    """Return a mock Groq *instance* whose chat.completions.create returns reply_text."""
    mock_msg = MagicMock()
    mock_msg.content = reply_text
    mock_choice = MagicMock()
    mock_choice.message = mock_msg
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]
    instance = MagicMock()
    instance.chat.completions.create.return_value = mock_response
    return instance


# Patch groq.Groq (the class) so that instantiating it returns a mock.
# We patch at the 'groq' package level so ALL importers get the mock,
# regardless of whether they do `from groq import Groq` or `import groq`.
_groq_class_mock = MagicMock(return_value=_make_groq_instance_mock())

# Apply the patch immediately (session-level, never stopped during the run).
_patcher = patch("groq.Groq", _groq_class_mock)
_patcher.start()

# Also patch agents.agent.Groq in case it was already imported separately.
# This is a no-op if agents.agent hasn't been imported yet.
try:
    import agents.agent as _aa
    _aa.Groq = _groq_class_mock
except ImportError:
    pass