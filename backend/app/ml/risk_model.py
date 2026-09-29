from sqlalchemy import text
import json
import pickle
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from pathlib import Path
import os
from typing import Dict, List, Optional, Tuple

import lightgbm as lgb
import numpy as np
import pandas as pd
import shap
from sklearn.metrics import roc_auc_score, accuracy_score, precision_score, recall_score, f1_score
from sklearn.model_selection import train_test_split

from app.analytics.kpis import calculate_all_kpis
from app.db.session import get_db_context


MODEL_DIR = Path(os.environ.get("MODEL_PATH", Path(__file__).resolve().parents[2] / "models"))
MODEL_DIR.mkdir(exist_ok=True, parents=True)

MODEL_PATH = MODEL_DIR / "risk_model.txt"
SCALER_PATH = MODEL_DIR / "scaler.pkl"
METRICS_PATH = MODEL_DIR / "model_metrics.json"
FEATURE_NAMES_PATH = MODEL_DIR / "feature_names.json"


@dataclass
class RiskFactors:
    financial_risk: float
    delivery_risk: float
    operational_risk: float
    client_risk: float
    data_quality_risk: float
    composite_score: float
    risk_level: str


@dataclass
class ModelMetrics:
    auc: float
    accuracy: float
    precision: float
    recall: float
    f1: float
    feature_importance: Dict[str, float]
    n_train: int
    n_test: int


DEFAULT_RISK_WEIGHTS = {
    "financial": 0.3,
    "delivery": 0.25,
    "operational": 0.2,
    "client": 0.15,
    "data_quality": 0.1,
}


def load_risk_weights() -> Dict[str, float]:
    """Baseline risk-component weights.

    Overridable via the RISK_MODEL_WEIGHTS env var (JSON object mapping each
    component to a weight). Falls back to DEFAULT_RISK_WEIGHTS on any missing
    or invalid value; custom weights are normalized to sum to 1.
    """
    try:
        from app.core.config import get_settings
        raw = json.loads(get_settings().risk_model_weights)
        weights = {k: float(raw[k]) for k in DEFAULT_RISK_WEIGHTS if k in raw}
        if not weights or sum(weights.values()) <= 0:
            return dict(DEFAULT_RISK_WEIGHTS)
        total = sum(weights.values())
        return {k: v / total for k, v in weights.items()}
    except Exception:
        return dict(DEFAULT_RISK_WEIGHTS)


def extract_features(db, engagement_id: str) -> Dict[str, float]:
    kpis = calculate_all_kpis(db, engagement_id)

    fin = kpis["financial"]
    deliv = kpis["delivery"]
    ops = kpis["operational"]
    client = kpis["client"]

    margin_pct = float(fin["margin_pct"])
    budget_var = float(fin["budget_variance_pct"])
    revenue = float(fin["revenue"])

    schedule_var = deliv["schedule_variance_days"]
    avg_critical_delay = float(deliv["avg_critical_path_delay_days"])

    ticket_total = ops["ticket_backlog"]["total"]
    ticket_high = ops["ticket_backlog"]["high_priority_open"]
    ticket_critical = ops["ticket_backlog"]["critical_open"]
    sla_breach_rate = float(ops["sla_breach_rate_pct"])
    sla_breaches = ops["sla_breaches"]
    cr_count = ops["change_request_count"]
    cr_approval_rate = float(ops["change_request_approval_rate_pct"])
    cr_cost = float(ops["change_request_cost_impact"])
    util = float(ops["utilization"]["avg_utilization"])
    overtime_pct = float(ops["utilization"]["overtime_pct"])

    sat_overall = float(client["overall_satisfaction"])
    sat_trend = 1 if client.get("trend") == "declining" else 0

    features = {
        "margin_pct": margin_pct,
        "budget_variance_pct": budget_var,
        "revenue_log": np.log1p(revenue) if revenue > 0 else 0,
        "schedule_variance_days": schedule_var,
        "avg_critical_delay_days": avg_critical_delay,
        "ticket_total": ticket_total,
        "ticket_high_priority": ticket_high,
        "ticket_critical": ticket_critical,
        "sla_breach_rate_pct": sla_breach_rate,
        "sla_breach_count": sla_breaches,
        "change_request_count": cr_count,
        "change_request_approval_rate": cr_approval_rate,
        "change_request_cost_impact": cr_cost,
        "utilization_pct": util,
        "overtime_pct": overtime_pct,
        "client_satisfaction": sat_overall,
        "client_satisfaction_declining": sat_trend,
    }

    return features


