"""
Tests for server.py — the new FastAPI backend added in this PR.

Covers:
  - Game class: __init__, reset(), step()
  - ChatSession class: __init__, reset(), send()
  - agent_state() serialization
  - full_state() serialization
  - chat_state() serialization
  - API endpoints via TestClient (mocked LLM calls)

Note: Groq is patched at session scope in conftest.py so that the module-level
GAME and CHAT objects in server.py are created without a real API key.
"""

import os
import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def client():
    """FastAPI TestClient (session-scoped; server module imported once)."""
    from server import app
    return TestClient(app, raise_server_exceptions=True)


@pytest.fixture
def fresh_game():
    """A fresh Game instance (independent of the global GAME)."""
    from server import Game
    return Game()


@pytest.fixture
def fresh_chat():
    """A fresh ChatSession (independent of the global CHAT)."""
    from server import ChatSession
    return ChatSession()


# ── Game class ────────────────────────────────────────────────────────────────

class TestGameInit:
    def test_default_topic_is_cancelled_project(self, fresh_game):
        assert fresh_game.topic == "Cancelled project"

    def test_turn_starts_at_zero(self, fresh_game):
        assert fresh_game.turn == 0

    def test_messages_empty_on_init(self, fresh_game):
        assert fresh_game.messages == []

    def test_agents_created(self, fresh_game):
        assert fresh_game.alex is not None
        assert fresh_game.sam is not None

    def test_alex_is_neurotic(self, fresh_game):
        assert fresh_game.alex.entity.personality == "neurotic"

    def test_sam_is_resilient(self, fresh_game):
        assert fresh_game.sam.entity.personality == "resilient"

    def test_opening_has_speaker_and_text(self, fresh_game):
        assert "speaker" in fresh_game.opening
        assert "text" in fresh_game.opening


class TestGameReset:
    def test_reset_with_valid_topic_changes_topic(self, fresh_game):
        fresh_game.reset("Dog died")
        assert fresh_game.topic == "Dog died"

    def test_reset_with_all_valid_topics(self, fresh_game):
        from server import STARTER_TOPICS
        for topic in STARTER_TOPICS:
            fresh_game.reset(topic)
            assert fresh_game.topic == topic

    def test_reset_with_invalid_topic_falls_back_to_default(self, fresh_game):
        fresh_game.reset("This topic does not exist")
        assert fresh_game.topic == "Cancelled project"

    def test_reset_clears_messages(self, fresh_game):
        fresh_game.messages = [{"turn": 1, "speaker": "Alex", "text": "hi"}]
        fresh_game.reset("Cancelled project")
        assert fresh_game.messages == []

    def test_reset_resets_turn_to_zero(self, fresh_game):
        fresh_game.turn = 5
        fresh_game.reset("Cancelled project")
        assert fresh_game.turn == 0

    def test_reset_with_custom_alex_reactivity(self, fresh_game):
        fresh_game.reset("Cancelled project", alex_rx=2.0)
        assert fresh_game.alex.entity.reactivity == pytest.approx(2.0)

    def test_reset_with_custom_sam_reactivity(self, fresh_game):
        fresh_game.reset("Cancelled project", sam_rx=0.5)
        assert fresh_game.sam.entity.reactivity == pytest.approx(0.5)

    def test_reset_without_custom_reactivity_uses_defaults(self, fresh_game):
        from engine.appraisal import REACTIVITY
        fresh_game.reset("Cancelled project")
        assert fresh_game.alex.entity.reactivity == pytest.approx(REACTIVITY["neurotic"])
        assert fresh_game.sam.entity.reactivity == pytest.approx(REACTIVITY["resilient"])

    def test_reset_dog_died_speaker_is_alex(self, fresh_game):
        fresh_game.reset("Dog died")
        # "Dog died" opener is from Alex, so Sam responds first
        assert fresh_game.next_speaker_is_sam is True

    def test_reset_unexpected_praise_speaker_is_sam(self, fresh_game):
        fresh_game.reset("Unexpected praise")
        # "Unexpected praise" opener is from Sam, so Alex responds first
        assert fresh_game.next_speaker_is_sam is False


