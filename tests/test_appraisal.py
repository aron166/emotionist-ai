"""
Tests for engine/appraisal.py — covering the changes made in this PR:
  - Witness empathy condition: "fears_confirmed" removed from the triggering set
  - apply_transitions() no longer wraps condition checks in try/except
  - Emotion transition rules (Fear→Distress, Shame→Anger, etc.)
  - OCCAppraisalEngine.compute_deltas() main event paths
"""

import random
import pytest
from unittest.mock import patch, MagicMock

from entity.entity import Entity
from engine.appraisal import OCCAppraisalEngine, REACTIVITY, _transition_rules


# ── Helpers ────────────────────────────────────────────────────────────────────

def make_entity(personality="average", reactivity=1.0):
    return Entity("Tester", personality, reactivity=reactivity)


def make_event(event_type, severity=0.8, directed_at_self=True, intentional=True):
    return {
        "event_type": event_type,
        "severity": severity,
        "directed_at_self": directed_at_self,
        "intentional": intentional,
    }


# ── REACTIVITY constants ────────────────────────────────────────────────────────

class TestReactivity:
    def test_neurotic_is_highest(self):
        assert REACTIVITY["neurotic"] > REACTIVITY["average"]

    def test_resilient_is_lowest(self):
        assert REACTIVITY["resilient"] < REACTIVITY["average"]

    def test_average_is_baseline(self):
        assert REACTIVITY["average"] == 1.0

    def test_all_three_keys_present(self):
        assert set(REACTIVITY.keys()) == {"neurotic", "average", "resilient"}


# ── OCCAppraisalEngine.compute_deltas ─────────────────────────────────────────

