# 2024 GIRAI Visualization Challenge

2024 Global Index on Responsible AI data visualization challenge.

## About
What is the Global Index on Responsible AI Data Visualization Challenge? It’s a global competition inviting individuals and teams to create data visualizations using the 2024 Global Index on Responsible AI dataset. Participants explore trends, challenges, and disparities in Responsible AI to inspire action and policy change.

## Objective
**1. Promote Understanding of Responsible AI**
Transform the Global Index on Responsible AI data into clear, impactful visualisations that uncover trends, and challenges in Responsible AI worldwide. This will raise awareness and inform the public about responsible AI challenges such as governance gaps, human rights implications, and gender and inclusion issues.

**2. Highlight Global and Regional Trends**
Showcase the uneven progress of responsible AI across regions and topics, emphasising advancements and areas needing improvement, particularly in human rights. Empower participants to delve deep into the data to uncover hidden trends and discover narratives.

**3. Inspire Action and Policy Change**
Drive change through visualisations that can serve as advocacy tools for policymakers, stakeholders and non-state actors, encouraging improvements in responsible AI frameworks and practices.

## Global Index on Responsible AI Data Visualization Challenge Themes
This challenge invites participants to explore the data and insights from the Global Index on Responsible AI report by creating impactful visualisations. Participants can choose from three broad themes, each designed to provide flexibility while encouraging meaningful exploration of responsible AI. These themes cover specific thematic areas, highlight global and regional trends, and offer an open-ended option for creative exploration.

**Theme 1**: Exploring the Thematic Areas of Responsible AI What Are the Thematic Areas?
The Global Index on Responsible AI collects data on key thematic areas, each of which focuses on core aspects of responsible AI. These areas assess how governments and non-state actors are working (or not) on each of these aspects to create the conditions for the design, deployment and use of AI in ways that are safe, and respect and uphold human rights. These thematic areas cover critical areas of responsible AI, such as their intersection with human rights, technical standards and the existence of key capacities required to advance responsible AI. The thematic areas can be found here: Global Index on Responsible AI Thematic Areas

*Focus*: This theme invites participants to explore one or more of the thematic areas from the Global Index on Responsible AI. Participants can create visualisations that highlight key trends, disparities, and advancements in responsible AI. They can focus on how regions are performing across these themes, identifying where gaps exist, or showing how these thematic areas interact with one another.

**Theme 2**: Exploring Global and Regional Trends in Responsible AI
What Are the Global and Regional Trends?
The Global Index on Responsible AI also identifies broader global trends in responsible AI. These trends reveal critical patterns and insights into AI principles and practices around the world and where gaps remain. These trends highlight the state of responsible AI globally,showing progress and also where more efforts are needed. The trends can be found throughout the Global Index on Responsible AI report.

*Focus*: This theme invites participants to explore the major global trends identified in the Global Index on Responsible AI report and deepen on how these trends look across different regions. Through this theme, participants can highlight key patterns, disparities, and
commonalities that define the global state of responsible AI. This theme provides flexibility, allowing participants to focus on specific trends or create a broader visualisation that integrates multiple trends.

## Project structure
```
GIRAI-Viz-Challenge/
├── app.py
├── data_engine.py
├── GIRAI_2024_Edition_Data.xlsx
├── pyproject.toml
├── README.md
├── requirements.txt
│
│
├── data/
│   ├── metadata.json
│   ├── observations.ndjson
│   └── rankings.ndjson
│
├── static/
│   ├── app.js
│   └── styles.css   
│
├── scripts/
│   └── prepare_data.py
│
├── templates/
│   ├── index.html
│   └── 404.html
│
├── tests/
│   └── test_data_engine.py
```

## Run locally

Python 3.12+ is recommended.

```bash
pip install -r requirements.txt
python app.py
```

Then open `http://127.0.0.1:5000`.
