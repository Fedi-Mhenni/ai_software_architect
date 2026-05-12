# Prompts

This project uses prompts as versioned engineering assets. The goal is not to generate long prose, but to produce predictable, structured JSON that can be validated, tested, and orchestrated.

## Prompt Strategy

- Keep prompts short, explicit, and role-focused.
- Require JSON-only answers.
- Include the exact schema shape in the prompt when possible.
- Add examples of valid outputs so the model can follow the format.
- Avoid hidden assumptions: ask clarification questions before moving to architecture.

## Pipeline V1

1. User submits a project idea.
2. Idea analyzer summarizes the idea and detects project type.
3. Question generator produces clarification questions.
4. The orchestrator validates the JSON output.
5. The validated response is returned to the API layer.

## Structured Output Rules

- The LLM must return JSON only.
- No markdown, no explanations, no code fences.
- The output must match the `ClarificationResponse` schema.
- If the response is invalid, the orchestrator parses and validates again before failing.

## Prompt Versioning

- Keep prompt files in `/prompts`.
- Store prompt experiments in `/examples`.
- Update prompts only through commits so changes remain traceable.

## Current Prompt

- `prompts/architect_prompt.txt`: first architect prompt for clarification and JSON output.