class TestGameStep:
    def test_step_increments_turn(self, fresh_game):
        with patch.object(fresh_game.sam, "receive_and_respond", return_value="Sam reply"):
            fresh_game.step()
        assert fresh_game.turn == 1

    def test_step_appends_to_messages(self, fresh_game):
        with patch.object(fresh_game.sam, "receive_and_respond", return_value="Sam reply"):
            fresh_game.step()
        assert len(fresh_game.messages) == 1

    def test_step_message_has_required_keys(self, fresh_game):
        with patch.object(fresh_game.sam, "receive_and_respond", return_value="Sam reply"):
            fresh_game.step()
        msg = fresh_game.messages[0]
        assert "turn" in msg
        assert "speaker" in msg
        assert "text" in msg
        assert "event" in msg
        assert "alex" in msg
        assert "sam" in msg

    def test_step_first_speaker_is_sam_for_alex_opener(self, fresh_game):
        # "Cancelled project" opener is Alex, so Sam responds first
        with patch.object(fresh_game.sam, "receive_and_respond", return_value="Sam reply") as m:
            fresh_game.step()
            m.assert_called_once()
        assert fresh_game.messages[0]["speaker"] == "Sam"

    def test_step_alternates_speaker(self, fresh_game):
        with patch.object(fresh_game.sam, "receive_and_respond", return_value="Sam reply"):
            fresh_game.step()
        with patch.object(fresh_game.alex, "receive_and_respond", return_value="Alex reply"):
            fresh_game.step()
        speakers = [m["speaker"] for m in fresh_game.messages]
        assert speakers == ["Sam", "Alex"]

    def test_step_uses_custom_message(self, fresh_game):
        with patch.object(fresh_game.sam, "receive_and_respond", return_value="Sam reply") as m:
            fresh_game.step(message="Custom injected message")
        call_args = m.call_args
        assert call_args[0][0] == "Custom injected message"

    def test_step_updates_next_message_to_reply(self, fresh_game):
        with patch.object(fresh_game.sam, "receive_and_respond", return_value="Sam reply"):
            fresh_game.step()
        assert fresh_game.next_message == "Sam reply"

    def test_step_passes_witness_event_to_responder(self, fresh_game):
        # Sender's last_event should be passed as witness_event
        fresh_game.alex.last_event = {"event_type": "compliment", "severity": 0.8}
        with patch.object(fresh_game.sam, "receive_and_respond", return_value="Sam reply") as m:
            fresh_game.step()
        _, kwargs = m.call_args
        assert kwargs.get("witness_event") == {"event_type": "compliment", "severity": 0.8}


# ── ChatSession class ─────────────────────────────────────────────────────────

class TestChatSessionInit:
    def test_default_agent_name_is_morgan(self, fresh_chat):
        assert fresh_chat.agent.name == "Morgan"

    def test_default_personality_is_average(self, fresh_chat):
        assert fresh_chat.agent.entity.personality == "average"

    def test_messages_empty_on_init(self, fresh_chat):
        assert fresh_chat.messages == []


