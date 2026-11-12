# EduSimplify – AI-Powered Course Content Simplification Agent

An AICTE × IBM University Engagement Student Project (2026) powered by **IBM Granite** on **IBM watsonx.ai** to simplify complex academic concepts into level-tailored, structured study modules.

---

## 1. Project Title

**EduSimplify – AI-Powered Course Content Simplification Agent**  
*AICTE × IBM Student Engagement Program | Problem Statement PS19*

---

## 2. Problem Statement

### PS19 – Course Content Simplification Agent
Academic course materials, textbooks, research papers, and faculty lecture notes often vary widely in complexity and syntactic density. Students—particularly first-generation learners and those from diverse academic backgrounds—frequently struggle to grasp foundational concepts due to jargon-heavy language, abstract formulations, and a lack of differentiated explanations.

Traditional educational delivery is one-size-fits-all, failing to provide learners with adaptive explanations tailored to their existing knowledge level. There is a pressing need for an intelligent system that can analyze complex academic content and autonomously reframe explanations across multiple proficiency levels (Beginner to Expert) while maintaining rigorous factual integrity.

---

## 3. Project Overview

**EduSimplify** is a lightweight, full-stack educational AI agent built using Python, Flask, and IBM watsonx.ai. It bridges the academic comprehension gap by reframing student-submitted topics or textbook excerpts into structured, bite-sized, and pedagogically rich learning modules.

The agent leverages IBM's enterprise foundation model, **`ibm/granite-4-h-small`**, to deliver multi-tier adaptive explanations. Rather than generating unstructured text, EduSimplify enforces a standardized 7-section learning framework complete with real-world analogies, concise summaries, key terms, and self-assessment quiz questions.

---

## 4. Objectives

- **Democratize Education**: Make dense academic concepts accessible to learners from diverse educational and linguistic backgrounds.
- **Adaptive Depth**: Deliver three distinct proficiency tiers (**Beginner**, **Intermediate**, and **Expert**) to match the learner's current mastery.
- **Structured Pedagogical Framework**: Enforce an evidence-based 7-section output architecture that reinforces intuition, conceptual understanding, practical examples, and active recall.
- **Active Self-Assessment**: Automatically produce multiple-choice quiz questions to evaluate comprehension immediately after studying.
- **Generation Consistency**: Deterministic greedy decoding and structured prompt constraints improve consistency and reduce conversational drift.
- **Verified Production Quality**: Maintain a clean, production-ready codebase supported by automated tests.

---

## 5. Key Features

- **3 Differentiated Learning Levels**:
  - **Beginner**: Simple language, intuitive analogies, everyday metaphors, and clear introductory explanations.
  - **Intermediate**: Balanced academic tone, standard industry/scientific terminology, and applied examples.
  - **Expert**: Rigorous technical depth, formal definitions, theoretical nuances, and advanced academic context.
- **7 Structured Output Sections**:
  1. **Simplified Explanation**: Core topic broken down according to selected proficiency level.
  2. **Key Concepts**: Bulleted breakdown of essential foundational pillars.
  3. **Real-world Analogy**: Intuitive relatable scenario that connects abstract theory to everyday life.
  4. **Example**: Concrete scenario, numerical walk-through, or practical application.
  5. **Important Terms**: Key terminologies clearly defined.
  6. **Quick Revision**: High-yield bullet points for rapid review before exams.
  7. **Quiz Questions**: 3 multiple-choice questions with answer keys.
- **Robust Guardrails**:
  - Input length boundaries (1–2000 characters), level validation, and multi-strategy regex fallback parsing.

---

## 6. System Architecture

The EduSimplify architecture follows a decoupled client-server model integrating securely with IBM Cloud services:

![EduSimplify Architecture](docs/architecture_diagram.svg)

![EduSimplify Architecture Detailed](docs/architecture%20diagram.png)

### Data Flow Pipeline:
1. **User Interaction**: The student inputs an academic topic or textbook excerpt in the browser and selects a proficiency level (**Beginner**, **Intermediate**, or **Expert**).
2. **Request Validation**: The Flask application receives the POST payload at `/simplify`, validating payload structure, string lengths, and level parameters.
3. **Prompt Synthesis**: `prompts.py` builds an instruction-bounded prompt specifying level-specific persona instructions and strict 7-section contracts.
4. **IAM Token Exchange**: `watsonx_client.py` requests a short-lived OAuth 2.0 Bearer token from `https://iam.cloud.ibm.com/identity/token` using the configured IBM Cloud API key.
5. **Foundation Model Inference**: The prompt is submitted via HTTPS POST to the IBM watsonx.ai Text Generation endpoint (`ibm/granite-4-h-small`).
6. **Robust Section Parsing**: `app.py` parses the generated text using multi-pattern regular expressions into structured JSON.
7. **Client-Side Rendering**: `script.js` dynamically populates the 7 HTML cards.

