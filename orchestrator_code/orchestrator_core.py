from typing import TypedDict, List
from langgraph.graph import StateGraph, END
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage
import subprocess
import time
import wandb

# 1. Initialize Local Model (Qwen)
# 172.17.0.1 is the default IP address the container uses to talk to your host server
llm = ChatOllama(model="qwen2.5:7b", base_url="http://host.docker.internal:11434")

wandb.init(project="red-blue-llm-arena", name="baseline-nmap-detection")

# 2. Define the State Memory
class AgentState(TypedDict):
    objective: str
    vulnerabilities_found: List[str]
    blue_team_alerts: List[str]
    current_agent: str
    # --- New Metrics Fields ---
    start_time: float
    attack_time: float
    detect_time: float

# 3. Define the Director Node (The Brain)
def director_agent(state: AgentState):
    print("\n[DIRECTOR] Reviewing current intelligence...")
    
    prompt = f"""
    You are the Director of an autonomous Red Team. 
    Objective: {state['objective']}
    Vulnerabilities Found: {state['vulnerabilities_found']}
    
    Rule 1: If Vulnerabilities Found is empty, you MUST use the scanner.
    Rule 2: If Vulnerabilities Found has items, you MUST use the exploiter.
    
    Reply with exactly ONE word: either 'scanner' or 'exploiter'.
    """
    
    # Send the prompt to Qwen running on your A6000 GPUs
    response = llm.invoke([HumanMessage(content=prompt)])
    
    # Clean up the output to ensure exact routing
    decision = response.content.strip().lower()
    decision = ''.join(e for e in decision if e.isalnum())
    
    print(f"[DIRECTOR] AI Decision -> Routing to {decision.upper()}")
    return {"current_agent": decision}

# 4. Mock Specialist Nodes (We will replace these with real hacking tools next)
def scanner_agent(state: AgentState):
    print("\n[SCANNER] Waking up. Executing real network scan inside the sandbox...")
    
    # We use subprocess to tell the Docker socket to run nmap inside the sandbox container.
    # We are scanning the 'decepticon_target' container. 
    # -p 21,22,80 limits the scan for speed right now.
    cmd = [
        "docker", "exec", "decepticon_sandbox", 
        "nmap", "-p", "21,22,80", "-sV", "decepticon_target"
    ]
    
    try:
        # Fire the command!
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        raw_output = result.stdout
        print(f"\n--- RAW NMAP OUTPUT ---\n{raw_output.strip()}\n-----------------------\n")
        
        # Simple parsing to extract open ports to feed back to the AI
        found_vulns = []
        for line in raw_output.split('\n'):
            if "open" in line and "/" in line:
                found_vulns.append(line.strip())
                
        if not found_vulns:
            found_vulns = ["Scan completed, but no obvious ports open."]
            
        return {
            "vulnerabilities_found": found_vulns,
            "current_agent": "director"
        }
        
    except subprocess.CalledProcessError as e:
        print(f"[SCANNER ERROR] Failed to run nmap: {e.stderr}")
        return {
            "vulnerabilities_found": ["Scanner failed to execute."],
            "current_agent": "director"
        }

    # Record exactly when the attack payload/scan was fired
    state["attack_time"] = time.time()
    
    return {
        "vulnerabilities_found": found_vulns,
        "attack_time": state["attack_time"],
        "current_agent": "director"
    }

def exploiter_agent(state: AgentState):
    print(f"\n[EXPLOITER] Developing payload for: {state['vulnerabilities_found'][-1]}")
    print("[EXPLOITER] Payload fired successfully. Target compromised.")
    return {"current_agent": "end"}


