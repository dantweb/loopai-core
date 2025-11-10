# Task-Splitting: Abstract Logic, Validation, and Implementation Guide

## Introduction

This document outlines the abstract logic for decomposing a high-level task prompt into subtasks, executing them in a structured manner, and validating completion. The approach is grounded in formal logic and graph theory to ensure stability, clarity, and mathematical rigor. We model tasks as a **Directed Acyclic Graph (DAG)**, where nodes represent subtasks with boolean predicates for success, and edges enforce dependencies.

The system ensures:
- **Completeness**: The union of subtasks fully covers the original prompt.
- **Atomicity**: Each subtask is indivisible and has a single, verifiable success condition.
- **Orderliness**: Dependencies prevent cycles and enforce sequencing.

This logic is implemented in Python, with code snippets provided for key components.

## 1. Hierarchical Decomposition Logic

### Principle: Predicate Decomposition
A task prompt \( P \) is a boolean predicate: \( P \) is true if the task is completed. We decompose \( P \) into child predicates \( P_1, P_2, \dots, P_n \) such that:
\[
P \equiv \bigwedge_{i=1}^n P_i
\]
(Logical AND: \( P \) holds if *all* \( P_i \) hold.)

- **Coverage Invariant**: Every \( P_i \) must semantically contribute to \( P \). Formally, \( \bigcup \text{domain}(P_i) = \text{domain}(P) \), where "domain" refers to the conceptual space covered by the task (e.g., actions, resources).
- **Atomicity Invariant**: Each \( P_i \) is atomic—no further decomposition needed. It has a single success predicate \( V_i \) (validation function) that evaluates to true/false.
- **Sequencing Invariant**: Dependencies form a partial order. Represented as a DAG:
  - Nodes: Subtasks \( t_i = (id, title, desc, deps, V_i) \)
  - Edges: \( t_j \to t_i \) if \( t_j \) depends on \( t_i \) (i.e., \( t_i \) must complete before \( t_j \)).

**Decomposition Process**:
1. **LLM-Driven Split**: Feed the prompt to an LLM with a system prompt enforcing the invariants:
   ```
   Decompose {prompt} into 3-7 atomic subtasks. Each subtask must:
   - Cover a unique part of the prompt.
   - Have a clear validation criterion (e.g., "Output: list of 3 options with prices").
   - List dependencies as IDs (1-based).
   Output ONLY JSON: {structure}.
   ```
2. **Post-Processing Check**:
   - Verify no cycles (using topological sort).
   - Ensure coverage via semantic similarity (e.g., cosine similarity > 0.8 between prompt and concatenated subtask descriptions, using embeddings from `sentence-transformers`).
   - If invalid, re-query LLM.

**Mathematical Formalism**:
- Let \( G = (V, E) \) be the DAG, \( V = \{t_1, \dots, t_n\} \).
- Completion time \( c(t_i) \): Timestamp when \( V_i \) evaluates to true.
- Global completion: \( P \) is true iff \( \forall i: V_i = \true \) and \( \forall (t_j \to t_i) \in E: c(t_j) \geq c(t_i) \).

### Example Decomposition
Prompt: "Plan and buy a laptop under $1000 online."

- \( t_1 \): Research options. \( V_1 \): "At least 3 laptops listed with specs/prices." Deps: [].
- \( t_2 \): Compare prices. \( V_2 \): "Comparison table with sources." Deps: [1].
- \( t_3 \): Purchase. \( V_3 \): "Order confirmation URL." Deps: [2].

DAG: \( t_1 \to t_2 \to t_3 \).

## 2. Execution Flow: Following the DAG

### Principle: Topological Execution
Execute subtasks in topological order to respect dependencies. This ensures no subtask starts until prerequisites are validated.

**Algorithm**:
1. Compute topological sort \( \sigma = [t_{i_1}, t_{i_2}, \dots, t_{i_n}] \) (linear extension of the partial order).
2. For each \( t_{i_k} \) in \( \sigma \):
   - If all deps completed (i.e., \( \forall d \in \deps(t_{i_k}): V_d = \true \)), execute \( t_{i_k} \) (e.g., via agent or script).
   - Update status: "in_progress" → "completed" if \( V_{i_k} = \true \), else "failed".
3. Propagate failures: If any \( V_i = \false \), mark dependent subtasks as "blocked".

**Handling Parallelism**: Independent subtasks (no shared deps) can run concurrently (e.g., via async queues in Python).

**Code Snippet: Topological Sort and Execution**
```python
from collections import defaultdict, deque
from typing import List, Dict, Any

class Subtask:
    def __init__(self, id: int, title: str, deps: List[int], validation: str):
        self.id = id
        self.title = title
        self.deps = deps
        self.validation = validation  # String representation of V_i
        self.status = "pending"
        self.result = None  # Output after execution

def topological_sort(subtasks: List[Subtask]) -> List[int]:
    graph = defaultdict(list)
    indegree = {s.id: 0 for s in subtasks}
    for s in subtasks:
        for dep in s.deps:
            graph[dep].append(s.id)
            indegree[s.id] += 1
    queue = deque([s.id for s in subtasks if indegree[s.id] == 0])
    order = []
    while queue:
        tid = queue.popleft()
        order.append(tid)
        for neighbor in graph[tid]:
            indegree[neighbor] -= 1
            if indegree[neighbor] == 0:
                queue.append(neighbor)
    if len(order) != len(subtasks):
        raise ValueError("Cycle detected in dependencies!")
    return order

def execute_dag(subtasks: List[Subtask], executor: callable) -> Dict[int, Any]:
    order = topological_sort(subtasks)
    results = {}
    for tid in order:
        subtask = next(s for s in subtasks if s.id == tid)
        if all(next(s for s in subtasks if s.id == d).status == "completed" for d in subtask.deps):
            subtask.status = "in_progress"
            subtask.result = executor(subtask)  # e.g., LLM agent call
            subtask.status = "completed" if validate_subtask(subtask) else "failed"
        else:
            subtask.status = "blocked"
        results[tid] = subtask.result
    return results
```