class TestComputeDeltasBasicEvents:
    def setup_method(self):
        self.engine = OCCAppraisalEngine()
        self.entity = make_entity()

    def test_compliment_self_directed_raises_pride_and_joy(self):
        event = make_event("compliment", severity=1.0, directed_at_self=True)
        deltas = self.engine.compute_deltas(event, self.entity)
        assert "Pride" in deltas and deltas["Pride"] > 0
        assert "Joy" in deltas and deltas["Joy"] > 0

    def test_compliment_not_self_directed_raises_admiration_and_happyfor(self):
        event = make_event("compliment", directed_at_self=False)
        deltas = self.engine.compute_deltas(event, self.entity)
        assert "Admiration" in deltas and deltas["Admiration"] > 0
        assert "HappyFor" in deltas and deltas["HappyFor"] > 0
        assert "Pride" not in deltas

    def test_insult_self_directed_intentional_raises_anger_distress_reproach(self):
        event = make_event("insult", severity=1.0, directed_at_self=True, intentional=True)
        deltas = self.engine.compute_deltas(event, self.entity)
        assert "Anger" in deltas and deltas["Anger"] > 0
        assert "Distress" in deltas and deltas["Distress"] > 0
        assert "Reproach" in deltas and deltas["Reproach"] > 0

    def test_insult_self_directed_not_intentional_no_anger(self):
        event = make_event("insult", severity=1.0, directed_at_self=True, intentional=False)
        deltas = self.engine.compute_deltas(event, self.entity)
        assert "Anger" not in deltas
        assert "Distress" in deltas
        assert "Shame" in deltas

    def test_insult_not_self_directed_raises_reproach_only(self):
        event = make_event("insult", directed_at_self=False, intentional=True)
        deltas = self.engine.compute_deltas(event, self.entity)
        assert "Reproach" in deltas
        assert "Anger" not in deltas

    def test_threat_self_directed_raises_fear_and_distress(self):
        event = make_event("threat", severity=1.0, directed_at_self=True)
        deltas = self.engine.compute_deltas(event, self.entity)
        assert "Fear" in deltas and deltas["Fear"] > 0
        assert "Distress" in deltas and deltas["Distress"] > 0

    def test_threat_not_self_directed_raises_smaller_fear(self):
        event_self = make_event("threat", severity=1.0, directed_at_self=True)
        event_other = make_event("threat", severity=1.0, directed_at_self=False)
        d_self = self.engine.compute_deltas(event_self, self.entity)
        d_other = self.engine.compute_deltas(event_other, self.entity)
        assert d_other["Fear"] < d_self["Fear"]
        assert "Distress" not in d_other

    def test_good_news_self_directed_raises_joy_and_satisfaction(self):
        event = make_event("good_news", severity=1.0, directed_at_self=True)
        deltas = self.engine.compute_deltas(event, self.entity)
        assert "Joy" in deltas and deltas["Joy"] > 0
        assert "Satisfaction" in deltas and deltas["Satisfaction"] > 0

    def test_good_news_not_self_directed_raises_happyfor_and_hope(self):
        event = make_event("good_news", directed_at_self=False)
        deltas = self.engine.compute_deltas(event, self.entity)
        assert "HappyFor" in deltas
        assert "Hope" in deltas
        assert "Joy" not in deltas

    def test_bad_news_self_directed_raises_distress_and_fear(self):
        event = make_event("bad_news", severity=1.0, directed_at_self=True)
        deltas = self.engine.compute_deltas(event, self.entity)
        assert "Distress" in deltas and deltas["Distress"] > 0
        assert "Fear" in deltas and deltas["Fear"] > 0

    def test_bad_news_not_self_directed_raises_pity_and_distress(self):
        event = make_event("bad_news", directed_at_self=False)
        deltas = self.engine.compute_deltas(event, self.entity)
        assert "Pity" in deltas
        assert "Distress" in deltas

    def test_achievement_self_directed_raises_pride_joy_gratification(self):
        event = make_event("achievement", severity=1.0, directed_at_self=True)
        deltas = self.engine.compute_deltas(event, self.entity)
        assert "Pride" in deltas and deltas["Pride"] > 0
        assert "Joy" in deltas and deltas["Joy"] > 0
        assert "Gratification" in deltas and deltas["Gratification"] > 0

    def test_achievement_not_self_directed_raises_admiration(self):
        event = make_event("achievement", directed_at_self=False)
        deltas = self.engine.compute_deltas(event, self.entity)
        assert "Admiration" in deltas
        assert "Gratification" not in deltas

    def test_failure_self_directed_raises_shame_distress_remorse(self):
        event = make_event("failure", severity=1.0, directed_at_self=True)
        deltas = self.engine.compute_deltas(event, self.entity)
        assert "Shame" in deltas and deltas["Shame"] > 0
        assert "Distress" in deltas and deltas["Distress"] > 0
        assert "Remorse" in deltas and deltas["Remorse"] > 0

    def test_failure_not_self_directed_raises_pity(self):
        event = make_event("failure", directed_at_self=False)
        deltas = self.engine.compute_deltas(event, self.entity)
        assert "Pity" in deltas

    def test_agreement_raises_joy_trust_satisfaction(self):
        event = make_event("agreement", directed_at_self=True)
        deltas = self.engine.compute_deltas(event, self.entity)
        assert "Joy" in deltas and deltas["Joy"] > 0
        assert "Trust" in deltas and deltas["Trust"] > 0
        assert "Satisfaction" in deltas and deltas["Satisfaction"] > 0

    def test_disagreement_raises_distress(self):
        event = make_event("disagreement", directed_at_self=True, intentional=False)
        deltas = self.engine.compute_deltas(event, self.entity)
        assert "Distress" in deltas

    def test_disagreement_intentional_adds_reproach_and_resentment(self):
        event = make_event("disagreement", directed_at_self=True, intentional=True)
        deltas = self.engine.compute_deltas(event, self.entity)
        assert "Reproach" in deltas
        assert "Resentment" in deltas

    def test_praise_of_other_raises_admiration_and_happyfor(self):
        event = make_event("praise_of_other")
        deltas = self.engine.compute_deltas(event, self.entity)
        assert "Admiration" in deltas
        assert "HappyFor" in deltas

    def test_blame_of_other_raises_reproach(self):
        event = make_event("blame_of_other", directed_at_self=False)
        deltas = self.engine.compute_deltas(event, self.entity)
        assert "Reproach" in deltas

    def test_blame_of_other_self_directed_also_raises_anger(self):
        event = make_event("blame_of_other", directed_at_self=True)
        deltas = self.engine.compute_deltas(event, self.entity)
        assert "Anger" in deltas

    def test_neutral_with_high_distress_sustains_distress(self):
        entity = make_entity()
        entity.emotions["Distress"].activate(0.7)  # > 0.5 threshold
        event = make_event("neutral")
        deltas = self.engine.compute_deltas(event, entity)
        assert "Distress" in deltas and deltas["Distress"] > 0

    def test_neutral_with_low_distress_no_sustain(self):
        entity = make_entity()
        entity.emotions["Distress"].activate(0.3)  # below 0.5 threshold
        event = make_event("neutral")
        deltas = self.engine.compute_deltas(event, entity)
        assert "Distress" not in deltas

    def test_neutral_with_high_fear_sustains_fear(self):
        entity = make_entity()
        entity.emotions["Fear"].activate(0.5)  # > 0.4 threshold
        event = make_event("neutral")
        deltas = self.engine.compute_deltas(event, entity)
        assert "Fear" in deltas

    def test_neutral_with_high_sadness_sustains_sadness(self):
        entity = make_entity()
        entity.emotions["Sadness"].activate(0.5)  # > 0.4 threshold
        event = make_event("neutral")
        deltas = self.engine.compute_deltas(event, entity)
        assert "Sadness" in deltas

    def test_unknown_event_type_produces_no_deltas(self):
        event = make_event("completely_unknown_event_type")
        deltas = self.engine.compute_deltas(event, self.entity)
        assert len(deltas) == 0


