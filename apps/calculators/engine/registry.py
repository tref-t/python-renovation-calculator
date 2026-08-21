from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .base import BaseCalculator


class CalculatorRegistry:
    """Реєстр усіх доступних будівельних калькуляторів."""
    _calculators: dict[str, BaseCalculator] = {}
    _categories: dict[str, str] = {}  # slug -> title

    @classmethod
    def register(cls, calculator: BaseCalculator) -> None:
        """Реєструє калькулятор у системі."""
        cls._calculators[calculator.id] = calculator
        if calculator.category_slug and calculator.category:
            cls._categories[calculator.category_slug] = calculator.category

    @classmethod
    def get(cls, calc_id: str) -> BaseCalculator | None:
        """Повертає калькулятор за його id (slug)."""
        return cls._calculators.get(calc_id)

    @classmethod
    def all(cls) -> list[BaseCalculator]:
        """Повертає список усіх зареєстрованих калькуляторів."""
        return list(cls._calculators.values())

    @classmethod
    def get_by_category(cls, category_slug: str) -> list[BaseCalculator]:
        """Фільтрує калькулятори за слагом категорії."""
        return [c for c in cls._calculators.values() if c.category_slug == category_slug]

    @classmethod
    def categories(cls) -> list[dict[str, str]]:
        """Повертає список категорій з кількістю калькуляторів."""
        result = []
        for slug, title in cls._categories.items():
            count = len(cls.get_by_category(slug))
            result.append({
                "slug": slug,
                "title": title,
                "count": count,
            })
        return result

    @classmethod
    def search(cls, query: str) -> list[BaseCalculator]:
        """Швидкий пошук за запитом у назві, описі та ключових словах."""
        if not query:
            return cls.all()
        q = query.lower().strip()
        matches = []
        for c in cls._calculators.values():
            text_corpus = f"{c.title} {c.description} {c.category} {c.seo_keywords}".lower()
            if q in text_corpus:
                matches.append(c)
        return matches

    @classmethod
    def clear(cls) -> None:
        """Очищує реєстр (корисно для тестів)."""
        cls._calculators.clear()
        cls._categories.clear()


def register_all_calculators() -> None:
    """Імпортує та реєструє 10 основних калькуляторів."""
    CalculatorRegistry.clear()

    from apps.calculators.definitions.laminate import LaminateCalculator
    from apps.calculators.definitions.screed import ScreedCalculator
    from apps.calculators.definitions.tile import TileCalculator
    from apps.calculators.definitions.gasblock import GasblockCalculator
    from apps.calculators.definitions.brick import BrickCalculator
    from apps.calculators.definitions.plaster import PlasterCalculator
    from apps.calculators.definitions.putty import PuttyCalculator
    from apps.calculators.definitions.primer import PrimerCalculator
    from apps.calculators.definitions.paint import PaintCalculator
    from apps.calculators.definitions.wallpaper import WallpaperCalculator

    CalculatorRegistry.register(LaminateCalculator())
    CalculatorRegistry.register(ScreedCalculator())
    CalculatorRegistry.register(TileCalculator())
    CalculatorRegistry.register(GasblockCalculator())
    CalculatorRegistry.register(BrickCalculator())
    CalculatorRegistry.register(PlasterCalculator())
    CalculatorRegistry.register(PuttyCalculator())
    CalculatorRegistry.register(PrimerCalculator())
    CalculatorRegistry.register(PaintCalculator())
    CalculatorRegistry.register(WallpaperCalculator())
