"""
Tests for engine/prompt_modifier.py — covering the functions and data
that were changed in this PR:
  - weighted_params() (renamed from _weighted_params)
  - describe_level()  (renamed from _describe_level)
  - BEHAVIORAL_PROFILES (removed "Relief" entry)
  - PromptModifier.build_system_prompt() (now calls weighted_params internally)
"""

import pytest
from entity.entity import Entity
from engine.prompt_modifier import (
    BEHAVIORAL_PROFILES,
    NEUTRAL_PROFILE,
    weighted_params,
    describe_level,
    PromptModifier,
)


# ── describe_level ─────────────────────────────────────────────────────────────

class TestDescribeLevel:
    def test_very_high_at_exactly_80(self):
        assert describe_level(80.0) == "very high"

    def test_very_high_above_80(self):
        assert describe_level(95.0) == "very high"
        assert describe_level(100.0) == "very high"

    def test_high_at_exactly_60(self):
        assert describe_level(60.0) == "high"

    def test_high_below_80(self):
        assert describe_level(79.9) == "high"
        assert describe_level(65.0) == "high"

    def test_moderate_at_exactly_40(self):
        assert describe_level(40.0) == "moderate"

    def test_moderate_below_60(self):
        assert describe_level(59.9) == "moderate"
        assert describe_level(50.0) == "moderate"

    def test_low_at_exactly_20(self):
        assert describe_level(20.0) == "low"

    def test_low_below_40(self):
        assert describe_level(39.9) == "low"
        assert describe_level(25.0) == "low"

    def test_very_low_below_20(self):
        assert describe_level(19.9) == "very low"
        assert describe_level(0.0) == "very low"
        assert describe_level(10.0) == "very low"

    def test_boundary_just_below_very_high(self):
        # 79.99... is still "high"
        assert describe_level(79.999) == "high"

    def test_boundary_just_below_high(self):
        assert describe_level(59.999) == "moderate"

    def test_boundary_just_below_moderate(self):
        assert describe_level(39.999) == "low"

    def test_boundary_just_below_low(self):
        assert describe_level(19.999) == "very low"

    def test_negative_value_is_very_low(self):
        # Negative values (shouldn't occur but should be handled gracefully)
        assert describe_level(-5.0) == "very low"


# ── weighted_params ────────────────────────────────────────────────────────────

class TestWeightedParams:
    def test_empty_list_returns_neutral_profile(self):
        result = weighted_params([])
        assert result == NEUTRAL_PROFILE

    def test_empty_list_returns_copy_not_original(self):
        result = weighted_params([])
        result["aggression"] = 999
        assert NEUTRAL_PROFILE["aggression"] != 999

    def test_zero_intensity_returns_neutral_profile(self):
        # All zeros → total_weight == 0 → NEUTRAL_PROFILE
        result = weighted_params([("Joy", 0.0), ("Anger", 0.0)])
        assert result == NEUTRAL_PROFILE

    def test_single_emotion_returns_that_emotions_profile(self):
        result = weighted_params([("Joy", 1.0)])
        expected = BEHAVIORAL_PROFILES["Joy"]
        for k in NEUTRAL_PROFILE:
            assert abs(result[k] - expected[k]) < 1e-9, f"{k}: {result[k]} != {expected[k]}"

    def test_two_equal_weight_emotions_returns_average(self):
        result = weighted_params([("Joy", 0.5), ("Anger", 0.5)])
        joy = BEHAVIORAL_PROFILES["Joy"]
        anger = BEHAVIORAL_PROFILES["Anger"]
        for k in NEUTRAL_PROFILE:
            expected = (joy[k] + anger[k]) / 2
            assert abs(result[k] - expected) < 1e-9, f"{k}: {result[k]} != {expected}"

    def test_unequal_weights_produce_weighted_average(self):
        # Joy at 0.8, Anger at 0.2
        result = weighted_params([("Joy", 0.8), ("Anger", 0.2)])
        joy = BEHAVIORAL_PROFILES["Joy"]
        anger = BEHAVIORAL_PROFILES["Anger"]
        for k in NEUTRAL_PROFILE:
            expected = joy[k] * (0.8 / 1.0) + anger[k] * (0.2 / 1.0)
            assert abs(result[k] - expected) < 1e-9

    def test_unknown_emotion_falls_back_to_neutral_profile_for_that_emotion(self):
        # An emotion name not in BEHAVIORAL_PROFILES should use NEUTRAL_PROFILE
        result = weighted_params([("NonExistentEmotion", 1.0)])
        # Should equal NEUTRAL_PROFILE (used as fallback)
        assert result == NEUTRAL_PROFILE

    def test_result_has_all_expected_keys(self):
        result = weighted_params([("Joy", 0.5)])
        expected_keys = {"aggression", "openness", "creativity", "confidence", "cooperation"}
        assert set(result.keys()) == expected_keys

    def test_result_values_are_floats(self):
        result = weighted_params([("Joy", 0.7), ("Fear", 0.3)])
        for v in result.values():
            assert isinstance(v, float)

    def test_intensity_scaling_doesnt_change_proportional_result(self):
        # Scaling all intensities by a constant doesn't change the output
        result1 = weighted_params([("Joy", 0.5), ("Anger", 0.5)])
        result2 = weighted_params([("Joy", 5.0), ("Anger", 5.0)])
        for k in NEUTRAL_PROFILE:
            assert abs(result1[k] - result2[k]) < 1e-9

    def test_high_aggression_emotion_produces_high_aggression(self):
        result = weighted_params([("Anger", 1.0)])
        assert result["aggression"] == pytest.approx(90.0)

    def test_high_cooperation_emotion_produces_high_cooperation(self):
        result = weighted_params([("Trust", 1.0)])
        assert result["cooperation"] == pytest.approx(95.0)