def defender_agent(state: AgentState):
    print("\n[DEFENDER] Waking up. Analyzing target server logs for anomalies...")
    
    # Grab the last 15 lines of the target's web server logs
    cmd = ["docker", "logs", "--tail", "15", "decepticon_target"]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        # Web traffic logs usually go to stderr in this specific container
        logs = result.stderr if result.stderr else result.stdout 
        
        prompt = f"""
        You are a Blue Team SOC Analyst. Review these recent web server logs:
        {logs}
        
        Do you see any evidence of an automated scanner (like Nmap, Nikto, or DirBuster) or an exploit attempt? 
        If yes, reply with a brief 1-sentence alert describing the threat. 
        If no, reply exactly with 'No threats detected.'
        """
        
        response = llm.invoke([HumanMessage(content=prompt)])
        alert = response.content.strip()
        
        print(f"\n--- SOC ALERT ---\n{alert}\n-----------------\n")
        
        return {
            "blue_team_alerts": [alert],
            "current_agent": "end" # End the loop for now
        }
        
    except subprocess.CalledProcessError as e:
        print(f"[DEFENDER ERROR] Failed to fetch logs: {e.stderr}")
        return {"current_agent": "end"}

    
    # Record exactly when the Blue Team successfully identified the threat
    detect_time = time.time()
    mttd = detect_time - state.get("attack_time", detect_time)
    
    # Log the metrics directly to WandB
    wandb.log({
        "mttd_seconds": mttd,
        "defender_alert_length": len(alert),
        "threat_detected": "Yes" in alert
    })
    
    print(f"\n--- SOC ALERT ---\n{alert}\n-----------------\n")
    print(f"[METRIC] Time to Detect (MTTD): {mttd:.2f} seconds")
    
    return {
        "blue_team_alerts": [alert],
        "detect_time": detect_time,
        "current_agent": "end"
    }


def patcher_agent(state: AgentState):
    print("\n[PATCHER] Waking up. Developing mitigation based on SOC alert...")
    
    alert = state["blue_team_alerts"][-1]
    offender_ip = "172.19.0.2"
    
    prompt = f"""
    You are a SOC Engineer. Alert: "{alert}" Offender IP: {offender_ip}.
    Write ONE 'iptables' command to drop traffic from this IP.
    Reply ONLY with the command. NO markdown, NO backticks, NO explanations.
    """
    
    response = llm.invoke([HumanMessage(content=prompt)])
    raw_output = response.content.strip()
    
    # Bulletproof parsing: Find the exact line containing the command
    clean_cmd = ""
    for line in raw_output.split('\n'):
        if "iptables" in line:
            # Remove any lingering backticks or markdown
            clean_cmd = line.replace("`", "").strip()
            break
            
    if not clean_cmd:
        print("[PATCHER ERROR] AI failed to generate a valid iptables command.")
        wandb.log({"mitigation_applied": False})
        return {"current_agent": "end"}
        
    print(f"[PATCHER] Executing cleaned rule: {clean_cmd}")
    
    try:
        cmd = ["docker", "exec", "--privileged", "decepticon_target"] + clean_cmd.split()
        subprocess.run(cmd, capture_output=True, text=True, check=True)
        
        print("[PATCHER] Firewall rule applied successfully. Target secured.")
        wandb.log({"mitigation_applied": True})
        
    except subprocess.CalledProcessError as e:
        print(f"[PATCHER ERROR] Failed to apply firewall rule: {e.stderr}")
        wandb.log({"mitigation_applied": False})
        
    return {"current_agent": "end"}


# 5. Routing Logic Engine
def router(state: AgentState):
    if state["current_agent"] == "scanner":
        return "scanner_node"
    elif state["current_agent"] == "exploiter":
        return "exploiter_node"
    elif state["current_agent"] == "defender":
        return "defender_node"
    elif state["current_agent"] == "patcher":
        return "patcher_node"
    elif state["current_agent"] == "end":
        return END
    else:
        return "director_node"

# 6. Compile the LangGraph
workflow = StateGraph(AgentState)
workflow.add_node("director_node", director_agent)
workflow.add_node("scanner_node", scanner_agent)
workflow.add_node("exploiter_node", exploiter_agent)
workflow.add_node("defender_node", defender_agent)
workflow.add_node("patcher_node", patcher_agent)

workflow.set_entry_point("director_node")
workflow.add_conditional_edges("director_node", router, {
    "scanner_node": "scanner_node", 
    "exploiter_node": "exploiter_node",
    "defender_node": "defender_node",
    "patcher_node": "patcher_node", # Add patcher here
    END: END
})
workflow.add_edge("scanner_node", "director_node")
workflow.add_edge("exploiter_node", "defender_node") # Handoff to Blue Team
workflow.add_edge("defender_node", "patcher_node") 
workflow.add_edge("patcher_node", END)

app = workflow.compile()

# 7. Execute the Graph
if __name__ == "__main__":
    print("--- INITIATING AUTONOMOUS RED TEAM ---")
    initial_state = {
        "objective": "Find an open port and compromise the target",
        "vulnerabilities_found": [],
        "blue_team_alerts": [],
        "current_agent": "director",
        "start_time": time.time(),
        "attack_time": 0.0,
        "detect_time": 0.0
    }
    app.invoke(initial_state)
    wandb.finish()
    print("\n--- OPERATION CONCLUDED ---")
