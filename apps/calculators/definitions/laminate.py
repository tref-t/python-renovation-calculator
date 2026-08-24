from __future__ import annotations

import math
from typing import Any

from apps.calculators.engine.base import (
    BaseCalculator,
    CalculationResult,
    CalculatorField,
    MaterialItem,
)


class LaminateCalculator(BaseCalculator):
    id = "laminate"
    title = "Калькулятор ламінату"
    category = "Підлога"
    category_slug = "flooring"
    description = "Розрахунок кількості ламінату в упаковках, рулонів підкладки, плінтуса та клинів з урахуванням способу укладання."
    icon = "layers"
    seo_keywords = "калькулятор ламінату, розрахунок ламінату, ламінат на кімнату, підкладка під ламінат, плінтус"
    seo_text = """
    Калькулятор ламінату дозволяє точно визначити кількість упаковок підлогового покриття, площу підкладки та метраж плінтуса.
    Коефіцієнт підрізки залежить від геометрії кімнати та схеми монтажу: пряме укладання (+5%), по діагоналі (+15%) або класичною ялинкою (+20%).
    """

    fields = [
        CalculatorField(
            id="area",
            label="Площа приміщення",
            field_type="number",
            unit="м²",
            default_value=20.0,
            min_value=0.5,
            max_value=1000.0,
            step=0.5,
            help_text="Загальна площа підлоги в кімнаті",
        ),
        CalculatorField(
            id="pack_area",
            label="Площа в одній упаковці",
            field_type="number",
            unit="м²",
            default_value=2.131,
            min_value=0.5,
            max_value=5.0,
            step=0.001,
            help_text="Зазначена виробником на пачці ламінату (зазвичай 1.8 – 2.4 м²)",
        ),
        CalculatorField(
            id="laying_method",
            label="Спосіб укладання",
            field_type="select",
            default_value="straight",
            options=[
                ("straight", "Пряме вздовж стіни (запас 5%)"),
                ("diagonal", "По діагоналі 45° (запас 15%)"),
                ("herringbone", "Англійська ялинка (запас 20%)"),
            ],
            help_text="Діагональне укладання та ялинка потребують більше матеріалу на підрізку",
        ),
        CalculatorField(
            id="has_underlayment",
            label="Потрібна підкладка",
            field_type="toggle",
            default_value=True,
            help_text="Підкладка зі спіненого поліетилену, полістиролу або корку",
        ),
        CalculatorField(
            id="underlayment_roll",
            label="Площа рулону підкладки",
            field_type="number",
            unit="м²",
            default_value=10.0,
            min_value=1.0,
            max_value=100.0,
            step=1.0,
            help_text="Стандартний рулон зазвичай 10 або 20 м²",
        ),
        CalculatorField(
            id="include_plinth",
            label="Розрахувати плінтус",
            field_type="toggle",
            default_value=True,
            help_text="Плінтус по периметру кімнати з відрахуванням дверного отвору",
        ),
    ]

    def calculate(self, inputs: dict[str, Any]) -> CalculationResult:
        data = self.clean_inputs(inputs)
        area = data["area"]
        pack_area = max(0.1, data["pack_area"])
        laying_method = data["laying_method"]
        has_underlayment = data["has_underlayment"]
        underlayment_roll = max(1.0, data["underlayment_roll"])
        include_plinth = data["include_plinth"]

        # Коефіцієнт відходів
        waste_coef = {
            "straight": 1.05,
            "diagonal": 1.15,
            "herringbone": 1.20,
        }.get(laying_method, 1.05)

        # 1. Ламінат
        laminate_needed_sqm = area * waste_coef
        laminate_packs = self.ceil(laminate_needed_sqm / pack_area)
        total_laminate_sqm = laminate_packs * pack_area

        materials = [
            MaterialItem(
                name="Ламінат (упаковки)",
                unit="упак.",
                quantity=self.round_val(area / pack_area, 2),
                quantity_with_reserve=self.round_val(laminate_needed_sqm / pack_area, 2),
                purchase_quantity=laminate_packs,
                category="Основне покриття",
                note=f"Разом {self.round_val(total_laminate_sqm, 2)} м² у {laminate_packs} упак.",
            )
        ]

        # 2. Підкладка (нахльост 15%)
        if has_underlayment:
            underlay_area = area * 1.15
            underlay_rolls = self.ceil(underlay_area / underlayment_roll)
            materials.append(
                MaterialItem(
                    name="Підкладка під ламінат",
                    unit="рулон",
                    quantity=self.round_val(area / underlayment_roll, 2),
                    quantity_with_reserve=self.round_val(underlay_area / underlayment_roll, 2),
                    purchase_quantity=underlay_rolls,
                    category="Ізоляційні матеріали",
                    note=f"Із запасом 15% на нахльост ({self.round_val(underlay_area, 1)} м²)",
                )
            )

        # 3. Периметр для плінтуса та клинів (оцінка за площею прямокутної кімнати)
        perimeter = max(2.0, (math.sqrt(area) * 4) - 0.9)  # мінус 1 дверний отвір 0.9 м
        if include_plinth:
            plinth_length = perimeter * 1.05  # +5% на стики та кути
            plinth_pieces = self.ceil(plinth_length / 2.5)  # планки по 2.5 м
            materials.append(
                MaterialItem(
                    name="Плінтус підлоговий (планки 2.5 м)",
                    unit="шт",
                    quantity=self.round_val(perimeter / 2.5, 1),
                    quantity_with_reserve=self.round_val(plinth_length / 2.5, 1),
                    purchase_quantity=plinth_pieces,
                    category="Фурнітура",
                    note=f"Периметр за мінусом дверей ~{self.round_val(perimeter, 1)} м",
                )
            )

        # 4. Клини розпірні (по периметру через кожні 0.5 м)
        wedges = self.ceil(perimeter / 0.5)
        materials.append(
            MaterialItem(
                name="Клини розпірні монтажні",
                unit="шт",
                quantity=wedges,
                quantity_with_reserve=wedges,
                purchase_quantity=wedges,
                category="Кріплення та монтаж",
                note="Для забезпечення деформаційного зазору 8–10 мм біля стін",
            )
        )

        # Попередження та поради
        warnings = []
        if area < 3.0:
            warnings.append("Мала площа приміщення: реальний відсоток підрізки може бути на 5–7% вищим через велику кількість країв.")
        if laying_method == "herringbone":
            warnings.append("При укладанні ялинкою обов'язково контролюйте лівий та правий замок планок (типи А і В).")
        if area > 50.0:
            warnings.append("Площа понад 50 м² вимагає деформаційного термошва між приміщеннями під дверним полотном.")

        recommendations = [
            "Дайте ламінату акліматизуватися в приміщенні щонайменше 48 годин у закритих пачках.",
            "Перепад висоти основи не повинен перевищувати 2 мм на 2 погонних метри.",
            "Завжди залишайте термозазор 8–10 мм між ламінатом і стінами, трубами, порогами.",
        ]

        totals = {
            "Площа кімнати": f"{area} м²",
            "Корисна площа у закупівлі": f"{self.round_val(total_laminate_sqm, 2)} м²",
            "Запас на підрізку": f"{int((waste_coef - 1) * 100)}%",
            "Орієнтовний периметр": f"{self.round_val(perimeter, 1)} м",
        }

        return CalculationResult(
            materials=materials,
            totals=totals,
            warnings=warnings,
            recommendations=recommendations,
        )
