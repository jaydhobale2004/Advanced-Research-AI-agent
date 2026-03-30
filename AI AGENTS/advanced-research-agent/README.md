# Advanced Research Agent

An autonomous research assistant built with LangGraph, Streamlit, NVIDIA-hosted models, SerpAPI search, and a lightweight self-improving optimization loop.

The project does two main jobs:

1. It runs a multi-step research workflow that plans a topic, searches the web, extracts findings, critiques gaps, and writes a cited markdown report.
2. It can evaluate and optimize its own agent instructions/configuration, then promote a better version automatically when it beats the current baseline.

## What This Project Does

When you enter a topic in the Streamlit app, the system:

1. Loads similar past findings from FAISS memory.
2. Creates a structured research plan.
3. Searches Google through SerpAPI.
4. Extracts grounded findings from the returned snippets.
5. Critiques whether the research is complete enough.
6. Repeats extra search rounds if needed.
7. Writes a final markdown report with numbered citations.

The optimizer uses a small evaluation dataset to compare the current active configuration against several candidate configs. If one candidate improves the score enough, it becomes the new active config.

## Tech Stack

- `Streamlit` for the UI
- `LangGraph` for orchestration
- `langchain-nvidia-ai-endpoints` for chat + embeddings
- `SerpAPI` for search
- `FAISS` for persistent semantic memory
- `Pydantic` for structured outputs

## Requirements

- Python 3.10+
- An NVIDIA API key
- A SerpAPI key
- Internet access for model and search API calls

## Environment Variables

Create a `.env` file in the project root:

```env
NVIDIA_API_KEY=your_nvidia_api_key_here
SERPAPI_API_KEY=your_serpapi_api_key_here
NVIDIA_CHAT_MODEL=nvidia/nemotron-3-super-120b-a12b
NVIDIA_EMBED_MODEL=nvidia/nv-embed-v1
```

What each variable does:

- `NVIDIA_API_KEY`: authenticates chat model calls and embeddings.
- `SERPAPI_API_KEY`: authenticates Google search requests through SerpAPI.
- `NVIDIA_CHAT_MODEL`: model used by planner, researcher, critic, writer, and optimizer grading.
- `NVIDIA_EMBED_MODEL`: embedding model used for FAISS memory.

## Installation

From the project root:

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## How To Use The App

### 1. Start the Streamlit UI

```powershell
streamlit run app.py
```

### 2. Open the local app

Streamlit will print a local URL, usually:

```text
http://localhost:8501
```

### 3. Enter a research topic

Example:

```text
Compare the latest open-source and closed-source LLM observability platforms for small engineering teams.
```

### 4. Pick the chat model

The sidebar lets you override the NVIDIA chat model used for the run.

### 5. Run the full pipeline

Click `Run full pipeline`.

The app will then:

- generate a plan
- search the web
- extract findings
- critique coverage
- write the final report

### 6. Review the output tabs

- `Final Report`: markdown report with numbered references
- `Plan`: structured plan created by the planner
- `Critique`: critique result, including missing points and follow-up queries
- `Sources`: title, snippet, and URL for each source
- `Logs`: execution trace for the run

### 7. Download the report

Use the `Download report` button to export the markdown output.

## How The Research Pipeline Works

### Step 1: Memory Load

The system checks the FAISS vector store for similar earlier findings and passes that memory into planning and writing.

Why it matters:

- helps the agent reuse prior research context
- makes future runs smarter over time
- avoids treating every topic as a completely blank start

### Step 2: Planning

The planner creates:

- a problem statement
- subquestions
- search queries
- success criteria

This keeps the rest of the workflow structured instead of doing a single open-ended search.

### Step 3: Search

For each search query, the app calls SerpAPI and collects organic Google results.

Each source keeps:

- title
- URL
- snippet
- originating search query

### Step 4: Finding Extraction

The researcher model turns source snippets into structured findings:

- `claim`
- `evidence`
- `importance`
- linked source

If structured extraction fails, the system falls back to source-based findings so the pipeline can still complete.

### Step 5: Critique

The critic decides whether the current evidence is sufficient.

If it is not sufficient, it returns:

- missing points
- weak spots
- extra search queries

The graph may loop back into another research round until it reaches `max_rounds`.

### Step 6: Writing

The writer generates the final markdown report using only collected findings and the reference registry.

Required sections:

1. Introduction
2. Key Insights
3. Detailed Analysis
4. Limitations / Gaps
5. Conclusion
6. References

## How To Run The Optimizer

The optimizer evaluates the current active config against a few candidate variants and optionally promotes the winner.

Run:

```powershell
python optimize_agent.py
```

What it does:

1. Loads the current active config from `agent_registry/active_config.json`.
2. Runs evaluation on the baseline config.
3. Mines failure patterns from the evaluation summary.
4. Builds candidate configs that try to fix those weaknesses.
5. Evaluates each candidate.
6. Chooses the best candidate.
7. Promotes it if it clears the minimum improvement threshold.
8. Saves the optimization report to `agent_registry/last_optimization.json`.

## Files and Folders Explained

### Root Files

#### `app.py`

Main Streamlit entrypoint.

Responsibilities:

- renders the UI
- reads the active config
- validates API keys
- launches the research pipeline
- displays plan, critique, sources, logs, and final report

Use this when you want to run the research assistant interactively.

#### `optimize_agent.py`

CLI entrypoint for the self-improving optimizer.

Responsibilities:

- builds runtime config
- validates keys
- runs the optimizer graph
- prints logs, promotion decisions, and results

Use this when you want the system to evaluate and refine its own agent instructions/config.

#### `requirements.txt`

Python dependencies needed by the project.

Notable packages:

- `streamlit` for the UI
- `langgraph` for orchestration
- `langchain-nvidia-ai-endpoints` for NVIDIA chat/embedding support
- `langchain-openai` for evaluation grading helper
- `faiss-cpu` for vector memory

#### `.env`

Local secrets and model settings.

This file should not be committed.

#### `.gitignore`

Prevents local-only or generated files from being committed, such as:

- virtual environment
- cache files
- FAISS memory
- registry artifacts
- `.env`

### Data and Persistence Folders

#### `data/eval_dataset.json`

Small evaluation dataset used by the optimizer.

Each row contains:

- `topic`: what the system should research
- `goal`: what a good answer is expected to cover

#### `faiss_research_memory/`

Generated local vector index.

Purpose:

- stores prior findings as semantic memory
- lets the app retrieve similar past research context

This folder is created and updated automatically after normal research runs.

#### `agent_registry/`

Generated config registry folder.

Important files:

- `active_config.json`: current live agent config used by the app
- `last_optimization.json`: latest optimizer result and promotion decision

### Source Package: `src/`

#### `src/__init__.py`

Empty package marker so Python treats `src` as a package.

#### `src/config.py`

Central configuration module.

Responsibilities:

- loads `.env`
- defines project constants
- defines `RuntimeConfig`
- builds runtime settings
- validates required keys

This is the first place to update if you want to change default models or shared runtime settings.

#### `src/runtime.py`

Thin execution layer for research runs.

Responsibilities:

- loads the active config if none is passed
- builds the graph
- creates the initial research state
- invokes the graph

Think of this as the clean entrypoint into the research workflow.

#### `src/graph.py`

Core orchestration logic for the research agent.

This is the most important file in the app.

Responsibilities:

- creates planner/researcher/critic/writer LLMs
- defines each graph node
- handles structured-output fallback logic
- performs search and finding extraction
- critiques completeness
- routes between extra research rounds and final writing

If you want to change workflow behavior, this is usually the main file to inspect.

#### `src/state.py`

Typed state definitions for LangGraph.

Contains:

- `ResearchState`: shared state for the research pipeline
- `OptimizerState`: shared state for the optimization pipeline

This defines what information moves between graph steps.

#### `src/schemas.py`

Pydantic models for structured outputs.

Contains:

- `ResearchPlan`
- `Finding`
- `FindingBatch`
- `CritiqueResult`
- `LLMGrade`

These schemas keep LLM outputs consistent and easier to validate.

### Services: `src/services/`

#### `src/services/__init__.py`

Empty package marker.

#### `src/services/search.py`

Search service wrapper.

Responsibilities:

- calls SerpAPI
- normalizes organic results into a simple source format

If you ever swap SerpAPI for another search provider, this is the best replacement point.

#### `src/services/vectorstore.py`

FAISS memory service.

Responsibilities:

- loads the FAISS index
- creates embeddings
- saves findings into memory
- retrieves related memory by similarity search

This file powers the project's long-term local memory behavior.

