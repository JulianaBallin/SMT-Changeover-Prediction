"""Clean the SMT dataset, train models, and build the project charts."""

# pylint: disable=too-many-arguments,too-many-positional-arguments
# pylint: disable=too-many-locals,too-many-statements

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier, DummyRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    confusion_matrix,
    f1_score,
    mean_absolute_error,
    mean_squared_error,
    precision_score,
    r2_score,
    recall_score,
    roc_auc_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor


PROJECT_DIR = Path(__file__).resolve().parents[2]
DATASET_PATH = PROJECT_DIR / "dataset" / "raw" / "N4_TrocaSMT.csv"
PROCESSED_DATA_DIR = PROJECT_DIR / "dataset" / "processed"
CHART_DIR = PROJECT_DIR / "outputs" / "charts"
METRICS_DIR = PROJECT_DIR / "outputs" / "metrics"

NUMERIC_FEATURES = [
    "alimentadores_a_trocar",
    "kit_preparado_pct",
    "experiencia_operador_meses",
    "componentes_novos",
    "tamanho_lote_placas",
]
CATEGORICAL_FEATURES = ["linha_smt", "muda_familia", "turno"]
FEATURES = NUMERIC_FEATURES + CATEGORICAL_FEATURES
REGRESSION_TARGET = "tempo_troca_min"
CLASSIFICATION_TARGET = "troca_demorada"
LEAKAGE_COLUMNS = ["atraso_no_plano_min"]

VALID_RANGES = {
    "alimentadores_a_trocar": (0, 80),
    "kit_preparado_pct": (0, 100),
    "experiencia_operador_meses": (0, 400),
    "componentes_novos": (0, 30),
    "tamanho_lote_placas": (1, 5000),
}

INK = "#102A33"
TEAL = "#006D77"
GREEN = "#18B889"
CORAL = "#FF6448"
YELLOW = "#FFC43D"
BLUE = "#36A9E1"
CREAM = "#FFF8E8"
MINT = "#CDEDE3"
LIGHT_BLUE = "#C7E9F8"
GRAY = "#64747A"
LIGHT_GRAY = "#E9EFEE"


def read_raw_data(path: Path = DATASET_PATH) -> pd.DataFrame:
    """Read every original field as text for an auditable cleaning process."""
    return pd.read_csv(path, dtype=str, keep_default_na=False)


def _append_audit(
    rows: list[dict[str, Any]], step: str, column: str, quantity: int
) -> None:
    """Append one cleaning audit record."""
    rows.append({"Etapa": step, "Coluna": column, "Quantidade": int(quantity)})


