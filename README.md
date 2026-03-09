# Honduran News & Slang Corpus Pipeline (v2.0)

Automated pipeline for scraping, processing, and fine-tuning GPT models on a high-quality corpus of Honduran journalism and local slang.

## 🚀 Project Overview

This project provides a complete end-to-end framework to:

1. **Scrape** articles from major Honduran outlets (_Criterio.hn, La Prensa, El Heraldo, Diez, and various blogs_).
2. **Collect** local slang and social commentary from Reddit (_r/Honduras_).
3. **Clean & Process** the data using aggressive surgical filters to remove scraper boilerplate and navigation artifacts.
4. **Deduplicate** records using OpenAI vector embeddings (cosine similarity).
5. **Fine-tune** GPT-4o-mini to speak in an authentic Honduran journalistic voice.
6. **Evaluate** the model's performance via a 3-way comparison (Base vs v1 vs v2).

## 📂 Repository Structure

```text
├── project/
│   ├── datasets/         # Surgical-cleaned and deduplicated training data
│   ├── outputs/          # Evaluation reports, JSON results, and comparison metrics
│   ├── training/         # Core scripts for cleaning, training, and evaluation
│   └── config/           # Model and Job registries
├── scrapers/             # Apify-based scraping logic for news and Reddit
├── utils/                # Data processing and reporting helpers
└── .env                  # Project environment variables
```

## 🛠 Setup & Installation

### 1. Prerequisites

- Python 3.10+
- OpenAI API Key
- Apify API Token

### 2. Install Dependencies

```bash
python -m venv venv
source venv/bin/activate
pip install openai apify-client python-dotenv tqdm numpy sentence-transformers
```

### 3. Environment Variables

Ensure your `.env` file contains:

```env
OPENAI_API_KEY=your_openai_key
APIFY_API_TOKEN=your_apify_token
```

## 📈 Performance (v2.0 "Surgical")

The v2 model features an aggressive improvement cycle to eliminate "Scraper Noise".

| Metric                   | Base Model | v1 (Initial) | v2 (Surgical) |
| ------------------------ | ---------- | ------------ | ------------- |
| **Tone Accuracy**        | 4.64       | 3.96         | **4.36**      |
| **Boilerplate Count**    | 0          | 6            | **0**         |
| **Hallucination Safety** | 4.80       | 4.64         | **4.84**      |

## 🕹️ Usage

### Data Cleaning & Deduplication

```bash
python project/training/clean_dataset_v2.py
python project/training/deduplicate_v2.py
```

### Run Fine-Tuning (v2)

```bash
python project/training/run_v2_training.py
```

### Run Multi-Model Evaluation

```bash
python project/training/run_v2_evaluation.py
```

## 📝 License

This project is developed for OpenAI Fine-tuning research on regional linguistic nuances.
