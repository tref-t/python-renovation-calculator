from __future__ import annotations

import math
from typing import Any

from apps.calculators.engine.base import (
    BaseCalculator,
    CalculationResult,
    CalculatorField,
    MaterialItem,
)


class WallpaperCalculator(BaseCalculator):
    id = "wallpaper"
    title = "Калькулятор шпалер"
    category = "Оздоблення"
    category_slug = "finishes"
    description = "Розрахунок кількості рулонів шпалер за розмірами кімнати, шириною рулону (0.53 або 1.06 м) та рапортом малюнка."
    icon = "maximize"
    seo_keywords = "калькулятор шпалер, розрахунок шпалер на кімнату, скільки рулонів шпалер, шпалери метрові розрахунок, клей для шпалер"
    seo_text = """
    Калькулятор шпалер розраховує кількість цілих смуг (полотен) та рулонів для стандартних (0.53 м)
    і метрових (1.06 м) шпалер з урахуванням зсуву рапорту малюнка та запасу на верхню й нижню підрізку.
    """

    fields = [
        CalculatorField(
            id="room_length",
            label="Довжина кімнати",
            field_type="number",
            unit="м",
            default_value=5.0,
            min_value=1.0,
            max_value=100.0,
            step=0.1,
            help_text="Довша стіна приміщення",
        ),
        CalculatorField(
            id="room_width",
            label="Ширина кімнати",
            field_type="number",
            unit="м",
            default_value=4.0,
            min_value=1.0,
            max_value=100.0,
            step=0.1,
            help_text="Коротша стіна приміщення",
        ),
        CalculatorField(
            id="ceiling_height",
            label="Висота стелі",
            field_type="number",
            unit="м",
            default_value=2.65,
            min_value=1.5,
            max_value=6.0,
            step=0.05,
            help_text="Від чистової підлоги до чистової стелі",
        ),
        CalculatorField(
            id="roll_width",
            label="Ширина рулону",
            field_type="select",
            default_value="1.06",
            options=[
                ("1.06", "1.06 м («метрові» флізелінові або вінілові)"),
                ("0.53", "0.53 м (класичний півметровий стандарт)"),
            ],
            help_text="Ширина полотна зазначена на етикетці рулону",
        ),
        CalculatorField(
            id="roll_length",
            label="Довжина рулону",
            field_type="select",
            default_value="10.05",
            options=[
                ("10.05", "10.05 м (стандартний єврорулон)"),
                ("25.0", "25.0 м (великий рулон під фарбування)"),
            ],
            help_text="Довжина намотки в одному рулоні",
        ),
        CalculatorField(
            id="pattern_repeat",
            label="Підгонка малюнка (рапорт)",
            field_type="select",
            default_value="0",
            options=[
                ("0", "Без підгонки / вільне стикування (рапорт 0 см)"),
                ("32", "Пряме або зміщене стикування 32 см"),
                ("64", "Великий рапорт зі зміщенням 64 см"),
            ],
            help_text="Великий рапорт збільшує довжину відрізу полотна та кількість відходів",
        ),
        CalculatorField(
            id="openings_area",
            label="Площа вікон та дверей",
            field_type="number",
            unit="м²",
            default_value=4.5,
            min_value=0.0,
            max_value=50.0,
            step=0.5,
            help_text="Сумарна площа дверних і віконних отворів",
        ),
    ]

    def calculate(self, inputs: dict[str, Any]) -> CalculationResult:
        data = self.clean_inputs(inputs)
        length = data["room_length"]
        width = data["room_width"]
        height = data["ceiling_height"]
        roll_width = float(data["roll_width"])
        roll_length = float(data["roll_length"])
        repeat_cm = float(data["pattern_repeat"])
        openings_area = data["openings_area"]

        # 1. Периметр приміщення
        perimeter = 2.0 * (length + width)

        # 2. Довжина одного відрізу полотна (висота + рапорт + 5 см технологічний запас на підрізку)
        cut_length = height + (repeat_cm / 100.0) + 0.05
        # Кількість цілих смуг з одного рулону
        strips_per_roll = math.floor(roll_length / cut_length)
        if strips_per_roll < 1:
            strips_per_roll = 1

        # 3. Сумарна кількість смуг за периметром
        total_strips = self.ceil(perimeter / roll_width)

        # 4. Коригування на отвори (якщо площа отворів велика, переводимо її в умовну ширину)
        openings_width = openings_area / max(1.8, height)
        deducted_strips = math.floor(openings_width / roll_width)
        effective_strips = max(1, total_strips - deducted_strips)

        # 5. Кількість рулонів
        rolls_count = self.ceil(effective_strips / strips_per_roll)

        # Площа обклеювання для розрахунку клею
        gross_walls_area = perimeter * height
        net_walls_area = max(1.0, gross_walls_area - openings_area)

        materials = [
            MaterialItem(
                name=f"Шпалери (рулони {roll_width}×{roll_length} м)",
                unit="рулон",
                quantity=self.round_val(effective_strips / strips_per_roll, 1),
                quantity_with_reserve=rolls_count,
                purchase_quantity=rolls_count,
                category="Оздоблювальні матеріали",
                note=f"Разом {effective_strips} смуг ({strips_per_roll} смуги з рулону)",
            )
        ]

        # Розрахунок клею для шпалер (1 стандартна пачка 250 г покриває близько 30–35 м² флізеліну)
        glue_packs = self.ceil(net_walls_area / 30.0)
        materials.append(
            MaterialItem(
                name="Клей для флізелінових/вінілових шпалер (пачки 250 г)",
                unit="пачка",
                quantity=self.round_val(net_walls_area / 30.0, 1),
                quantity_with_reserve=glue_packs,
                purchase_quantity=glue_packs,
                category="Клейові суміші",
                note=f"Для площі стін {self.round_val(net_walls_area, 1)} м²",
            )
        )

        materials.append(
            MaterialItem(
                name="Притискний шпатель / валик для розгладжування шпалер",
                unit="шт",
                quantity=1,
                quantity_with_reserve=1,
                purchase_quantity=1,
                category="Інструменти",
                note="Для видалення повітряних бульбашок від центру до країв",
            )
        )

        warnings = []
        if repeat_cm > 0 and strips_per_roll == 3 and (roll_length - (3 * cut_length)) > 1.5:
            warnings.append(f"Через підгонку малюнка ({int(repeat_cm)} см) з кожного рулону залишатиметься обрізок понад 1.5 м. Використовуйте залишки для зон над дверима та під вікнами.")

        recommendations = [
            "Звіряйте номер партії (Batch/Lot number) на всіх рулонах: різні партії можуть мати ледь помітну відмінність у відтінку.",
            "Для флізелінових шпалер клей наноситься безпосередньо на стіну, на самі полотна клей наносити не потрібно.",
            "Уникайте протягів та не відчиняйте вікна під час поклейки і до повного висихання шпалер (24–36 годин).",
        ]

        totals = {
            "Периметр кімнати": f"{self.round_val(perimeter, 1)} м",
            "Чиста площа стін": f"{self.round_val(net_walls_area, 1)} м²",
            "Смуг з одного рулону": f"{strips_per_roll} шт",
            "Потрібно смуг": f"{effective_strips} шт",
            "Кількість рулонів": f"{rolls_count} шт",
        }

        return CalculationResult(
            materials=materials,
            totals=totals,
            warnings=warnings,
            recommendations=recommendations,
        )