class TestChatSessionReset:
    def test_reset_changes_agent_name(self, fresh_chat):
        fresh_chat.reset("Alice", "neurotic", 1.4, "You are Alice.")
        assert fresh_chat.agent.name == "Alice"

    def test_reset_changes_personality(self, fresh_chat):
        fresh_chat.reset("Bob", "resilient", 0.75, "You are Bob.")
        assert fresh_chat.agent.entity.personality == "resilient"

    def test_reset_invalid_personality_defaults_to_average(self, fresh_chat):
        fresh_chat.reset("Charlie", "invalid_personality", 1.0, "You are Charlie.")
        assert fresh_chat.agent.entity.personality == "average"

    def test_reset_clears_messages(self, fresh_chat):
        fresh_chat.messages = [{"role": "user", "text": "hi"}]
        fresh_chat.reset("Morgan", "average", 1.0, "You are Morgan.")
        assert fresh_chat.messages == []

    def test_reset_with_seed_emotion_activates_it(self, fresh_chat):
        fresh_chat.reset("Morgan", "average", 1.0, "persona", seed_emotion="Joy", seed_intensity=0.7)
        assert fresh_chat.agent.entity.emotions["Joy"].is_active

    def test_reset_with_none_seed_emotion_no_activation(self, fresh_chat):
        fresh_chat.reset("Morgan", "average", 1.0, "persona", seed_emotion=None, seed_intensity=0.7)
        # No emotions should be seeded
        assert not fresh_chat.agent.entity.emotions["Joy"].is_active

    def test_reset_with_none_string_seed_emotion_no_activation(self, fresh_chat):
        fresh_chat.reset("Morgan", "average", 1.0, "persona", seed_emotion="None", seed_intensity=0.7)
        assert not fresh_chat.agent.entity.emotions["Joy"].is_active

    def test_reset_with_zero_seed_intensity_no_activation(self, fresh_chat):
        fresh_chat.reset("Morgan", "average", 1.0, "persona", seed_emotion="Joy", seed_intensity=0.0)
        assert not fresh_chat.agent.entity.emotions["Joy"].is_active

    def test_reset_with_unknown_seed_emotion_is_safe(self, fresh_chat):
        # Should not crash if seed_emotion doesn't exist in entity
        fresh_chat.reset("Morgan", "average", 1.0, "persona",
                         seed_emotion="NonExistentEmotion", seed_intensity=0.5)
        # No crash = pass

    def test_reset_empty_name_defaults_to_morgan(self, fresh_chat):
        fresh_chat.reset("", "average", 1.0, "persona")
        assert fresh_chat.agent.name == "Morgan"

    def test_reset_empty_persona_uses_empty_string(self, fresh_chat):
        fresh_chat.reset("Morgan", "average", 1.0, "")
        # Agent should be created with "" persona — no crash
        assert fresh_chat.agent.base_persona == ""


class TestChatSessionSend:
    def test_send_appends_user_and_agent_messages(self, fresh_chat):
        with patch.object(fresh_chat.agent, "receive_and_respond", return_value="Agent response"):
            fresh_chat.send("Hello agent")
        assert len(fresh_chat.messages) == 2
        assert fresh_chat.messages[0]["role"] == "user"
        assert fresh_chat.messages[1]["role"] == "agent"

    def test_send_records_user_text_correctly(self, fresh_chat):
        with patch.object(fresh_chat.agent, "receive_and_respond", return_value="Response"):
            fresh_chat.send("My message")
        assert fresh_chat.messages[0]["text"] == "My message"

    def test_send_records_agent_reply_text(self, fresh_chat):
        with patch.object(fresh_chat.agent, "receive_and_respond", return_value="Agent speaks"):
            fresh_chat.send("Hi")
        assert fresh_chat.messages[1]["text"] == "Agent speaks"

    def test_send_records_event_in_agent_message(self, fresh_chat):
        fresh_chat.agent.last_event = {"event_type": "compliment", "severity": 0.5}
        with patch.object(fresh_chat.agent, "receive_and_respond", return_value="Response"):
            fresh_chat.send("Hi")
        assert "event" in fresh_chat.messages[1]

    def test_send_calls_receive_and_respond_without_witness_event(self, fresh_chat):
        with patch.object(fresh_chat.agent, "receive_and_respond", return_value="resp") as m:
            fresh_chat.send("hello")
        m.assert_called_once_with("hello")

    def test_send_multiple_messages_accumulates_history(self, fresh_chat):
        with patch.object(fresh_chat.agent, "receive_and_respond", return_value="r1"):
            fresh_chat.send("msg1")
        with patch.object(fresh_chat.agent, "receive_and_respond", return_value="r2"):
            fresh_chat.send("msg2")
        assert len(fresh_chat.messages) == 4


# ── Serialization functions ───────────────────────────────────────────────────