### Utilities: `src/utils/`

#### `src/utils/__init__.py`

Empty package marker.

#### `src/utils/helpers.py`

General helper functions used across the workflow.

Responsibilities:

- append timestamped logs
- deduplicate sources
- deduplicate findings
- format sources for the LLM
- build the numbered reference registry
- format findings for the writer

This file mainly supports cleanliness and report assembly.

### Evaluation Modules: `src/evals/`

#### `src/evals/__init__.py`

Empty package marker.

#### `src/evals/dataset.py`

Loads the evaluation dataset from `data/eval_dataset.json`.

#### `src/evals/graders.py`

Grades a research run using rule-based metrics plus an LLM grader.

Responsibilities:

- counts citations
- checks required section coverage
- measures source diversity
- measures source count
- asks an LLM to score completeness, clarity, citation quality, and practical value

#### `src/evals/metrics.py`

Aggregates evaluation rows into overall scores.

Responsibilities:

- compute per-run overall score
- compute dataset-level averages

### Evolution / Self-Improvement: `src/evolution/`

#### `src/evolution/__init__.py`

Empty package marker.

#### `src/evolution/registry.py`

Manages saved agent configurations.

Responsibilities:

- defines the default config
- loads the active config
- saves the active config
- saves the latest optimization report

This file is the persistence layer for the self-improving agent config.

#### `src/evolution/optimizer_graph.py`

LangGraph workflow for config optimization.

Responsibilities:

- evaluate baseline
- mine failures
- build candidates
- evaluate candidates
- choose and promote the winner

This is the main orchestration file for self-improvement.

#### `src/evolution/candidate_builder.py`

Creates candidate configs based on observed weaknesses.

Examples of changes it can make:

- stricter citation instructions
- stricter critique behavior
- more search results per query
- extra research rounds
- targeted prompt improvements based on failure types

#### `src/evolution/eval_runner.py`

Runs the active or candidate config against the evaluation dataset.

Responsibilities:

- executes research runs in evaluation mode
- grades each run
- builds a structured evaluation summary

#### `src/evolution/failure_miner.py`

Converts aggregate evaluation metrics into concrete failure labels.

Current failure labels include:

- `weak_citations`
- `missing_sections`
- `low_source_diversity`
- `low_quality_reasoning`

#### `src/evolution/promoter.py`

Decides whether a candidate should replace the current baseline.

Responsibilities:

- compare candidate scores against baseline
- enforce minimum gain threshold
- save the promoted config if allowed

## Execution Flow Summary

Normal app run:

1. `app.py`
2. `src.config.build_runtime_config`
3. `src.evolution.registry.load_active_config`
4. `src.runtime.run_research`
5. `src.graph.build_graph`
6. graph nodes execute: memory -> plan -> research -> critique -> write

Optimizer run:

1. `optimize_agent.py`
2. `src.evolution.optimizer_graph.build_optimizer_graph`
3. baseline evaluation
4. failure mining
5. candidate generation
6. candidate evaluation
7. promotion decision
8. registry update

## Output Artifacts

After using the project, you may see these generated artifacts:

- `faiss_research_memory/` after normal research runs
- `agent_registry/active_config.json` after first run or promotion
- `agent_registry/last_optimization.json` after optimizer runs

## Important Notes

- Search quality depends heavily on SerpAPI results and the model's ability to reason from snippets.
- The current search pipeline uses search-result snippets, not full page crawling.
- FAISS memory is skipped during evaluation mode to keep comparisons cleaner.
- The optimizer uses the runtime chat model name for grading as well.

## Troubleshooting

### Missing API keys

If the app says keys are missing, make sure `.env` contains:

- `NVIDIA_API_KEY`
- `SERPAPI_API_KEY`

### Streamlit command not found

Run it with Python:

```powershell
python -m streamlit run app.py
```

### Optimizer fails during grading

Make sure dependencies are installed from the latest `requirements.txt`, including `langchain-openai`.

### No FAISS memory yet

That is normal on the first run. The index is created only after findings are saved.

### Search returns weak results

Try:

- a more specific topic
- a different model in the sidebar
- increasing search depth by tuning the active config

## Suggested Next Improvements

- add full webpage retrieval instead of snippet-only evidence
- store richer metadata in memory
- add per-source trust scoring
- export optimization summaries in a nicer report format
- add tests for graph nodes and helper functions
