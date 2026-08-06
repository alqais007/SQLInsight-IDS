# SQLInsight-IDS
## Machine Learning-Based Intrusion Detection System for SQL Injection Attacks

![Cybersecurity](https://img.shields.io/badge/Domain-Cybersecurity-red)
![Machine Learning](https://img.shields.io/badge/Technology-Machine%20Learning-blue)
![Python](https://img.shields.io/badge/Language-Python-yellow)
![Security](https://img.shields.io/badge/Focus-SQL%20Injection%20Detection-green)

---

## 📌 Project Overview

SQLInsight-IDS is a Machine Learning-based Intrusion Detection System (IDS) designed to detect and classify SQL Injection (SQLi) attacks against web applications.

The project explores how machine learning techniques can enhance traditional security detection methods by identifying malicious SQL query patterns and distinguishing them from legitimate database requests.

The system was developed as a cybersecurity research project focusing on intelligent threat detection, web application security, and automated attack classification.

---

# 🎯 Objectives

The main objectives of SQLInsight-IDS are:

- Detect SQL Injection attacks using Machine Learning.
- Analyze SQL query patterns and identify malicious behavior.
- Reduce dependency on traditional signature-based detection.
- Minimize false positive detection.
- Evaluate machine learning performance using classification metrics.
- Demonstrate detection capabilities through a vulnerable web application environment.

---

# 🛡️ Problem Statement

SQL Injection remains one of the most critical web application vulnerabilities.

Traditional security solutions often rely on predefined rules and signatures, which may fail against:

- New attack variations
- Obfuscated payloads
- Unknown SQL Injection patterns

SQLInsight-IDS addresses this challenge by applying machine learning techniques to identify malicious SQL queries based on learned attack characteristics.

---

# ⚙️ System Workflow

The project follows the following workflow:
SQL Query Input
|
↓
Data Preprocessing
|
↓
Feature Extraction
|
↓
Machine Learning Model
|
↓
Classification
|
↓
Benign Query / SQL Injection Attack



---

# 🏗️ System Components

## 1. Dataset

The dataset contains SQL query samples divided into:

- Benign SQL queries
- Malicious SQL Injection payloads

The dataset is processed and prepared before model training.

---

## 2. Machine Learning Model

The model performs binary classification:

| Class | Description |
|---|---|
| 0 | Benign SQL Query |
| 1 | SQL Injection Attack |

The model learns patterns associated with malicious SQL behavior.

---

## 3. Detection Engine

The detection engine analyzes incoming SQL queries and provides classification results:

- Legitimate request
- Potential SQL Injection attack

---

## 4. Web Application Proof of Concept

A vulnerable WordPress environment was used to demonstrate:

- SQL Injection exploitation
- Query analysis
- Detection capability
- Model response

---

# 📊 Model Performance

The trained model achieved the following results:

| Metric | Score |
|---|---|
| Accuracy | 99.08% |
| Precision | 99.03% |
| Recall | 98.47% |
| F1-Score | 98.75% |

These results demonstrate strong capability in detecting SQL Injection attacks with high classification performance.

---

# 🧪 Testing Environment

The project was tested using:

- Vulnerable WordPress Application
- SQL Injection attack scenarios
- Machine Learning classification model

---

# 📸 Demonstration

Screenshots will be added:
/Assets
├── wordpress-demo.png
├── sqli-testing.png
└── model-results.png


Examples:

- Vulnerable application testing
- SQL Injection attack execution
- Detection results
- Model evaluation output

---

# 📂 Repository Structure
SQLInsight-IDS
│
├── README.md
│
├── Documentation
│ └── README.md
│
├── Dataset
│ └── README.md
│
├── Model
│ └── README.md
│
├── Source-Code
│ └── README.md
│
└── Results
└── README.md


---

# 🚀 Future Improvements

Future enhancements include:

- Real-time SQL traffic monitoring
- Integration with SIEM platforms
- Microsoft Defender XDR integration
- Automated threat response using SOAR
- Deep learning-based detection models
- API deployment for enterprise environments

---

# 🛠️ Technologies Used

- Python
- Machine Learning
- SQL
- WordPress
- Web Application Security
- SQL Injection Testing
- Data Processing Techniques

---

# 👨‍💻 Author

Cybersecurity Research Project

**SQLInsight-IDS**

Developed as part of cybersecurity research focusing on intelligent intrusion detection and web application protection.






