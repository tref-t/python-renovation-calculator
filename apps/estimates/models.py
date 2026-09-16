from django.db import models
from django.db.models import Sum


class MaterialCategory(models.TextChoices):
    FLOORING = 'flooring', 'Підлога та стяжка'
    WALLS = 'walls', 'Стіни та кладка'
    PLASTER = 'plaster', 'Штукатурка та шпаклівка'
    FINISHES = 'finishes', 'Оздоблення та фарбування'
    CONSUMABLES = 'consumables', 'Витратні матеріали та кріплення'


class MaterialPrice(models.Model):
    name = models.CharField('Назва матеріалу', max_length=200, unique=True)
    category = models.CharField('Категорія', max_length=30, choices=MaterialCategory.choices, default=MaterialCategory.FLOORING)
    unit = models.CharField('Одиниця виміру', max_length=30, help_text='м², мішок 25кг, упак, відро, шт, л')
    price_uah = models.DecimalField('Ціна (грн)', max_digits=10, decimal_places=2)
    is_active = models.BooleanField('Активний для розрахунків', default=True)
    updated_at = models.DateTimeField('Останнє оновлення', auto_now=True)

    class Meta:
        verbose_name = 'Ціна на матеріал'
        verbose_name_plural = 'Каталог цін на матеріали'
        ordering = ['category', 'name']

    def __str__(self):
        return f"{self.name} — {self.price_uah} грн / {self.unit}"


class ProjectStatus(models.TextChoices):
    DRAFT = 'draft', 'Чернетка'
    IN_PROGRESS = 'in_progress', 'В роботі'
    COMPLETED = 'completed', 'Завершено'
    ARCHIVED = 'archived', 'В архіві'


class Project(models.Model):
    name = models.CharField('Назва проекту / об\'єкта', max_length=200, help_text='Наприклад: Квартира вул. Хрещатик 15, кв. 42')
    client_name = models.CharField('Замовник / Клієнт', max_length=150, blank=True)
    client_phone = models.CharField('Телефон клієнта', max_length=50, blank=True)
    address = models.CharField('Адреса об\'єкта', max_length=255, blank=True)
    status = models.CharField('Статус проекту', max_length=20, choices=ProjectStatus.choices, default=ProjectStatus.DRAFT)
    notes = models.TextField('Нотатки та коментарі виконроба', blank=True)
    created_at = models.DateTimeField('Створено', auto_now_add=True)
    updated_at = models.DateTimeField('Оновлено', auto_now=True)

    class Meta:
        verbose_name = 'Будівельний об\'єкт'
        verbose_name_plural = 'Будівельні проекти'
        ordering = ['-updated_at']

    def __str__(self):
        return self.name

    @property
    def total_cost(self):
        result = self.estimates.aggregate(total=Sum('estimated_cost'))['total']
        return result or 0

    @property
    def estimates_count(self):
        return self.estimates.count()


class CalculationEstimate(models.Model):
    CALCULATOR_CHOICES = [
        ('laminate', 'Ламінат та паркетна дошка'),
        ('screed', 'Стяжка підлоги'),
        ('tile', 'Керамічна плитка та клей'),
        ('gasblock', 'Газобетонні блоки'),
        ('brick', 'Будівельна цегла'),
        ('plaster', 'Штукатурка стін'),
        ('putty', 'Шпаклівка стін та стелі'),
        ('primer', 'Ґрунтовка поверхонь'),
        ('paint', 'Фарба для стін і стелі'),
        ('wallpaper', 'Шпалери та клей'),
    ]

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='estimates', verbose_name='Об\'єкт / Проект')
    calculator_id = models.CharField('Тип калькулятора', max_length=50, choices=CALCULATOR_CHOICES)
    title = models.CharField('Назва розрахунку', max_length=200, help_text='Наприклад: Укладання ламінату у спальні')
    area = models.DecimalField('Розрахункова площа / об\'єм', max_digits=8, decimal_places=2, default=0, help_text='м² або м³')
    inputs_data = models.JSONField('Параметри розрахунку (JSON)', default=dict, blank=True)
    materials_data = models.JSONField('Специфікація матеріалів (JSON)', default=list, blank=True)
    estimated_cost = models.DecimalField('Орієнтовна вартість матеріалів (грн)', max_digits=12, decimal_places=2, default=0)
    notes = models.TextField('Примітки майстра', blank=True)
    created_at = models.DateTimeField('Дата створення', auto_now_add=True)

    class Meta:
        verbose_name = 'Кошторисний розрахунок'
        verbose_name_plural = 'Збережені кошториси'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} ({self.get_calculator_id_display()})"
