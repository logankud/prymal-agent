from agents import manager_agent
from smolagents.memory import ActionStep, FinalAnswerStep

def test_run(prompt):
    stepper = manager_agent.run(prompt, max_steps=20)
    for step in stepper:
        if isinstance(step, ActionStep):
            print(f"=== Step {step.step_number} ===")
            print("Prompt:", step.model_input)
            print("Output:", step.model_output)
            if step.tool_call:
                print("Tool:", step.tool_call, "→", step.tool_call_result)
        elif isinstance(step, FinalAnswerStep):
            print("🔹 Final Answer:", step.model_output)
            break

if __name__ == "__main__":

    # Take user input
    prompt = input("Enter your prompt: ")

    test_run(prompt)
