<h1 align="center">Bureaubot: Bureaucracy, Simplified

Your AI Assistant for Immigration Guidance & Form Filling </h1>

![BureauBot (1)](https://github.com/user-attachments/assets/42654523-726c-4011-8776-4a19c8ef8356)

**Bureaubot** is an AI assistant that simplifies immigration paperwork. It identifies the right form, asks only the questions that matter, and fills official PDFs accurately—saving users hours of waiting and the high costs of legal help.

---

## **Table of Contents**
1. [Project Motivation](#project-motivation)  
2. [Overview of Bureaubot](#overview-of-bureaubot)  
3. [How It Works](#how-it-works)  
4. [Bureaubot’s Market Fit and Growth Potential](#bureaubots-market-fit-and-growth-potential)  
5. [Future Scope](#future-scope)  
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

[![Watch here:](https://img.youtube.com/vi/GrFyE-HmMas/0.jpg)](https://youtu.be/GrFyE-HmMas)


### **Key Features**
- **Immigration Form Guidance:** Recommends the right forms based on each user’s situation.
- **Interactive Q&A:** Provides, clear, tailored answers on eligibility and documentation.
- **Automated Form Filling:** Accurately pre-populates official PDFs using user data.

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

![datapipeline (1)](https://github.com/user-attachments/assets/d7602d0c-261b-49a5-a2e9-831445ea7181)


Bureaubot’s data system is built entirely on official U.S. government sources—USCIS, CBP, EOIR, and ICE. All forms, instructions, and policy materials are routinely collected and processed through a structured update pipeline centered on a single Central Dictionary.

The pipeline has three stages:

Official PDF Forms
Latest PDFs are scraped directly from agency websites and added to the Central Dictionary.

Metadata Extraction
Each PDF is parsed into YAML/JSON schemas defining field types, validation rules, and dependencies for accurate and programmatic form filling.

Reference Information
Filing instructions and contextual details are linked to the metadata, creating a complete reference layer for question flow and validation.

The system automatically checks for new versions and integrates updates, ensuring Bureaubot always operates with current, authoritative, and reproducible information—without relying on live web searches or unverifiable LLM knowledge.

---

## **Our Engines**

![WhatsApp Image](https://github.com/anuja2900/BureauBot/blob/main/WhatsApp%20Image%202025-11-12%20at%2019.19.16.jpeg?raw=true)



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


### **How It Works**

![howitworks (1)](https://github.com/user-attachments/assets/81d98a62-58fa-4ba7-af52-ce2b2360e0c0)

BureauBot is designed to feel like a conversation but behave like a form engine.

- **User Enters a Query:** The user begins by describing their situation or requesting a specific form.
- **Chatbot Asks Clarifying Questions:** Bureaubot collects the necessary context through a guided, one-question-at-a-time interface.
- **User Confirms the Form:** Based on the inputs, Bureaubot recommends the appropriate form and asks the user to confirm before continuing.
- **Chatbot Gathers Required Information:** Relevant form fields are presented in a logical sequence. Conditional logic ensures users only see fields that apply to them.
- **Chatbot Fills the Form:** Responses are mapped to the official YAML/JSON schema, and a clean, validated PDF is generated.
- **Completed Form Is Returned to the User:** The user receives a completed packet, including the filled PDF and supporting data files.


---

## **Bureaubot’s Market Fit and Growth Potential**

Demand for affordable, dependable immigration support continues to rise as traditional legal services become harder to access and slower to deliver. In this environment, Bureaubot fills a widening gap by offering guided form selection, step-by-step clarification, and structured PDF completion built entirely on verified government data. What is often a confusing and intimidating process becomes organized, consistent, and far less stressful.

Instead of replacing legal experts, Bureaubot works alongside them. Its schema-based approach and standardized outputs help maintain accuracy while giving individuals and institutions a tool that scales when human capacity is limited—whether due to long waitlists, heavy caseloads, or cost barriers.

**Target Audience:**
- **Self-Filers:** Individuals navigating immigration paperwork alone gain accessible, structured guidance and automatically formatted, submission-ready PDFs.
- **Community Clinics and Nonprofits:** Legal aid and student organizations benefit from standardized intakes, faster packet preparation, and reduced staff workload.
- **Paralegals and Attorneys:** Legal professionals use Bureaubot to pre-fill and verify forms efficiently, minimizing clerical errors and improving turnaround time.

---

## **Future Scope**

BureauBot has significant potential for expansion and enhancement. In future iterations, the following capabilities can be integrated to make it even more accessible, intelligent, and inclusive:

1. **Voice Interaction (Speech-to-Text):**  
   Enable users to interact with BureauBot through natural speech, allowing voice-based form guidance and dictation for hands-free accessibility.

2. **Multilingual Support:**  
   Incorporate translation features to assist users who are not fluent in English, making immigration guidance available in multiple languages.

3. **Document Scanning & Validation (Computer Vision):**  
   Use computer vision to automatically read, interpret, and validate uploaded documents or pre-filled forms, ensuring completeness and correctness before submission.

4. **Optical Character Recognition (OCR):**  
   Integrate OCR capabilities to extract data directly from physical documents (e.g., passports, ID cards) for automated form population.

5. **Form Progress Tracking & Notifications:**  
   Allow users to save form progress, receive reminders, and get real-time updates about form status or policy changes.

6. **Legal Aid Integration:**  
   Connect users to verified immigration lawyers or legal aid resources for complex cases where expert review is necessary.

By incorporating these advanced features, BureauBot can evolve into a **comprehensive, AI-driven immigration assistant** — bridging the gap between automation, accessibility, and trust in digital immigration services.

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





















