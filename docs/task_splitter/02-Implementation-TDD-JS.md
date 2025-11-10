# 02-Implementation-TDD-JS.md

# Task-Splitting: TDD Implementation in JavaScript

**Version**: 1.0  
**Date**: November 10, 2025  
**Author**: Grok (xAI)  

## Introduction

Building on the logical architecture outlined in `01-Architecture-Logic-Overview.md` and the Python reference in `00-architecture.md`, this document details how to implement the same task-splitting logic—hierarchical DAG decomposition, bounded recursion, topological execution, and predicate-based validation—in **JavaScript (Node.js)** using **Test-Driven Development (TDD)**. TDD ensures robustness by writing failing tests first, then minimal code to pass them, iterating through red-green-refactor cycles. This approach aligns with the project's emphasis on testability, covering invariants like atomicity, coverage, and acyclicity.

The JS port maintains Clean Architecture:
- **Domain**: Pure JS classes/interfaces (Task, Subtask, ValidationPredicate).
- **Application**: Services (TaskSplitterService, etc.) orchestrated via composition.
- **Infrastructure**: Adapters (e.g., OpenAI SDK), utils (topo sort via `graphology`).
- **Tests**: Jest for unit/integration, with mocks for LLM/externals.

Key adaptations for JS:
- **Recursion**: Handled with async functions; depth limit via counters.
- **DAG**: Use `graphology` for cycle detection/topo sort.
- **Validation**: Predicate functions (e.g., regex for UI, numerical for KPIs).
- **LLM**: `@openai/openai` SDK; prompt engineering mirrors Python.
- **TDD Flow**: Start with tests for core invariants, then layers; examples use the E2E testing and consulting scenarios from `01-Architecture-Logic-Overview.md`.

**Project Setup**: Use `npm init -y`; deps: `jest@^29`, `@openai/openai@^4`, `graphology@^0.25`, `zod@^3` (for schemas, JS analog to Pydantic). Run: `npm test`.

File structure mirrors Python's (adjusted for JS):
```
task-splitter-js/
├── README.md
├── package.json
├── 00-architecture.md  # Python ref
├── 01-architecture-logic-overview.md
├── src/
│   ├── index.js  # Exports
│   ├── models.js  # Domain: Task, Subtask, ValidationPredicate
│   ├── taskSplitterService.js  # Application facade
│   ├── decompositionEngine.js  # LLM + recursion
│   ├── executionOrchestrator.js  # Topo execution
│   ├── validationEngine.js  # Predicates
│   └── infra/
│       ├── llmProvider.js  # Factory/adapters
│       └── utils.js  # Topo sort, cycle detect
└── __tests__/
    └── taskSplitting.test.js  # TDD suite
```

## TDD Cycle: Red-Green-Refactor Overview

For each component, follow:
1. **Red**: Write failing test (e.g., assert decomposition has subtasks with deps).
2. **Green**: Implement minimal code to pass (e.g., stub LLM response).
3. **Refactor**: Optimize (e.g., extract recursion guard); add coverage.

We'll walk through TDD for key features using the examples from `01-Architecture-Logic-Overview.md`. Full tests in `taskSplitting.test.js`.

## 1. Domain Models: TDD for Invariants

Start with `models.js`: Define classes ensuring DAG invariants.

**TDD Example: Subtask Atomicity & Recursion Limit**
- **Red Test** (fails: no depth check):
  ```js
  // __tests__/taskSplitting.test.js
  const { Subtask } = require('../src/models');

  test('subtask enforces max depth on recursion', () => {
    const parent = new Subtask({ id: 1, title: 'Add Products', subtasks: [] });
    const child1 = new Subtask({ id: 2, title: 'Search', subtasks: [new Subtask({ id: 3, title: 'Select' })] });
    parent.subtasks.push(child1);
    expect(() => parent.flattenSubtasks(4)).toThrow('Max depth exceeded');  // Fails initially
  });
  ```
