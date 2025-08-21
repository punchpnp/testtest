import pandas as pd
from pathlib import Path

def load_company_data(company_name: str):
    data_dir = Path("data")
    for ext in ["xlsx", "csv"]:
        file_path = data_dir / f"{company_name.lower()}.{ext}"
        if file_path.exists():
            if ext == "xlsx":
                return pd.read_excel(file_path)
            else:
                return pd.read_csv(file_path)
    raise FileNotFoundError(f"No data found for {company_name}")
