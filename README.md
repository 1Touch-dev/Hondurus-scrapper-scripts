# 🇭🇳 Honduran News & Slang Corpus Pipeline (v2.0 "Surgical")

An end-to-end autonomous pipeline for scraping, processing, and fine-tuning GPT models on high-fidelity Honduran journalism and regional linguistic nuances.

## 🚀 Project Overview

This project was built to address the lack of high-quality, localized training data for Central American Spanish, specifically focusing on the **Honduran** context. The pipeline transforms raw, noisy web-scraped data into a structured knowledge base used for supervised fine-tuning (SFT).

### Key Accomplishments

- **Boilerplate Elimination**: Removed 100% of scraper artifacts ("Comparte esto", "Noticias Relacionadas") that plagued v1.
- **Tone Restoration**: Achieved a **4.36/5.0** tone accuracy score, matching the nuances of national outlets like _Criterio.hn_ and _La Prensa_.
- **Lexical Diversity**: Integrated sub-reddits and blogs to capture "Hondureñismos" (slang) alongside formal journalism.

---

## 🧠 Model Details

- **Base Model**: `gpt-4o-mini-2024-07-18`
- **Fine-Tuned Model (v2)**: `ft:gpt-4o-mini-2024-07-18:1touch:honduras-news-v2:DHQyNyzt`
- **Training Method**: Supervised Fine-Tuning (SFT)
- **Metadata Conditioning**: The model uses tag-based conditioning in the system prompt for maximum controllability:
  - `[COUNTRY=Honduras]`
  - `[DOMAIN=sports|political_investigation|breaking_news|cultural_blog]`
  - `[OUTLET=criterio.hn|laprensa.hn|elheraldo.hn|diez.hn]`
  - `[TASK=article_generation]`

---

## 📊 Dataset & Composition

The final **v2 surgical dataset** consists of **293 high-quality records**, meticulously filtered:

1.  **Cleaned Scraper Data (213 items)**:
    - Sourced from _Criterio.hn_, _La Prensa_, _El Heraldo_, and _Diez_.
    - Processed through a structural normalizer that enforces paragraph separation and minimum word counts (200-1200 words).
2.  **Synthetic Augmentation (80 items)**:
    - High-signal articles generated to fill gaps in specific domains like Investigative Journalism and Cultural Commentary.
3.  **Deduplication**:
    - Used `text-embedding-3-small` with a **0.92 cosine similarity threshold** to remove 152 redundant or near-duplicate articles.

---

## 🕹️ Interactive Testing (How to Run)

To generate articles using the production-ready v2 model, use the provided `test_model_v2.py` utility.

### 1. Environment Setup

```bash
# Activate virtual environment
source venv/bin/activate

# Ensure .env is populated with
# OPENAI_API_KEY=your_key
```

### 2. Basic Generation

Run the script with a default topic (Judicial Transparency):

```bash
python test_model_v2.py
```

### 3. Custom Topic Generation

Pass any topic as an argument:

```bash
python test_model_v2.py "El impacto de la inflación en la canasta básica en San Pedro Sula"
```

### 4. Adjusting Tone

You can modify the `domain` and `outlet` in the script's `generate_article` function calls to switch between:

- **Sports** (`domain="sports"`, `outlet="diez.hn"`)
- **Breaking News** (`domain="breaking_news"`)
- **Cultural Blogs** (`domain="cultural_blog"`)

---

## 📂 Repository Structure

```text
├── project/
│   ├── datasets/         # Final .jsonl files (train/validation)
│   ├── outputs/          # 3-way model comparison reports & metrics
│   ├── training/         # Core logic:
│   │   ├── clean_dataset_v2.py    # Surgical regex filters
│   │   ├── deduplicate_v2.py      # Embedding-based similarity check
│   │   ├── run_v2_evaluation.py   # Automated LLM-Judged scoring
│   │   └── run_v2_training.py     # OpenAI job orchestration
│   └── config/           # Model Registry (tracks FT Job IDs)
├── scrapers/             # Apify-based actors for news & Reddit
└── test_model_v2.py      # Production inference test utility
```

## 🛠 Advanced Pipeline Usage

### Run Full Evaluation (Base vs v1 vs v2)

```bash
python project/training/run_v2_evaluation.py
```

This generates a detailed markdown report in `project/outputs/model_comparison_report.md` comparing Tone, Structure, and Hallucination rates.

---

## 📝 License

Proprietary research for 1Touch-dev. Focuses on linguistic modeling for Central American dialects.