## 3. Validation Logic: Acceptance Criteria and Fulfillment

### Principle: Predicate Evaluation
Each subtask \( t_i \) has a validation predicate \( V_i: \text{Result} \to \{\true, \false\} \). \( V_i \) is defined by acceptance criteria in natural language but parsed into executable rules.

**Types of Validation Rules** (Extensible):
- **String Match**: e.g., "contains 'URL'" → Check if result includes a valid URL.
- **Regex Pattern**: e.g., "matches r'https?://\S+'" for links.
- **Quantitative**: e.g., "length >= 3" for lists.
- **External Check**: e.g., API call to verify purchase (e.g., check email for confirmation).
- **LLM Judgment**: Fallback: Query LLM with "Does [result] satisfy [criteria]?" and threshold on confidence.

**Evaluation**:
- Input: Subtask result (string/JSON).
- Output: Boolean + explanation.
- Stability: Rules are deterministic where possible; probabilistic (LLM) ones use fixed seeds/temperatures.

**Global Validation**: Whole task done when:
\[
\text{TaskComplete} = \left( \bigwedge_{i=1}^n V_i \right) \land \left( \forall (t_j \to t_i) \in E: c(t_j) \geq c(t_i) \right)
\]
- All subtasks completed *and* order respected.
- If any failed, task is "failed" unless retry logic (e.g., re-execute up to 3x).

**Code Snippet: Validation Engine**
```python
import re
from typing import Callable, Dict, Any

class ValidationEngine:
    def __init__(self, subtasks: List[Subtask]):
        self.subtasks = {s.id: s for s in subtasks}
        self.validators: Dict[int, Callable[[str], bool]] = self._build_validators()

    def _build_validators(self) -> Dict[int, Callable[[str], bool]]:
        validators = {}
        for sid, subtask in self.subtasks.items():
            if "contains URL" in subtask.validation.lower():
                validators[sid] = lambda r: bool(re.search(r'https?://\S+', r))
            elif "list of" in subtask.validation.lower():
                # Parse expected count, e.g., "list of 3"
                count = re.search(r'(\d+)', subtask.validation).group(1)
                validators[sid] = lambda r: len(re.findall(r'-?\s*\w+', r)) >= int(count)
            # Add more rule parsers...
            else:
                # Fallback: LLM validator (pseudo-code)
                validators[sid] = self._llm_validate(subtask.validation)
        return validators

    def _llm_validate(self, criteria: str) -> Callable[[str], bool]:
        def validator(result: str) -> bool:
            # Query LLM: "Does '{result}' meet '{criteria}'? Yes/No"
            # Return true if "Yes" with >0.8 confidence
            pass  # Implement with openai
        return validator

    def validate_subtask(self, sid: int, result: str) -> bool:
        subtask = self.subtasks[sid]
        is_valid = self.validators[sid](result)
        subtask.status = "completed" if is_valid else "failed"
        return is_valid

    def is_task_complete(self) -> bool:
        all_valid = all(s.status == "completed" for s in self.subtasks.values())
        # Check order: Simulate timestamps, ensure deps completed earlier
        for sid, subtask in self.subtasks.items():
            for dep in subtask.deps:
                if self.subtasks[dep].status != "completed":
                    return False
                # Assuming completion_ts in subtask; compare timestamps
        return all_valid
```

## 4. Status Propagation and Error Handling

- **Propagation**: Parent status derives from children:
  \[
  \text{status}(t) = 
  \begin{cases} 
  \text{failed} & \text{if any child failed} \\
  \text{completed} & \text{if all children completed} \\
  \text{partially_completed} & \text{if some completed, none failed} \\
  \text{pending} & \text{otherwise}
  \end{cases}
  \]
- **Retries**: On failure, re-queue if < max_retries.
- **Logging**: Track all evaluations for audit.

**Code Snippet: Propagation**
```python
def propagate_status(subtasks: List[Subtask]) -> None:
    for subtask in subtasks:
        children = [s for s in subtasks if subtask.id in s.deps]
        if not children:
            continue  # Leaf
        child_statuses = [c.status for c in children]
        if "failed" in child_statuses:
            subtask.status = "failed"
        elif all(cs == "completed" for cs in child_statuses):
            subtask.status = "completed"
        elif any(cs == "completed" for cs in child_statuses):
            subtask.status = "partially_completed"
        # else: remains pending
```

## 5. Integration and Extensibility

- **JSON Schema**: Enforce structure with Pydantic.
- **Execution Hooks**: `executor` param in `execute_dag` for custom agents (e.g., LangChain).
- **Monitoring**: Add metrics like completion time variance for optimization.

This framework provides a stable, logically sound system for task splitting. For full code, extend the skeletons above. Questions? Extend with domain-specific validators.