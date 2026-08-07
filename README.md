# SQLInsight-IDS

## Machine Learning-Based SQL Injection Detection System

![Python](https://img.shields.io/badge/Python-3.x-blue)
![Machine Learning](https://img.shields.io/badge/Machine%20Learning-Logistic%20Regression-orange)
![Security](https://img.shields.io/badge/Focus-Cybersecurity-red)
![IDS](https://img.shields.io/badge/Type-Intrusion%20Detection%20System-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

![System Architecture](Assets/Architecture/system_architecture_diagram.png)

## Project Overview

SQLInsight-IDS is a Machine Learning-based Intrusion Detection System (IDS) designed to detect SQL Injection (SQLi) attacks against web applications.

The project combines data preprocessing, machine learning classification, and detection mechanisms to identify malicious SQL queries and distinguish them from legitimate database requests.

The system was developed as a cybersecurity research project to investigate how machine learning techniques can improve SQL Injection detection accuracy compared to traditional signature-based approaches.

---

# Objectives

The main objectives of SQLInsight-IDS are:

* Detect SQL Injection attacks using Machine Learning.
* Classify SQL queries as malicious or benign.
* Reduce false positive detection.
* Analyze SQL query patterns.
* Evaluate model performance using machine learning metrics.
* Demonstrate detection capabilities through a vulnerable web application environment.

---

# System Architecture

The overall system architecture consists of:

* Dataset collection and preparation
* Data preprocessing
* Feature extraction
* Machine learning model training
* Detection engine
* Alert generation
* Web application testing environment

Architecture diagram:

![System Architecture](Assets/Architecture/system_architecture_diagram.png)

---

# Machine Learning Workflow

![ML Workflow](Assets/Diagrams/ml_workflow_diagram.png)

The workflow consists of:

1. Dataset preparation
2. Data cleaning and preprocessing
3. Feature extraction
4. Model training
5. Model evaluation
6. SQL Injection detection
7. Alert generation

---

# Machine Learning Model

## Algorithm

The project uses:

**Logistic Regression**

as the classification algorithm.

The model performs binary classification:

| Class | Description         |
| ----- | ------------------- |
| 0     | Benign SQL Query    |
| 1     | SQL Injection Query |

The trained model analyzes SQL query features and predicts whether the input query represents a potential SQL Injection attack.

---

# Dataset

The dataset contains:

* Normal SQL queries
* SQL Injection payloads
* Malicious query patterns

Dataset processing includes:

* Data cleaning
* Feature preparation
* Label assignment
* Model-ready transformation

Available datasets:

```
Assets/Dataset/
├── clean-dataset.csv
└── modified-dataset.csv
```

---

# Detection Engine

The detection engine provides:

* SQL query analysis
* Access log monitoring
* Attack simulation
* Alert generation
* Detection result processing

Source code:

```
Assets/Source-Code/Detection-Engine/
```

Components:

* `detection.py`
* `monitor.py`
* `alerts.py`
* `accesslog.py`
* `simulate_traffic.py`
* `geoip.py`

---

# Model Performance

The Logistic Regression model was evaluated using:

* Accuracy
* Precision
* Recall
* F1-Score

Performance:

| Metric    | Score  |
| --------- | ------ |
| Accuracy  | 99.08% |
| Precision | 99.03% |
| Recall    | 98.47% |
| F1-Score  | 98.75% |

Evaluation results and confusion matrices:

```
Assets/Performance/
```

---

# Experiments

The project includes multiple experiments to evaluate model effectiveness.

Experiment results include:

* Performance metrics
* Confusion matrices
* Detection analysis

Available in:

```
Assets/Performance/
```

---

# Web Application Testing

# Project Screenshots

## Frontend Interface

![Frontend Interface](Assets/Screenshots/frontend_interface_01.png)

## SQL Injection Detection

![SQL Injection Detection](Assets/Screenshots/sqli_alert_01.png)

## Detection Results

![Detection Results](Assets/Screenshots/detection_result_01.png)

## Database Backend

![Database Backend](Assets/Screenshots/database_backend_01.png)


The system was tested using a vulnerable web application environment.

Testing included:

* SQL Injection attempts
* Frontend interaction
* Database communication
* Detection response

Screenshots:

```
Assets/Screenshots/
```

---

# Repository Structure

```
SQLInsight-IDS

├── README.md
├── LICENSE
│
└── Assets
    │
    ├── Architecture
    ├── Diagrams
    ├── Screenshots
    ├── Performance
    ├── Dataset
    ├── Source-Code
    └── Thesis
```

---

# Technologies Used

## Programming

* Python

## Machine Learning

* Logistic Regression
* Scikit-learn

## Cybersecurity

* SQL Injection Detection
* Intrusion Detection Systems
* Web Application Security

## Development Environment

* Google Colab
* Python Libraries
* WordPress Testing Environment

---

# Future Improvements

Future enhancements include:

* Real-time SQL traffic monitoring
* SIEM integration
* API-based deployment
* Automated incident response
* Advanced machine learning models
* Integration with security monitoring platforms

---

# Documentation

Additional documentation:

```
Assets/Source-Code/Documentation/
```

Includes:

* Architecture documentation
* Dataset documentation
* Model documentation
* API documentation
* Security documentation

---

# Author

Cybersecurity Research Project

SQLInsight-IDS
