from __future__ import annotations

import math
from typing import Any

from apps.calculators.engine.base import (
    BaseCalculator,
    CalculationResult,
    CalculatorField,
    MaterialItem,
)


class PlasterCalculator(BaseCalculator):
    id = "plaster"
    title = "Калькулятор штукатурки стін"
    category = "Стіни"
    category_slug = "walls"
    description = "Розрахунок гіпсової та цементної штукатурки у мішках, маяків та ґрунтовки за площею стін і товщиною шару."
    icon = "edit"
    seo_keywords = "калькулятор штукатурки, розрахунок штукатурки стін, ротбанд витрата, штукатурка на м2, скільки мішків штукатурки"
    seo_text = """
    Калькулятор штукатурки розраховує точну вагу сухої будівельної суміші та кількість мішків (25 або 30 кг)
    для гіпсових (Knauf Rotband, Plato) та цементних штукатурок залежно від середньої товщини шару за маяками.
    """

    fields = [
        CalculatorField(
            id="area",
            label="Площа стін під штукатурку",
            field_type="number",
            unit="м²",
            default_value=40.0,
            min_value=1.0,
            max_value=2000.0,
            step=1.0,
            help_text="Загальна площа стін за вирахуванням вікон і дверей",
        ),
        CalculatorField(
            id="thickness",
            label="Середня товщина шару",
            field_type="number",
            unit="мм",
            default_value=15.0,
            min_value=5.0,
            max_value=80.0,
            step=1.0,
            help_text="Середня товщина за маяками (зазвичай 10–20 мм для рівних стін, 25–40 мм при значних завалах)",
        ),
        CalculatorField(
            id="plaster_type",
            label="Тип штукатурки",
            field_type="select",
            default_value="gypsum",
            options=[
                ("gypsum", "Гіпсова (Knauf Rotband/HP Start ~8.5 кг/м²/10мм)"),
                ("cement", "Цементно-піщана фасадна/для ванних (~16 кг/м²/10мм)"),
                ("cement_lime", "Цементно-вапняна полегшена (~14 кг/м²/10мм)"),
            ],
            help_text="Гіпсова суміш — для сухих житлових кімнат, цементна — для вологих зон і фасадів",
        ),
        CalculatorField(
            id="bag_weight",
            label="Вага мішка",
            field_type="select",
            default_value="30",
            options=[
                ("30", "30 кг (стандарт гіпсових сумішей Knauf)"),
                ("25", "25 кг (стандарт більшості цементних сумішей)"),
            ],
            help_text="Вага мішка за заводською фасовкою",
        ),
    ]

    def calculate(self, inputs: dict[str, Any]) -> CalculationResult:
        data = self.clean_inputs(inputs)
        area = data["area"]
        thickness_mm = data["thickness"]
        plaster_type = data["plaster_type"]
        bag_weight = float(data["bag_weight"])

        # Витрата сухої суміші в кг на 1 м² при товщині шару 1 мм:
        rate_per_mm = {
            "gypsum": 0.85,       # 8.5 кг/м² на 10 мм
            "cement": 1.60,       # 16.0 кг/м² на 10 мм
            "cement_lime": 1.40,  # 14.0 кг/м² на 10 мм
        }.get(plaster_type, 0.85)

        type_name = {
            "gypsum": "Гіпсова штукатурка",
            "cement": "Цементна штукатурка",
            "cement_lime": "Цементно-вапняна штукатурка",
        }.get(plaster_type, "Штукатурка")

        # Загальна вага з запасом 5% на нерівності та втрати на правилі
        exact_weight_kg = area * thickness_mm * rate_per_mm
        weight_with_reserve = exact_weight_kg * 1.05
        bags_count = self.ceil(weight_with_reserve / bag_weight)

        materials = [
            MaterialItem(
                name=f"{type_name} ({int(bag_weight)} кг)",
                unit="мішок",
                quantity=self.round_val(exact_weight_kg / bag_weight, 1),
                quantity_with_reserve=self.round_val(weight_with_reserve / bag_weight, 1),
                purchase_quantity=bags_count,
                category="Сухі штукатурні суміші",
                note=f"Разом {self.round_val(weight_with_reserve, 0)} кг при середній товщині {thickness_mm} мм",
            )
        ]

        # Маяки штукатурні Т-подібні 6 мм (довжина 2.5–3 м, крок встановлення 1.2–1.4 м)
        beacons_count = self.ceil(area / 3.0)
        materials.append(
            MaterialItem(
                name="Маяки штукатурні оцинковані 6 мм (рейка 3 м)",
                unit="шт",
                quantity=beacons_count,
                quantity_with_reserve=beacons_count,
                purchase_quantity=beacons_count,
                category="Монтажні елементи",
                note="Крок встановлення під правило 1.5–2.0 м",
            )
        )

        # Ґрунтовка глибокого проникнення (1 шар, ~0.15 л/м²)
        primer_liters = area * 0.15 * 1.10
        primer_canisters = self.ceil(primer_liters / 10.0)  # каністри по 10 л
        materials.append(
            MaterialItem(
                name="Ґрунтовка глибокого проникнення (каністри 10 л)",
                unit="каністра",
                quantity=self.round_val(primer_liters / 10.0, 1),
                quantity_with_reserve=self.round_val(primer_liters / 10.0, 1),
                purchase_quantity=primer_canisters,
                category="Ґрунтовки",
                note=f"Витрата {self.round_val(primer_liters, 1)} л для зміцнення основи перед штукатуренням",
            )
        )

        warnings = []
        if thickness_mm > 50.0 and plaster_type == "gypsum":
            warnings.append("Товщина гіпсової штукатурки понад 50 мм за один прохід неприпустима: суміш може поплисти. Наносьте у два шари з проміжним ґрунтуванням або використовуйте армувальну сітку.")
        if thickness_mm < 6.0:
            warnings.append("Товщина менше 6 мм: неможливо якісно втопити стандартний штукатурний маяк 6 мм.")

        recommendations = [
            "Перед нанесенням гіпсової штукатурки на гладкий монолітний бетон обов'язково нанесіть адгезійний ґрунт «Бетоноконтакт».",
            "Для газобетону обов'язково застосовуйте паропроникний ґрунт глибокого проникнення у 2 шари, щоб блок не витягнув воду зі штукатурки.",
            "Видаляйте металеві маяки зі стін після схоплювання гіпсу, щоб уникнути появи іржі через фінішне оздоблення.",
        ]

        totals = {
            "Площа стін": f"{area} м²",
            "Середня товщина": f"{thickness_mm} мм",
            "Сумарна вага суміші": f"{self.round_val(weight_with_reserve, 0)} кг",
            "Кількість мішків": f"{bags_count} шт",
        }

        return CalculationResult(
            materials=materials,
            totals=totals,
            warnings=warnings,
            recommendations=recommendations,
        )
