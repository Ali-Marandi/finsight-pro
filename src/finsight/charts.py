"""Automatic financial charts using a non-interactive Matplotlib backend."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "finsight-matplotlib"))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd


def create_dashboard(statement: pd.DataFrame, ratios: pd.DataFrame, output: str | Path) -> Path:
    target = Path(output)
    target.parent.mkdir(parents=True, exist_ok=True)
    periods = statement["period"].astype(str)
    fig, axes = plt.subplots(2, 2, figsize=(13, 8), constrained_layout=True)
    fig.suptitle("Financial performance dashboard", fontsize=17, fontweight="bold")

    axes[0, 0].plot(periods, statement["revenue"], marker="o", label="Revenue")
    axes[0, 0].plot(periods, statement["net_income"], marker="o", label="Net income")
    axes[0, 0].set_title("Growth and earnings")
    axes[0, 0].legend()

    for name in ("gross_margin", "operating_margin", "net_margin"):
        axes[0, 1].plot(periods, ratios[name] * 100, marker="o", label=name.replace("_", " ").title())
    axes[0, 1].set_title("Profitability margins")
    axes[0, 1].set_ylabel("%")
    axes[0, 1].legend()

    axes[1, 0].plot(periods, ratios["current_ratio"], marker="o", label="Current")
    axes[1, 0].plot(periods, ratios["quick_ratio"], marker="o", label="Quick")
    axes[1, 0].axhline(1, color="#c2410c", linestyle="--", linewidth=1)
    axes[1, 0].set_title("Liquidity")
    axes[1, 0].legend()

    axes[1, 1].plot(periods, ratios["debt_to_equity"], marker="o", label="Debt / equity")
    axes[1, 1].plot(periods, ratios["return_on_assets"] * 100, marker="o", label="ROA %")
    axes[1, 1].plot(periods, ratios["return_on_equity"] * 100, marker="o", label="ROE %")
    axes[1, 1].set_title("Capital efficiency and leverage")
    axes[1, 1].legend()

    for axis in axes.flat:
        axis.grid(alpha=0.2)
        axis.tick_params(axis="x", rotation=30)
    fig.savefig(target, dpi=160, bbox_inches="tight")
    plt.close(fig)
    return target
