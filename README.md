# Frenchway Travel Web Scraper

## Project Description

This project is a web scraping project developed for Hasmo Consulting. The goal is to collect structured information from the Frenchway Travel website using Python web scraping tools.

The project uses BeautifulSoup, Scrapy, and Requests for retrieving, parsing, and processing web content.

## Setup Instructions

1. Clone or download the project repository.

2. Navigate to the project directory:

```bash
cd Project_1_Frenchway
```

3. Create a Python virtual environment:

```bash
python3 -m venv frenchway
```

4. Activate the virtual environment:

```bash
source frenchway/bin/activate
```

5. Install the required dependencies:

```bash
python -m pip install -r requirements.txt
```

## Usage

The main scraping scripts are located in the `scripts/` directory.

Run the main scraper with:

```bash
python scripts/main.py
```

Raw scraped data will be stored in:

```text
data/raw/
```

Jupyter notebooks used for data exploration or analysis are stored in:

```text
notebooks/
```

## Project Structure

```text
Project_1_Frenchway/
├── frenchway/
├── data/
│   └── raw/
├── scripts/
│   ├── __init__.py
│   ├── main.py
│   └── utils.py
├── notebooks/
├── requirements.txt
├── README.md
└── .gitignore
```