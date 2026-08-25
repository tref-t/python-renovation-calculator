from __future__ import annotations

import math
from typing import Any

from apps.calculators.engine.base import (
    BaseCalculator,
    CalculationResult,
    CalculatorField,
    MaterialItem,
)


class ScreedCalculator(BaseCalculator):
    id = "screed"
    title = "Калькулятор стяжки підлоги"
    category = "Підлога"
    category_slug = "flooring"
    description = "Розрахунок об'єму розчину, мішків суміші, цементу, піску, армування, маяків та демпферної стрічки для вирівнювання підлоги."
    icon = "hammer"
    seo_keywords = "калькулятор стяжки, розрахунок стяжки підлоги, цемент і пісок на стяжку, суміш для стяжки, товщина стяжки"
    seo_text = """
    Калькулятор стяжки підлоги розраховує точний об'єм бетонного розчину з урахуванням технологічного коефіцієнта усадки (15%).
    Підтримує розрахунок як готових фасованих піскобетонів (М150, М300), так і класичного самозамісу цементу з піском (пропорція 1:3) або сучасної напівсухої стяжки з фіброволокном.
    """

    fields = [
        CalculatorField(
            id="area",
            label="Площа стяжки",
            field_type="number",
            unit="м²",
            default_value=25.0,
            min_value=1.0,
            max_value=1000.0,
            step=1.0,
            help_text="Площа підлоги під заливку",
        ),
        CalculatorField(
            id="thickness",
            label="Товщина шару",
            field_type="number",
            unit="мм",
            default_value=50.0,
            min_value=10.0,
            max_value=200.0,
            step=5.0,
            help_text="Середня товщина стяжки (мінімум 30 мм для ЦПС по плиті, 45-50 мм для теплої підлоги)",
        ),
        CalculatorField(
            id="screed_type",
            label="Тип суміші",
            field_type="select",
            default_value="ready_mix",
            options=[
                ("ready_mix", "Готова суха суміш ЦПС М150 / М200 (мішки)"),
                ("handmade_1_3", "Класичний самозаміс 1:3 (цемент М500 + пісок)"),
                ("semidry", "Напівсуха стяжка з фіброволокном"),
            ],
            help_text="Оберіть технологію приготування розчину",
        ),
        CalculatorField(
            id="bag_weight",
            label="Фасовка мішка суміші",
            field_type="select",
            default_value="25",
            options=[
                ("25", "Мішки по 25 кг"),
                ("50", "Мішки по 50 кг"),
            ],
            help_text="Стандартний розмір мішка готової суміші або цементу",
        ),
        CalculatorField(
            id="reinforcement",
            label="Армування",
            field_type="select",
            default_value="mesh",
            options=[
                ("mesh", "Металева або композитна сітка 100×100 мм"),
                ("fiber", "Поліпропіленова фібра (0.9 кг/м³)"),
                ("none", "Без додаткового армування"),
            ],
            help_text="Обов'язкове для плаваючих стяжок та водяної теплої підлоги",
        ),
        CalculatorField(
            id="include_damper",
            label="Демпферна стрічка по периметру",
            field_type="toggle",
            default_value=True,
            help_text="Компенсує теплове розширення та запобігає передачі ударного шуму на стіни",
        ),
    ]

    def calculate(self, inputs: dict[str, Any]) -> CalculationResult:
        data = self.clean_inputs(inputs)
        area = data["area"]
        thickness_mm = data["thickness"]
        screed_type = data["screed_type"]
        bag_weight = float(data["bag_weight"])
        reinforcement = data["reinforcement"]
        include_damper = data["include_damper"]

        thickness_m = thickness_mm / 1000.0
        # Геометричний об'єм з урахуванням усадки та нерівностей плити (+15%)
        net_volume = area * thickness_m
        compaction_factor = 1.15
        total_volume = net_volume * compaction_factor

        materials = []

        if screed_type == "ready_mix":
            # Густина готового розчину ЦПС ~2000 кг/м³
            total_dry_mix_kg = total_volume * 2000.0
            bags_count = self.ceil(total_dry_mix_kg / bag_weight)
            materials.append(
                MaterialItem(
                    name=f"Суха будівельна суміш ЦПС ({int(bag_weight)} кг)",
                    unit="мішок",
                    quantity=self.round_val(total_dry_mix_kg / bag_weight, 1),
                    quantity_with_reserve=self.round_val(total_dry_mix_kg / bag_weight, 1),
                    purchase_quantity=bags_count,
                    category="В'яжучі та суміші",
                    note=f"Разом {self.round_val(total_dry_mix_kg, 0)} кг сухої суміші",
                )
            )
        elif screed_type == "handmade_1_3":
            # 1 частина цементу, 3 частини піску
            # На 1 м³ розчину потрібно близько 450 кг цементу М500 і 1.4 тонни піску
            cement_kg = total_volume * 450.0
            cement_bags = self.ceil(cement_kg / bag_weight)
            sand_tons = total_volume * 1.4
            water_liters = total_volume * 190.0

            materials.append(
                MaterialItem(
                    name=f"Цемент М500 ({int(bag_weight)} кг)",
                    unit="мішок",
                    quantity=self.round_val(cement_kg / bag_weight, 1),
                    quantity_with_reserve=self.round_val(cement_kg / bag_weight, 1),
                    purchase_quantity=cement_bags,
                    category="В'яжучі та суміші",
                    note=f"Разом {self.round_val(cement_kg, 0)} кг цементу",
                )
            )
            materials.append(
                MaterialItem(
                    name="Пісок митий річковий / кар'єрний",
                    unit="т",
                    quantity=self.round_val(sand_tons, 2),
                    quantity_with_reserve=self.round_val(sand_tons * 1.05, 2),
                    purchase_quantity=self.ceil(sand_tons * 1.05),
                    category="Інертні матеріали",
                    note="Модуль крупності 1.8–2.5 мм, без глини",
                )
            )
            materials.append(
                MaterialItem(
                    name="Вода для замісу",
                    unit="л",
                    quantity=self.round_val(water_liters, 0),
                    quantity_with_reserve=self.round_val(water_liters, 0),
                    purchase_quantity=int(water_liters),
                    category="Супутні матеріали",
                    note="Приблизно 0.42–0.5 л на 1 кг цементу",
                )
            )
        else:  # semidry
            # Напівсуха стяжка густиною ~1800 кг/м³
            total_semidry_kg = total_volume * 1800.0
            materials.append(
                MaterialItem(
                    name="Розчин напівсухої стяжки",
                    unit="м³",
                    quantity=self.round_val(total_volume, 2),
                    quantity_with_reserve=self.round_val(total_volume, 2),
                    purchase_quantity=self.ceil(total_volume),
                    category="Основні матеріали",
                    note=f"Вага суміші близько {self.round_val(total_semidry_kg / 1000, 2)} т",
                )
            )

        # Армування
        if reinforcement == "mesh":
            mesh_sqm = area * 1.15  # 15% нахльост
            materials.append(
                MaterialItem(
                    name="Сітка армувальна кладочна",
                    unit="м²",
                    quantity=self.round_val(area, 1),
                    quantity_with_reserve=self.round_val(mesh_sqm, 1),
                    purchase_quantity=self.ceil(mesh_sqm),
                    category="Армування",
                    note="Вкладається на фіксатори з відривом від основи на 15–20 мм",
                )
            )
        elif reinforcement == "fiber":
            # 0.9 кг поліпропіленової фібри на 1 м³ розчину
            fiber_kg = total_volume * 0.9
            fiber_packages = self.ceil(fiber_kg / 0.6)  # стандартні пакети по 0.6 кг
            materials.append(
                MaterialItem(
                    name="Фіброволокно поліпропіленове (пакети 0.6 кг)",
                    unit="шт",
                    quantity=self.round_val(fiber_kg / 0.6, 1),
                    quantity_with_reserve=self.round_val(fiber_kg / 0.6, 1),
                    purchase_quantity=fiber_packages,
                    category="Армування",
                    note=f"Витрата {self.round_val(fiber_kg, 2)} кг фібри на весь об'єм",
                )
            )

        # Демпферна стрічка
        perimeter = math.sqrt(area) * 4
        if include_damper:
            damper_length = perimeter * 1.05
            damper_rolls = self.ceil(damper_length / 25.0)  # рулони по 25 м
            materials.append(
                MaterialItem(
                    name="Демпферна стрічка (рулони по 25 м)",
                    unit="рулон",
                    quantity=self.round_val(perimeter / 25.0, 1),
                    quantity_with_reserve=self.round_val(damper_length / 25.0, 1),
                    purchase_quantity=damper_rolls,
                    category="Ізоляційні матеріали",
                    note=f"Периметр кімнати ~{self.round_val(perimeter, 1)} м",
                )
            )

        # Маяки штукатурні Т-подібні (крок 1.2-1.5 м)
        beacons_count = self.ceil(area / 2.0)
        materials.append(
            MaterialItem(
                name="Маяки направляючі 10 мм (рейки 3 м)",
                unit="шт",
                quantity=beacons_count,
                quantity_with_reserve=beacons_count,
                purchase_quantity=beacons_count,
                category="Монтажні елементи",
                note="Встановлюються на розчинні горбки за лазерним рівнем",
            )
        )

        warnings = []
        if thickness_mm < 30.0:
            warnings.append("Товщина менше 30 мм: класична цементна стяжка може потріскатися або відшаруватися. Рекомендується наливна підлога або контактний шар бетоноконтакту.")
        if thickness_mm > 80.0:
            warnings.append("Товщина понад 80 мм: значна вага на перекриття. Рекомендується підсипка керамзиту або полістиролбетон у нижній шар.")

        recommendations = [
            "Після заливки накрийте стяжку поліетиленовою плівкою на 7–10 днів для утримання вологи.",
            "Не вмикайте теплу підлогу до повного набору міцності бетону (мінімум 28 діб).",
            "Обов'язково видаліть металеві маяки через 1-2 доби після заливки та загладьте борозни розчином, щоб уникнути появи іржі.",
        ]

        totals = {
            "Площа стяжки": f"{area} м²",
            "Товщина": f"{thickness_mm} мм",
            "Чистий об'єм розчину": f"{self.round_val(net_volume, 3)} м³",
            "Об'єм з усадкою (15%)": f"{self.round_val(total_volume, 3)} м³",
        }

        return CalculationResult(
            materials=materials,
            totals=totals,
            warnings=warnings,
            recommendations=recommendations,
        )
