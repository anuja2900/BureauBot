# 🏛️ **Bureaubot**

**Bureaubot** is an AI assistant that simplifies immigration paperwork. It identifies the right form, asks only the questions that matter, and fills official PDFs accurately—saving users hours of waiting and the high costs of legal help.

---

## 📚 **Table of Contents**
1. [Project Motivation](#project-motivation)  
2. [Overview of Bureaubot](#overview-of-bureaubot)  
3. [How It Works](#how-it-works)  
4. [Bureaubot’s Market Fit and Growth Potential](#bureaubots-market-fit-and-growth-potential)  
5. [Future Works](#future-works)  
6. [Tools Utilized](#tools-utilized)  
7. [About the Team](#about-the-team)  

---

## 💡 **Project Motivation**

### **Background**
As a team of four immigrants navigating the complex U.S. immigration system, we personally experienced the challenges of filling out multiple forms, understanding eligibility requirements, and finding reliable information. There was no single, trustworthy platform where all our questions could be answered efficiently. The process was time-consuming, stressful, and often confusing, which inspired us to develop **Bureaubot**.

### **Challenges Faced by International Students and Immigrants**
- **Information Overload:** Immigrants often have to search across multiple government websites and documents to find the right forms and instructions.  
- **Complex Forms:** Many forms are lengthy, with technical language and conditional sections, making them difficult to fill correctly without guidance.  
- **Eligibility Confusion:** Determining which forms apply to a specific case is not always straightforward.  
- **Time and Stress:** The process is slow, stressful, and prone to errors, leading to delays or incorrect submissions.  
- **High Cost of Professional Help:** Legal consultations are expensive, often inaccessible for students or first-time applicants.  

Bureaubot aims to **streamline and simplify the immigration process** through an interactive, guardrailed workflow that connects a user’s situation to the correct form, asks only what’s necessary, and fills the official PDF reliably—while generating a checklist that flags inconsistencies and missing attachments.

### **Why Bureaubot?**
Existing AI tools either provide limited assistance or handle form-filling for isolated cases. There is **no comprehensive, consumer-facing solution** that integrates both **conversational guidance** and **automated form completion** across a broad range of U.S. immigration forms.  

This gap motivated us to build **Bureaubot**—a unified platform that combines accuracy, structure, and accessibility for anyone navigating immigration paperwork.

---

## 🧭 **Overview of Bureaubot**

<img width="1051" height="379" alt="Flow chart" src="https://github.com/user-attachments/assets/79d1adf6-8c26-4ac6-818f-6c72664a7953" />

### **Demo**

[Insert demo link here]

### **Key Features**
- **Immigration Form Guidance:** Directs users to the correct forms based on their individual circumstances.  
- **Interactive Q&A:** Offers accurate, context-specific answers about eligibility, documentation, and requirements.  
- **Automated Form Filling:** Uses **PyMuPDF** to populate forms automatically and correctly.  
- **Domain-Specific LLM:** Trained exclusively on immigration data to minimize irrelevant or incorrect responses.  
- **Reliable and Efficient:** Combines pre-trained LLMs with structured metadata for accurate, fast results.  

> ⚠️ *Not legal advice. Bureaubot is a research project and does not replace an attorney.*

---

## 🔬 **Methodology**

**Step 1: Large Language Model Integration**  
Leveraged **Gemini 2.0** to interpret user queries and generate precise, context-aware responses, fine-tuned on immigration forms and metadata for reliability.

**Step 2: Form Metadata Extraction**  
Parsed official immigration forms to extract structures, requirements, and conditional logic, building an accurate mapping system for each form.

**Step 3: Multi-Step Prompting**  
Applied iterative prompting to transform free-form input into structured, field-aligned data validated against schemas.

**Step 4: Automated Form Population**  
Used **PyMuPDF** to fill PDFs programmatically with structured data, ensuring submission-ready documents.

**Step 5: Validation and Accuracy Checks**  
Integrated consistency checks, dependency validation, and error handling to ensure compliance with official standards.

---

## 🧱 **Data Architecture**

Bureaubot’s data architecture is grounded entirely in **official government sources**—including **USCIS**, **CBP**, **EOIR**, and **ICE**.  
All forms and instructions are regularly collected and converted into structured **YAML** and **JSON** schemas defining field types, validation rules, dependencies, and filing conditions.

These schemas are stored in a centralized **form dictionary**, the system’s single source of truth.  
Unlike typical AI tools, Bureaubot does **not rely on LLM memory or live web searches**. Instead, it maintains its own verified database reflecting the most recent form versions and policies.

The system periodically checks official agency websites for updates and automatically integrates changes into its metadata pipeline—ensuring **accuracy, compliance, and adaptability** in a shifting political and legal climate.

---

## ⚙️ **How It Works**

<img width="3282" height="813" alt="Untitled diagram-2025-10-27-015507" src="https://github.com/user-attachments/assets/b63bba96-0d9a-40e5-9927-00646e90263c" />


### **Bureaubot’s Brain: Our LLM Agents**

**Form Selection Agent**  
Analyzes the user’s description and matches it with the most relevant immigration forms (e.g., EOIR-29, CBP 3124).  
Considers context like filing type, decision source, and timing.

**Interview Agent**  
Turns each form’s schema into a structured, one-question-at-a-time interview.  
Automatically handles dependent questions and formatting rules.

**Validation Agent**  
Checks for missing data, invalid dates, or mismatched fields using YAML/JSON-based rule sets.

**PDF Filling Agent**  
Writes responses into the correct form fields—text, checkbox, radio, or multibox—with stable formatting.  
Outputs: `filled.pdf`, `answers.json`, `review.md`.

### **Bureaubot’s Interface: Your Filing Playground**
- **Clean, guided screens:** One question at a time.  
- **Live preview:** Optional “field heatmap” view.  
- **Fix-list panel:** Highlights issues for quick corrections.  
- **Session resume:** Auto-saves progress in `answers.json`.  
- **Easy export:** Download all completed artifacts in one click.

---

## 💸 **Bureaubot’s Market Fit and Growth Potential**

Bureaubot is strategically positioned in the **legal automation and immigrant-services** market, addressing growing barriers to affordable and timely legal support.  
By combining **AI-guided form selection**, **contextual interviews**, and **precise PDF filling**, Bureaubot turns a complex, stressful process into a clear, reliable experience.

**With hours-long clinic wait times and high legal costs**, Bureaubot offers a scalable alternative that saves time without compromising accuracy or compliance.

### **Target Audience**
- **Self-Filers:** Accessible, structured guidance and submission-ready PDFs.  
- **Community Clinics & Nonprofits:** Standardized intakes and reduced workloads.  
- **Paralegals & Attorneys:** Faster packet preparation and error reduction.

---

## 🚀 **Future Works**

Future development focuses on expanding **reliability, reach, and accessibility**:

- **Product:** Real-time PDF previews, multi-form packet support, resumable sessions.  
- **Intelligence:** Larger rule library, attachment inference, multilingual support.  
- **Platform:** Secure API for clinics and firms, e-signature integration, and cloud export.  
- **Computer Vision:** Extract form data directly from scanned documents.

Bureaubot’s long-term vision is to become the **trusted infrastructure layer for legal document automation**—making bureaucratic processes faster, fairer, and more human.

---

## 🧰 **Tools Utilized**

| **Category** | **Tool(s)** |
|---------------|-------------|
| **Design** | Figma (flows, mockups) |
| **Project Management** | GitHub Projects / Trello |
| **Languages** | Python, JavaScript |
| **Frameworks** | FastAPI / Flask, React |
| **LLM** | Gemini 2.5 Pro |
| **PDF** | PyPDF / pdfrw / pikepdf, Poppler / pdftk |
| **Cloud** | Google Cloud Platform |

---

## 👥 **About the Team**

**Minh Phan**  
**Anuja Tipare**  
**Connor Yeh**  
**Kanav Goyal**
