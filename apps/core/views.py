from django.shortcuts import render
from apps.calculators.engine.registry import CalculatorRegistry


def index_view(request):
    """Головна сторінка з пошуком, популярними калькуляторами та категоріями."""
    query = request.GET.get("q", "").strip()
    category_filter = request.GET.get("category", "").strip()

    if query:
        calculators = CalculatorRegistry.search(query)
    elif category_filter:
        calculators = CalculatorRegistry.get_by_category(category_filter)
    else:
        calculators = CalculatorRegistry.all()

    categories = CalculatorRegistry.categories()

    context = {
        "calculators": calculators,
        "categories": categories,
        "active_category": category_filter,
        "query": query,
        "total_calculators_count": len(CalculatorRegistry.all()),
    }
    return render(request, "core/index.html", context)


def about_view(request):
    """Сторінка про проект та будівельні стандарти."""
    return render(request, "core/about.html")
