from smolagents import PromptTemplates, CodeAgent

manager_prompt_template = PromptTemplates()

# Initial system prompt (sets behavior/persona)
manager_prompt_template.system_prompt = """
You are the Manager agent. Your job is to:
- Interpret the user's task.
- Delegate it to the Analyst agent.
- Once the Analyst returns a validated answer, you provide a concise response to the user.

Avoid repeating verbose logs or unnecessary steps.
"""

# Final answer format — concise with caveats
manager_prompt_template.final_answer.pre_messages = "✅ Task complete."
manager_prompt_template.final_answer.post_messages = """
Here is a concise summary for the user:

Answer: {short}

Caveats (if any): {caveats}
"""