class TestAgentState:
    def test_agent_state_has_required_keys(self, fresh_game):
        from server import agent_state
        state = agent_state(fresh_game.alex)
        required = {"name", "personality", "decay", "emotions", "params"}
        assert required.issubset(set(state.keys()))

    def test_agent_state_name_matches_agent(self, fresh_game):
        from server import agent_state
        state = agent_state(fresh_game.alex)
        assert state["name"] == "Alex"

    def test_agent_state_personality_matches(self, fresh_game):
        from server import agent_state
        state = agent_state(fresh_game.alex)
        assert state["personality"] == "neurotic"

    def test_agent_state_params_has_all_keys(self, fresh_game):
        from server import agent_state, PARAM_KEYS
        state = agent_state(fresh_game.alex)
        for k in PARAM_KEYS:
            assert k in state["params"]

    def test_agent_state_param_entries_have_level_and_value(self, fresh_game):
        from server import agent_state
        state = agent_state(fresh_game.alex)
        for k, v in state["params"].items():
            assert "level" in v, f"param {k} missing 'level'"
            assert "value" in v, f"param {k} missing 'value'"

    def test_agent_state_param_level_is_valid_string(self, fresh_game):
        from server import agent_state
        valid_levels = {"very high", "high", "moderate", "low", "very low"}
        state = agent_state(fresh_game.alex)
        for k, v in state["params"].items():
            assert v["level"] in valid_levels, f"{k}: invalid level '{v['level']}'"

    def test_agent_state_emotions_is_list(self, fresh_game):
        from server import agent_state
        state = agent_state(fresh_game.alex)
        assert isinstance(state["emotions"], list)

    def test_agent_state_emotions_entries_have_name_and_intensity(self, fresh_game):
        from server import agent_state
        # Activate an emotion so we get at least one entry
        fresh_game.alex.entity.emotions["Joy"].activate(0.8)
        state = agent_state(fresh_game.alex)
        for emo in state["emotions"]:
            assert "name" in emo
            assert "intensity" in emo

    def test_agent_state_decay_is_float(self, fresh_game):
        from server import agent_state
        state = agent_state(fresh_game.alex)
        assert isinstance(state["decay"], float)

    def test_agent_state_with_no_active_emotions_uses_neutral_profile(self, fresh_game):
        from server import agent_state
        from engine.prompt_modifier import NEUTRAL_PROFILE
        # Ensure no emotions active
        for e in fresh_game.alex.entity.emotions.values():
            e.intensity = 0.0
            e.is_active = False
        state = agent_state(fresh_game.alex)
        # Params should reflect NEUTRAL_PROFILE
        for k, v in state["params"].items():
            expected_level_value = NEUTRAL_PROFILE[k]
            assert abs(v["value"] - expected_level_value) < 0.1, (
                f"{k}: expected {expected_level_value} got {v['value']}"
            )


class TestFullState:
    def test_full_state_has_required_keys(self, fresh_game):
        from server import full_state, GAME
        # Temporarily redirect to fresh_game
        import server
        original = server.GAME
        server.GAME = fresh_game
        try:
            state = full_state()
        finally:
            server.GAME = original
        required = {"turn", "topic", "topics", "opening", "next_speaker",
                    "messages", "alex", "sam", "reactivity_ref", "has_key"}
        assert required.issubset(set(state.keys()))

    def test_full_state_topics_contains_all_starters(self):
        from server import full_state, STARTER_TOPICS
        import server
        state = full_state()
        for topic in STARTER_TOPICS:
            assert topic in state["topics"]

    def test_full_state_has_key_is_bool(self):
        from server import full_state
        state = full_state()
        assert isinstance(state["has_key"], bool)

    def test_full_state_reactivity_ref_matches_constants(self):
        from server import full_state
        from engine.appraisal import REACTIVITY
        state = full_state()
        assert state["reactivity_ref"] == REACTIVITY


# ── API endpoints ─────────────────────────────────────────────────────────────

class TestApiState:
    def test_get_state_returns_200(self, client):
        response = client.get("/api/state")
        assert response.status_code == 200

    def test_get_state_returns_json_with_turn(self, client):
        data = client.get("/api/state").json()
        assert "turn" in data

    def test_get_state_returns_json_with_topics(self, client):
        data = client.get("/api/state").json()
        assert "topics" in data
        assert len(data["topics"]) > 0


