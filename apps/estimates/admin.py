from django.contrib import admin
from django.utils.html import format_html
from .models import MaterialPrice, Project, CalculationEstimate

admin.site.site_header = "МайстерОк — Панель адміністрування"
admin.site.site_title = "МайстерОк Адмін"
admin.site.index_title = "Керування будівельними проектами, кошторисами та цінами"


@admin.register(MaterialPrice)
class MaterialPriceAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'unit', 'price_uah', 'is_active', 'updated_at')
    list_filter = ('category', 'is_active', 'updated_at')
    search_fields = ('name', 'unit')
    list_editable = ('price_uah', 'is_active')
    ordering = ('category', 'name')
    list_per_page = 25


class CalculationEstimateInline(admin.TabularInline):
    model = CalculationEstimate
    extra = 0
    fields = ('title', 'calculator_id', 'area', 'estimated_cost', 'created_at')
    readonly_fields = ('created_at',)
    show_change_link = True


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'client_name', 'client_phone', 'status_badge', 'estimates_count_display', 'total_cost_display', 'updated_at')
    list_filter = ('status', 'created_at', 'updated_at')
    search_fields = ('name', 'client_name', 'client_phone', 'address', 'notes')
    inlines = [CalculationEstimateInline]
    date_hierarchy = 'created_at'
    list_per_page = 20

    fieldsets = (
        ('Основна інформація про об\'єкт', {
            'fields': ('name', 'status', 'address')
        }),
        ('Контакти замовника', {
            'fields': ('client_name', 'client_phone')
        }),
        ('Нотатки виконроба', {
            'fields': ('notes',)
        }),
    )

    @admin.display(description='Статус')
    def status_badge(self, obj):
        colors = {
            'draft': 'background: #f1f5f9; color: #475569;',
            'in_progress': 'background: #fef3c7; color: #b45309;',
            'completed': 'background: #dcfce7; color: #15803d;',
            'archived': 'background: #e2e8f0; color: #64748b;',
        }
        style = colors.get(obj.status, 'background: #f1f5f9; color: #475569;')
        return format_html(
            '<span style="padding: 4px 10px; border-radius: 9999px; font-size: 11px; font-weight: 700; {}">{}</span>',
            style,
            obj.get_status_display()
        )

    @admin.display(description='К-сть розрахунків')
    def estimates_count_display(self, obj):
        count = obj.estimates_count
        return f"{count} розр."

    @admin.display(description='Сума кошторису')
    def total_cost_display(self, obj):
        return f"{obj.total_cost:,.2f} грн".replace(',', ' ')


@admin.register(CalculationEstimate)
class CalculationEstimateAdmin(admin.ModelAdmin):
    list_display = ('title', 'project', 'calculator_badge', 'area_display', 'estimated_cost_display', 'created_at')
    list_filter = ('calculator_id', 'created_at', 'project__status')
    search_fields = ('title', 'project__name', 'notes')
    date_hierarchy = 'created_at'
    list_per_page = 25

    fieldsets = (
        ('Об\'єкт та калькулятор', {
            'fields': ('project', 'calculator_id', 'title', 'area')
        }),
        ('Фінанси', {
            'fields': ('estimated_cost',)
        }),
        ('Збережені дані розрахунку', {
            'classes': ('collapse',),
            'fields': ('inputs_data', 'materials_data')
        }),
        ('Коментарі майстра', {
            'fields': ('notes',)
        }),
    )

    @admin.display(description='Калькулятор')
    def calculator_badge(self, obj):
        return format_html(
            '<span style="background: #eff6ff; color: #1d4ed8; padding: 3px 8px; border-radius: 6px; font-size: 11px; font-weight: 600;">{}</span>',
            obj.get_calculator_id_display()
        )

    @admin.display(description='Площа/Об\'єм')
    def area_display(self, obj):
        return f"{obj.area} од."

    @admin.display(description='Вартість')
    def estimated_cost_display(self, obj):
        return f"{obj.estimated_cost:,.2f} грн".replace(',', ' ')
