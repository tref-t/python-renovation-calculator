from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any


@dataclass
class CalculatorField:
    """Опис окремого поля введення для калькулятора."""
    id: str
    label: str
    field_type: str = "number"  # "number", "select", "toggle"
    unit: str = ""
    default_value: float | int | str | bool = 0.0
    min_value: float | None = None
    max_value: float | None = None
    step: float = 1.0
    options: list[tuple[str, str]] = field(default_factory=list)  # (value, label)
    help_text: str = ""
    group: str = "Основні параметри"


@dataclass
class MaterialItem:
    """Елемент специфікації матеріалів для закупівлі."""
    name: str
    unit: str
    quantity: float
    quantity_with_reserve: float
    purchase_quantity: int
    category: str = "Основні матеріали"
    note: str = ""

    @property
    def formatted_quantity(self) -> str:
        """Гарне форматування кількості."""
        val = float(self.quantity)
        if val.is_integer():
            return f"{int(val)}"
        return f"{val:.2f}".rstrip("0").rstrip(".")

    @property
    def formatted_with_reserve(self) -> str:
        val = float(self.quantity_with_reserve)
        if val.is_integer():
            return f"{int(val)}"
        return f"{val:.2f}".rstrip("0").rstrip(".")


@dataclass
class CalculationResult:
    """Результат розрахунку будь-якого калькулятора."""
    materials: list[MaterialItem] = field(default_factory=list)
    totals: dict[str, Any] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)


class BaseCalculator:
    """Базовий клас для всіх будівельних калькуляторів."""
    id: str = ""
    title: str = ""
    category: str = ""
    category_slug: str = ""
    description: str = ""
    icon: str = "calculator"
    seo_keywords: str = ""
    seo_text: str = ""

    fields: list[CalculatorField] = []

    def get_default_inputs(self) -> dict[str, Any]:
        """Повертає словник дефолтних значень полів."""
        return {f.id: f.default_value for f in self.fields}

    def clean_inputs(self, raw_inputs: dict[str, Any]) -> dict[str, Any]:
        """Очищує та конвертує сирі вхідні дані відповідно до типів полів."""
        cleaned: dict[str, Any] = {}
        for f in self.fields:
            raw_val = raw_inputs.get(f.id, f.default_value)
            if f.field_type == "number":
                try:
                    val = float(str(raw_val).replace(",", ".").strip())
                except (ValueError, TypeError):
                    val = float(f.default_value)
                if f.min_value is not None:
                    val = max(f.min_value, val)
                if f.max_value is not None:
                    val = min(f.max_value, val)
                cleaned[f.id] = val
            elif f.field_type == "toggle":
                if isinstance(raw_val, bool):
                    cleaned[f.id] = raw_val
                elif str(raw_val).lower() in ("true", "1", "on", "yes", "так"):
                    cleaned[f.id] = True
                else:
                    cleaned[f.id] = False
            else:  # select, text
                cleaned[f.id] = str(raw_val).strip()
        return cleaned

    def calculate(self, inputs: dict[str, Any]) -> CalculationResult:
        """Головний метод розрахунку. Має бути перевизначений у підкласі."""
        raise NotImplementedError("Метод calculate повинен бути реалізований у підкласі")

    @staticmethod
    def ceil(val: float) -> int:
        """Округлення вгору до цілого для закупівельної кількості."""
        return math.ceil(val) if val > 0 else 0

    @staticmethod
    def round_val(val: float, digits: int = 2) -> float:
        """Округлення до потрібної кількості знаків."""
        return round(val, digits)
