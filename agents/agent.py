import os
from groq import Groq
from entity.entity import Entity
from engine.evaluator import AppraisalEvaluator
from engine.appraisal import OCCAppraisalEngine, REACTIVITY
from engine.prompt_modifier import PromptModifier


class Agent:
    def __init__(
        self,
        name: str,
        personality: str = "average",
        base_persona: str = "",
        model: str = "llama-3.3-70b-versatile",
        reactivity: float = None,
    ):
        self.name = name
        self.base_persona = base_persona
        self.model = model
        resolved_reactivity = reactivity if reactivity is not None else REACTIVITY.get(personality, 1.0)
        self.entity = Entity(name, personality, reactivity=resolved_reactivity)
        self.evaluator = AppraisalEvaluator(model=model)
        self.appraisal_engine = OCCAppraisalEngine()
        self.prompt_modifier = PromptModifier()
        self.client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
        self.conversation_history: list[dict] = []
        self.last_event: dict = {}

    def receive_and_respond(self, incoming_message: str, witness_event: dict = None) -> str:
        """
        Full pipeline: appraise incoming message → update emotional state →
        build emotionally-modulated prompt → generate response.

        witness_event: the appraisal event the *sender* experienced on the
        previous turn — used to generate empathic emotion deltas independently
        of the surface language of their message.
        """
        # 1. Appraise incoming message
        event = self.evaluator.evaluate(incoming_message)
        self.last_event = event

        # 2. Apply OCC rules → emotion deltas (+ witness empathy track)
        deltas = self.appraisal_engine.compute_deltas(event, self.entity, witness_event)
        self.entity.apply_deltas(deltas)

        # 3. Apply emotion transitions
        self.appraisal_engine.apply_transitions(self.entity)

        # 4. Decay emotions one step
        self.entity.decay_all()

        # 5. Build system prompt from emotional state
        system_prompt = self.prompt_modifier.build_system_prompt(
            self.entity, self.base_persona
        )

        # 6. Update conversation history
        self.conversation_history.append({"role": "user", "content": incoming_message})

        # 7. Call LLM to generate response
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "system", "content": system_prompt}] + self.conversation_history,
            temperature=0.8,
            max_tokens=256,
        )
        reply = response.choices[0].message.content.strip()

        # 8. Add own reply to history
        self.conversation_history.append({"role": "assistant", "content": reply})

        return reply

    def get_state_display(self) -> str:
        return self.entity.display_state()
