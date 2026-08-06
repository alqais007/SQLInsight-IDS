# Dataset

## Overview

This directory contains the datasets used for developing and evaluating the SQLInsight-IDS machine learning model.

The dataset consists of SQL query samples collected for the purpose of detecting SQL Injection attacks.

---

## Dataset Categories

The dataset contains two main categories:

### Benign Queries

Normal SQL queries generated from legitimate database operations.

Examples:

- Data retrieval queries
- User authentication queries
- Database management queries

### Malicious Queries

SQL Injection payloads designed to exploit vulnerable web applications.

Examples:

- Authentication bypass attempts
- Union-based SQL Injection
- Error-based SQL Injection
- Boolean-based SQL Injection

---

## Data Preprocessing

Before training the model, the dataset undergoes preprocessing:

- Data cleaning
- Removing duplicate samples
- Feature extraction
- Label encoding
- Training and testing split

---

## Purpose

The dataset enables SQLInsight-IDS to learn patterns associated with SQL Injection attacks and classify incoming SQL queries as malicious or legitimate.
