import json
from difflib import SequenceMatcher
from termcolor import colored

# Update this import to match the correct path in your repo
from agent import manager_agent

def load_eval_questions(file_path: str):
    with open(file_path, "r") as f:
        return json.load(f)

def similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def evaluate_agent(eval_questions, threshold=0.85):
    results = []

    for idx, item in enumerate(eval_questions):
        question = item["question"]
        ground_truth = item["ground_truth"]

        print(colored(f"\n[Q{idx+1}] {question}", "cyan"))

        try:
            response = manager_agent.run(question)
        except Exception as e:
            print(colored(f"Error running agent: {e}", "red"))
            results.append({
                "question": question,
                "error": str(e),
                "score": 0.0,
                "pass": False
            })
            continue

        score = similarity(response, ground_truth)
        passed = score >= threshold

        print(colored(f"Agent Response: {response}", "green"))
        print(colored(f"Ground Truth:   {ground_truth}", "yellow"))
        print(colored(f"Similarity:     {score:.2f}", "magenta"))
        print(colored(f"Pass:           {'✅' if passed else '❌'}", "white"))

        results.append({
            "question": question,
            "ground_truth": ground_truth,
            "agent_response": response,
            "score": score,
            "pass": passed
        })

    return results

if __name__ == "__main__":
    questions_path = "eval/eval_questions.json"  # path to evaluation questions & answers
    eval_questions = load_eval_questions(questions_path)

    print(colored(f"\n🔍 Running Evaluation on {len(eval_questions)} Questions...\n", "blue"))
    results = evaluate_agent(eval_questions)

    passed = sum(1 for r in results if r["pass"])
    total = len(results)
    accuracy = passed / total * 100

    print(colored(f"\n✅ Eval Complete: {passed}/{total} passed ({accuracy:.1f}%)\n", "blue"))
