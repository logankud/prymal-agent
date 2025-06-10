
import json
import os
from difflib import SequenceMatcher
from termcolor import colored
from datetime import datetime
from sentence_transformers import SentenceTransformer, util



# Import the actual agent from agent.py
from agent import manager_agent

def load_eval_questions(file_path: str):
    with open(file_path, "r") as f:
        return json.load(f)

def similarity(a: str, b: str) -> float:
    """Compute similarity between two strings using Sentence Transformers.

    Args:
        a (str): The first string.
        b (str): The second string.

    Returns:    
        float: The similarity score between the two strings.
    
    """

    model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

    embedding1 = model.encode(a, convert_to_tensor=True)
    embedding2 = model.encode(b, convert_to_tensor=True)

    # Compute cosine similarity between the embeddings
    cosine_sim = util.cos_sim(embedding1, embedding2)
    return cosine_sim.item()

def save_evaluation_results(results, file_path="eval/evaluation_results.json"):
    """Save evaluation results with timestamp for tracking"""
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    evaluation_data = {
        "timestamp": datetime.now().isoformat(),
        "total_questions": len(results),
        "passed": sum(1 for r in results if r.get("pass", False)),
        "accuracy": sum(1 for r in results if r.get("pass", False)) / len(results) * 100 if results else 0,
        "results": results
    }
    
    with open(file_path, "w") as f:
        json.dump(evaluation_data, f, indent=2)
    
    print(colored(f"📊 Results saved to {file_path}", "blue"))

def save_live_responses(live_responses, file_path="eval/live_responses.json"):
    """Save live responses as they are generated"""
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "w") as f:
        json.dump(live_responses, f, indent=2)

def evaluate_agent(eval_questions, threshold=0.85):
    results = []
    live_responses = {}  # Dictionary to track responses in real-time
    
    print(colored("📝 Live responses will be saved to eval/live_responses.json", "blue"))

    for idx, item in enumerate(eval_questions):
        question = item["question"]
        ground_truth = item["ground_truth"]

        print(colored(f"\n[Q{idx+1}] {question}", "cyan"))

        try:
            # Use the manager agent from agent.py
            agent_response = manager_agent.run(question)
            
            # Store the response for tracking
            score = similarity(agent_response, ground_truth)
            passed = score >= threshold

            print(colored(f"Agent Response: {agent_response}", "green"))
            print(colored(f"Ground Truth:   {ground_truth}", "yellow"))
            print(colored(f"Similarity:     {score:.2f}", "magenta"))
            print(colored(f"Pass:           {'✅' if passed else '❌'}", "white"))

            # Create result object
            result = {
                "question_id": idx + 1,
                "question": question,
                "ground_truth": ground_truth,
                "agent_response": agent_response,  # Store the actual agent response
                "similarity_score": score,
                "pass": passed,
                "threshold": threshold,
                "timestamp": datetime.now().isoformat()
            }
            
            results.append(result)
            
            # Update live responses dict and save immediately
            live_responses[f"question_{idx + 1}"] = result
            save_live_responses(live_responses)
            
            print(colored(f"💾 Response {idx + 1} saved to live_responses.json", "cyan"))

        except Exception as e:
            print(colored(f"Error running agent: {e}", "red"))
            
            # Create error result
            error_result = {
                "question_id": idx + 1,
                "question": question,
                "ground_truth": ground_truth,
                "agent_response": None,
                "error": str(e),
                "similarity_score": 0.0,
                "pass": False,
                "threshold": threshold,
                "timestamp": datetime.now().isoformat()
            }
            
            results.append(error_result)
            
            # Update live responses dict and save immediately
            live_responses[f"question_{idx + 1}"] = error_result
            save_live_responses(live_responses)
            
            print(colored(f"💾 Error response {idx + 1} saved to live_responses.json", "cyan"))

    return results

if __name__ == "__main__":
    questions_path = "eval/eval_questions.json"
    eval_questions = load_eval_questions(questions_path)

    print(colored(f"\n🔍 Running Evaluation on {len(eval_questions)} Questions...\n", "blue"))
    print(colored(f"Using Manager Agent from agent.py", "blue"))
    print(colored(f"Progress will be saved in real-time to eval/live_responses.json", "blue"))
    
    results = evaluate_agent(eval_questions)

    # Calculate summary stats
    passed = sum(1 for r in results if r.get("pass", False))
    total = len(results)
    accuracy = passed / total * 100 if total > 0 else 0

    print(colored(f"\n✅ Eval Complete: {passed}/{total} passed ({accuracy:.1f}%)\n", "blue"))
    
    # Save results for tracking
    save_evaluation_results(results)
    
    # Print summary of agent responses for review
    print(colored("\n📋 Agent Response Summary:", "blue"))
    for result in results:
        status = "✅ PASS" if result.get("pass", False) else "❌ FAIL"
        print(colored(f"Q{result['question_id']}: {status} (Score: {result.get('similarity_score', 0):.2f})", "white"))
    
    print(colored(f"\n💾 Live responses tracked in: eval/live_responses.json", "blue"))
    print(colored(f"📊 Final results saved in: eval/evaluation_results.json", "blue"))