# ── Reactivity scaling ─────────────────────────────────────────────────────────

class TestDeltaReactivityScaling:
    def setup_method(self):
        self.engine = OCCAppraisalEngine()

    def test_higher_reactivity_produces_larger_deltas(self):
        entity_neurotic = make_entity("neurotic", reactivity=REACTIVITY["neurotic"])
        entity_resilient = make_entity("resilient", reactivity=REACTIVITY["resilient"])
        event = make_event("compliment", severity=0.8, directed_at_self=True)
        d_n = self.engine.compute_deltas(event, entity_neurotic)
        d_r = self.engine.compute_deltas(event, entity_resilient)
        assert d_n["Pride"] > d_r["Pride"]

    def test_reactivity_1_gives_unscaled_pride_for_compliment(self):
        entity = make_entity(reactivity=1.0)
        event = make_event("compliment", severity=1.0, directed_at_self=True)
        deltas = self.engine.compute_deltas(event, entity)
        # Pride should be sev * 0.8 * 1.0 = 0.8
        assert abs(deltas["Pride"] - 0.8) < 1e-9

    def test_zero_severity_produces_zero_deltas(self):
        entity = make_entity()
        event = make_event("compliment", severity=0.0, directed_at_self=True)
        deltas = self.engine.compute_deltas(event, entity)
        for v in deltas.values():
            assert v == 0.0


# ── Witness / empathy track ────────────────────────────────────────────────────

