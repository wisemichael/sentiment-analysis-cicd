from ml.train import train

def test_train_returns_metrics():
    X = ["good", "bad", "ok", "nice", "awful", "great", "terrible", "awesome"]
    y = [0,1,0,0,1,0,1,0]
    vec, clf, metrics = train(X, y, max_iter=50)
    assert {"val_acc","val_f1","fit_ms"} <= set(metrics.keys())