def generate_training_labels(db) -> Tuple[pd.DataFrame, pd.Series]:
    engagements = db.execute(
        text("SELECT id FROM engagements WHERE status IN ('completed', 'cancelled')")
    ).fetchall()

    if not engagements:
        engagements = db.execute(text("SELECT id FROM engagements LIMIT 30")).fetchall()

    features_list = []
    labels = []

    for (eng_id,) in engagements:
        try:
            feats = extract_features(db, eng_id)
            features_list.append(feats)

            margin = feats["margin_pct"]
            schedule_var = feats["schedule_variance_days"]
            sla_breach = feats["sla_breach_rate_pct"]
            sat = feats["client_satisfaction"]
            budget_var = feats["budget_variance_pct"]

            risk_score = 0
            if margin < 10: risk_score += 3
            elif margin < 20: risk_score += 2
            elif margin < 30: risk_score += 1

            if schedule_var > 30: risk_score += 2
            elif schedule_var > 14: risk_score += 1

            if sla_breach > 20: risk_score += 2
            elif sla_breach > 10: risk_score += 1

            if sat < 5: risk_score += 3
            elif sat < 6.5: risk_score += 2
            elif sat < 7.5: risk_score += 1

            if budget_var > 25: risk_score += 2
            elif budget_var > 15: risk_score += 1

            label = 1 if risk_score >= 4 else 0
            labels.append(label)

        except Exception:
            continue

    df = pd.DataFrame(features_list)
    return df, pd.Series(labels)


def train_model(db) -> Tuple[lgb.LGBMClassifier, ModelMetrics]:
    X, y = generate_training_labels(db)

    if len(X) < 10:
        raise ValueError("Insufficient training data")

    feature_names = X.columns.tolist()

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.3, random_state=42, stratify=y
    )

    model = lgb.LGBMClassifier(
        n_estimators=200,
        max_depth=5,
        learning_rate=0.05,
        num_leaves=31,
        min_child_samples=5,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        verbosity=-1,
        class_weight="balanced",
    )

    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    y_pred_proba = model.predict_proba(X_test)[:, 1]

    metrics = ModelMetrics(
        auc=roc_auc_score(y_test, y_pred_proba),
        accuracy=accuracy_score(y_test, y_pred),
        precision=precision_score(y_test, y_pred, zero_division=0),
        recall=recall_score(y_test, y_pred, zero_division=0),
        f1=f1_score(y_test, y_pred, zero_division=0),
        feature_importance=dict(zip(feature_names, model.feature_importances_.tolist())),
        n_train=len(X_train),
        n_test=len(X_test),
    )

    model.booster_.save_model(str(MODEL_PATH))

    with open(METRICS_PATH, "w") as f:
        json.dump({
            "auc": metrics.auc,
            "accuracy": metrics.accuracy,
            "precision": metrics.precision,
            "recall": metrics.recall,
            "f1": metrics.f1,
            "feature_importance": metrics.feature_importance,
            "n_train": len(X_train),
            "n_test": len(X_test),
        }, f, indent=2)

    with open(FEATURE_NAMES_PATH, "w") as f:
        json.dump(feature_names, f)

    return model, metrics


def load_model() -> Optional[lgb.LGBMClassifier]:
    if not MODEL_PATH.exists():
        return None

    model = lgb.Booster(model_file=str(MODEL_PATH))
    return model


