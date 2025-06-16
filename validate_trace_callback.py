
from smolagents.schema import ActionStep

def validate_trace(step: ActionStep, agent):
    """
    Step callback to validate an agent's final answer using the full trace of steps.
    If the final answer fails validation, an exception is raised.
    """
    # Only act on the final answer step
    if not getattr(step, "is_final_answer", False):
        return

    final_answer = step.action_output

    # Collect full trace of agent's steps
    all_steps = agent.memory.get_full_steps()
    trace_str = "\n".join(
        f"Step {s['step_number']}:\n"
        f"Thoughts: {s.get('thoughts', '')}\n"
        f"Code:\n{s.get('code', '')}\n"
        f"Observations: {s.get('observations', '')}\n"
        for s in all_steps
    )

    # Validation prompt
    prompt = f"""
The agent has produced the following final answer:

```
{final_answer}
```

Here is the full trace of steps taken by the agent:

```
{trace_str}
```

You are a critical reviewer responsible for validating the trustworthiness of an Analyst Agent’s final answer.

Please answer the following checklist strictly. Use ✅ Yes / ❌ No / 🤔 Unclear for each, and include a short justification.

1. Does the final answer include executable Python code used to perform the analysis or extract the data?
2. If API calls were required, does the code include pagination logic (e.g., loops, cursors, or query limits)?
3. Does the answer mention what data source(s) were used and how they were accessed?
4. Does the answer indicate that the result was computed or derived — rather than guessed or assumed?
5. If data was unavailable or insufficient, does the answer clearly state this and explain why?
6. Are caveats or assumptions listed, especially when working with incomplete or uncertain data?
7. Is the "short version" answer consistent with the detailed explanation?
8. Overall, would a domain expert trust this answer based on the reasoning and evidence provided?

List your reasoning. If the answer is insufficient or untrustworthy, reply with **FAIL**. Otherwise, reply with **PASS**.
"""

    response = agent.model([{"role": "user", "content": prompt}])
    verdict = response.content.strip()

    if "**FAIL**" in verdict or "FAIL" in verdict:
        raise Exception(f"Validation failed:\n{verdict}")

    print("Validation passed.")