- **Green Implementation**:
  ```js
  // src/models.js
  class Subtask {
    constructor(data) {
      this.id = data.id;
      this.title = data.title;
      this.dependencies = data.dependencies || [];
      this.validation = data.validation;
      this.subtasks = data.subtasks || [];  // Recursive
      this.status = 'pending';
      this.maxDepth = 3;
    }
    flattenSubtasks(currentDepth = 0) {
      if (currentDepth > this.maxDepth) throw new Error('Max depth exceeded');
      let flat = [this];
      this.subtasks.forEach(child => flat.push(...child.flattenSubtasks(currentDepth + 1)));
      return flat;
    }
    // ... other methods
  }
  module.exports = { Subtask, Task /* etc. */ };
  ```
- **Refactor**: Add Zod schema for validation:
  ```js
  const { z } = require('zod');
  const SubtaskSchema = z.object({ id: z.number(), /* ... */ });
  ```

**For E2E Testing Scenario**: Test recursive flattening for "Add 3 Random Products" (t5 → t5.1-5.3), asserting depth=2 < 3.

## 2. Decomposition Engine: TDD for LLM-Driven Split & Recursion

`decompositionEngine.js`: Queries LLM, parses JSON, builds DAG with recursion.

**TDD Example: Recursive Decomposition with Cycle Detection**
- **Red Test** (using E2E prompt; fails: no cycle detect):
  ```js
  const { DecompositionEngine } = require('../src/decompositionEngine');
  const mockOpenAI = require('../infra/llmProvider');  // Mocked

  test('decomposes E2E prompt recursively, detects cycles', async () => {
    const engine = new DecompositionEngine(mockOpenAI);
    const prompt = "Run a full E2E test on demoshop.local: ...";  // Full from 01-doc
    const task = await engine.decompose(prompt);
    expect(task.subtasks.length).toBeGreaterThan(10);  // ~12 expected
    expect(task.subtasks[4].subtasks.length).toBe(3);  // t5 recursion: search/select/add
    // Simulate cycle: Add dep loop
    task.subtasks[0].dependencies = [task.subtasks[11].id];  // t1 deps t12 (invalid)
    expect(() => engine.validateDAG(task)).toThrow('Cycle detected');
  });
  ```
- **Green Implementation** (stub LLM, use graphology):
  ```js
  // src/decompositionEngine.js
  const { LLMProviderFactory } = require('./infra/llmProvider');
  const Graph = require('graphology');
  const { topologicalSort } = require('./infra/utils');

  class DecompositionEngine {
    constructor(llmFactory) { this.llmFactory = llmFactory; }
    async decompose(prompt, provider = 'openai') {
      const adapter = this.llmFactory.create(provider);
      const systemPrompt = `Decompose: ${prompt} into JSON DAG with recursion <=3...`;  // Enforce invariants
      const jsonStr = await adapter.query(systemPrompt, prompt);
      const data = JSON.parse(jsonStr);  // Assume valid
      const task = new Task(data);  // From models
      await this.recursiveDecompose(task, 0);  // Async recursion
      this.validateDAG(task);
      return task;
    }
    async recursiveDecompose(task, depth = 0) {
      if (depth >= 3) return;  // Bound
      for (let sub of task.subtasks) {
        if (sub.title.includes('recursive')) {  // Trigger
          const subData = await this.decompose(sub.description);  // Re-query
          sub.subtasks = subData.subtasks;
          await this.recursiveDecompose(sub, depth + 1);
        }
      }
    }
    validateDAG(task) {
      const g = new Graph();
      task.flattenSubtasks().forEach(s => {
        g.addNode(s.id);
        s.dependencies.forEach(d => g.addEdge(d, s.id));
      });
      if (!topologicalSort(g)) throw new Error('Cycle detected');
    }
  }
  module.exports = { DecompositionEngine };
  ```
- **Refactor**: Add coverage check (e.g., semantic similarity via simple keyword overlap).

**For Consulting Scenario**: Test decomposes "SWOT per competitor" (t3 → t3.1-3.4 per 5 competitors), flattening to 20+ nodes, no cycles.

## 3. Execution Orchestrator & Validation: TDD for Flow & Predicates

`executionOrchestrator.js` & `validationEngine.js`: Topo execution, predicate eval.

