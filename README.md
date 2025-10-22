# BureauBot

## Table of Contents
1. [Motivation 🌎](#motivation-)
   - [Background](#background)
   - [Common Challenges Faced by International Students](#common-challenges-faced-by-international-students)
   - [Goals & Value Proposition](#goals--value-proposition)
2. [Overview of BureauBot 🗺️](#overview-of-bureaubot-️)
   - [Key Features](#key-features)
   - [Methodology](#methodology)
   - [Data](#data)
   - [Code Structure](#code-structure)
3. [User Interface 💻](#user-interface-)
   - [Application](#application)
   - [Demo](#demo)
4. [Evaluation & Testing 📊](#evaluation--testing-)
   - [Evaluation Framework and Results](#evaluation-framework-and-results)
   - [User Testing](#user-testing)
5. [Differentiators ✨](#differentiators-)
   - [Comparison with Gemini 1.5 Pro](#comparison-with-gemini-15-pro)
6. [Future Work 🚀](#future-work-)
7. [Conclusion 🎓](#conclusion-)
8. [Tools Used 🛠️](#tools-used-)
9. [References 📚](#references-)
10. [Acknowledgements / About Us 👤](#acknowledgements--about-us-)

---

## 1. Motivation 🌎

### Background
As a team of four immigrants navigating the complex U.S. immigration system, we personally experienced the challenges of filling out multiple forms, understanding eligibility requirements, and finding reliable information. There was no single, trustworthy platform where all our questions could be answered efficiently. The process was time-consuming, stressful, and often confusing, which inspired us to develop **BureauBot** — a chatbot designed specifically to simplify the immigration process.

### Common Challenges Faced by International Students and Immigrants
- **Information Overload:** Immigrants often have to search across multiple government websites and documents to find the right forms and instructions.  
- **Complex Forms:** Many forms are lengthy, with technical language and conditional sections, making them difficult to fill correctly without guidance.  
- **Eligibility Confusion:** Determining which forms apply to a specific case is not always straightforward.  
- **Time and Stress:** The process is slow, stressful, and prone to errors, leading to delays or incorrect submissions.  

### Goals & Value Proposition
BureauBot aims to **streamline and simplify the immigration process** for individuals by:  
1. **Answering Queries:** Users can ask questions about immigration forms, eligibility, and required documentation, and get precise, reliable answers.  
2. **Form Guidance:** BureauBot directs users to the correct forms based on their specific circumstances.  
3. **Automated Form Filling:** Users can input their personal details, and BureauBot will fill out the forms accurately, minimizing errors and saving time.  
4. **Domain-Specific Focus:** Unlike general-purpose chatbots, BureauBot is trained exclusively on immigration forms and processes, ensuring high accuracy and relevance.  

By addressing these pain points, BureauBot reduces the cognitive load on immigrants, increases confidence in form submissions, and provides a **single, reliable platform** for immigration guidance.  

---


## 2. Overview of BureauBot 🗺️

### Key Features
- **Immigration Form Guidance:** BureauBot directs users to the correct immigration forms based on their individual circumstances.  
- **Interactive Q&A:** Users can ask detailed questions about eligibility, documentation, and form requirements, and get accurate, context-specific answers.  
- **Automated Form Filling:** Using Pymupdf, BureauBot can populate forms automatically from user-provided details, ensuring correctly formatted submissions.  
- **Domain-Specific LLM:** The chatbot is trained exclusively on immigration forms and official instructions, reducing errors and irrelevant responses.  
- **Reliable and Efficient:** By leveraging pre-trained LLMs and structured data from official sources, BureauBot minimizes latency while maintaining high accuracy.

### Methodology
- **Large Language Models (LLMs):** Leveraged Gemini 2.0 to understand user queries and generate precise responses. The model was fine-tuned on immigration forms and metadata from official sources to ensure domain-specific accuracy.  
- **Form Metadata Extraction:** Downloaded official immigration forms and extracted metadata (field names, requirements, conditions) to train the model to recognize and correctly fill each section.  
- **Multi-Step Prompting:** Applied iterative prompting techniques to convert free-form user input into structured data suitable for form filling. This ensures that all user details are correctly mapped to the corresponding fields.  
- **Automated Form Population:** Integrated Pymupdf to fill forms programmatically based on the structured output from the LLM, producing ready-to-submit documents.  
- **Validation and Accuracy Checks:** Implemented consistency checks and error handling to ensure that filled forms adhere to official requirements and reduce user mistakes.

  ### Data
- **[U.S. Citizenship and Immigration Services (USCIS)](https://www.uscis.gov/):** Official forms, instructions, and eligibility criteria were downloaded and used to train the model on accurate form completion.  
- **[Customs and Border Protection (CBP)](https://www.cbp.gov/):** Metadata and documentation from CBP were included to provide guidance on entry, travel, and border-related queries.  
- **[Executive Office for Immigration Review (EOIR)](https://www.justice.gov/eoir):** Legal documents and procedural information from EOIR were used to ensure accurate responses on hearings, appeals, and immigration court processes.  
- **[Immigration and Customs Enforcement (ICE)](https://www.ice.gov/):** Relevant forms, policies, and guidelines from ICE were incorporated to provide users with reliable compliance and enforcement information.  

All data was **curated directly from official sources**, extracted for metadata, and structured to train the LLM. This ensures BureauBot delivers **accurate, trustworthy, and domain-specific guidance** for users navigating the U.S. immigration system.  

 ---
