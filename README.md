# EduAI: AI-Powered Assignment Evaluation & Test Management System

EduAI is a modern educational platform designed to automate the academic workflow. It leverages Large Language Models (LLMs) to evaluate handwritten student assignments and generate MCQ tests from source documents (PDF, DOCX, PPTX).

## 🚀 Live Demo
**URL:** [https://assignment-checker-main.onrender.com](https://assignment-checker-main.onrender.com)

---

## ✨ Key Features

### 👨‍🏫 Teacher Module
- **AI Assignment Evaluation:** Upload a question paper and the AI generates a logic-based answer key. Students' handwritten work is processed via OCR and graded against this key.
- **Automated MCQ Generation:** Generate full MCQ tests from textbook files (.pdf, .docx, .pptx) in seconds.
- **Dynamic Test Editor:** Preview, edit, add, or delete AI-generated questions before publishing.
- **Student Analytics:** View a comprehensive gradebook of all student scores and class averages.
- **Attendance Management:** Record and track lecture-wise attendance.

### 👨‍🎓 Student Module
- **Online Exam Engine:** A proctored-style interface with a countdown timer, question palette, and auto-submit functionality.
- **AI Teaching Assistant:** A real-time chat widget for academic support.
- **Assignment Submission:** Snap a photo of handwritten work and get instant AI feedback.

### 🛡️ Security & Auth
- **Admin Bypass:** Hardcoded admin credentials for system oversight.
- **Email Verification:** Secure 6-digit OTP verification via Brevo (Sendinblue) API.
- **Role-Based Access:** Strict separation of Admin, Teacher, and Student permissions.

---

## 🛠️ Tech Stack

- **Backend:** Python 3.9+, Flask
- **Frontend:** HTML5, JavaScript (ES6), Tailwind CSS
- **Database:** PostgreSQL (Production on Render) / SQLite (Local)
- **AI Engines:** Groq API (Llama-3.3-70b & Llama-3.2-11b-Vision)
- **OCR & Document Parsing:** Pytesseract, pypdf, python-docx, python-pptx
- **Email Service:** Brevo SMTP API

---

## 📦 Installation & Setup

### 1. Clone the Repository
```bash
git clone [https://github.com/Viraj/EduAI-Main.git](https://github.com/Viraj/EduAI-Main.git)
cd EduAI-Main ``` 