class TestWitnessEmpathy:
    def setup_method(self):
        self.engine = OCCAppraisalEngine()
        self.entity = make_entity(reactivity=1.0)

    def _base_event(self):
        return make_event("neutral", severity=0.0)

    def test_bad_news_witness_triggers_pity_and_distress(self):
        witness = make_event("bad_news", severity=1.0, directed_at_self=True)
        deltas = self.engine.compute_deltas(self._base_event(), self.entity, witness_event=witness)
        assert "Pity" in deltas and deltas["Pity"] > 0
        assert "Distress" in deltas and deltas["Distress"] > 0
        assert "Guilt" in deltas and deltas["Guilt"] > 0

    def test_failure_witness_triggers_pity(self):
        witness = make_event("failure", severity=1.0, directed_at_self=True)
        deltas = self.engine.compute_deltas(self._base_event(), self.entity, witness_event=witness)
        assert "Pity" in deltas and deltas["Pity"] > 0

    def test_threat_witness_triggers_pity(self):
        witness = make_event("threat", severity=1.0, directed_at_self=True)
        deltas = self.engine.compute_deltas(self._base_event(), self.entity, witness_event=witness)
        assert "Pity" in deltas and deltas["Pity"] > 0

    def test_fears_confirmed_witness_does_NOT_trigger_pity(self):
        """PR change: 'fears_confirmed' removed from the witness-empathy condition set."""
        witness = {
            "event_type": "fears_confirmed",
            "severity": 1.0,
            "directed_at_self": True,
            "intentional": False,
        }
        deltas = self.engine.compute_deltas(self._base_event(), self.entity, witness_event=witness)
        # 'fears_confirmed' is no longer in ("bad_news", "failure", "threat")
        # so the pity/distress/guilt block should NOT fire from the witness track alone
        # (the base event is "neutral" with sev=0, so deltas should be empty or minimal)
        pity_from_witness = deltas.get("Pity", 0)
        assert pity_from_witness == 0.0, (
            f"fears_confirmed witness should no longer trigger Pity but got {pity_from_witness}"
        )

    def test_insult_intentional_witness_triggers_pity_and_reproach(self):
        witness = make_event("insult", severity=1.0, directed_at_self=True, intentional=True)
        deltas = self.engine.compute_deltas(self._base_event(), self.entity, witness_event=witness)
        assert "Pity" in deltas
        assert "Reproach" in deltas

    def test_insult_not_intentional_witness_does_not_trigger_pity(self):
        witness = make_event("insult", severity=1.0, directed_at_self=True, intentional=False)
        deltas = self.engine.compute_deltas(self._base_event(), self.entity, witness_event=witness)
        # The insult+not-intentional branch doesn't match any witness condition
        assert "Pity" not in deltas or deltas.get("Pity", 0) == 0

    def test_good_news_witness_triggers_happyfor_and_joy(self):
        witness = make_event("good_news", severity=1.0, directed_at_self=True)
        deltas = self.engine.compute_deltas(self._base_event(), self.entity, witness_event=witness)
        assert "HappyFor" in deltas and deltas["HappyFor"] > 0
        assert "Joy" in deltas and deltas["Joy"] > 0

    def test_achievement_witness_triggers_happyfor_and_joy(self):
        witness = make_event("achievement", severity=1.0, directed_at_self=True)
        deltas = self.engine.compute_deltas(self._base_event(), self.entity, witness_event=witness)
        assert "HappyFor" in deltas and deltas["HappyFor"] > 0

    def test_compliment_witness_triggers_happyfor(self):
        witness = make_event("compliment", severity=1.0, directed_at_self=True)
        deltas = self.engine.compute_deltas(self._base_event(), self.entity, witness_event=witness)
        assert "HappyFor" in deltas and deltas["HappyFor"] > 0

    def test_witness_pity_suppressed_when_agent_is_already_sufferer(self):
        """agent_is_sufferer: agent received bad_news self-directed AND has high Distress."""
        entity = make_entity(reactivity=1.0)
        entity.emotions["Distress"].activate(0.7)  # above 0.6 threshold
        # Agent receives bad_news directed at self
        primary_event = make_event("bad_news", severity=1.0, directed_at_self=True)
        witness = make_event("bad_news", severity=1.0, directed_at_self=True)
        deltas = self.engine.compute_deltas(primary_event, entity, witness_event=witness)
        # Witness Pity should NOT be added because agent_is_sufferer == True
        # (primary event Pity may be 0, distress comes from primary event, not witness)
        # The key check: no extra Pity from witness when agent is the sufferer
        # We compare against primary-only deltas
        deltas_no_witness = self.engine.compute_deltas(primary_event, entity)
        # Both should have Pity == 0 from primary bad_news (not self-directed pity path)
        # and witness should be suppressed
        assert deltas.get("Pity", 0) == pytest.approx(deltas_no_witness.get("Pity", 0))

    def test_no_witness_event_produces_no_empathy_deltas(self):
        # With witness_event=None, no witness track fires
        event = make_event("neutral", severity=0.0)
        deltas = self.engine.compute_deltas(event, self.entity, witness_event=None)
        # Neutral + no emotions active → empty deltas
        assert deltas == {}

    def test_witness_not_directed_at_self_does_not_trigger_empathy(self):
        witness = make_event("bad_news", severity=1.0, directed_at_self=False)
        deltas = self.engine.compute_deltas(self._base_event(), self.entity, witness_event=witness)
        assert "Pity" not in deltas or deltas.get("Pity", 0) == 0

    def test_witness_scale_factor_is_55_percent_of_severity(self):
        """ws = wsev * 0.55; Pity delta = ws * 0.9 (scaled by reactivity=1)."""
        entity = make_entity(reactivity=1.0)
        witness = {"event_type": "bad_news", "severity": 1.0, "directed_at_self": True, "intentional": False}
        base = make_event("neutral", severity=0.0)
        deltas = self.engine.compute_deltas(base, entity, witness_event=witness)
        expected_pity = 1.0 * 0.55 * 0.9 * 1.0  # wsev * ws_factor * coeff * reactivity
        assert abs(deltas.get("Pity", 0) - expected_pity) < 1e-9


# ── apply_transitions ─────────────────────────────────────────────────────────

