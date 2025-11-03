<h1 align="center">Bureaubot: Bureaucracy, Simplified

Your AI Assistant for Immigration Guidance & Form Filling </h1>

<img width="7200" height="1136" alt="bureaubot" src="https://github.com/user-attachments/assets/a5f8e4c0-461c-4337-bb66-40c41306175a" />

**Bureaubot** is an AI assistant that simplifies immigration paperwork. It identifies the right form, asks only the questions that matter, and fills official PDFs accurately—saving users hours of waiting and the high costs of legal help.

---

## **Table of Contents**
1. [Project Motivation](#project-motivation)  
2. [Overview of Bureaubot](#overview-of-bureaubot)  
3. [How It Works](#how-it-works)  
4. [Bureaubot’s Market Fit and Growth Potential](#bureaubots-market-fit-and-growth-potential)  
5. [Future Works](#future-works)  
6. [Tools Utilized](#tools-utilized)  
7. [Meet the Team](#meet-the-team)  

---

## **Project Motivation**

### **Background**
As a team of four immigrants navigating the complex U.S. immigration system, we personally experienced the challenges of filling out multiple forms, understanding eligibility requirements, and finding reliable information. There was no single, trustworthy platform where all our questions could be answered efficiently. The process was time-consuming, stressful, and often confusing, which inspired us to develop **Bureaubot**.

### **Challenges Faced by International Students and Immigrants**
- **Information Overload:** Immigrants often have to search across multiple government websites and documents to find the right forms and instructions.
- **Complex Forms:** Many forms are lengthy, with technical language and conditional sections, making them difficult to fill correctly without guidance.
- **Eligibility Confusion:** Determining which forms apply to a specific case is not always straightforward.
- **Time and Stress:** The process is slow, stressful, and prone to errors, leading to delays or incorrect submissions.
- **High Cost of Professional Help:** When unsure, many individuals turn to immigration attorneys or consultants, which can be very expensive, especially for students or first-time applicants. 

Bureaubot aims to **streamline and simplify the immigration process** through an interactive, guardrailed workflow that connects a user’s situation to the correct form, asks only what’s necessary, and fills the official PDF reliably—while generating a checklist that flags inconsistencies and missing attachments.

### **Why Bureaubot?**

Although a few emerging AI tools provide limited assistance with immigration-related questions or automate form entry for specific use cases, there is currently **no comprehensive, consumer-facing solution** that integrates both — **conversational guidance** and **automated form-filling** — across a wide range of U.S. immigration forms.  

Most existing tools either focus on a single form type (e.g., naturalization) or are built primarily for **legal firms** rather than individuals.  

This clear gap in accessibility and usability motivated us to build **Bureaubot** — a unified platform that not only answers immigration queries with accuracy and reliability but also assists users in completing and generating properly filled immigration forms tailored to their specific situations.


---

## **Overview of Bureaubot**

### **Demo**

[Insert demo link here]

### **Key Features**
- **Immigration Form Guidance:** Directs users to the correct forms based on their individual circumstances.  
- **Interactive Q&A:** Offers accurate, context-specific answers about eligibility, documentation, and requirements.  
- **Automated Form Filling:** Uses **PyMuPDF** to populate forms automatically and correctly.  
- **Domain-Specific LLM:** Trained exclusively on immigration data to minimize irrelevant or incorrect responses.  

> ⚠️ *Not legal advice. Bureaubot is a research project and does not replace an attorney.*

---

## **Methodology**

### **Step 1: Large Language Model Integration**
Leveraged **Gemini 2.0** to interpret user queries and generate precise, context-aware responses.  
The model was fine-tuned using immigration forms and metadata from official government sources to ensure domain-specific understanding and reliability.  

### **Step 2: Form Metadata Extraction**
Downloaded official immigration forms and extracted their **field structures, requirements, and conditional rules**.  
This metadata trains the system to recognize each field’s context and accurately map user-provided information.  

### **Step 3: Multi-Step Prompting**
Applied **iterative prompting techniques** to transform free-form user input into structured data aligned with form schemas.  
Each exchange refines and validates the user’s responses, ensuring every detail corresponds to the correct field.  

### **Step 4: Automated Form Population**
Integrated **PyMuPDF** to programmatically populate PDF forms using the structured data output from the LLM.  
This step produces **submission-ready documents** while maintaining official formatting and field integrity.  

### **Step 5: Validation and Accuracy Checks**
Implemented **consistency checks, dependency validation, and error handling** to detect missing or mismatched entries.  
This ensures that all completed forms comply with official standards, reducing user errors and rejections.

---

## **Data Architecture**

Bureaubot’s data architecture is grounded entirely in **official government sources**, including the **U.S. Citizenship and Immigration Services (USCIS)**, **Customs and Border Protection (CBP)**, **Executive Office for Immigration Review (EOIR)**, and **Immigration and Customs Enforcement (ICE)**.  

All forms, filing instructions, and policy materials are periodically downloaded, parsed, and converted into structured **YAML** and **JSON** schemas that define field types, validation rules, dependencies, and filing conditions.  

These schemas are stored in a centralized **form dictionary**, which serves as the system’s single source of truth—governing how forms are interpreted, validated, and populated.  

Rather than depending on live web searches or LLM-generated knowledge, Bureaubot maintains its own **curated, verifiable database** that reflects the most recent versions of every form and instruction.  

The system routinely checks official agency websites for updates to form versions and procedural guidance. When changes occur, they are automatically integrated into the metadata pipeline, ensuring that Bureaubot always operates with **current, authoritative information** while remaining **fully offline and reproducible**.  

This design guarantees both **accuracy** and **transparency** in an ever-evolving immigration environment.


---

## **How It Works**

<img width="3282" height="813" alt="Untitled diagram-2025-10-27-015507" src="https://github.com/user-attachments/assets/b63bba96-0d9a-40e5-9927-00646e90263c" />


## **Bureaubot’s Brain: Our LLM Agents**

At the core of Bureaubot is a small, focused network of agents that turns messy real-world scenarios into a clean, reviewable packet.

### **Form Selection Agent**
Takes the user’s plain-English situation (e.g., “My green card application was denied by an immigration judge — what now?”) and matches it to candidate forms using a reference catalog and light metadata (eligibility notes, filing venues, typical attachments).  
Outputs the top form(s) with a confidence explanation and next steps.  

**Context-Aware Selection:**  
The agent considers filing posture (appeal vs. initial), decision source (IJ vs. USCIS), and timing cues (deadlines, within/after window) to avoid obvious mismatches.


### **Interview Agent**
Turns each form’s field schema into a sequential, minimal interview. Every question maps to a real field or a rule prerequisite (no meandering chit-chat).  
Captures values, formats them (e.g., **MM/DD/YYYY**), and logs an `answers.json` file for auditing.  

**Dependency-Aware Prompts:**  
If a checkbox implies a sub-section, questions branch automatically.  
If a field is derived (e.g., full name from given/middle/family), derivations remain consistent across the packet.


### **Validation Agent**
Backed by a rule rubric (`YAML`/`JSON`), this agent runs cross-checks and emits actionable messages:
- Date ordering (e.g., filing date vs. decision date)  
- Required fields and sections  
- Consistency across repeated fields (name, A-Number)  
- Attachment expectations (e.g., decision notice, fee payment proof)


### **PDF Filling Agent**
A deterministic writer that maps canonical field names to **AcroForm fields or coordinates**:
- Text boxes with formatting (names, addresses, phones)  
- Multi-box entries (A-Numbers, SSNs, date components)  
- Checkbox/Radio selections with stable on/off values  
- Repeat fills for fields that appear in multiple locations  

**Outputs:** `filled.pdf`, `answers.json`, and a concise `review.md`.


### **Bureaubot’s Interface: Your Filing Playground**

<img width="1051" height="379" alt="Flow chart" src="https://github.com/user-attachments/assets/79d1adf6-8c26-4ac6-818f-6c72664a7953" />

Designed to feel like a conversation but behave like a form engine.

- **Clean, guided screens:** One question at a time with clear helper text.  
- **Live preview:** Optional PDF preview with “field heatmap” when supported.  
- **Fix-list panel:** See warnings as they appear; click to jump directly to the question.  
- **Session resume:** Come back later—your progress persists in `answers.json`.  
- **Export packet:** Download `filled.pdf`, `answers.json`, and `review.md` in one click.

---

## **Bureaubot’s Market Fit and Growth Potential**

Bureaubot is strategically positioned within the rapidly expanding legal automation and immigrant-services market, where individuals face increasing barriers to affordable and timely legal support. By combining AI-guided form selection, contextual Q&A, and precise PDF completion, Bureaubot transforms a traditionally stressful, error-prone process into a clear, reliable experience.

With hours-long wait times at legal clinics and the high cost of professional assistance, Bureaubot offers a scalable alternative that preserves accuracy without replacing human oversight. Its schema-first approach and audit-ready output make it a trustworthy companion for both self-filers and institutions.

**Target Audience:**
- **Self-Filers:** Individuals navigating immigration paperwork alone gain accessible, structured guidance and automatically formatted, submission-ready PDFs.
- **Community Clinics and Nonprofits:** Legal aid and student organizations benefit from standardized intakes, faster packet preparation, and reduced staff workload.
- **Paralegals and Attorneys:** Legal professionals use Bureaubot to pre-fill and verify forms efficiently, minimizing clerical errors and improving turnaround time.

---

## **Future Works**

Future development focuses on enhancing reliability, reach, and accessibility:
- **Product:** Interactive PDF previews with real-time field mapping, multi-form packet support, and resumable interviews.
- **Intelligence:** Expanded rule libraries, attachment inference, and multilingual interviews.
- **Platform:** Secure, containerized deployment with API access for clinics and firms; optional e-signature integration and cloud export.
- **Computer Vision:** Extract form data directly from scanned documents.
Bureaubot’s long-term goal is to become a trusted infrastructure layer for legal document automation—a tool that reduces friction, saves time, and brings bureaucratic processes within reach for everyone.
---

## **Tools Utilized**

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

## **Meet the Team**

**Minh Phan**  
**Anuja Tipare**  
**Connor Yeh**  
**Kanav Goyal**