def predict_risk(db, engagement_id: str, model: Optional[lgb.Booster] = None) -> RiskFactors:
    features = extract_features(db, engagement_id)

    if model is None:
        model = load_model()

    if model is not None:
        with open(FEATURE_NAMES_PATH) as f:
            feature_names = json.load(f)

        X = pd.DataFrame([features])[feature_names]
        prob = model.predict(X, num_iteration=model.best_iteration)[0]
        ml_score = float(prob)
    else:
        ml_score = 0.5

    fin = features["margin_pct"]
    budget_var = features["budget_variance_pct"]
    schedule_var = features["schedule_variance_days"]
    sla_breach = features["sla_breach_rate_pct"]
    sat = features["client_satisfaction"]
    ticket_critical = features["ticket_critical"]
    util = features["utilization_pct"]
    overtime = features["overtime_pct"]

    financial_risk = 0.0
    if fin < 10: financial_risk = 0.9
    elif fin < 20: financial_risk = 0.6
    elif fin < 30: financial_risk = 0.3
    if budget_var > 25: financial_risk = max(financial_risk, 0.7)
    elif budget_var > 15: financial_risk = max(financial_risk, 0.4)

    delivery_risk = 0.0
    if schedule_var > 30: delivery_risk = 0.8
    elif schedule_var > 14: delivery_risk = 0.5
    elif schedule_var > 7: delivery_risk = 0.2

    operational_risk = 0.0
    if sla_breach > 20: operational_risk = 0.8
    elif sla_breach > 10: operational_risk = 0.5
    if ticket_critical > 5: operational_risk = max(operational_risk, 0.9)
    elif ticket_critical > 2: operational_risk = max(operational_risk, 0.6)

    client_risk = 0.0
    if sat < 5: client_risk = 0.9
    elif sat < 6.5: client_risk = 0.6
    elif sat < 7.5: client_risk = 0.3
    if features["client_satisfaction_declining"]: client_risk = max(client_risk, 0.7)

    data_quality_risk = 0.0
    if util < 40 or util > 95: data_quality_risk = 0.5
    if overtime > 20: data_quality_risk = max(data_quality_risk, 0.6)

    weights = load_risk_weights()
    composite = (
        weights["financial"] * financial_risk +
        weights["delivery"] * delivery_risk +
        weights["operational"] * operational_risk +
        weights["client"] * client_risk +
        weights["data_quality"] * data_quality_risk
    )

    if model is not None:
        composite = 0.6 * composite + 0.4 * ml_score

    if composite >= 0.7:
        level = "critical"
    elif composite >= 0.5:
        level = "high"
    elif composite >= 0.3:
        level = "medium"
    else:
        level = "low"

    return RiskFactors(
        financial_risk=financial_risk,
        delivery_risk=delivery_risk,
        operational_risk=operational_risk,
        client_risk=client_risk,
        data_quality_risk=data_quality_risk,
        composite_score=round(composite, 3),
        risk_level=level,
    )


def get_shap_explanation(db, engagement_id: str, model: Optional[lgb.Booster] = None) -> Dict:
    features = extract_features(db, engagement_id)

    if model is None:
        model = load_model()

    if model is None:
        return {"error": "Model not trained"}

    with open(FEATURE_NAMES_PATH) as f:
        feature_names = json.load(f)

    X = pd.DataFrame([features])[feature_names]

    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X)

    if isinstance(shap_values, list):
        shap_values = shap_values[1]

    feature_contributions = []
    for i, name in enumerate(feature_names):
        feature_contributions.append({
            "feature": name,
            "value": float(X.iloc[0, i]),
            "shap_value": float(shap_values[0, i]),
        })

    feature_contributions.sort(key=lambda x: abs(x["shap_value"]), reverse=True)

    return {
        "engagement_id": engagement_id,
        "base_value": float(explainer.expected_value[1] if isinstance(explainer.expected_value, list) else explainer.expected_value),
        "contributions": feature_contributions[:10],
    }


def get_model_metrics() -> Dict:
    if not METRICS_PATH.exists():
        return {"error": "Model not trained"}

    with open(METRICS_PATH) as f:
        return json.load(f)


def retrain_model() -> ModelMetrics:
    with get_db_context() as db:
        model, metrics = train_model(db)
    return metrics
