from __future__ import annotations

import math
from typing import Any

from apps.calculators.engine.base import (
    BaseCalculator,
    CalculationResult,
    CalculatorField,
    MaterialItem,
)


class TileCalculator(BaseCalculator):
    id = "tile"
    title = "Калькулятор керамічної плитки"
    category = "Оздоблення"
    category_slug = "finishes"
    description = "Розрахунок плитки, керамограніту, кількості клею в мішках, затирки швів та кліпс СВП для підлоги чи стін."
    icon = "grid"
    seo_keywords = "калькулятор плитки, розрахунок плитки, клей для плитки, затирка для швів плитки, керамограніт"
    seo_text = """
    Калькулятор плитки розраховує точну кількість плитки або керамограніту в штуках та упаковках,
    витрату плиткового клею за товщиною гребінки і вагу епоксидної або цементної затирки для швів.
    """

    fields = [
        CalculatorField(
            id="area",
            label="Площа облицювання",
            field_type="number",
            unit="м²",
            default_value=15.0,
            min_value=0.5,
            max_value=1000.0,
            step=0.5,
            help_text="Площа стін або підлоги під укладання",
        ),
        CalculatorField(
            id="tile_length",
            label="Довжина плитки",
            field_type="number",
            unit="см",
            default_value=60.0,
            min_value=5.0,
            max_value=300.0,
            step=1.0,
            help_text="Наприклад, 60 для плитки 60×60 см або 120 для 60×120 см",
        ),
        CalculatorField(
            id="tile_width",
            label="Ширина плитки",
            field_type="number",
            unit="см",
            default_value=60.0,
            min_value=5.0,
            max_value=300.0,
            step=1.0,
            help_text="Ширина плитки в сантиметрах",
        ),
        CalculatorField(
            id="pack_sqm",
            label="Площа в упаковці",
            field_type="number",
            unit="м²",
            default_value=1.44,
            min_value=0.2,
            max_value=10.0,
            step=0.01,
            help_text="Зазначена на заводській упаковці виробником",
        ),
        CalculatorField(
            id="laying_method",
            label="Спосіб укладання",
            field_type="select",
            default_value="straight",
            options=[
                ("straight", "Прямий шов у шов (запас 10%)"),
                ("diagonal", "Діагональний 45° (запас 15%)"),
                ("offset", "Зі зміщенням / в розбіжку (запас 12%)"),
            ],
            help_text="Складні схеми розкладки збільшують відсоток обрізків",
        ),
        CalculatorField(
            id="joint_width",
            label="Ширина міжплиткового шва",
            field_type="number",
            unit="мм",
            default_value=2.0,
            min_value=1.0,
            max_value=15.0,
            step=0.5,
            help_text="Для ректифікованого керамограніту 1.5–2 мм, для звичайної плитки 2.5–3 мм",
        ),
        CalculatorField(
            id="glue_thickness",
            label="Середній шар клею",
            field_type="number",
            unit="мм",
            default_value=4.0,
            min_value=2.0,
            max_value=15.0,
            step=1.0,
            help_text="Висота зубця шпателя: 6 мм дає ~3 мм шар, 8-10 мм зубець дає ~4-5 мм шар",
        ),
    ]

    def calculate(self, inputs: dict[str, Any]) -> CalculationResult:
        data = self.clean_inputs(inputs)
        area = data["area"]
        length_cm = max(1.0, data["tile_length"])
        width_cm = max(1.0, data["tile_width"])
        pack_sqm = max(0.1, data["pack_sqm"])
        laying_method = data["laying_method"]
        joint_width_mm = max(0.5, data["joint_width"])
        glue_thickness_mm = max(1.0, data["glue_thickness"])

        waste_coef = {
            "straight": 1.10,
            "offset": 1.12,
            "diagonal": 1.15,
        }.get(laying_method, 1.10)

        # Розрахунок плитки
        tile_area_m2 = (length_cm / 100.0) * (width_cm / 100.0)
        needed_sqm = area * waste_coef
        packs_count = self.ceil(needed_sqm / pack_sqm)
        tiles_count = self.ceil(needed_sqm / tile_area_m2)
        total_purchased_sqm = packs_count * pack_sqm

        materials = [
            MaterialItem(
                name=f"Плитка {int(length_cm)}×{int(width_cm)} см (упаковки)",
                unit="упак.",
                quantity=self.round_val(area / pack_sqm, 2),
                quantity_with_reserve=self.round_val(needed_sqm / pack_sqm, 2),
                purchase_quantity=packs_count,
                category="Основне покриття",
                note=f"Разом {tiles_count} шт ({self.round_val(total_purchased_sqm, 2)} м²)",
            )
        ]

        # Розрахунок плиткового клею (суха суміш)
        # Витрата: ~1.3 кг сухої суміші на 1 м² на кожен 1 мм шару + 10% запас
        glue_kg = area * glue_thickness_mm * 1.3 * 1.10
        glue_bags = self.ceil(glue_kg / 25.0)
        materials.append(
            MaterialItem(
                name="Клей для плитки (мішки 25 кг)",
                unit="мішок",
                quantity=self.round_val((area * glue_thickness_mm * 1.3) / 25.0, 1),
                quantity_with_reserve=self.round_val(glue_kg / 25.0, 1),
                purchase_quantity=glue_bags,
                category="Клейові суміші",
                note=f"Витрата {self.round_val(glue_kg, 1)} кг (для шару {glue_thickness_mm} мм)",
            )
        )

        # Розрахунок затирки для швів
        # Формула за ГОСТ: ((L + W) / (L * W)) * JointWidth * JointDepth * 1.6 * Area * 1.10
        # де L, W в мм, глибина шва приймається рівною товщині плитки ~8 мм
        l_mm = length_cm * 10
        w_mm = width_cm * 10
        depth_mm = 8.0  # середня товщина плитки
        grout_kg_exact = ((l_mm + w_mm) / (l_mm * w_mm)) * joint_width_mm * depth_mm * 1.6 * area
        grout_kg = max(1.0, grout_kg_exact * 1.10)
        materials.append(
            MaterialItem(
                name="Затирка для міжплиткових швів",
                unit="кг",
                quantity=self.round_val(grout_kg_exact, 2),
                quantity_with_reserve=self.round_val(grout_kg, 2),
                purchase_quantity=self.ceil(grout_kg),
                category="Оздоблення швів",
                note=f"Для шва {joint_width_mm} мм (цементна або епоксидна)",
            )
        )

        # СВП (система вирівнювання плитки: затискачі/кліпси)
        # Для формату 60х60 потрібно приблизно 11-12 затискачів на 1 м²
        svp_per_sqm = max(8, int(4 / tile_area_m2))
        svp_clips = self.ceil(area * svp_per_sqm * 1.05)
        materials.append(
            MaterialItem(
                name="Затискачі СВП (одноразові)",
                unit="шт",
                quantity=area * svp_per_sqm,
                quantity_with_reserve=svp_clips,
                purchase_quantity=svp_clips,
                category="Монтажні елементи",
                note="Забезпечують ідеально рівну площину без перепадів між плитками",
            )
        )

        warnings = []
        if glue_thickness_mm > 10.0:
            warnings.append("Шар клею понад 10 мм неприпустимий для тонкошарових сумішей: клей дасть усадку та потягне плитку. Попередньо вирівняйте основу штукатуркою або стяжкою.")
        if (length_cm >= 60 or width_cm >= 60) and glue_thickness_mm < 3.0:
            warnings.append("Великоформатна плитка вимагає нанесення клею як на основу (гребінка 8-10 мм), так і на здир на плитку (метод подвійного нанесення).")

        recommendations = [
            "Обов'язково ґрунтуйте основу ґрунтовкою глибокого проникнення за 4–6 годин до початку робіт.",
            "Для ванних кімнат та душових зон обов'язково виконайте обмазувальну гідроізоляцію з проклеюванням кутової гідроізоляційної стрічки.",
            "Затирати шви слід не раніше ніж через 24 години після укладання плитки.",
        ]

        totals = {
            "Площа укладання": f"{area} м²",
            "Кількість плитки": f"{tiles_count} шт",
            "Упаковок до закупівлі": f"{packs_count} шт",
            "Запас на підрізку": f"{int((waste_coef - 1) * 100)}%",
        }

        return CalculationResult(
            materials=materials,
            totals=totals,
            warnings=warnings,
            recommendations=recommendations,
        )
