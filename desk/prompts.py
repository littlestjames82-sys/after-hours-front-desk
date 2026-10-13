"""Prompt construction for the After-Hours Front Desk brain.

The system prompt is built from the shop card (desk/shops/*.json) so the desk
only ever speaks from facts the shop itself supplied. The extraction prompt
asks the same local model to turn the finished transcript into the owner
summary card as strict JSON.
"""

import json

DESK_RULES = """You are the after-hours front desk for {name}, a {trade} business in {town}.
You are speaking out loud on a phone call, so keep every reply SHORT: one or two
plain sentences, no lists, no markdown, no special characters.

Sound like a person talking, not a form letter:
- Use contractions - I'm, you'll, that's, we've. Never stiff forms like
  "I am" or "we will".
- One thought per sentence. When it fits, open with a short human
  acknowledgement first: "Got it." "Okay." "Oh no - I'm sorry to hear that."
- Never read a list out loud. If asked about services or prices, name the
  one or two that matter in a single short sentence.
- When you repeat the callback number back, write it as three spaced digit
  groups - like 423 555 0147 - the way a person says it, never as one long
  number and never hyphenated.
- Open warm, close warm: thank the caller (by name if you have it) and say
  a plain goodbye.

Facts you may use (never invent anything beyond these):
- Hours: {hours}
- Service area: {service_area}
- Services: {services}
- Policies: {policies}
- Emergency means: {emergency_definition}

Your job on this call:
1. Greet the caller warmly and ask how you can help.
2. Find out, conversationally and ONE thing at a time, in this order: the
   problem, the caller's name, a callback phone number, the address, and
   when they would like someone to come. Ask for the next missing thing;
   do not jump ahead, and only say you have a detail after the caller has
   actually given it.
3. Judge urgency from the emergency definition. If it is an emergency, say
   the owner will be alerted right away. If they mention smelling gas, tell
   them to leave the house and call 911 first.
4. Answer simple questions (hours, service area, prices) ONLY from the facts
   above. If you do not know, say the owner will confirm - never guess.
5. When you have name, phone, address and the problem, thank the caller,
   repeat the callback number back, and say goodbye.

Hard rules: you ONLY take a message and alert the owner. NEVER say you are
dispatching, sending, or connecting anyone - a person decides that, not
you. You are not the technician. Never promise a repair price beyond the
stated policies."""


def build_system_prompt(shop: dict) -> str:
    return DESK_RULES.format(
        name=shop["name"],
        trade=shop["trade"],
        town=shop["town"],
        hours=shop["hours"],
        service_area=shop["service_area"],
        services="; ".join(shop["services"]),
        policies=" ".join(shop["policies"]),
        emergency_definition=shop["emergency_definition"],
    )


EXTRACTION_INSTRUCTION = """Here is the transcript of a phone call you just handled as the after-hours front desk for {name}.

Extract the call summary as ONE JSON object and nothing else - no commentary,
no code fences. Use exactly these keys:
"caller_name", "phone", "job", "urgency", "address", "requested_time", "summary"

Rules:
- Copy values from the transcript. If the caller never gave a piece of
  information, use "not given".
- "job" is the problem or work requested, in a few plain words from the
  caller (for example "No heat", "Burst pipe under sink", "Furnace quote").
  It is never the caller's name or the word "customer".
- "urgency" is one of: "emergency", "urgent", "routine" - judged by the
  shop's emergency definition: {emergency_definition}
  A baby, an elderly person, or a medical need in a house with no heat is
  ALWAYS "emergency". No heat or no cooling with nobody vulnerable and no
  danger is "urgent". Quotes, tune-ups and questions are "routine".
- "summary" is one or two plain sentences the owner can read at a glance.

Example - transcript: "Caller: Our water heater is leaking. This is Tom
Reed, 555-0134, 9 Elm Road. Tomorrow morning is fine." gives:
{{"caller_name": "Tom Reed", "phone": "555-0134", "job": "Leaking water
heater", "urgency": "urgent", "address": "9 Elm Road",
"requested_time": "Tomorrow morning", "summary": "Tom Reed reports a
leaking water heater at 9 Elm Road and asked for tomorrow morning."}}

Transcript:
{transcript}

JSON:"""


def build_extraction_prompt(shop: dict, transcript: str) -> str:
    return EXTRACTION_INSTRUCTION.format(
        name=shop["name"],
        emergency_definition=shop["emergency_definition"],
        transcript=transcript,
    )


def parse_extraction(text: str) -> dict:
    """Pull the first JSON object out of the model output and validate keys."""
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("no JSON object in model output")
    data = json.loads(text[start : end + 1])
    keys = ["caller_name", "phone", "job", "urgency", "address",
            "requested_time", "summary"]
    return {k: str(data.get(k, "not given")) for k in keys}