class TestApiReset:
    def test_post_reset_returns_200(self, client):
        response = client.post("/api/reset", json={"topic": "Cancelled project"})
        assert response.status_code == 200

    def test_post_reset_returns_state_with_turn_zero(self, client):
        data = client.post("/api/reset", json={"topic": "Cancelled project"}).json()
        assert data["turn"] == 0

    def test_post_reset_with_all_valid_topics(self, client):
        from server import STARTER_TOPICS
        for topic in STARTER_TOPICS:
            response = client.post("/api/reset", json={"topic": topic})
            assert response.status_code == 200, f"Failed for topic: {topic}"
            assert response.json()["topic"] == topic

    def test_post_reset_invalid_topic_falls_back_to_default(self, client):
        data = client.post("/api/reset", json={"topic": "Nonsense topic"}).json()
        assert data["topic"] == "Cancelled project"

    def test_post_reset_with_custom_reactivity_values(self, client):
        response = client.post("/api/reset", json={
            "topic": "Cancelled project",
            "alex_reactivity": 2.0,
            "sam_reactivity": 0.5,
        })
        assert response.status_code == 200

    def test_post_reset_empty_body_uses_defaults(self, client):
        response = client.post("/api/reset", json={})
        assert response.status_code == 200
        assert response.json()["topic"] == "Cancelled project"

    def test_post_reset_clears_messages(self, client):
        # First do a turn (if key present), then reset and check messages
        data = client.post("/api/reset", json={"topic": "Dog died"}).json()
        assert data["messages"] == []


class TestApiTurn:
    def test_post_turn_without_api_key_returns_error(self, client):
        """When GROQ_API_KEY is not set, the endpoint returns an error dict."""
        env_backup = os.environ.pop("GROQ_API_KEY", None)
        try:
            data = client.post("/api/turn", json={}).json()
            assert "error" in data
        finally:
            if env_backup:
                os.environ["GROQ_API_KEY"] = env_backup

    def test_post_turn_with_api_key_calls_game_step(self, client):
        import server
        with patch.dict(os.environ, {"GROQ_API_KEY": "test-key"}):
            with patch.object(server.GAME, "step", return_value=None) as mock_step:
                client.post("/api/turn", json={})
                mock_step.assert_called_once()

    def test_post_turn_with_message_passes_it_to_step(self, client):
        import server
        with patch.dict(os.environ, {"GROQ_API_KEY": "test-key"}):
            with patch.object(server.GAME, "step") as mock_step:
                client.post("/api/turn", json={"message": "Custom message"})
                mock_step.assert_called_once_with("Custom message")


class TestApiChatState:
    def test_get_chat_state_returns_200(self, client):
        response = client.get("/api/chat/state")
        assert response.status_code == 200

    def test_get_chat_state_returns_agent_key(self, client):
        data = client.get("/api/chat/state").json()
        assert "agent" in data

    def test_get_chat_state_returns_messages_key(self, client):
        data = client.get("/api/chat/state").json()
        assert "messages" in data

    def test_get_chat_state_returns_seed_options(self, client):
        data = client.get("/api/chat/state").json()
        assert "seed_options" in data
        assert len(data["seed_options"]) > 0

    def test_get_chat_state_returns_personalities(self, client):
        data = client.get("/api/chat/state").json()
        assert "personalities" in data
        assert set(data["personalities"]) == {"neurotic", "average", "resilient"}

    def test_get_chat_state_agent_has_system_prompt(self, client):
        data = client.get("/api/chat/state").json()
        assert "system_prompt" in data["agent"]

    def test_get_chat_state_agent_has_persona(self, client):
        data = client.get("/api/chat/state").json()
        assert "persona" in data["agent"]

    def test_get_chat_state_agent_has_reactivity(self, client):
        data = client.get("/api/chat/state").json()
        assert "reactivity" in data["agent"]