def clean_data(
    raw: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Apply the course cleaning contract without imputing model inputs."""
    data = raw.copy()
    audit: list[dict[str, Any]] = []

    duplicate_count = int(data.duplicated().sum())
    data = data.drop_duplicates().reset_index(drop=True)
    original = data.copy()
    _append_audit(audit, "Duplicatas exatas", "(linha)", duplicate_count)

    spaces = data[CATEGORICAL_FEATURES].apply(
        lambda series: series.ne(series.str.strip())
    ).sum()
    for column in CATEGORICAL_FEATURES:
        data[column] = data[column].str.strip()
        _append_audit(audit, "Espaços nas bordas", column, int(spaces[column]))

    corrections = {
        "linha_smt": {"smt1": "SMT1", "smt2": "SMT2", "smt3": "SMT3"},
        "muda_familia": {"não": "Não", "sim": "Sim"},
        "turno": {
            "manha": "Manhã",
            "manhã": "Manhã",
            "tarde": "Tarde",
            "noite": "Noite",
        },
    }
    for column in CATEGORICAL_FEATURES:
        before = data[column].copy()
        data[column] = data[column].str.lower().replace(corrections[column])
        _append_audit(
            audit, "Grafias padronizadas", column, int(before.ne(data[column]).sum())
        )

    missing_markers = ["", "nan", "NaN", "NA", "na", "null"]
    textual_missing = data.isin(missing_markers).sum()
    data = data.replace(missing_markers, np.nan)
    for column in data.columns:
        _append_audit(
            audit, "Vazios reconhecidos", column, int(textual_missing[column])
        )

    comma_counts = data[NUMERIC_FEATURES].apply(
        lambda series: series.str.contains(",", regex=False, na=False)
    ).sum()
    for column in NUMERIC_FEATURES:
        data[column] = pd.to_numeric(
            data[column].str.replace(",", ".", regex=False), errors="raise"
        )
        _append_audit(audit, "Vírgulas decimais", column, int(comma_counts[column]))

    code_counts = data[NUMERIC_FEATURES].eq(9999).sum()
    data[NUMERIC_FEATURES] = data[NUMERIC_FEATURES].replace(9999, np.nan)
    for column in NUMERIC_FEATURES:
        _append_audit(audit, "Código 9999", column, int(code_counts[column]))

    date_text = data["data_operacao"].str.strip()
    brazilian_dates = date_text.str.contains("/", regex=False, na=False)
    dates_iso = pd.to_datetime(date_text, format="%Y-%m-%d", errors="coerce")
    dates_br = pd.to_datetime(date_text, format="%d/%m/%Y", errors="coerce")
    data["data_operacao"] = dates_iso.fillna(dates_br)
    _append_audit(
        audit, "Datas brasileiras", "data_operacao", int(brazilian_dates.sum())
    )
    if data["data_operacao"].isna().any():
        raise ValueError("Há datas de operação não reconhecidas.")

    suspicious_rows: list[dict[str, Any]] = []
    for column, (lower, upper) in VALID_RANGES.items():
        invalid = data[column].notna() & ~data[column].between(lower, upper)
        for index in data.index[invalid]:
            suspicious_rows.append(
                {
                    "id_registro": data.at[index, "id_registro"],
                    "coluna": column,
                    "valor_original": original.at[index, column],
                    "valor_convertido": data.at[index, column],
                }
            )
        _append_audit(
            audit, "Fora do critério", column, int(invalid.sum())
        )
        data.loc[invalid, column] = np.nan

    for column in [REGRESSION_TARGET, CLASSIFICATION_TARGET, *LEAKAGE_COLUMNS]:
        data[column] = pd.to_numeric(data[column], errors="raise")

    expected_class = data[REGRESSION_TARGET].gt(42).astype(int)
    if not data[CLASSIFICATION_TARGET].eq(expected_class).all():
        raise ValueError("A classe não corresponde à regra de 42 minutos.")

    quality = pd.DataFrame(
        {
            "Ausentes": data[FEATURES].isna().sum(),
            "Ausentes (%)": (100 * data[FEATURES].isna().mean()).round(2),
        }
    )
    audit_frame = pd.DataFrame(audit)
    suspicious = pd.DataFrame(suspicious_rows)
    return data, audit_frame, suspicious, quality


def temporal_split(data: pd.DataFrame) -> tuple[pd.Series, pd.Timestamp, pd.Timestamp]:
    """Reserve recent complete days for validation and test."""
    days = data["data_operacao"]
    train_end = days.quantile(0.60).normalize()
    validation_end = days.quantile(0.80).normalize()
    split = pd.Series(
        np.select(
            [days.le(train_end), days.le(validation_end)],
            ["treino", "validacao"],
            default="teste",
        ),
        index=data.index,
        name="divisao",
    )
    return split, train_end, validation_end


def make_preprocessor() -> ColumnTransformer:
    """Build preprocessing fitted only on each training partition."""
    numeric = Pipeline([("imputer", SimpleImputer(strategy="median"))])
    categorical = Pipeline(
        [
            ("imputer", SimpleImputer(strategy="most_frequent")),
            (
                "encoder",
                OneHotEncoder(handle_unknown="ignore", sparse_output=False),
            ),
        ]
    )
    return ColumnTransformer(
        [
            ("numericas", numeric, NUMERIC_FEATURES),
            ("categoricas", categorical, CATEGORICAL_FEATURES),
        ],
        verbose_feature_names_out=False,
    )


def make_pipeline(model: Any) -> Pipeline:
    """Join preprocessing and one estimator."""
    return Pipeline([("preparo", make_preprocessor()), ("modelo", model)])


def _regression_metrics(observed: pd.Series, predicted: np.ndarray) -> dict[str, float]:
    """Calculate the regression measures used by the course."""
    return {
        "MAE": float(mean_absolute_error(observed, predicted)),
        "RMSE": float(mean_squared_error(observed, predicted) ** 0.5),
        "R2": float(r2_score(observed, predicted)),
    }


def _classification_metrics(
    observed: pd.Series, predicted: np.ndarray, probability: np.ndarray
) -> dict[str, Any]:
    """Calculate classification measures and the confusion matrix."""
    true_negative, false_positive, false_negative, true_positive = confusion_matrix(
        observed, predicted, labels=[0, 1]
    ).ravel()
    return {
        "Acurácia": float(accuracy_score(observed, predicted)),
        "Precisão": float(precision_score(observed, predicted, zero_division=0)),
        "Recall": float(recall_score(observed, predicted, zero_division=0)),
        "F1": float(f1_score(observed, predicted, zero_division=0)),
        "AP": float(average_precision_score(observed, probability)),
        "AUC_ROC": float(roc_auc_score(observed, probability)),
        "VN": int(true_negative),
        "FP": int(false_positive),
        "FN": int(false_negative),
        "VP": int(true_positive),
    }


def train_and_evaluate(data: pd.DataFrame, split: pd.Series) -> dict[str, Any]:
    """Select model depth on validation and evaluate once on the final test."""
    x_values = data[FEATURES]
    y_regression = data[REGRESSION_TARGET]
    y_classification = data[CLASSIFICATION_TARGET].astype(int)
    train = split.eq("treino")
    validation = split.eq("validacao")
    train_validation = split.isin(["treino", "validacao"])
    test = split.eq("teste")

    regression_candidates: dict[str, Any] = {
        "Referência mediana": DummyRegressor(strategy="median"),
        "Regressão linear": LinearRegression(),
    }
    for depth in range(2, 11):
        regression_candidates[f"Árvore prof. {depth}"] = DecisionTreeRegressor(
            max_depth=depth, min_samples_leaf=10, random_state=42
        )

    regression_validation_rows = []
    for name, estimator in regression_candidates.items():
        pipeline = make_pipeline(estimator)
        pipeline.fit(x_values.loc[train], y_regression.loc[train])
        predicted = pipeline.predict(x_values.loc[validation])
        regression_validation_rows.append(
            {"Modelo": name, **_regression_metrics(y_regression.loc[validation], predicted)}
        )
    regression_validation = pd.DataFrame(regression_validation_rows).sort_values("MAE")
    tree_rows = regression_validation["Modelo"].str.startswith("Árvore")
    best_regression_name = regression_validation.loc[tree_rows].iloc[0]["Modelo"]

    selected_regressors = {
        "Referência mediana": DummyRegressor(strategy="median"),
        "Regressão linear": LinearRegression(),
        best_regression_name: regression_candidates[best_regression_name],
    }
    regression_test_rows = []
    fitted_regressors = {}
    regression_predictions = {}
    for name, estimator in selected_regressors.items():
        pipeline = make_pipeline(estimator)
        pipeline.fit(x_values.loc[train_validation], y_regression.loc[train_validation])
        predicted = pipeline.predict(x_values.loc[test])
        fitted_regressors[name] = pipeline
        regression_predictions[name] = predicted
        regression_test_rows.append(
            {"Modelo": name, **_regression_metrics(y_regression.loc[test], predicted)}
        )
    regression_test = pd.DataFrame(regression_test_rows).sort_values("MAE")

    classification_candidates: dict[str, Any] = {
        "Referência maioria": DummyClassifier(strategy="most_frequent"),
        "Regressão logística": LogisticRegression(
            max_iter=2000, class_weight="balanced", random_state=42
        ),
    }
    for depth in range(2, 11):
        classification_candidates[f"Árvore prof. {depth}"] = DecisionTreeClassifier(
            max_depth=depth,
            min_samples_leaf=10,
            class_weight="balanced",
            random_state=42,
        )

    classification_validation_rows = []
    for name, estimator in classification_candidates.items():
        pipeline = make_pipeline(estimator)
        pipeline.fit(x_values.loc[train], y_classification.loc[train])
        predicted = pipeline.predict(x_values.loc[validation])
        probability = pipeline.predict_proba(x_values.loc[validation])[:, 1]
        classification_validation_rows.append(
            {
                "Modelo": name,
                **_classification_metrics(
                    y_classification.loc[validation], predicted, probability
                ),
            }
        )
    classification_validation = pd.DataFrame(
        classification_validation_rows
    ).sort_values(["F1", "Recall"], ascending=False)
    classifier_tree_rows = classification_validation["Modelo"].str.startswith("Árvore")
    best_classification_name = classification_validation.loc[
        classifier_tree_rows
    ].iloc[0]["Modelo"]

    selected_classifiers = {
        "Referência maioria": DummyClassifier(strategy="most_frequent"),
        "Regressão logística": LogisticRegression(
            max_iter=2000, class_weight="balanced", random_state=42
        ),
        best_classification_name: classification_candidates[best_classification_name],
    }
    classification_test_rows = []
    fitted_classifiers = {}
    classification_predictions = {}
    classification_probabilities = {}
    for name, estimator in selected_classifiers.items():
        pipeline = make_pipeline(estimator)
        pipeline.fit(
            x_values.loc[train_validation], y_classification.loc[train_validation]
        )
        predicted = pipeline.predict(x_values.loc[test])
        probability = pipeline.predict_proba(x_values.loc[test])[:, 1]
        fitted_classifiers[name] = pipeline
        classification_predictions[name] = predicted
        classification_probabilities[name] = probability
        classification_test_rows.append(
            {
                "Modelo": name,
                **_classification_metrics(
                    y_classification.loc[test], predicted, probability
                ),
            }
        )
    classification_test = pd.DataFrame(classification_test_rows).sort_values(
        ["F1", "Recall"], ascending=False
    )

    best_regression = fitted_regressors[best_regression_name]
    regression_feature_names = best_regression.named_steps[
        "preparo"
    ].get_feature_names_out()
    regression_importance = pd.DataFrame(
        {
            "Característica": regression_feature_names,
            "Importância": best_regression.named_steps["modelo"].feature_importances_,
        }
    ).sort_values("Importância", ascending=False)

    best_classifier = fitted_classifiers[best_classification_name]
    classification_feature_names = best_classifier.named_steps[
        "preparo"
    ].get_feature_names_out()
    classification_importance = pd.DataFrame(
        {
            "Característica": classification_feature_names,
            "Importância": best_classifier.named_steps["modelo"].feature_importances_,
        }
    ).sort_values("Importância", ascending=False)

    return {
        "regression_validation": regression_validation,
        "regression_test": regression_test,
        "classification_validation": classification_validation,
        "classification_test": classification_test,
        "best_regression_name": best_regression_name,
        "best_classification_name": best_classification_name,
        "fitted_regressors": fitted_regressors,
        "fitted_classifiers": fitted_classifiers,
        "regression_predictions": regression_predictions,
        "classification_predictions": classification_predictions,
        "classification_probabilities": classification_probabilities,
        "regression_importance": regression_importance,
        "classification_importance": classification_importance,
        "test_mask": test,
    }


def _chart_style() -> None:
    """Apply the visual system shared by notebook, slides, and report."""
    sns.set_theme(style="whitegrid")
    plt.rcParams.update(
        {
            "figure.facecolor": CREAM,
            "axes.facecolor": "#FFFFFF",
            "axes.edgecolor": "#D4DEDC",
            "axes.labelcolor": INK,
            "axes.titlecolor": TEAL,
            "axes.titlesize": 15,
            "axes.titleweight": "bold",
            "font.family": "DejaVu Sans",
            "font.size": 10,
            "xtick.color": INK,
            "ytick.color": INK,
            "text.color": INK,
        }
    )


def _save_figure(figure: plt.Figure, filename: str) -> None:
    """Save a chart with consistent dimensions and padding."""
    CHART_DIR.mkdir(parents=True, exist_ok=True)
    figure.savefig(CHART_DIR / filename, dpi=180, bbox_inches="tight", facecolor=CREAM)
    plt.close(figure)


def generate_charts(
    data: pd.DataFrame,
    split: pd.Series,
    results: dict[str, Any],
    quality: pd.DataFrame,
) -> None:
    """Generate the figures consumed by all final deliverables."""
    _chart_style()
    train = data.loc[split.eq("treino")].copy()
    test = data.loc[results["test_mask"]].copy()

    figure, axis = plt.subplots(figsize=(9, 4.8))
    axis.hist(
        train[REGRESSION_TARGET],
        bins=14,
        color=GREEN,
        edgecolor="white",
        linewidth=1.2,
    )
    axis.axvline(42, color=CORAL, linestyle="--", linewidth=2.4, label="Limiar: 42 min")
    axis.set(
        title="A maioria das trocas fica abaixo de 42 minutos",
        xlabel="Tempo de troca (min)",
        ylabel="Trocas no treino",
    )
    axis.legend(frameon=False)
    _save_figure(figure, "01_distribuicao_tempo.png")

    figure, axes = plt.subplots(1, 2, figsize=(11.2, 4.6))
    sns.regplot(
        data=train,
        x="kit_preparado_pct",
        y=REGRESSION_TARGET,
        scatter_kws={"alpha": 0.38, "s": 24, "color": BLUE},
        line_kws={"color": CORAL, "linewidth": 2.2},
        ax=axes[0],
    )
    axes[0].set(
        title="Kit mais preparado, troca mais curta",
        xlabel="Kit preparado (%)",
        ylabel="Tempo de troca (min)",
    )
    sns.regplot(
        data=train,
        x="alimentadores_a_trocar",
        y=REGRESSION_TARGET,
        scatter_kws={"alpha": 0.38, "s": 24, "color": GREEN},
        line_kws={"color": CORAL, "linewidth": 2.2},
        ax=axes[1],
    )
    axes[1].set(
        title="Mais alimentadores, troca mais longa",
        xlabel="Alimentadores a trocar",
        ylabel="Tempo de troca (min)",
    )
    figure.tight_layout()
    _save_figure(figure, "02_relacoes_principais.png")

    kit_bins = pd.cut(
        train["kit_preparado_pct"],
        bins=[0, 20, 40, 60, 80, 100],
        include_lowest=True,
        labels=["0 a 20", "21 a 40", "41 a 60", "61 a 80", "81 a 100"],
    )
    rates = (
        train.assign(faixa_kit=kit_bins)
        .groupby(["faixa_kit", "muda_familia"], observed=True)[CLASSIFICATION_TARGET]
        .agg(["mean", "size"])
        .reset_index()
    )
    rates["mean"] *= 100
    figure, axis = plt.subplots(figsize=(9.4, 4.9))
    sns.barplot(
        data=rates,
        x="faixa_kit",
        y="mean",
        hue="muda_familia",
        palette={"Não": BLUE, "Sim": CORAL},
        ax=axis,
    )
    axis.set(
        title="Preparar o kit reduz o risco em ambos os tipos de troca",
        xlabel="Kit preparado (%)",
        ylabel="Trocas acima de 42 min (%)",
    )
    axis.legend(title="Muda de família?", frameon=False)
    _save_figure(figure, "03_risco_por_kit_e_familia.png")

    regression_test = results["regression_test"].copy()
    regression_test["Melhora vs referência (%)"] = 100 * (
        regression_test.loc[
            regression_test["Modelo"].eq("Referência mediana"), "MAE"
        ].iloc[0]
        - regression_test["MAE"]
    ) / regression_test.loc[
        regression_test["Modelo"].eq("Referência mediana"), "MAE"
    ].iloc[0]
    figure, axis = plt.subplots(figsize=(9, 4.6))
    ordered = regression_test.sort_values("MAE", ascending=False)
    colors = [LIGHT_BLUE, YELLOW, GREEN]
    bars = axis.barh(ordered["Modelo"], ordered["MAE"], color=colors[: len(ordered)])
    axis.bar_label(bars, fmt="%.2f min", padding=5, color=INK, fontweight="bold")
    axis.set(
        title="A árvore reduz o erro médio para 2,66 minutos",
        xlabel="MAE no teste (menor é melhor)",
        ylabel="",
    )
    axis.set_xlim(0, ordered["MAE"].max() * 1.2)
    _save_figure(figure, "04_comparacao_regressao.png")

    best_regression_name = results["best_regression_name"]
    regression_predicted = results["regression_predictions"][best_regression_name]
    figure, axis = plt.subplots(figsize=(6.8, 6.0))
    axis.scatter(
        test[REGRESSION_TARGET],
        regression_predicted,
        color=BLUE,
        alpha=0.62,
        s=32,
        edgecolor="white",
        linewidth=0.4,
    )
    lower = min(test[REGRESSION_TARGET].min(), regression_predicted.min())
    upper = max(test[REGRESSION_TARGET].max(), regression_predicted.max())
    axis.plot([lower, upper], [lower, upper], color=CORAL, linestyle="--", linewidth=2)
    axis.set(
        title="Previsto e observado ficam próximos",
        xlabel="Tempo observado (min)",
        ylabel="Tempo previsto (min)",
        xlim=(lower, upper),
        ylim=(lower, upper),
    )
    _save_figure(figure, "05_previsto_vs_observado.png")

    best_classification_name = results["best_classification_name"]
    classification_predicted = results["classification_predictions"][
        best_classification_name
    ]
    matrix = confusion_matrix(
        test[CLASSIFICATION_TARGET].astype(int), classification_predicted, labels=[0, 1]
    )
    figure, axis = plt.subplots(figsize=(6.6, 5.5))
    sns.heatmap(
        matrix,
        annot=True,
        fmt="d",
        cmap=sns.light_palette(TEAL, as_cmap=True),
        cbar=False,
        linewidths=3,
        linecolor=CREAM,
        annot_kws={"size": 18, "weight": "bold"},
        ax=axis,
    )
    axis.set_xticklabels(["Até 42", "Acima de 42"])
    axis.set_yticklabels(["Até 42", "Acima de 42"], rotation=0)
    axis.set(
        title="A árvore encontra 89 de 102 trocas demoradas",
        xlabel="Previsão",
        ylabel="Resultado real",
    )
    _save_figure(figure, "06_matriz_confusao.png")

    importance = results["regression_importance"].head(8).sort_values("Importância")
    friendly_names = {
        "kit_preparado_pct": "Kit preparado",
        "alimentadores_a_trocar": "Alimentadores",
        "experiencia_operador_meses": "Experiência",
        "componentes_novos": "Componentes novos",
        "tamanho_lote_placas": "Tamanho do lote",
        "muda_familia_Sim": "Muda de família: Sim",
        "muda_familia_Não": "Muda de família: Não",
        "linha_smt_SMT1": "Linha SMT1",
        "linha_smt_SMT2": "Linha SMT2",
        "linha_smt_SMT3": "Linha SMT3",
        "turno_Manhã": "Turno manhã",
        "turno_Tarde": "Turno tarde",
        "turno_Noite": "Turno noite",
    }
    importance["Rótulo"] = importance["Característica"].map(friendly_names).fillna(
        importance["Característica"]
    )
    figure, axis = plt.subplots(figsize=(8.4, 4.9))
    bars = axis.barh(importance["Rótulo"], importance["Importância"], color=GREEN)
    axis.bar_label(bars, fmt="%.2f", padding=4, color=INK)
    axis.set(
        title="Kit e alimentadores concentram a explicação da árvore",
        xlabel="Importância relativa",
        ylabel="",
    )
    _save_figure(figure, "07_importancia_caracteristicas.png")

    missing = quality.sort_values("Ausentes (%)")
    figure, axis = plt.subplots(figsize=(8.8, 4.8))
    bars = axis.barh(missing.index, missing["Ausentes (%)"], color=YELLOW)
    axis.bar_label(bars, fmt="%.1f%%", padding=4, color=INK)
    axis.set(
        title="Ausências foram preservadas e tratadas no pipeline",
        xlabel="Ausentes na base limpa (%)",
        ylabel="",
    )
    axis.set_xlim(0, max(7, missing["Ausentes (%)"].max() * 1.25))
    _save_figure(figure, "08_qualidade_ausencias.png")


def _json_ready(value: Any) -> Any:
    """Convert NumPy and pandas scalar values into JSON-safe values."""
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return float(value)
    if isinstance(value, pd.Timestamp):
        return value.strftime("%Y-%m-%d")
    if isinstance(value, dict):
        return {key: _json_ready(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    return value


def save_outputs(
    data: pd.DataFrame,
    split: pd.Series,
    train_end: pd.Timestamp,
    validation_end: pd.Timestamp,
    audit: pd.DataFrame,
    suspicious: pd.DataFrame,
    quality: pd.DataFrame,
    results: dict[str, Any],
) -> dict[str, Any]:
    """Persist cleaned data, diagnostics, predictions, and a compact summary."""
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    METRICS_DIR.mkdir(parents=True, exist_ok=True)
    clean_path = PROCESSED_DATA_DIR / "N4_TrocaSMT_limpo.csv"
    clean_export = data.copy()
    clean_export["data_operacao"] = clean_export["data_operacao"].dt.strftime(
        "%Y-%m-%d"
    )
    clean_export.to_csv(clean_path, index=False, encoding="utf-8-sig")

    division_map = data[["id_registro", "data_operacao"]].copy()
    division_map["divisao"] = split
    division_map.to_csv(
        PROCESSED_DATA_DIR / "N4_divisoes.csv", index=False, encoding="utf-8-sig"
    )
    audit.to_csv(
        PROCESSED_DATA_DIR / "N4_registro_limpeza.csv",
        index=False,
        encoding="utf-8-sig",
    )
    suspicious.to_csv(
        PROCESSED_DATA_DIR / "N4_medidas_para_conferencia.csv",
        index=False,
        encoding="utf-8-sig",
    )
    quality.to_csv(PROCESSED_DATA_DIR / "N4_qualidade.csv", encoding="utf-8-sig")
    results["regression_validation"].to_csv(
        PROCESSED_DATA_DIR / "N4_regressao_validacao.csv",
        index=False,
        encoding="utf-8-sig",
    )
    results["regression_test"].to_csv(
        PROCESSED_DATA_DIR / "N4_regressao_teste.csv",
        index=False,
        encoding="utf-8-sig",
    )
    results["classification_validation"].to_csv(
        PROCESSED_DATA_DIR / "N4_classificacao_validacao.csv",
        index=False,
        encoding="utf-8-sig",
    )
    results["classification_test"].to_csv(
        PROCESSED_DATA_DIR / "N4_classificacao_teste.csv",
        index=False,
        encoding="utf-8-sig",
    )
    results["regression_importance"].to_csv(
        PROCESSED_DATA_DIR / "N4_importancia_regressao.csv",
        index=False,
        encoding="utf-8-sig",
    )

    test = results["test_mask"]
    prediction_table = data.loc[
        test,
        ["id_registro", "data_operacao", REGRESSION_TARGET, CLASSIFICATION_TARGET],
    ].copy()
    best_regression_name = results["best_regression_name"]
    best_classification_name = results["best_classification_name"]
    prediction_table["tempo_previsto_min"] = results["regression_predictions"][
        best_regression_name
    ]
    prediction_table["classe_prevista"] = results["classification_predictions"][
        best_classification_name
    ]
    prediction_table["probabilidade_demorada"] = results[
        "classification_probabilities"
    ][best_classification_name]
    prediction_table.to_csv(
        PROCESSED_DATA_DIR / "N4_previsoes_teste.csv",
        index=False,
        encoding="utf-8-sig",
    )

    regression_test = results["regression_test"].set_index("Modelo")
    classification_test = results["classification_test"].set_index("Modelo")
    reference_mae = float(regression_test.loc["Referência mediana", "MAE"])
    best_mae = float(regression_test.loc[best_regression_name, "MAE"])
    best_classification = classification_test.loc[best_classification_name]
    split_summary = (
        pd.DataFrame({"data_operacao": data["data_operacao"], "divisao": split})
        .groupby("divisao")
        .agg(
            registros=("data_operacao", "size"),
            inicio=("data_operacao", "min"),
            fim=("data_operacao", "max"),
        )
    )
    summary = {
        "project": "SMT em Tempo",
        "raw_rows": int(len(read_raw_data())),
        "clean_rows": int(len(data)),
        "exact_duplicates_removed": int(len(read_raw_data()) - len(data)),
        "date_start": data["data_operacao"].min(),
        "date_end": data["data_operacao"].max(),
        "train_end": train_end,
        "validation_end": validation_end,
        "splits": {
            index: {
                "records": int(row["registros"]),
                "start": row["inicio"],
                "end": row["fim"],
            }
            for index, row in split_summary.iterrows()
        },
        "delayed_rate": float(data[CLASSIFICATION_TARGET].mean()),
        "target_median": float(data[REGRESSION_TARGET].median()),
        "target_mean": float(data[REGRESSION_TARGET].mean()),
        "best_regression": best_regression_name,
        "test_mae": best_mae,
        "reference_mae": reference_mae,
        "mae_reduction": float((reference_mae - best_mae) / reference_mae),
        "test_r2": float(regression_test.loc[best_regression_name, "R2"]),
        "best_classifier": best_classification_name,
        "test_accuracy": float(best_classification["Acurácia"]),
        "test_precision": float(best_classification["Precisão"]),
        "test_recall": float(best_classification["Recall"]),
        "test_f1": float(best_classification["F1"]),
        "test_average_precision": float(best_classification["AP"]),
        "true_negative": int(best_classification["VN"]),
        "false_positive": int(best_classification["FP"]),
        "false_negative": int(best_classification["FN"]),
        "true_positive": int(best_classification["VP"]),
        "model_features": FEATURES,
        "excluded_after_event": LEAKAGE_COLUMNS,
    }
    summary_path = METRICS_DIR / "resumo_resultados.json"
    summary_path.write_text(
        json.dumps(_json_ready(summary), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return _json_ready(summary)


def run_analysis() -> dict[str, Any]:
    """Execute the complete reproducible analysis."""
    raw = read_raw_data()
    data, audit, suspicious, quality = clean_data(raw)
    split, train_end, validation_end = temporal_split(data)
    results = train_and_evaluate(data, split)
    generate_charts(data, split, results, quality)
    summary = save_outputs(
        data,
        split,
        train_end,
        validation_end,
        audit,
        suspicious,
        quality,
        results,
    )
    return {
        "raw": raw,
        "data": data,
        "audit": audit,
        "suspicious": suspicious,
        "quality": quality,
        "split": split,
        "results": results,
        "summary": summary,
    }


if __name__ == "__main__":
    analysis = run_analysis()
    print(json.dumps(analysis["summary"], ensure_ascii=False, indent=2))
