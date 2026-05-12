# Prompt Test

## Input

```text
I want to build a SaaS that helps restaurants manage deliveries and online orders with AI-driven recommendations.
```

## Expected Behavior

- Return JSON only.
- Include a short project summary.
- Detect the project as a SaaS.
- Estimate complexity as medium.
- Ask clarification questions about users, scale, data, realtime, and security.

## Expected Output Shape

- `project_summary`: string
- `detected_project_type`: string
- `complexity`: low | medium | high
- `questions`: array of clarification questions

## Reference Output

See `clarification_output.json`.
