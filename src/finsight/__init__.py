"""Financial statement analytics with explicit formulas and provenance."""

from .io import REQUIRED_COLUMNS, load_statement
from .ratios import calculate_ratios

__all__ = ["REQUIRED_COLUMNS", "calculate_ratios", "load_statement"]
__version__ = "0.1.0"
