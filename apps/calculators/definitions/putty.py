from __future__ import annotations

import math
from typing import Any

from apps.calculators.engine.base import (
    BaseCalculator,
    CalculationResult,
    CalculatorField,
    MaterialItem,
)


class PuttyCalculator(BaseCalculator):
    id = "putty"
    title = "Калькулятор шпаклівки стін та стелі"
    category = "Оздоблення"
    category_slug = "finishes"
    description = "Розрахунок стартової та фінішної шпаклівки в мішках або готових відрах під шпалери чи фарбування."
    icon = "edit-3"
    seo_keywords = "калькулятор шпаклівки, розрахунок шпаклівки на м2, фінішна шпаклівка витрата, сатенгіпс, скільки мішків шпаклівки"
    seo_text = """
    Калькулятор шпаклівки визначає точну вагу та кількість мішків або відер шпаклівки
    залежно від кількості шарів, середньої товщини та типу суміші (стартова, фінішна суха або готова полімерна паста).
    """

    fields = [
        CalculatorField(
            id="area",
            label="Площа поверхонь під шпаклювання",
            field_type="number",
            unit="м²",
            default_value=40.0,
            min_value=1.0,
            max_value=2000.0,
            step=1.0,
            help_text="Площа стін або стелі",
        ),
        CalculatorField(
            id="putty_type",
            label="Тип шпаклівки",
            field_type="select",
            default_value="finish_dry",
            options=[
                ("start_dry", "Стартова гіпсова суха (товщина 1.5–3 мм, ~1.1 кг/м²/мм)"),
                ("finish_dry", "Фінішна гіпсова суха (Knauf HP Finish, Сатенгіпс ~0.9 кг/м²/мм)"),
                ("finish_ready", "Готова полімерна паста у відрах (Sheetrock, Semin ~1.6 кг/м²/мм)"),
            ],
            help_text="Оберіть вид матеріалу для підготовки поверхні",
        ),
        CalculatorField(
            id="layers_count",
            label="Кількість шарів",
            field_type="select",
            default_value="2",
            options=[
                ("1", "1 шар (для рівних поверхонь або під шпалери)"),
                ("2", "2 шари (стандартна підготовка)"),
                ("3", "3 шари (ідеальна площина під бездоганне фарбування)"),
            ],
            help_text="Кількість проходів шпателем з проміжним шліфуванням",
        ),
        CalculatorField(
            id="thickness_per_layer",
            label="Середня товщина одного шару",
            field_type="number",
            unit="мм",
            default_value=1.0,
            min_value=0.3,
            max_value=5.0,
            step=0.2,
            help_text="Зазвичай 1–2 мм для старту, 0.5–1 мм для фінішу",
        ),
    ]

    def calculate(self, inputs: dict[str, Any]) -> CalculationResult:
        data = self.clean_inputs(inputs)
        area = data["area"]
        putty_type = data["putty_type"]
        layers = int(data["layers_count"])
        thickness_mm = data["thickness_per_layer"]

        # Норми витрати (кг/м² на 1 мм шару)
        rate_per_mm = {
            "start_dry": 1.10,
            "finish_dry": 0.90,
            "finish_ready": 1.60,
        }.get(putty_type, 0.90)

        pack_weight = 20.0 if putty_type == "finish_ready" else 25.0
        pack_unit = "відро" if putty_type == "finish_ready" else "мішок"

        name_label = {
            "start_dry": "Стартова гіпсова шпаклівка (мішки 25 кг)",
            "finish_dry": "Фінішна шпаклівка суха (мішки 25 кг)",
            "finish_ready": "Готова полімерна паста-фініш (відра 20 кг)",
        }.get(putty_type, "Шпаклівка")

        # Розрахунок з запасом 10% на шліфування та зачистку інструменту
        exact_kg = area * thickness_mm * rate_per_mm * layers
        total_kg = exact_kg * 1.10
        packs_count = self.ceil(total_kg / pack_weight)

        materials = [
            MaterialItem(
                name=name_label,
                unit=pack_unit,
                quantity=self.round_val(exact_kg / pack_weight, 1),
                quantity_with_reserve=self.round_val(total_kg / pack_weight, 1),
                purchase_quantity=packs_count,
                category="Шпаклівки",
                note=f"Разом {self.round_val(total_kg, 0)} кг на {layers} шари (товщина шару ~{thickness_mm} мм)",
            )
        ]

        # Абразивний папір / сітка для шліфування (орієнтовно 1 лист на кожні 10 м²)
        sanding_sheets = self.ceil((area * layers) / 10.0)
        materials.append(
            MaterialItem(
                name="Абразивна сітка / шліфувальний папір (P150–P240)",
                unit="шт",
                quantity=sanding_sheets,
                quantity_with_reserve=sanding_sheets,
                purchase_quantity=sanding_sheets,
                category="Витратні матеріали",
                note="Для проміжного та фінішного затирання шарів під лампу",
            )
        )

        warnings = []
        if thickness_mm > 2.0 and putty_type in ("finish_dry", "finish_ready"):
            warnings.append("Фінішну шпаклівку не слід наносити шаром товще 2 мм за один прохід — вона може потріскатися або сповзти під час висихання.")

        recommendations = [
            "Кожен шар шпаклівки після повного висихання та шліфування обов'язково ґрунтуйте перед нанесенням наступного шару.",
            "Під фарбування обов'язково контролюйте площину з проявною косою лампою (типу Lossew), щоб виявити всі подряпини та мікроями.",
        ]

        totals = {
            "Площа поверхонь": f"{area} м²",
            "Кількість шарів": f"{layers}",
            "Загальна маса суміші": f"{self.round_val(total_kg, 0)} кг",
            "Кількість упаковок": f"{packs_count} {pack_unit}",
        }

        return CalculationResult(
            materials=materials,
            totals=totals,
            warnings=warnings,
            recommendations=recommendations,
        )
