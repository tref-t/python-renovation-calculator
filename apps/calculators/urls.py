from django.urls import path
from . import views

app_name = "calculators"

urlpatterns = [
    path("category/<slug:category_slug>/", views.category_view, name="category"),
    path("<slug:calc_id>/", views.calculator_detail_view, name="detail"),
    path("<slug:calc_id>/api/", views.api_calculate, name="api"),
]
