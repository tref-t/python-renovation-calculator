from apps.calculators.engine.registry import CalculatorRegistry, register_all_calculators


def setup_module():
    register_all_calculators()


def test_registry_contains_ten_calculators():
    calcs = CalculatorRegistry.all()
    assert len(calcs) == 10
    ids = {c.id for c in calcs}
    expected = {
        "laminate", "screed", "tile", "gasblock", "brick",
        "plaster", "putty", "primer", "paint", "wallpaper"
    }
    assert ids == expected


def test_laminate_calculation():
    calc = CalculatorRegistry.get("laminate")
    assert calc is not None

    res = calc.calculate({
        "area": 20.0,
        "pack_area": 2.131,
        "laying_method": "straight",
        "has_underlayment": True,
        "underlayment_roll": 10.0,
        "include_plinth": True,
    })

    # 20 * 1.05 = 21.0 m2 -> 21.0 / 2.131 = 9.85 -> 10 packs
    laminate_item = next(m for m in res.materials if "Ламінат" in m.name)
    assert laminate_item.purchase_quantity == 10

    # Underlayment: 20 * 1.15 = 23 m2 -> 23 / 10 = 2.3 -> 3 rolls
    underlay_item = next(m for m in res.materials if "Підкладка" in m.name)
    assert underlay_item.purchase_quantity == 3

    assert len(res.warnings) == 0
    assert len(res.recommendations) > 0


def test_screed_calculation():
    calc = CalculatorRegistry.get("screed")
    assert calc is not None

    res = calc.calculate({
        "area": 25.0,
        "thickness": 50.0,
        "screed_type": "ready_mix",
        "bag_weight": "25",
        "reinforcement": "mesh",
        "include_damper": True,
    })

    # Volume = 25 * 0.05 * 1.15 = 1.4375 m3
    # Weight = 1.4375 * 2000 = 2875 kg -> 2875 / 25 = 115 bags
    cement_item = next(m for m in res.materials if "суміш ЦПС" in m.name)
    assert cement_item.purchase_quantity == 115
    assert len(res.materials) >= 3


def test_tile_calculation():
    calc = CalculatorRegistry.get("tile")
    assert calc is not None

    res = calc.calculate({
        "area": 15.0,
        "tile_length": 60.0,
        "tile_width": 60.0,
        "pack_sqm": 1.44,
        "laying_method": "straight",
        "joint_width": 2.0,
        "glue_thickness": 4.0,
    })

    tile_item = next(m for m in res.materials if "Плитка" in m.name)
    assert tile_item.purchase_quantity == 12  # (15 * 1.10) / 1.44 = 11.45 -> 12 packs
    assert any("Клей для плитки" in m.name for m in res.materials)
    assert any("Затирка" in m.name for m in res.materials)


def test_gasblock_calculation():
    calc = CalculatorRegistry.get("gasblock")
    assert calc is not None

    res = calc.calculate({
        "wall_length": 40.0,
        "wall_height": 2.8,
        "block_thickness": "300",
        "block_height": "200",
        "openings_area": 12.0,
        "pallet_volume": 1.8,
    })

    block_item = next(m for m in res.materials if "Газобетонний блок" in m.name)
    assert block_item.purchase_quantity > 0
    assert any("Клей для газобетону" in m.name for m in res.materials)
    assert any("Арматура" in m.name for m in res.materials)


def test_brick_calculation():
    calc = CalculatorRegistry.get("brick")
    assert calc is not None

    res = calc.calculate({
        "wall_length": 20.0,
        "wall_height": 2.8,
        "wall_thickness": "250",
        "brick_type": "single",
        "openings_area": 5.0,
    })

    brick_item = next(m for m in res.materials if "Цегла" in m.name)
    assert brick_item.purchase_quantity > 1000
    assert any("Цемент" in m.name for m in res.materials)


def test_plaster_calculation():
    calc = CalculatorRegistry.get("plaster")
    assert calc is not None

    res = calc.calculate({
        "area": 40.0,
        "thickness": 15.0,
        "plaster_type": "gypsum",
        "bag_weight": "30",
    })

    plaster_item = next(m for m in res.materials if "Гіпсова штукатурка" in m.name)
    # 40 * 15 * 0.85 * 1.05 = 535.5 kg -> 535.5 / 30 = 17.85 -> 18 bags
    assert plaster_item.purchase_quantity == 18


def test_putty_calculation():
    calc = CalculatorRegistry.get("putty")
    assert calc is not None

    res = calc.calculate({
        "area": 40.0,
        "putty_type": "finish_dry",
        "layers_count": "2",
        "thickness_per_layer": 1.0,
    })

    putty_item = next(m for m in res.materials if "Фінішна шпаклівка" in m.name)
    assert putty_item.purchase_quantity > 0


def test_primer_calculation():
    calc = CalculatorRegistry.get("primer")
    assert calc is not None

    res = calc.calculate({
        "area": 50.0,
        "surface_type": "plaster",
        "layers_count": "1",
        "canister_size": "10",
    })

    canister_item = next(m for m in res.materials if "Ґрунтовка" in m.name)
    assert canister_item.purchase_quantity >= 1


def test_paint_calculation():
    calc = CalculatorRegistry.get("paint")
    assert calc is not None

    res = calc.calculate({
        "area": 30.0,
        "layers_count": "2",
        "paint_type": "latex",
        "can_volume": "5",
    })

    paint_item = next(m for m in res.materials if "Латексна" in m.name)
    assert paint_item.purchase_quantity >= 1


def test_wallpaper_calculation():
    calc = CalculatorRegistry.get("wallpaper")
    assert calc is not None

    res = calc.calculate({
        "room_length": 5.0,
        "room_width": 4.0,
        "ceiling_height": 2.65,
        "roll_width": "1.06",
        "roll_length": "10.05",
        "pattern_repeat": "0",
        "openings_area": 4.5,
    })

    wallpaper_item = next(m for m in res.materials if "Шпалери" in m.name)
    assert wallpaper_item.purchase_quantity >= 4
    assert any("Клей для" in m.name for m in res.materials)
