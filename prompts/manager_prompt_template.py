from smolagents.agents import PromptTemplates, FinalAnswerPromptTemplate, ManagedAgentPromptTemplate, PlanningPromptTemplate

manager_prompt_template = PromptTemplates(
    system_prompt="""You are the Manager agent. Your job is to interpret the user's question,
    delegate it to the appropriate managed_agent, and return a clear summary of the result returned to you by the managed_agent.""",

    planning=PlanningPromptTemplate(
        initial_plan="Let's break this question down into steps.",
        update_plan_pre_messages="Received new input. Updating plan...",
        update_plan_post_messages="Plan updated.",
    ),

    managed_agent=ManagedAgentPromptTemplate(
        task="Here is the task to perform:",
        report="Report back with your answer and caveats.",
    ),

    final_answer=FinalAnswerPromptTemplate(
        pre_messages="✅ Analysis complete.",
        post_messages="Answer:\n{answer}\n\nCaveats:\n{caveats}"
    )
)