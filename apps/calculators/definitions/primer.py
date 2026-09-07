from __future__ import annotations

import math
from typing import Any

from apps.calculators.engine.base import (
    BaseCalculator,
    CalculationResult,
    CalculatorField,
    MaterialItem,
)


class PrimerCalculator(BaseCalculator):
    id = "primer"
    title = "Калькулятор ґрунтовки"
    category = "Оздоблення"
    category_slug = "finishes"
    description = "Розрахунок ґрунтовки глибокого проникнення або бетоноконтакту в літрах та каністрах за типом основи."
    icon = "droplet"
    seo_keywords = "калькулятор грунтовки, розрахунок грунтовки, грунтовка глибокого проникнення витрата, скільки каністр грунтовки"
    seo_text = """
    Калькулятор розраховує потрібну кількість ґрунтовки для зміцнення основи, зниження поглинальної здатності
    та підвищення адгезії перед штукатуренням, шпаклюванням, фарбуванням чи наклеюванням шпалер.
    """

    fields = [
        CalculatorField(
            id="area",
            label="Площа оброблюваної поверхні",
            field_type="number",
            unit="м²",
            default_value=50.0,
            min_value=1.0,
            max_value=3000.0,
            step=1.0,
            help_text="Площа стін, стелі чи підлоги",
        ),
        CalculatorField(
            id="surface_type",
            label="Тип поверхні (основи)",
            field_type="select",
            default_value="plaster",
            options=[
                ("plaster", "Штукатурка / шпаклівка / гіпсокартон (~0.15 л/м²)"),
                ("porous", "Газобетон / піноблок / цегла з високим поглинанням (~0.30 л/м²)"),
                ("screed", "Стяжка підлоги цементно-піщана (~0.20 л/м²)"),
                ("concrete_contact", "Гладкий монолітний бетон (Бетоноконтакт ~0.30 кг/м²)"),
            ],
            help_text="Різні матеріали мають суттєво різний коефіцієнт вбирання рідини",
        ),
        CalculatorField(
            id="layers_count",
            label="Кількість шарів",
            field_type="select",
            default_value="1",
            options=[
                ("1", "1 шар (для звичайних оштукатурених стін)"),
                ("2", "2 шари (для газоблоку або перед фарбуванням)"),
            ],
            help_text="На пористі основи рекомендовано наносити мінімум 2 шари",
        ),
        CalculatorField(
            id="canister_size",
            label="Об'єм каністри",
            field_type="select",
            default_value="10",
            options=[
                ("10", "10 літрів (стандартна велика каністра)"),
                ("5", "5 літрів (компактна каністра)"),
            ],
            help_text="Об'єм заводської тари для округлення покупки",
        ),
    ]

    def calculate(self, inputs: dict[str, Any]) -> CalculationResult:
        data = self.clean_inputs(inputs)
        area = data["area"]
        surface_type = data["surface_type"]
        layers = int(data["layers_count"])
        canister_size = float(data["canister_size"])

        rate = {
            "plaster": 0.15,
            "porous": 0.30,
            "screed": 0.20,
            "concrete_contact": 0.30,
        }.get(surface_type, 0.15)

        is_contact = surface_type == "concrete_contact"
        unit_label = "кг" if is_contact else "л"
        pack_label = "відро" if is_contact else "каністра"

        name_label = {
            "plaster": "Ґрунтовка глибокого проникнення акрилова",
            "porous": "Ґрунтовка глибокого проникнення для пористих поверхонь",
            "screed": "Ґрунтовка для стяжки та підлог зміцнююча",
            "concrete_contact": "Адгезійний кварцовий ґрунт (Бетоноконтакт)",
        }.get(surface_type, "Ґрунтовка глибокого проникнення")

        exact_amount = area * layers * rate
        amount_with_reserve = exact_amount * 1.10  # 10% запас на поглинання та валик
        canisters_count = self.ceil(amount_with_reserve / canister_size)

        materials = [
            MaterialItem(
                name=f"{name_label} ({int(canister_size)} {unit_label})",
                unit=pack_label,
                quantity=self.round_val(exact_amount / canister_size, 1),
                quantity_with_reserve=self.round_val(amount_with_reserve / canister_size, 1),
                purchase_quantity=canisters_count,
                category="Ґрунтувальні суміші",
                note=f"Разом {self.round_val(amount_with_reserve, 1)} {unit_label} у {layers} шар(и)",
            ),
            MaterialItem(
                name="Валик малярний велюровий / поліамідний з ванночкою",
                unit="шт",
                quantity=1,
                quantity_with_reserve=1,
                purchase_quantity=1,
                category="Інструменти",
                note="Ворс 8–12 мм для рівномірного нанесення без бризок",
            ),
        ]

        warnings = []
        if surface_type == "porous" and layers < 2:
            warnings.append("Для газобетону обов'язково рекомендується 2 шари ґрунтування, інакше блок миттєво вбере вологу зі шпаклівки чи штукатурки.")

        recommendations = [
            "Час повного висихання ґрунтовки становить від 3 до 6 годин (залежно від температури та вологості).",
            "Не наносьте наступні шари сумішей по невисохлій плівці ґрунту.",
            "Для важких гладких бетонних поверхонь використовуйте тільки адгезійний ґрунт з кварцовим піском.",
        ]

        totals = {
            "Площа": f"{area} м²",
            "Потрібний об'єм": f"{self.round_val(amount_with_reserve, 1)} {unit_label}",
            "Кількість ємностей": f"{canisters_count} {pack_label}",
        }

        return CalculationResult(
            materials=materials,
            totals=totals,
            warnings=warnings,
            recommendations=recommendations,
        )