# ── BEHAVIORAL_PROFILES ────────────────────────────────────────────────────────

class TestBehavioralProfiles:
    def test_core_emotions_present(self):
        core = ["Joy", "Anger", "Fear", "Sadness", "Disgust", "Trust", "Surprise"]
        for emotion in core:
            assert emotion in BEHAVIORAL_PROFILES, f"Missing core emotion: {emotion}"

    def test_each_profile_has_all_five_keys(self):
        required_keys = {"aggression", "openness", "creativity", "confidence", "cooperation"}
        for name, profile in BEHAVIORAL_PROFILES.items():
            assert set(profile.keys()) == required_keys, (
                f"{name} profile missing keys: {required_keys - set(profile.keys())}"
            )

    def test_profile_values_in_valid_range(self):
        for name, profile in BEHAVIORAL_PROFILES.items():
            for key, val in profile.items():
                assert 0 <= val <= 100, f"{name}.{key} = {val} out of range [0, 100]"

    def test_joy_has_low_aggression_high_cooperation(self):
        joy = BEHAVIORAL_PROFILES["Joy"]
        assert joy["aggression"] < 20
        assert joy["cooperation"] > 80

    def test_anger_has_high_aggression_low_cooperation(self):
        anger = BEHAVIORAL_PROFILES["Anger"]
        assert anger["aggression"] > 80
        assert anger["cooperation"] < 20

    def test_neutral_profile_values_in_range(self):
        for key, val in NEUTRAL_PROFILE.items():
            assert 0 <= val <= 100


# ── PromptModifier.build_system_prompt ────────────────────────────────────────

class TestPromptModifier:
    def _make_entity(self, personality="average"):
        return Entity("TestAgent", personality)

    def test_build_system_prompt_with_no_active_emotions_contains_calm(self):
        modifier = PromptModifier()
        entity = self._make_entity()
        prompt = modifier.build_system_prompt(entity)
        assert "calm" in prompt.lower()

    def test_build_system_prompt_includes_base_persona(self):
        modifier = PromptModifier()
        entity = self._make_entity()
        persona = "You are a helpful assistant named Chip."
        prompt = modifier.build_system_prompt(entity, base_persona=persona)
        assert persona in prompt

    def test_build_system_prompt_without_persona_excludes_persona_block(self):
        modifier = PromptModifier()
        entity = self._make_entity()
        prompt = modifier.build_system_prompt(entity, base_persona="")
        # Should not start with a persona block
        assert not prompt.startswith("\n\n")

    def test_build_system_prompt_with_active_emotion_mentions_emotion(self):
        modifier = PromptModifier()
        entity = self._make_entity()
        entity.emotions["Joy"].activate(0.8)
        prompt = modifier.build_system_prompt(entity)
        assert "Joy" in prompt

    def test_build_system_prompt_with_high_intensity_uses_strongly_prefix(self):
        modifier = PromptModifier()
        entity = self._make_entity()
        entity.emotions["Anger"].activate(0.8)
        prompt = modifier.build_system_prompt(entity)
        assert "strongly" in prompt

    def test_build_system_prompt_with_moderate_intensity_uses_feeling_prefix(self):
        modifier = PromptModifier()
        entity = self._make_entity()
        entity.emotions["Fear"].activate(0.5)
        prompt = modifier.build_system_prompt(entity)
        assert "feeling" in prompt.lower() or "hint" in prompt.lower()

    def test_build_system_prompt_with_low_intensity_uses_hint_prefix(self):
        modifier = PromptModifier()
        entity = self._make_entity()
        entity.emotions["Sadness"].activate(0.2)
        prompt = modifier.build_system_prompt(entity)
        assert "hint" in prompt

    def test_build_system_prompt_very_low_intensity_suppressed(self):
        # Emotions below 0.15 are not narrated
        modifier = PromptModifier()
        entity = self._make_entity()
        entity.emotions["Joy"].activate(0.1)  # below 0.15 threshold
        prompt = modifier.build_system_prompt(entity)
        # Joy at 0.1 is active but below narrative threshold
        assert "calm" in prompt.lower()

    def test_build_system_prompt_includes_behavioural_section(self):
        modifier = PromptModifier()
        entity = self._make_entity()
        prompt = modifier.build_system_prompt(entity)
        assert "behaviour" in prompt.lower()

    def test_build_system_prompt_includes_response_section(self):
        modifier = PromptModifier()
        entity = self._make_entity()
        prompt = modifier.build_system_prompt(entity)
        assert "response" in prompt.lower()

    def test_build_system_prompt_returns_string(self):
        modifier = PromptModifier()
        entity = self._make_entity()
        result = modifier.build_system_prompt(entity)
        assert isinstance(result, str)
        assert len(result) > 100  # should be a non-trivial prompt