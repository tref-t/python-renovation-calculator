from __future__ import annotations

import math
from typing import Any

from apps.calculators.engine.base import (
    BaseCalculator,
    CalculationResult,
    CalculatorField,
    MaterialItem,
)


class GasblockCalculator(BaseCalculator):
    id = "gasblock"
    title = "Калькулятор газоблоку"
    category = "Стіни"
    category_slug = "walls"
    description = "Розрахунок газобетонних блоків (шт, м³, піддони), клею для тонкошовного мурування та арматури для штроблення."
    icon = "box"
    seo_keywords = "калькулятор газоблоку, розрахунок газобетону, блоки на будинок, клей для газоблоку, армування газобетону"
    seo_text = """
    Калькулятор розраховує кількість газобетонних блоків для зовнішніх несучих стін або міжкімнатних перегородок.
    Враховує віднімання площі віконних і дверних отворів, нормативну товщину шва 2–3 мм, розрахунок клею та армування рядів арматурою Ø8 мм.
    """

    fields = [
        CalculatorField(
            id="wall_length",
            label="Загальна довжина стін",
            field_type="number",
            unit="м",
            default_value=40.0,
            min_value=1.0,
            max_value=500.0,
            step=1.0,
            help_text="Сумарна довжина всіх стін обраної товщини",
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
            help_text="Висота поверху в чистоті",
        ),
        CalculatorField(
            id="block_thickness",
            label="Товщина блоку",
            field_type="select",
            default_value="300",
            options=[
                ("100", "100 мм (перегородковий)"),
                ("150", "150 мм (перегородковий)"),
                ("200", "200 мм (внутрішні несучі)"),
                ("250", "250 мм (несучі стіни)"),
                ("300", "300 мм (популярний розмір)"),
                ("375", "375 мм (енергоефективний)"),
                ("400", "400 мм (без додаткового утеплення)"),
            ],
            help_text="Товщина стіни відповідає товщині блоку",
        ),
        CalculatorField(
            id="block_height",
            label="Висота блоку",
            field_type="select",
            default_value="200",
            options=[
                ("200", "200 мм (стандарт)"),
                ("250", "250 мм (високий)"),
            ],
            help_text="Стандартна висота газоблоку за каталогами (AEROC, UDK, Стоунлайт)",
        ),
        CalculatorField(
            id="openings_area",
            label="Площа вікон та дверей",
            field_type="number",
            unit="м²",
            default_value=12.0,
            min_value=0.0,
            max_value=500.0,
            step=0.5,
            help_text="Сумарна площа всіх прорізів у цих стінах",
        ),
        CalculatorField(
            id="pallet_volume",
            label="Об'єм одного піддона",
            field_type="number",
            unit="м³",
            default_value=1.8,
            min_value=0.5,
            max_value=3.0,
            step=0.1,
            help_text="Стандартна місткість заводського піддона (зазвичай 1.68–2.16 м³)",
        ),
    ]

    def calculate(self, inputs: dict[str, Any]) -> CalculationResult:
        data = self.clean_inputs(inputs)
        length = data["wall_length"]
        height = data["wall_height"]
        thickness_mm = float(data["block_thickness"])
        block_height_mm = float(data["block_height"])
        openings_area = data["openings_area"]
        pallet_volume = max(0.5, data["pallet_volume"])

        gross_area = length * height
        net_area = max(0.1, gross_area - openings_area)

        # Розміри блоку в метрах (стандартна довжина 600 мм = 0.6 м)
        b_len = 0.60
        b_h = block_height_mm / 1000.0
        b_th = thickness_mm / 1000.0

        block_face_area = b_len * b_h
        blocks_per_sqm = 1.0 / block_face_area
        one_block_vol = b_len * b_h * b_th

        # Кількість блоків з запасом 5% на підрізку
        exact_blocks = net_area * blocks_per_sqm
        blocks_with_reserve = self.ceil(exact_blocks * 1.05)
        total_vol_m3 = blocks_with_reserve * one_block_vol
        pallets_count = self.ceil(total_vol_m3 / pallet_volume)

        materials = [
            MaterialItem(
                name=f"Газобетонний блок 600×{int(thickness_mm)}×{int(block_height_mm)} мм",
                unit="шт",
                quantity=self.round_val(exact_blocks, 1),
                quantity_with_reserve=blocks_with_reserve,
                purchase_quantity=blocks_with_reserve,
                category="Стінові блоки",
                note=f"Разом {self.round_val(total_vol_m3, 2)} м³ (~{pallets_count} заводських піддонів)",
            )
        ]

        # Клей для тонкошовного мурування (витрата ~28 кг на 1 м³ кладки при шві 2 мм)
        glue_kg = total_vol_m3 * 28.0
        glue_bags = self.ceil(glue_kg / 25.0)
        materials.append(
            MaterialItem(
                name="Клей для газобетону тонкошовний (мішки 25 кг)",
                unit="мішок",
                quantity=self.round_val(glue_kg / 25.0, 1),
                quantity_with_reserve=self.round_val(glue_kg / 25.0, 1),
                purchase_quantity=glue_bags,
                category="Кладочні суміші",
                note=f"Витрата {self.round_val(glue_kg, 0)} кг на весь об'єм кладки",
            )
        )

        # Армування: 1-й ряд, підвіконні зони та кожен 3-й або 4-й ряд (2 прутки Ø8 мм у штроби)
        rows_count = self.ceil((height * 1000.0) / block_height_mm)
        reinforced_rows = max(2, self.ceil(rows_count / 3))
        # 2 прутки вздовж довжини стін + 10% нахльост і загини на кутах
        rebar_length_m = length * 2 * reinforced_rows * 1.10
        materials.append(
            MaterialItem(
                name="Арматура рифлена А500С Ø8 мм для штроб",
                unit="м.п.",
                quantity=self.round_val(length * 2 * reinforced_rows, 1),
                quantity_with_reserve=self.round_val(rebar_length_m, 1),
                purchase_quantity=self.ceil(rebar_length_m),
                category="Армування",
                note=f"Для армування {reinforced_rows} рядів у 2 нитки (прутки по 3 або 6 м)",
            )
        )

        warnings = []
        if openings_area >= gross_area * 0.4:
            warnings.append("Велика площа прорізів (понад 40% площі стіни): потрібен інженерний розрахунок міцності простінків та армопояса.")
        if thickness_mm < 300 and height > 3.2:
            warnings.append("При товщині блоку менше 300 мм і висоті стіни понад 3.2 м потрібні додаткові залізобетонні колони жорсткості.")

        recommendations = [
            "Перший ряд блоків обов'язково укладається на цементно-піщаний розчин поверх руберойду (гідроізоляції фундаменту).",
            "Штроби під арматуру ретельно очищайте від пилу щіткою або феном і заповнюйте клеєм перед укладанням прутка.",
            "Під плити або балки перекриття обов'язково влаштовуйте монолітний залізобетонний армопояс.",
        ]

        totals = {
            "Чиста площа стін": f"{self.round_val(net_area, 1)} м²",
            "Загальний об'єм блоків": f"{self.round_val(total_vol_m3, 2)} м³",
            "Кількість піддонів": f"{pallets_count} шт",
            "Кількість рядів у кладці": f"{rows_count} рядів",
        }

        return CalculationResult(
            materials=materials,
            totals=totals,
            warnings=warnings,
            recommendations=recommendations,
        )
