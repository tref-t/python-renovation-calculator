from __future__ import annotations

import math
from typing import Any

from apps.calculators.engine.base import (
    BaseCalculator,
    CalculationResult,
    CalculatorField,
    MaterialItem,
)


class PaintCalculator(BaseCalculator):
    id = "paint"
    title = "Калькулятор фарби для стін та стелі"
    category = "Оздоблення"
    category_slug = "finishes"
    description = "Розрахунок інтер'єрної акрилової, латексної або силіконової фарби у літрах та банках за кількістю шарів."
    icon = "sun"
    seo_keywords = "калькулятор фарби, розрахунок фарби на стіни, фарба для стелі витрата, скільки банок фарби"
    seo_text = """
    Калькулятор фарби розраховує необхідний літраж інтер'єрної фарби та кількість заводських банок
    для фарбування стін або стелі у 2–3 шари з урахуванням фактури основи та втрат на валику.
    """

    fields = [
        CalculatorField(
            id="area",
            label="Площа фарбування",
            field_type="number",
            unit="м²",
            default_value=30.0,
            min_value=1.0,
            max_value=2000.0,
            step=1.0,
            help_text="Загальна площа стін або стелі",
        ),
        CalculatorField(
            id="layers_count",
            label="Кількість шарів",
            field_type="select",
            default_value="2",
            options=[
                ("1", "1 шар (для оновлення ідентичного кольору)"),
                ("2", "2 шари (стандартне якісне перекриття)"),
                ("3", "3 шари (при кардинальній зміні кольору або темних тонах)"),
            ],
            help_text="Більшість сучасних інтер'єрних фарб наносяться у 2 шари",
        ),
        CalculatorField(
            id="paint_type",
            label="Тип фарби",
            field_type="select",
            default_value="latex",
            options=[
                ("latex", "Латексна зносостійка (матовий/шовковистий шовк ~110 мл/м²)"),
                ("acrylic", "Акрилова водно-дисперсійна глибокоматова (~120 мл/м²)"),
                ("silicone", "Силіконова вологостійка для ванних і кухонь (~130 мл/м²)"),
            ],
            help_text="Визначає покривну здатність та стійкість до вологого стирання (клас стирання)",
        ),
        CalculatorField(
            id="can_volume",
            label="Об'єм банки",
            field_type="select",
            default_value="5",
            options=[
                ("0.9", "0.9 л (маленька банка для підфарбовування)"),
                ("2.5", "2.5 л (стандарт)"),
                ("5", "5.0 л (середня банка)"),
                ("9", "9.0 л (економічна тара)"),
                ("14", "14.0 л (велике відро)"),
            ],
            help_text="Об'єм банки за каталогом виробника (Caparol, Tikkurila, Kolorit, Ceresit)",
        ),
    ]

    def calculate(self, inputs: dict[str, Any]) -> CalculationResult:
        data = self.clean_inputs(inputs)
        area = data["area"]
        layers = int(data["layers_count"])
        paint_type = data["paint_type"]
        can_volume = float(data["can_volume"])

        rate = {
            "latex": 0.11,
            "acrylic": 0.12,
            "silicone": 0.13,
        }.get(paint_type, 0.12)

        type_title = {
            "latex": "Латексна інтер'єрна фарба",
            "acrylic": "Акрилова матова фарба",
            "silicone": "Силіконова вологостійка фарба",
        }.get(paint_type, "Фарба інтер'єрна")

        exact_liters = area * layers * rate
        liters_with_reserve = exact_liters * 1.10  # 10% на поглинання, валик та кювету
        cans_count = self.ceil(liters_with_reserve / can_volume)
        total_purchased_liters = cans_count * can_volume

        materials = [
            MaterialItem(
                name=f"{type_title} (банки {can_volume} л)",
                unit="банка",
                quantity=self.round_val(exact_liters / can_volume, 1),
                quantity_with_reserve=self.round_val(liters_with_reserve / can_volume, 1),
                purchase_quantity=cans_count,
                category="Лакофарбові матеріали",
                note=f"Разом {self.round_val(total_purchased_liters, 1)} л фарби у {cans_count} банках",
            ),
            MaterialItem(
                name="Стрічка малярна паперова (скотч 50 мм × 50 м)",
                unit="рулон",
                quantity=self.ceil(math.sqrt(area) * 4 / 50.0),
                quantity_with_reserve=self.ceil(math.sqrt(area) * 4 / 50.0),
                purchase_quantity=self.ceil(math.sqrt(area) * 4 / 50.0),
                category="Захисні матеріали",
                note="Для захисту плінтусів, стельових багетів, віконних та дверних рам",
            ),
            MaterialItem(
                name="Валик малярний мікрофібра (ворс 9–11 мм)",
                unit="шт",
                quantity=1,
                quantity_with_reserve=1,
                purchase_quantity=1,
                category="Інструменти",
                note="Забезпечує мінімальну шагрень та відсутність смуг",
            ),
        ]

        warnings = []
        if layers == 1:
            warnings.append("Фарбування в 1 шар часто залишає смуги та просвіти шпаклівки. Для ідеального фінішного результату завжди рекомендується щонайменше 2 шари.")

        recommendations = [
            "Перед фарбуванням стіни мають бути бездоганно прошпакльовані, відшліфовані, знепилені та заґрунтовані.",
            "Фарбуйте кожну стіну безперервно методом «мокрим по мокрому» від кута до кута без зупинок посередині площини.",
            "Знімайте малярну стрічку відразу після нанесення фарби, поки шар ще вологий, щоб не пошкодити край плівки.",
        ]

        totals = {
            "Площа": f"{area} м²",
            "Кількість шарів": f"{layers}",
            "Розрахунковий літраж": f"{self.round_val(liters_with_reserve, 1)} л",
            "Кількість банок": f"{cans_count} шт",
        }

        return CalculationResult(
            materials=materials,
            totals=totals,
            warnings=warnings,
            recommendations=recommendations,
        )
