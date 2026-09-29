# Girai Visualization Challenge

2024 Global Index on Responsible AI data visualization challenge.

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