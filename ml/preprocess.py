import pandas as pd


def load_dataset(path: str) -> pd.DataFrame:
    """
    Supports either:
      - columns: text,label  (label ∈ {0,1})
      - Jigsaw subset columns: comment_text,toxic (toxic ∈ {0,1})
    """
    df = pd.read_csv(path)
    if "comment_text" in df.columns and "toxic" in df.columns:
        df = df.rename(columns={"comment_text": "text", "toxic": "label"})
    if not {"text", "label"}.issubset(df.columns):
        raise ValueError("CSV must have 'text' and 'label' columns (or 'comment_text' and 'toxic').")
    df = df.dropna(subset=["text"])
    df["label"] = df["label"].astype(int)
    return df[["text", "label"]]
