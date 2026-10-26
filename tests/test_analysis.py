"""Regression tests for the reproducible SMT analysis."""

# pylint: disable=duplicate-code

from __future__ import annotations

import numpy as np

from smt_changeover.analysis import (
    CLASSIFICATION_TARGET,
    REGRESSION_TARGET,
    VALID_RANGES,
    clean_data,
    read_raw_data,
    temporal_split,
    train_and_evaluate,
)


def test_cleaning_contract() -> None:
    """Cleaning must preserve valid cases and enforce the documented contract."""
    raw = read_raw_data()
    clean, audit, suspicious, quality = clean_data(raw)

    assert len(raw) == 2057
    assert len(clean) == 2043
    assert int(raw.duplicated().sum()) == 14
    assert not audit.empty
    assert len(suspicious) == 58
    assert quality.loc["experiencia_operador_meses", "Ausentes"] == 124
    assert clean["linha_smt"].isin(["SMT1", "SMT2", "SMT3"]).all()
    assert clean["muda_familia"].isin(["Sim", "Não"]).all()
    assert clean["turno"].isin(["Manhã", "Tarde", "Noite"]).all()
    assert clean[CLASSIFICATION_TARGET].eq(
        clean[REGRESSION_TARGET].gt(42).astype(int)
    ).all()

    for column, (lower, upper) in VALID_RANGES.items():
        observed = clean[column].dropna()
        assert observed.between(lower, upper).all()


def test_temporal_split_keeps_periods_ordered() -> None:
    """The final test must contain only dates after validation."""
    clean, _, _, _ = clean_data(read_raw_data())
    split, train_end, validation_end = temporal_split(clean)

    assert split.value_counts().to_dict() == {
        "treino": 1236,
        "validacao": 404,
        "teste": 403,
    }
    assert train_end.strftime("%Y-%m-%d") == "2026-05-27"
    assert validation_end.strftime("%Y-%m-%d") == "2026-07-15"
    assert clean.loc[split.eq("treino"), "data_operacao"].max() <= train_end
    assert clean.loc[split.eq("teste"), "data_operacao"].min() > validation_end


def test_selected_models_beat_simple_references() -> None:
    """Selected trees must add measurable value on the reserved test."""
    clean, _, _, _ = clean_data(read_raw_data())
    split, _, _ = temporal_split(clean)
    results = train_and_evaluate(clean, split)

    regression = results["regression_test"].set_index("Modelo")
    best_regression = results["best_regression_name"]
    assert regression.loc[best_regression, "MAE"] < regression.loc[
        "Referência mediana", "MAE"
    ]
    assert np.isclose(regression.loc[best_regression, "MAE"], 2.655604, atol=1e-5)

    classification = results["classification_test"].set_index("Modelo")
    best_classifier = results["best_classification_name"]
    assert classification.loc[best_classifier, "Recall"] > 0.85
    assert classification.loc[best_classifier, "VP"] == 89
    assert classification.loc[best_classifier, "FN"] == 13
    assert classification.loc[best_classifier, "FP"] == 31
