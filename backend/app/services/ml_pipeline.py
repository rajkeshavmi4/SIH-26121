import math
import json
import base64
import pickle
from typing import List, Dict, Any, Optional
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.calibration import CalibratedClassifierCV

class MLTrainingPipeline:
    def __init__(self):
        self.feature_names = ["wob", "rpm", "torque", "rop_mhr", "ecd_sg", "spp_kpa", "mse_mj_m3"]
        self.model = None
        self.is_trained = False

    def extract_features(self, telemetry_records: List[Dict[str, float]]) -> np.ndarray:
        features = []
        for rec in telemetry_records:
            wob = rec.get("wob", 12.0)
            rpm = rec.get("rpm", 110.0)
            torque = rec.get("torque", 15.0)
            rop = rec.get("rop_mhr", 18.0)
            ecd = rec.get("ecd_sg", 1.25)
            spp = rec.get("spp_kpa", 18000.0)
            mse = rec.get("mse_mj_m3", (wob * 1000) / max(1.0, rop))
            features.append([wob, rpm, torque, rop, ecd, spp, mse])
        return np.array(features)

    def train_baseline_model(self, synthetic_samples: int = 200) -> Dict[str, Any]:
        np.random.seed(42)
        X_normal = np.random.normal(loc=[12.0, 110.0, 15.0, 18.0, 1.25, 18000.0, 650.0], scale=[2.0, 10.0, 2.0, 3.0, 0.05, 1000.0, 50.0], size=(synthetic_samples // 2, 7))
        y_normal = np.zeros(synthetic_samples // 2)

        X_kick = np.random.normal(loc=[8.0, 130.0, 22.0, 28.0, 1.10, 14000.0, 400.0], scale=[1.5, 12.0, 3.0, 4.0, 0.04, 1200.0, 40.0], size=(synthetic_samples // 4, 7))
        y_kick = np.ones(synthetic_samples // 4)

        X_stuck = np.random.normal(loc=[18.0, 80.0, 32.0, 5.0, 1.35, 24000.0, 1200.0], scale=[2.5, 15.0, 4.0, 2.0, 0.06, 1500.0, 100.0], size=(synthetic_samples // 4, 7))
        y_stuck = np.ones(synthetic_samples // 4) * 2

        X = np.vstack([X_normal, X_kick, X_stuck])
        y = np.hstack([y_normal, y_kick, y_stuck])

        base_rf = RandomForestClassifier(n_estimators=30, random_state=42)
        calibrated = CalibratedClassifierCV(estimator=base_rf, method="sigmoid", cv=3)
        calibrated.fit(X, y)

        self.model = calibrated
        self.is_trained = True

        acc = float(calibrated.score(X, y))
        model_bytes = pickle.dumps(calibrated)
        model_b64 = base64.b64encode(model_bytes).decode("utf-8")

        return {
            "model_name": "NamowellHazardClassifier",
            "version": "1.0.0",
            "accuracy": round(acc, 4),
            "sample_count": synthetic_samples,
            "features": self.feature_names,
            "model_b64": model_b64
        }

    def predict_hazard(self, input_features: Dict[str, float]) -> Dict[str, Any]:
        if not self.is_trained or self.model is None:
            self.train_baseline_model()

        row = np.array([[
            input_features.get("wob", 12.0),
            input_features.get("rpm", 110.0),
            input_features.get("torque", 15.0),
            input_features.get("rop_mhr", 18.0),
            input_features.get("ecd_sg", 1.25),
            input_features.get("spp_kpa", 18000.0),
            input_features.get("mse_mj_m3", 650.0)
        ]])

        probs = self.model.predict_proba(row)[0]
        class_names = ["NORMAL", "KICK_RISK", "STUCK_PIPE_RISK"]
        pred_idx = int(np.argmax(probs))
        pred_class = class_names[pred_idx]
        calibrated_prob = float(probs[pred_idx])

        explainability = []
        base_values = [12.0, 110.0, 15.0, 18.0, 1.25, 18000.0, 650.0]
        current_values = row[0]
        for i, fname in enumerate(self.feature_names):
            diff = current_values[i] - base_values[i]
            impact = round(diff * 0.05, 3)
            explainability.append({
                "feature": fname,
                "value": float(current_values[i]),
                "baseline": base_values[i],
                "contribution": impact
            })

        explainability.sort(key=lambda x: abs(x["contribution"]), reverse=True)

        return {
            "predicted_hazard": pred_class,
            "calibrated_probability": round(calibrated_prob, 4),
            "hazard_probabilities": {class_names[i]: round(float(p), 4) for i, p in enumerate(probs)},
            "explainability": explainability[:4]
        }

ml_pipeline = MLTrainingPipeline()