---

## 7. Technology Stack

| Layer | Component | Technology | Description |
|---|---|---|---|
| **Backend** | Web Framework | Python 3.10+ / Flask 3.1 | Lightweight WSGI application handling routing, validation, and parsing |
| **Frontend** | Interface | HTML5 / CSS3 / Vanilla JS | Responsive, accessible UI with level selectors |
| **AI Foundation** | LLM | IBM Granite (`ibm/granite-4-h-small`) | Enterprise-grade instruction-tuned language model |
| **AI Platform** | Cloud Runtime | IBM watsonx.ai | Watson Machine Learning REST inference infrastructure |
| **Security & Auth** | Identity | IBM Cloud IAM OAuth 2.0 | Dynamic short-lived token generation without credential persistence |
| **Configuration** | Environment | python-dotenv | Local environment variable isolation |
| **Testing** | QA | pytest | Automated unit and integration test suite |

---

## 8. IBM watsonx.ai and IBM Granite Usage

EduSimplify connects directly to **IBM watsonx.ai** via official REST endpoints without third-party abstraction layers:

- **Model Identifier**: `ibm/granite-4-h-small`
- **Inference Endpoint**: `POST {WATSONX_URL}/ml/v1/text/generation?version=2023-05-29`
- **Auth Endpoint**: `POST https://iam.cloud.ibm.com/identity/token`
- **Inference Hyperparameters**:
  - `decoding_method`: `"greedy"` — Deterministic decoding for consistent structured output.
  - `max_new_tokens`: `2000` — Ensures sufficient output capacity for all 7 sections.
  - `repetition_penalty`: `1.1` — Eliminates repetitive loops in bullet points and definitions.
- **Security Posture**:
  - API keys are read strictly from OS environment variables (`_get_required_env`).
  - No credentials are hardcoded, logged, or returned to client browsers.

---

## 9. Project Structure

```
EduSimplify-Project/
│
├── app.py
├── watsonx_client.py
├── prompts.py
├── requirements.txt
├── README.md
├── AGENTS.md
├── .env.example
├── .gitignore
├── pytest.ini
│
├── templates/
│   └── index.html
│
├── static/
│   ├── style.css
│   └── script.js
│
├── tests/
│   ├── test_app.py
│   ├── test_watsonx.py
│   └── test_prompts.py
│
└── docs/
    ├── architecture diagram.png
    └── architecture_diagram.svg
```

---

## 10. Installation Instructions

### Prerequisites
- Python 3.10+
- IBM Cloud Account with watsonx.ai access

### 1. Clone the Repository
```bash
git clone <your-repo-url>
cd EduSimplify-Project
```

### 2. Create and Activate Virtual Environment
**Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**macOS / Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

---

## 11. Environment Variable Setup

Copy the template `.env.example` file to create your local `.env`:

**Windows:**
```powershell
copy .env.example .env
```

**macOS / Linux:**
```bash
cp .env.example .env
```

Open `.env` and fill in your IBM Cloud credentials:

```ini
WATSONX_API_KEY=your_ibm_cloud_api_key_here
WATSONX_PROJECT_ID=your_watsonx_project_id_here
WATSONX_URL=https://us-south.ml.cloud.ibm.com
WATSONX_MODEL_ID=ibm/granite-4-h-small

FLASK_DEBUG=false
FLASK_PORT=5000
```

> **Security Notice**: Never commit `.env` to GitHub. The `.env` file is explicitly ignored in `.gitignore`.

---

## 12. How to Run the Application

```bash
python app.py
```

Navigate to: `http://127.0.0.1:5000`

---

## 13. How to Run Tests

```bash
pytest tests/ -v
```

*Note: All external HTTP requests to IBM IAM and watsonx.ai are mocked in tests — no active internet connection or IBM API key is required.*

---

## 14. Example Usage

1. Open `http://localhost:5000`
2. Select a learning level: **Beginner**, **Intermediate**, or **Expert**
3. Enter a topic (e.g. `Binary Search Trees`, `Photosynthesis`, `Quantum Superposition`)
4. Click **✨ Simplify** — all 7 sections are generated in real-time

---

## 15. Future Scope

1. **Multilingual Support**: Translation into regional languages using IBM Granite capabilities.
2. **Audio Read-Aloud / TTS**: Integration with speech synthesis for auditory learners.
3. **Document Ingestion**: Upload lecture PDFs and slides for automated simplification.
4. **LMS Integration**: Export to Moodle, Canvas, and Google Classroom.

---

## License & Acknowledgments

Developed by **Madan Singh** as part of the **AICTE × IBM University Engagement Program (2026)**.
