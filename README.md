# Insurance Copilot

**Insurance Copilot** is a comprehensive, intelligent assistant built specifically for the Indian health insurance market. It uses powerful LLMs to analyze insurance policies via PDF, help users uncover hidden "freebies" (like health checkups and teleconsultations), calculate risk scores, find local hospitals with available beds, and provide 24/7 chat support.

---

## 🚀 Features

*   **PDF Policy Extraction**: Upload your health insurance policy document to automatically extract the insurer, policy name, terms, and hidden benefits.
*   **Benefits & Freebies Tracker**: Uncover and track free benefits provided by your insurance, such as teleconsultations or annual health checkups, complete with usage tracking.
*   **Risk Score Analysis**: Calculates a personalized risk score based on the policy terms (waiting periods, sub-limits, co-payments) using Groq-powered AI.
*   **Intelligent Chatbot**: Get instant answers about your specific policy coverages and exclusions from a domain-aware AI assistant.
*   **Hospital & Bed Finder**: Search for nearby hospitals and instantly check real-time bed availability to make informed health decisions.
*   **Eligibility Checker**: Upload hospital bills/estimates to quickly check what treatments are covered based on your specific policy clauses.

## 🛠️ Tech Stack

#### Frontend
*   **Framework**: React 19 + Vite
*   **Routing**: React Router DOM (v7)
*   **Styling**: Tailwind CSS
*   **Icons**: Lucide React

#### Backend
*   **Framework**: FastAPI (Python 3)
*   **AI Engine**: Groq API (LLaMA 3) & Tambo SDK
*   **Data Validation**: Pydantic
*   **Hosting/Deployment**: Vercel Serverless Functions

---

## 🏗️ Architecture

This repository is set up as a Monorepo:
*   `/frontend`: Contains the Vite React UI.
*   `/routers` & `/services`: Contain the FastAPI backend microservices and AI integrations.
*   `api/index.py` & `vercel.json`: Configuration for zero-config Serverless deployment to Vercel.

---

## ⚙️ Local Development Setup

### 1. Backend Setup (FastAPI)

1. **Create and activate a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use: venv\Scripts\activate
   ```
2. **Install requirements:**
   ```bash
   pip install -r requirements.txt
   ```
3. **Configure Environment Variables:**
   Create a `.env` file at the root folder based on `.env.example`:
   ```env
   GROQ_API_KEY=your_groq_api_key_here
   ```
4. **Run the FastAPI server:**
   ```bash
   uvicorn main:app --reload
   ```
   *The API will be available at `http://localhost:8000`*

### 2. Frontend Setup (Vite React)

1. **Navigate to the frontend directory:**
   ```bash
   cd frontend
   ```
2. **Install dependencies:**
   ```bash
   npm install
   ```
3. **Run the development server:**
   ```bash
   npm run dev
   ```
   *The web UI will be available at `http://localhost:5173`*

---

## 🌐 Deployment (Vercel)

The application is pre-configured to be deployed easily using Vercel. 

**Vercel Build Settings:**
*   **Framework Preset**: Vite
*   **Build Command**: `cd frontend && npm install && npm run build`
*   **Output Directory**: `frontend/dist`
*   **(Important)** Root directory should be set to `./` (the default) so Vercel can process the FastAPI serverless functions located at the root.

Make sure to add your `GROQ_API_KEY` and `TAMBO_API_KEY` to Vercel's Environment Variables during deployment!

---

## 📄 License
This project is for demonstration and hackathon purposes.