class TestApiChatReset:
    def test_post_chat_reset_returns_200(self, client):
        response = client.post("/api/chat/reset", json={})
        assert response.status_code == 200

    def test_post_chat_reset_changes_agent_name(self, client):
        data = client.post("/api/chat/reset", json={"name": "Zara"}).json()
        assert data["agent"]["name"] == "Zara"

    def test_post_chat_reset_changes_personality(self, client):
        data = client.post("/api/chat/reset", json={"personality": "neurotic"}).json()
        assert data["agent"]["personality"] == "neurotic"

    def test_post_chat_reset_invalid_personality_defaults_to_average(self, client):
        data = client.post("/api/chat/reset", json={"personality": "bogus"}).json()
        assert data["agent"]["personality"] == "average"

    def test_post_chat_reset_with_seed_emotion(self, client):
        response = client.post("/api/chat/reset", json={
            "name": "Morgan",
            "personality": "average",
            "reactivity": 1.0,
            "persona": "You are Morgan.",
            "seed_emotion": "Joy",
            "seed_intensity": 0.8,
        })
        assert response.status_code == 200

    def test_post_chat_reset_clears_messages(self, client):
        data = client.post("/api/chat/reset", json={}).json()
        assert data["messages"] == []


class TestApiChatSend:
    def test_post_chat_send_without_api_key_returns_error(self, client):
        env_backup = os.environ.pop("GROQ_API_KEY", None)
        try:
            data = client.post("/api/chat/send", json={"message": "hello"}).json()
            assert "error" in data
        finally:
            if env_backup:
                os.environ["GROQ_API_KEY"] = env_backup

    def test_post_chat_send_with_api_key_calls_send(self, client):
        import server
        with patch.dict(os.environ, {"GROQ_API_KEY": "test-key"}):
            with patch.object(server.CHAT, "send", return_value="Agent response") as mock_send:
                client.post("/api/chat/send", json={"message": "Hello!"})
                mock_send.assert_called_once_with("Hello!")

    def test_post_chat_send_whitespace_only_message_not_sent(self, client):
        import server
        with patch.dict(os.environ, {"GROQ_API_KEY": "test-key"}):
            with patch.object(server.CHAT, "send") as mock_send:
                client.post("/api/chat/send", json={"message": "   "})
                mock_send.assert_not_called()

    def test_post_chat_send_message_is_stripped(self, client):
        import server
        with patch.dict(os.environ, {"GROQ_API_KEY": "test-key"}):
            with patch.object(server.CHAT, "send", return_value="resp") as mock_send:
                client.post("/api/chat/send", json={"message": "  hello  "})
                mock_send.assert_called_once_with("hello")


# ── STARTER_TOPICS constant ───────────────────────────────────────────────────

class TestStarterTopics:
    def test_all_five_topics_present(self):
        from server import STARTER_TOPICS
        expected = {"Dog died", "Cancelled project", "Unexpected praise",
                    "Unfair blame", "New opportunity"}
        assert set(STARTER_TOPICS.keys()) == expected

    def test_each_topic_has_speaker_and_text(self):
        from server import STARTER_TOPICS
        for key, (speaker, text) in STARTER_TOPICS.items():
            assert speaker in ("Alex", "Sam"), f"{key}: unexpected speaker {speaker}"
            assert isinstance(text, str) and len(text) > 10

    def test_dog_died_speaker_is_alex(self):
        from server import STARTER_TOPICS
        speaker, _ = STARTER_TOPICS["Dog died"]
        assert speaker == "Alex"

    def test_unexpected_praise_speaker_is_sam(self):
        from server import STARTER_TOPICS
        speaker, _ = STARTER_TOPICS["Unexpected praise"]
        assert speaker == "Sam"


# ── SEED_EMOTIONS and PERSONALITIES constants ─────────────────────────────────

class TestConstants:
    def test_seed_emotions_list(self):
        from server import SEED_EMOTIONS
        assert "Joy" in SEED_EMOTIONS
        assert "Anger" in SEED_EMOTIONS
        assert len(SEED_EMOTIONS) >= 5

    def test_personalities_list(self):
        from server import PERSONALITIES
        assert set(PERSONALITIES) == {"neurotic", "average", "resilient"}