**TDD Example: Topological Execution with Validation (Parallelism)**
- **Red Test** (Consulting prompt; fails: no parallel handling):
  ```js
  const { ExecutionOrchestrator, ValidationEngine } = require('../src/executionOrchestrator');
  const mockExecutor = jest.fn();

  test('executes consulting DAG topologically, validates parallel branches', async () => {
    const task = await decomposeConsultingPrompt();  // Helper mock
    const orch = new ExecutionOrchestrator(new ValidationEngine());
    const results = await orch.executeDAG(task, mockExecutor);
    expect(mockExecutor).toHaveBeenCalledTimes(task.flattenSubtasks().length);
    // Parallel: t5 (forecast) & t7 (risks) after t4
    expect(results[5].status).toBe('completed');  // t5
    expect(results[7].status).toBe('completed');  // t7 independent
    expect(orch.isComplete(task)).toBe(true);  // Global: AND + order
  });
  ```
- **Green Implementation**:
  ```js
  // src/executionOrchestrator.js
  const { topologicalSort } = require('./infra/utils');

  class ExecutionOrchestrator {
    constructor(validator) { this.validator = validator; }
    async executeDAG(task, executor) {
      const order = topologicalSort(task.flattenSubtasks());
      const results = {};
      for (let id of order) {
        const sub = /* find by id */;
        if (sub.dependencies.every(d => results[d]?.status === 'completed')) {
          sub.status = 'in_progress';
          const result = await executor(sub);  // e.g., Selenium click
          sub.status = this.validator.validate(sub.id, result) ? 'completed' : 'failed';
          results[sub.id] = { result, status: sub.status };
        } else {
          sub.status = 'blocked';
        }
      }
      task.propagateStatus();  // Upward
      return results;
    }
    isComplete(task) { return this.validator.isTaskComplete(task); }
  }
  module.exports = { ExecutionOrchestrator };

  // src/validationEngine.js
  class ValidationEngine {
    buildValidators(subtasks) {
      return subtasks.map(s => {
        if (s.validation.includes('HTTP 200')) return (res) => res.status === 200;
        if (s.validation.includes('NPV >0')) return (res) => res.npv > 0;  // Domain-specific
        // Fallback: LLM judge
        return async (res) => (await llmJudge(s.validation, res)) > 0.8;
      });
    }
    validate(id, result) { /* ... */ }
    isTaskComplete(task) {
      const flat = task.flattenSubtasks();
      return flat.every(s => s.status === 'completed') && /* order check via timestamps */;
    }
  }
  ```
- **Refactor**: Use Promises.all for parallel independents (e.g., t5 || t7).

**For E2E Scenario**: Test executes t2 || t3 (parallel logins), validates UI predicates (e.g., `expect(page.locator('#cart-count')).toHaveText('3')` via Playwright mock).

## 4. Integration: Facade & Hooks

`taskSplitterService.js`: Ties it together.
```js
// src/taskSplitterService.js
const { DecompositionEngine } = require('./decompositionEngine');
const { ExecutionOrchestrator } = require('./executionOrchestrator');
const { LLMProviderFactory } = require('./infra/llmProvider');

class TaskSplitterService {
  constructor() {
    const factory = new LLMProviderFactory();
    this.decomp = new DecompositionEngine(factory);
    this.orch = new ExecutionOrchestrator(new ValidationEngine());
  }
  async splitAndExecute(prompt, executor) {
    const task = await this.decomp.decompose(prompt);
    return this.orch.executeDAG(task, executor);
  }
}
module.exports = { TaskSplitterService };
```

**TDD Integration Test**:
```js
test('full cycle: split E2E prompt → execute → complete', async () => {
  const service = new TaskSplitterService();
  const results = await service.splitAndExecute(e2ePrompt, mockExecutor);
  expect(results).toHaveProperty('completed', true);
});
```

## Conclusion

This TDD-driven JS implementation ports the Python logic faithfully, leveraging Jest for iterative development and ensuring safeguards like depth limits prevent infinite recursion in complex DAGs (e.g., E2E branching or consulting per-competitor loops). Run `jest --watch` for TDD workflow. For UI execution, integrate Playwright; for analytics, add math libs like `mathjs`.

**References**: Jest docs (jestjs.io); Graphology (graphology.github.io); OpenAI JS SDK. See `01-Architecture-Logic-Overview.md` for scenario details; extend with domain validators (e.g., CSS for testing, NPV formulas for consulting).