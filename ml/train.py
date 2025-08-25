# ml/train.py
import argparse
import os
import time
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import train_test_split

import mlflow
from mlflow import MlflowClient
import mlflow.sklearn


def load_data(csv_path: str):
    """CSV must have columns: 'text', 'label' (0/1)."""
    df = pd.read_csv(csv_path)
    if "text" not in df.columns or "label" not in df.columns:
        raise ValueError("CSV must have columns: 'text', 'label'")
    return df["text"].astype(str).tolist(), df["label"].astype(int).tolist()


def train(X, y, min_df=1, ngram_max=2, C=1.0, max_iter=400, seed=42):
    X_train, X_val, y_train, y_val = train_test_split(
        X, y, test_size=0.2, random_state=seed, stratify=y
    )

    vec = TfidfVectorizer(min_df=min_df, ngram_range=(1, ngram_max))
    clf = LogisticRegression(max_iter=max_iter, C=C)

    t0 = time.perf_counter()
    Xtr = vec.fit_transform(X_train)
    clf.fit(Xtr, y_train)
    fit_ms = (time.perf_counter() - t0) * 1000.0

    Xv = vec.transform(X_val)
    y_pred = clf.predict(Xv)
    y_prob = clf.predict_proba(Xv)[:, 1]

    acc = accuracy_score(y_val, y_pred)
    f1 = f1_score(y_val, y_pred)

    metrics = {"val_acc": float(acc), "val_f1": float(f1), "fit_ms": float(fit_ms)}
    return vec, clf, metrics


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default="ml/data/train.csv", help="CSV with text,label")
    parser.add_argument("--min_df", type=int, default=1)
    parser.add_argument("--ngram_max", type=int, default=2)
    parser.add_argument("--C", type=float, default=1.0)
    parser.add_argument("--max_iter", type=int, default=400)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--stage", default="Production", choices=["Staging", "Production"])
    args = parser.parse_args()

    # --------- MLflow configuration ---------
    tracking_uri = os.getenv("MLFLOW_TRACKING_URI", "http://127.0.0.1:5000")
    mlflow.set_tracking_uri(tracking_uri)

    experiment_name = os.getenv("MLFLOW_EXPERIMENT_NAME", "toxic-comment")
    mlflow.set_experiment(experiment_name)

    registered_model_name = os.getenv("MLFLOW_MODEL_NAME", "toxic-comment-model")

    # --------- Train ---------
    X, y = load_data(args.data)

    with mlflow.start_run(run_name="tfidf-logreg"):
        # Log params
        mlflow.log_params(
            {
                "min_df": args.min_df,
                "ngram_max": args.ngram_max,
                "C": args.C,
                "max_iter": args.max_iter,
                "seed": args.seed,
            }
        )

        vec, clf, metrics = train(
            X,
            y,
            min_df=args.min_df,
            ngram_max=args.ngram_max,
            C=args.C,
            max_iter=args.max_iter,
            seed=args.seed,
        )

        # Log metrics
        mlflow.log_metrics(metrics)

        # Save artifacts locally (useful fallback for the API)
        art_dir = Path("api/app/artifacts")
        art_dir.mkdir(parents=True, exist_ok=True)
        vec_path = art_dir / "vectorizer.joblib"
        clf_path = art_dir / "classifier.joblib"
        joblib.dump(vec, vec_path)
        joblib.dump(clf, clf_path)

        # Log artifacts to MLflow for traceability
        mlflow.log_artifact(str(vec_path), artifact_path="artifacts")
        mlflow.log_artifact(str(clf_path), artifact_path="artifacts")

        # Log a unified pyfunc model so the API can load from the MLflow Registry
        class ToxicCommentModel(mlflow.pyfunc.PythonModel):
            def load_context(self, context):
                import joblib
                from pathlib import Path
                v = joblib.load(Path(context.artifacts["vec"]))
                c = joblib.load(Path(context.artifacts["clf"]))
                self.vec = v
                self.clf = c

            def predict(self, context, model_input):
                # expects a list/Series of strings
                X = self.vec.transform(list(model_input))
                probs = self.clf.predict_proba(X)[:, 1]
                labels = (probs >= 0.5).astype(int)
                return pd.DataFrame({"label": labels, "prob": probs})

        pyfunc_info = mlflow.pyfunc.log_model(
            artifact_path="model",
            python_model=ToxicCommentModel(),
            artifacts={"vec": str(vec_path), "clf": str(clf_path)},
            registered_model_name=registered_model_name,
        )

        run_id = mlflow.active_run().info.run_id
        client = MlflowClient()

        versions = client.search_model_versions(f"name='{registered_model_name}'")
        my_version = None
        for v in versions:
            if v.run_id == run_id:
                my_version = v.version
                break

        if my_version is None:
            raise RuntimeError("Could not find model version we just logged.")

        client.transition_model_version_stage(
            name=registered_model_name,
            version=my_version,
            stage=args.stage,
            archive_existing_versions=False,
        )

        version_str = f"mlflow-{registered_model_name}-v{my_version}-{args.stage.lower()}"
        (art_dir / "MODEL_VERSION.txt").write_text(version_str, encoding="utf-8")
        print(f"✔ Registered '{registered_model_name}' v{my_version} -> {args.stage}")
        print(f"   Run: {mlflow.get_artifact_uri()}")

    print("✅ Training + MLflow logging complete.")


if __name__ == "__main__":
    main()
