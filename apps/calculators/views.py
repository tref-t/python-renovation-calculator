from django.http import Http404, JsonResponse
from django.shortcuts import render
from apps.calculators.engine.registry import CalculatorRegistry


def calculator_detail_view(request, calc_id: str):
    """Сторінка конкретного калькулятора з підтримкою реактивного оновлення через HTMX."""
    calculator = CalculatorRegistry.get(calc_id)
    if not calculator:
        raise Http404(f"Калькулятор '{calc_id}' не знайдено.")

    # Отримуємо вхідні дані з GET-параметрів або беремо значення за замовчуванням
    raw_inputs = {}
    for f in calculator.fields:
        if f.id in request.GET:
            raw_inputs[f.id] = request.GET[f.id]
        else:
            raw_inputs[f.id] = f.default_value

    # Очищуємо та розраховуємо
    cleaned_inputs = calculator.clean_inputs(raw_inputs)
    result = calculator.calculate(cleaned_inputs)

    context = {
        "calculator": calculator,
        "inputs": cleaned_inputs,
        "result": result,
        "fields": calculator.fields,
    }

    # Якщо це HTMX запит (зміна будь-якого поля форми) — повертаємо лише фрагмент з карткою результату
    if getattr(request, "htmx", False):
        return render(request, "calculators/partials/result_card.html", context)

    return render(request, "calculators/calculator_detail.html", context)


def category_view(request, category_slug: str):
    """Список калькуляторів обраної категорії."""
    calculators = CalculatorRegistry.get_by_category(category_slug)
    if not calculators:
        raise Http404(f"Категорію '{category_slug}' не знайдено.")

    category_title = calculators[0].category
    context = {
        "calculators": calculators,
        "category_title": category_title,
        "category_slug": category_slug,
        "categories": CalculatorRegistry.categories(),
    }
    return render(request, "calculators/category_list.html", context)


def api_calculate(request, calc_id: str):
    """JSON API для розрахунку калькулятора."""
    calculator = CalculatorRegistry.get(calc_id)
    if not calculator:
        return JsonResponse({"error": "Calculator not found"}, status=404)

    raw_inputs = request.GET.dict()
    cleaned = calculator.clean_inputs(raw_inputs)
    result = calculator.calculate(cleaned)

    return JsonResponse({
        "calculator_id": calculator.id,
        "title": calculator.title,
        "inputs": cleaned,
        "totals": result.totals,
        "warnings": result.warnings,
        "recommendations": result.recommendations,
        "materials": [
            {
                "name": m.name,
                "unit": m.unit,
                "quantity": m.quantity,
                "quantity_with_reserve": m.quantity_with_reserve,
                "purchase_quantity": m.purchase_quantity,
                "category": m.category,
                "note": m.note,
            }
            for m in result.materials
        ],
    })