class TestApplyTransitions:
    def setup_method(self):
        self.engine = OCCAppraisalEngine()

    def test_fear_prolonged_can_transition_to_distress(self):
        """Fear active for > 3 steps should probabilistically activate Distress."""
        entity = make_entity()
        fear = entity.emotions["Fear"]
        fear.activate(0.7)
        fear.time_active = 4  # above threshold of 3
        fear.is_active = True

        # Run many times to ensure at least one transition fires (prob=0.75)
        triggered = False
        for _ in range(50):
            e = make_entity()
            e.emotions["Fear"].activate(0.7)
            e.emotions["Fear"].time_active = 4
            e.emotions["Fear"].is_active = True
            with patch("random.random", return_value=0.1):  # 0.1 < 0.75 → fires
                self.engine.apply_transitions(e)
            if e.emotions["Distress"].is_active:
                triggered = True
                break
        assert triggered

    def test_fear_not_prolonged_does_not_transition_to_distress(self):
        """Fear active for <= 3 steps should NOT transition to Distress."""
        entity = make_entity()
        entity.emotions["Fear"].activate(0.7)
        entity.emotions["Fear"].time_active = 2  # below threshold
        entity.emotions["Fear"].is_active = True
        with patch("random.random", return_value=0.1):
            self.engine.apply_transitions(entity)
        assert not entity.emotions["Distress"].is_active

    def test_shame_high_intensity_can_transition_to_anger(self):
        """Shame with intensity > 0.4 should probabilistically activate Anger."""
        entity = make_entity()
        entity.emotions["Shame"].activate(0.6)  # > 0.4 threshold
        with patch("random.random", return_value=0.1):  # 0.1 < 0.60 → fires
            self.engine.apply_transitions(entity)
        assert entity.emotions["Anger"].is_active

    def test_shame_low_intensity_does_not_transition_to_anger(self):
        entity = make_entity()
        entity.emotions["Shame"].activate(0.3)  # below 0.4 threshold
        with patch("random.random", return_value=0.1):
            self.engine.apply_transitions(entity)
        assert not entity.emotions["Anger"].is_active

    def test_hope_high_intensity_can_transition_to_anticipation(self):
        entity = make_entity()
        entity.emotions["Hope"].activate(0.7)  # > 0.5 threshold
        with patch("random.random", return_value=0.1):  # 0.1 < 0.70 → fires
            self.engine.apply_transitions(entity)
        assert entity.emotions["Anticipation"].is_active

    def test_joy_high_intensity_can_transition_to_gratitude(self):
        entity = make_entity()
        entity.emotions["Joy"].activate(0.7)  # > 0.5 threshold
        with patch("random.random", return_value=0.1):  # 0.1 < 0.65 → fires
            self.engine.apply_transitions(entity)
        assert entity.emotions["Gratitude"].is_active

    def test_transition_carry_is_30_percent_of_source_intensity(self):
        """Carry = source_emotion.intensity * 0.3."""
        entity = make_entity()
        entity.emotions["Joy"].activate(0.8)
        with patch("random.random", return_value=0.0):  # always fires
            self.engine.apply_transitions(entity)
        # Gratitude should be activated with carry = 0.8 * 0.3 = 0.24
        expected_carry = pytest.approx(0.8 * 0.3, abs=1e-9)
        assert entity.emotions["Gratitude"].intensity == expected_carry

    def test_high_random_prevents_transition(self):
        """If random.random() >= prob, transition should NOT fire."""
        entity = make_entity()
        entity.emotions["Shame"].activate(0.9)  # well above threshold
        with patch("random.random", return_value=0.99):  # 0.99 >= 0.60 → no fire
            self.engine.apply_transitions(entity)
        assert not entity.emotions["Anger"].is_active

    def test_none_source_emotion_skipped_gracefully(self):
        """If source emotion is None (e.g. entity missing it), should skip (no crash)."""
        entity = make_entity()
        # The entity has all standard emotions, so this tests that None check works
        # We simulate by patching _transition_rules to return a rule with None source
        fake_rules = [(None, lambda e: True, "Fear", "Distress", 1.0)]
        with patch("engine.appraisal._transition_rules", return_value=fake_rules):
            self.engine.apply_transitions(entity)  # should not raise

    def test_apply_transitions_error_propagates_without_try_except(self):
        """PR change: removed try/except so condition errors now propagate."""
        entity = make_entity()
        entity.emotions["Fear"].activate(0.8)
        entity.emotions["Fear"].time_active = 5

        # A bad condition function that raises should now propagate (no swallowing)
        def bad_condition(e):
            raise RuntimeError("deliberate test error")

        fake_rules = [
            (entity.emotions["Fear"], bad_condition, "Fear", "Distress", 1.0)
        ]
        with patch("engine.appraisal._transition_rules", return_value=fake_rules):
            with pytest.raises(RuntimeError, match="deliberate test error"):
                self.engine.apply_transitions(entity)