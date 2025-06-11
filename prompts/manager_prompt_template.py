from smolagents.agents import PromptTemplates, FinalAnswerPromptTemplate, ManagedAgentPromptTemplate, PlanningPromptTemplate

manager_prompt_template = PromptTemplates(
    system_prompt="""You are the Manager agent. Your job is to interpret the user's question,
    delegate it to the appropriate managed_agent, and return a clear summary of the result returned to you by the managed_agent.""",

    planning=PlanningPromptTemplate(
        initial_plan="I need to delegate this task to my analyst agent.",
        update_plan_pre_messages="Received new input. Updating plan...",
        update_plan_post_messages="Plan updated.",
    ),

    managed_agent=ManagedAgentPromptTemplate(
        task="Please answer this question:",
        report="Report back with your findings.",
    ),

    final_answer=FinalAnswerPromptTemplate(
        pre_messages="Based on the analyst's work, here is the answer. Keep it concise - if there's a single word or number answer, just state that:",
        post_messages="{final_answer}"
    )
)