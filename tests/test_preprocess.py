import pandas as pd
from ml.preprocess import load_dataset

def test_load_dataset_accepts_text_label(tmp_path):
    p = tmp_path / "train.csv"
    pd.DataFrame({"text": ["hi"], "label": [0]}).to_csv(p, index=False)
    df = load_dataset(str(p))
    assert list(df.columns) == ["text", "label"]
    assert df.shape == (1, 2)
