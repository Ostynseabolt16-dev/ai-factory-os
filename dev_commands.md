# AI Factory OS Dev Commands

## Activate Virtual Environment
```bash
source .venv/bin/activate
```

## Compile Check
```bash
python -m compileall ai_factory
```

## Run All Tests
```bash
python -m unittest discover -s . -p "test_*.py"
```

## Run Queue Test
```bash
python -m unittest test_etsy_upload_queue.py
```

## Run Trend Score Test
```bash
python -m unittest test_trend_score.py
```

## Run Factory Map Test
```bash
python -m unittest test_factory_map.py
```

## Run Main Pipeline
```bash
python main.py
```

## Run CLI Menu
```bash
python -m ai_factory.cli
```

## Git Status
```bash
git status
```

## Save Progress
```bash
git add .
git commit -m "describe changes"
```

## View Branches
```bash
git branch
```

## Create Backup Branch
```bash
git checkout -b backup-before-major-change
```

## Quick Syntax Check (All Modified Files)
```bash
python -m py_compile ai_factory/**/*.py
```

## View Recent Commits
```bash
git log --oneline -10
```

## Check Virtual Env
```bash
which python
python --version
pip list | head -20
```

## Install Dependencies
```bash
pip install -r requirements.txt
```

## Run with Dry-Run Flag
```bash
python uploader.py
```

## Import Etsy CSV
```bash
python -c "from ai_factory.importers.etsy_shop_importer import import_existing_etsy_listings; print(import_existing_etsy_listings('path/to/etsy_export.csv'))"
```

## Import Trend Data
```bash
python -c "from ai_factory.intelligence.trend_score import import_trend_csv; print(import_trend_csv('path/to/trends.csv'))"
```

## Score All Products
```bash
python -c "from ai_factory.intelligence.trend_score import score_all_products, load_trend_data; print(score_all_products(load_trend_data()))"
```

## View Product CSV Schema
```bash
python -c "from ai_factory.products.product_manager import CSV_COLUMNS; print('\\n'.join(CSV_COLUMNS))"
```

## Inspect Product Record
```bash
python -c "from ai_factory.products.product_manager import read_products; products = read_products(); print(products[0] if products else 'No products')"
```
