from smolagents import PromptTemplates, CodeAgent

prompt_template = PromptTemplates()

# Initial system prompt (sets behavior/persona)
prompt_template.initial = """
You are the Manager agent. Your job is to:
- Interpret the user's task.
- Delegate it to the Analyst agent.
- Once the Analyst returns a validated answer, you provide a concise response to the user.

Avoid repeating verbose logs or unnecessary steps.
"""

# Final answer format — concise with caveats
prompt_template.final_answer.pre_messages = "✅ Task complete."
prompt_template.final_answer.post_messages = """
Here is a concise summary for the user:

Answer: {short}

Caveats (if any): {caveats}
"""
