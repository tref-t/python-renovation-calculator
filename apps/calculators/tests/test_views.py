import pytest
from django.urls import reverse
from django.test import Client


@pytest.fixture
def client():
    return Client()


@pytest.mark.django_db
def test_home_page(client):
    response = client.get(reverse("core:index"))
    assert response.status_code == 200
    assert "МайстерОк" in response.content.decode("utf-8")
    assert "Ламінат" in response.content.decode("utf-8")


@pytest.mark.django_db
def test_about_page(client):
    response = client.get(reverse("core:about"))
    assert response.status_code == 200
    assert "Будівельні норми" in response.content.decode("utf-8")


@pytest.mark.django_db
@pytest.mark.parametrize("calc_id", [
    "laminate", "screed", "tile", "gasblock", "brick",
    "plaster", "putty", "primer", "paint", "wallpaper"
])
def test_all_calculator_pages(client, calc_id):
    url = reverse("calculators:detail", kwargs={"calc_id": calc_id})
    response = client.get(url)
    assert response.status_code == 200
    assert "Специфікація матеріалів" in response.content.decode("utf-8")


@pytest.mark.django_db
def test_calculator_htmx_partial(client):
    url = reverse("calculators:detail", kwargs={"calc_id": "laminate"})
    response = client.get(
        f"{url}?area=35.0&laying_method=diagonal",
        HTTP_HX_REQUEST="true"
    )
    assert response.status_code == 200
    content = response.content.decode("utf-8")
    assert '<div id="result-card"' in content
    # In partial, base.html wrapper should not be present
    assert "<!DOCTYPE html>" not in content


@pytest.mark.django_db
def test_calculator_json_api(client):
    url = reverse("calculators:api", kwargs={"calc_id": "screed"})
    response = client.get(f"{url}?area=30&thickness=60&screed_type=ready_mix")
    assert response.status_code == 200
    data = response.json()
    assert data["calculator_id"] == "screed"
    assert "materials" in data
    assert len(data["materials"]) > 0
    assert "totals" in data


@pytest.mark.django_db
def test_category_page(client):
    url = reverse("calculators:category", kwargs={"category_slug": "flooring"})
    response = client.get(url)
    assert response.status_code == 200
    assert "Підлога" in response.content.decode("utf-8")
