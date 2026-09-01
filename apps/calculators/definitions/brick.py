from __future__ import annotations

import math
from typing import Any

from apps.calculators.engine.base import (
    BaseCalculator,
    CalculationResult,
    CalculatorField,
    MaterialItem,
)


class BrickCalculator(BaseCalculator):
    id = "brick"
    title = "Калькулятор цегли"
    category = "Стіни"
    category_slug = "walls"
    description = "Розрахунок одинарної, полуторної та подвійної цегли, об'єму розчину, цементу та піску для мурування стін."
    icon = "grid"
    seo_keywords = "калькулятор цегли, розрахунок цегли, цегла на стіну, одинарна цегла, розчин для кладки цегли"
    seo_text = """
    Калькулятор розраховує кількість будівельної або облицювальної цегли в штуках для різних типів кладки
    (в півцеглини, в одну, півтори, дві або дві з половиною цеглини) з урахуванням товщини розчинного шва 10 мм.
    """

    fields = [
        CalculatorField(
            id="wall_length",
            label="Загальна довжина стін",
            field_type="number",
            unit="м",
            default_value=20.0,
            min_value=1.0,
            max_value=500.0,
            step=1.0,
            help_text="Сумарна довжина стін кладки",
        ),
        CalculatorField(
            id="wall_height",
            label="Висота стін",
            field_type="number",
            unit="м",
            default_value=2.8,
            min_value=1.0,
            max_value=15.0,
            step=0.1,
            help_text="Висота кладки в метрах",
        ),
        CalculatorField(
            id="wall_thickness",
            label="Товщина кладки",
            field_type="select",
            default_value="250",
            options=[
                ("120", "0.5 цегли (120 мм — перегородка)"),
                ("250", "1.0 цегли (250 мм)"),
                ("380", "1.5 цегли (380 мм)"),
                ("510", "2.0 цегли (510 мм — несуча)"),
                ("640", "2.5 цегли (640 мм)"),
            ],
            help_text="Товщина стіни визначає витрату цегли на 1 м²",
        ),
        CalculatorField(
            id="brick_type",
            label="Тип та розмір цегли",
            field_type="select",
            default_value="single",
            options=[
                ("single", "Одинарна 1НФ (250×120×65 мм)"),
                ("one_and_half", "Полуторна 1.4НФ (250×120×88 мм)"),
                ("double", "Подвійна 2.1НФ (250×120×138 мм)"),
            ],
            help_text="Стандартні типорозміри цегли за ДСТУ",
        ),
        CalculatorField(
            id="openings_area",
            label="Площа вікон та дверей",
            field_type="number",
            unit="м²",
            default_value=5.0,
            min_value=0.0,
            max_value=300.0,
            step=0.5,
            help_text="Площа, яка віднімається з об'єму кладки",
        ),
    ]

    def calculate(self, inputs: dict[str, Any]) -> CalculationResult:
        data = self.clean_inputs(inputs)
        length = data["wall_length"]
        height = data["wall_height"]
        thickness_mm = float(data["wall_thickness"])
        brick_type = data["brick_type"]
        openings_area = data["openings_area"]

        gross_area = length * height
        net_area = max(0.1, gross_area - openings_area)
        thickness_m = thickness_mm / 1000.0
        wall_volume_m3 = net_area * thickness_m

        # Нормативи витрати цегли на 1 м³ кладки з урахуванням швів 10 мм за ДСТУ/СНиП:
        # Одинарна (65 мм): ~394 шт/м³ (без шва 512 шт)
        # Полуторна (88 мм): ~302 шт/м³ (без шва 378 шт)
        # Подвійна (138 мм): ~200 шт/м³ (без шва 242 шт)
        bricks_per_m3 = {
            "single": 394.0,
            "one_and_half": 302.0,
            "double": 200.0,
        }.get(brick_type, 394.0)

        brick_name = {
            "single": "Цегла одинарна 250×120×65 мм",
            "one_and_half": "Цегла полуторна 250×120×88 мм",
            "double": "Цегла подвійна 250×120×138 мм",
        }.get(brick_type, "Цегла одинарна 250×120×65 мм")

        # Кількість цегли з запасом 5% на бій та розколювання
        exact_bricks = wall_volume_m3 * bricks_per_m3
        bricks_with_reserve = self.ceil(exact_bricks * 1.05)

        # Витрата розчину на 1 м³ цегляної кладки становить близько 0.24 м³ (24%)
        mortar_volume_m3 = wall_volume_m3 * 0.24

        # На 1 м³ кладочного розчину М100 (1:4) потрібно ~350 кг цементу М500 та 1.4 т піску
        cement_kg = mortar_volume_m3 * 350.0
        cement_bags = self.ceil(cement_kg / 25.0)  # мішки 25 кг
        sand_tons = mortar_volume_m3 * 1.4

        materials = [
            MaterialItem(
                name=brick_name,
                unit="шт",
                quantity=self.round_val(exact_bricks, 0),
                quantity_with_reserve=bricks_with_reserve,
                purchase_quantity=bricks_with_reserve,
                category="Стінові матеріали",
                note=f"Об'єм кладки {self.round_val(wall_volume_m3, 2)} м³ (запас 5%)",
            ),
            MaterialItem(
                name="Цемент М500 для розчину (мішки 25 кг)",
                unit="мішок",
                quantity=self.round_val(cement_kg / 25.0, 1),
                quantity_with_reserve=self.round_val(cement_kg / 25.0, 1),
                purchase_quantity=cement_bags,
                category="В'яжучі та суміші",
                note=f"Разом {self.round_val(cement_kg, 0)} кг цементу",
            ),
            MaterialItem(
                name="Пісок митий кар'єрний або річковий",
                unit="т",
                quantity=self.round_val(sand_tons, 2),
                quantity_with_reserve=self.round_val(sand_tons * 1.05, 2),
                purchase_quantity=self.ceil(sand_tons * 1.05),
                category="Інертні матеріали",
                note=f"Об'єм готового розчину ~{self.round_val(mortar_volume_m3, 2)} м³",
            ),
        ]

        # Кладочна армувальна сітка (кожні 5 рядів для одинарної або 4 для полуторної)
        rows_per_meter = 1000.0 / (65.0 + 10.0 if brick_type == "single" else 88.0 + 10.0)
        total_rows = self.ceil(height * rows_per_meter)
        grid_layers = self.ceil(total_rows / 5)
        grid_sqm = net_area * 0.25 * grid_layers * 1.10
        materials.append(
            MaterialItem(
                name="Сітка кладочна армувальна 50×50 мм",
                unit="м²",
                quantity=self.round_val(grid_sqm, 1),
                quantity_with_reserve=self.round_val(grid_sqm, 1),
                purchase_quantity=self.ceil(grid_sqm),
                category="Армування",
                note=f"Для армування зв'язки {grid_layers} рядів кладки",
            )
        )

        warnings = []
        if thickness_mm == 120 and height > 3.0:
            warnings.append("Перегородка в 0.5 цеглини висотою понад 3 метри має недостатню стійкість: необхідна прив'язка анкерами до несучих стін через кожні 3–4 ряди.")

        recommendations = [
            "При кладці в жарку або суху погоду обов'язково змочуйте керамічну цеглу водою, щоб вона не витягувала вологу з розчину.",
            "Товщина горизонтальних швів повинна становити 12 мм, вертикальних — 10 мм.",
            "Перевіряйте вертикальність кутів схилом або лазерним рівнем кожні 3–4 ряди.",
        ]

        totals = {
            "Чиста площа стін": f"{self.round_val(net_area, 1)} м²",
            "Об'єм кладки": f"{self.round_val(wall_volume_m3, 2)} м³",
            "Об'єм розчину": f"{self.round_val(mortar_volume_m3, 2)} м³",
            "Загальна кількість цегли": f"{bricks_with_reserve} шт",
        }

        return CalculationResult(
            materials=materials,
            totals=totals,
            warnings=warnings,
            recommendations=recommendations,
        )
