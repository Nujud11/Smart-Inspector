# 🚗 Smart Traffic Investigator

An AI-powered prototype that automatically analyzes traffic accident images and generates a preliminary accident investigation report using Computer Vision, Large Language Models, and rule-based reasoning.

The system combines **YOLOv8**, **Google Gemini**, and a custom traffic rules engine to simulate the workflow of an intelligent accident investigator.

---

## ✨ Features

- 📷 Upload four accident photos from different angles.
- 🚘 Detect vehicles using YOLOv8.
- 🧠 Analyze visual evidence with Google Gemini.
- ⚖️ Apply traffic rules to determine the most likely accident scenario.
- 📊 Generate a structured accident investigation report.
- 📑 Export the complete report as a PDF.
- 🌐 Modern Arabic RTL web interface.

---

## 🏗️ System Architecture

```
User Uploads Images
        │
        ▼
YOLOv8 Vehicle Detection
        │
        ▼
Image Validation
        │
        ▼
Google Gemini Vision Analysis
        │
        ▼
Traffic Rules Engine
        │
        ▼
Confidence Calculation
        │
        ▼
Final Investigation Report
```

---

## 🛠️ Technologies

### Backend

- Python
- Flask
- Google Gemini API
- YOLOv8 (Ultralytics)
- OpenCV

### Frontend

- HTML5
- CSS3
- JavaScript

### AI Models

- YOLOv8
- Gemini 2.5 Flash

---

## 📁 Project Structure

```
smart-traffic-investigator/
│
├── app.py
├── vision_analyzer.py
├── rules.py
├── report_generator.py
├── prompts.py
│
├── templates/
│   ├── index.html
│   ├── upload.html
│   ├── analyze.html
│   ├── result.html
│   └── report.html
│
├── static/
│   ├── css/
│   ├── js/
│   ├── icons/
│   └── results/
│
├── uploads/
├── models/
├── requirements.txt
└── README.md
```

---

## 🚦 Current Supported Accident Scenarios

The current prototype supports preliminary analysis for the following scenarios:

- Rear-end Collision
- Unsafe Lane Change
- Failure to Yield in a Roundabout

Additional traffic scenarios can be added by extending the rule engine.

---

## 🧠 How It Works

### 1. Vehicle Detection

YOLOv8 detects vehicles in each uploaded image and estimates detection confidence.

### 2. Visual Evidence Extraction

Google Gemini analyzes the images and extracts structured information including:

- Vehicle positions
- Visible damage
- Relative movement
- Collision indicators
- Visual inconsistencies
- Overall confidence

### 3. Rule-Based Reasoning

The extracted evidence is evaluated using predefined traffic rules that simulate simplified traffic regulations.

Example:

- Rear vehicle with front damage
- Front vehicle with rear damage
- Rear vehicle positioned behind the leading vehicle

↓

Rear-end Collision

---

## 📄 Generated Report

The generated report includes:

- Case Information
- Vehicle Summary
- Accident Scenario
- Fault Distribution
- Visual Evidence
- YOLO Detection Images
- Technical Analysis
- Confidence Score
- AI Explanation
- Recommendations

---

## 🎯 Project Goals

This prototype aims to demonstrate how Artificial Intelligence can assist traffic investigators by:

- Reducing preliminary investigation time
- Assisting accident documentation
- Providing consistent initial assessments
- Supporting digital traffic investigation workflows
- Exploring AI applications for future smart cities

---

## ⚠️ Disclaimer

This project is a research prototype.

The generated results are preliminary AI-assisted assessments and **must not be considered official traffic decisions**.

Final responsibility remains with qualified traffic investigators and the competent authorities.

---

## 🚀 Installation

Clone the repository

```bash
git clone https://github.com/your-username/smart-traffic-investigator.git
```

Create a virtual environment

```bash
python -m venv venv
```

Activate it

Windows

```bash
venv\Scripts\activate
```

macOS / Linux

```bash
source venv/bin/activate
```

Install dependencies

```bash
pip install -r requirements.txt
```

Run the application

```bash
python app.py
```

Open

```
http://127.0.0.1:5000
```

---

## 🔮 Future Improvements

- Additional accident scenarios
- Official Saudi traffic regulations integration
- Vehicle damage segmentation
- Multi-image consistency verification
- Video accident reconstruction
- Explainable AI dashboard
- Integration with insurance systems
- Integration with smart city platforms
- Automatic accident timeline reconstruction

---

## 📸 Sample Workflow

1. Upload four accident images.
2. Vehicles are detected using YOLOv8.
3. Gemini extracts structured visual evidence.
4. Traffic rules determine the most probable scenario.
5. A complete accident investigation report is generated.

---

## 🌐 Live Demo

👉 https://smart-inspector-production.up.railway.app/

---

## 📌 Project Information

This prototype was developed as part of the **Future Cities Program (برنامج مدن المستقبل)**, organized by **Basmat Association (جمعية بصمات)**.

The project explores the use of Artificial Intelligence to support digital traffic accident investigation within the broader vision of smart city technologies.

It was designed as a proof-of-concept for educational, research, and demonstration purposes, and should not be used as an official accident investigation or legal decision-making system.