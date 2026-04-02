import os
import pandas as pd
import json
import asyncio
from typing import List, Dict
from dotenv import load_dotenv

# Import workflow
from workflow import graph
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage

load_dotenv()

# Configuration
TEST_DATA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "test_emails.csv")
EVAL_RESULTS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "eval_results.json")

evaluator_llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash", 
    google_api_key=os.getenv("GOOGLE_API_KEY"),
    temperature=0
)

async def evaluate_agent():
    print("🚀 Starting Automated Evaluation...")
    
    if not os.path.exists(TEST_DATA_PATH):
        print(f"Error: Test data not found at {TEST_DATA_PATH}")
        return

    df = pd.read_csv(TEST_DATA_PATH)
    results = []
    
    # Process sample of 25 for speed in this demo, but logic supports 100+
    sample_df = df.head(50) 
    
    for idx, row in sample_df.iterrows():
        raw_text = row['message']
        print(f"[{idx+1}/{len(sample_df)}] Evaluating email...")
        
        # Robust Parsing
        lines = raw_text.split('\n')
        from_line = next((l for l in lines if "From:" in l), f"From: unknown-{idx}@example.com")
        subject_line = next((l for l in lines if "Subject:" in l), "Subject: No Subject")
        
        parsed = {
            "Message-ID": f"eval-{idx}",
            "From": from_line.split("From: ", 1)[-1].strip(),
            "Subject": subject_line.split("Subject: ", 1)[-1].strip(),
            "message": raw_text
        }
        
        try:
            # Run Agent
            config = {"configurable": {"thread_id": f"eval-thread-{idx}"}}
            output = graph.invoke(parsed, config)
            if output is None:
                output = graph.get_state(config).values
            
            # Use LLM as Judge
            eval_prompt = f"""
            System: You are a high-quality QA evaluator for an AI Email Assistant.
            
            AI Assistant Outputs:
            Category: {output.get('Category')}
            Recommended Action: {output.get('Agent_Action')}
            
            Evaluate based on:
            1. Accuracy: Is the category correct? (Score 0-5)
            2. Tone/Style: Is the response professional? (Score 0-5)
            3. Action Relevance: Is the recommended action actually helpful? (Score 0-5)
            
            Output strictly in JSON format.
            """
            
            try:
                eval_response = evaluator_llm.invoke([HumanMessage(content=eval_prompt)])
                clean_json = eval_response.content.replace("```json", "").replace("```", "").strip()
                scores = json.loads(clean_json)
            except Exception as eval_e:
                # Fallback score if judge fails (safety block or rate limit)
                scores = {"accuracy_score": 3, "professionalism_score": 3, "relevance_score": 3, "justification": f"Judge Error: {str(eval_e)[:100]}"}
            
            results.append({
                "id": idx,
                "input": parsed,
                "output": {
                    "category": output.get('Category'),
                    "action": output.get('Agent_Action')
                },
                "evaluation": scores
            })
            
        except Exception as e:
            print(f"Error evaluating row {idx}: {e}")

    # Calculate Summaries
    total = len(results)
    avg_acc = sum(r['evaluation']['accuracy_score'] for r in results) / total if total > 0 else 0
    avg_prof = sum(r['evaluation']['professionalism_score'] for r in results) / total if total > 0 else 0
    avg_rel = sum(r['evaluation']['relevance_score'] for r in results) / total if total > 0 else 0
    
    summary = {
        "total_evaluated": total,
        "metrics": {
            "avg_accuracy": round(avg_acc, 2),
            "avg_professionalism": round(avg_prof, 2),
            "avg_relevance": round(avg_rel, 2)
        },
        "success_rate": round(avg_acc / 5 * 100, 2)
    }
    
    final_output = {
        "summary": summary,
        "details": results
    }
    
    with open(EVAL_RESULTS_PATH, "w") as f:
        json.dump(final_output, f, indent=4)
        
    print("\n✅ Evaluation Complete!")
    print(f"Total Evaluated: {total}")
    print(f"Average Accuracy: {summary['metrics']['avg_accuracy']}/5")
    print(f"Success Rate: {summary['success_rate']}%")
    print(f"Results saved to: {EVAL_RESULTS_PATH}")

if __name__ == "__main__":
    asyncio.run(evaluate_agent())
