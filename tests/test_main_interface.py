import ctypes
import os
import sys
import pytest

# Ensure we can import from root / src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src import main as m
from src import ai

MC_1_19_4 = 33
MC_1_16 = 16
SEED = 262
OUTPOST = 10
FORTRESS = 35
END_CITY = 37


# ==============================================================================
# Section 1: Biome & Dimension Queries
# ==============================================================================

def test_get_biome_at():
    g = m.create_generator(MC_1_19_4)
    m.apply_seed(g, 0, SEED)
    biome_id = m.get_biome_at(g, 1, 0, 63, 0)
    assert biome_id == 14, f"Expected 14 (Mushroom Fields), got {biome_id}"

def test_gen_biomes_layout():
    g = m.create_generator(MC_1_19_4)
    m.apply_seed(g, 0, SEED)
    cache = (ctypes.c_int * 100)()
    r = m.Range(4, 0, 0, 10, 10, 0, 1)
    status = m.gen_biomes_layout(g, cache, r)
    assert status == 0, f"Expected status 0, got {status}"
    assert cache[0] >= 0, f"Expected valid biome ID in cache[0], got {cache[0]}"

def test_biome_exists():
    assert m.biome_exists(MC_1_19_4, 14) == 1
    assert m.biome_exists(MC_1_19_4, 9999) == 0

def test_get_dimension_and_category():
    dim, cat = m.get_dimension_and_category(MC_1_19_4, 14)
    assert dim == 0, f"Expected Overworld (0), got {dim}"
    assert isinstance(cat, int)

def test_get_mutated_biome():
    mutated = m.get_mutated_biome(MC_1_19_4, 1)
    assert isinstance(mutated, int)

def test_get_environment_flags():
    flags = m.get_environment_flags(MC_1_19_4, 14, 1)
    assert flags["isOverworld"] == 1
    assert "areSimilar" in flags
    assert flags["isOceanic"] in [0, 1]


# ==============================================================================
# Section 2: Structure Attempt Positions
# ==============================================================================

def test_get_structure_attempt():
    pos = m.Pos()
    res = m.get_structure_attempt(OUTPOST, MC_1_19_4, 12345, 0, 0, ctypes.byref(pos))
    assert res in [0, 1]
    assert isinstance(pos.x, int) and isinstance(pos.z, int)

def test_get_mineshafts():
    out = (m.Pos * 10)()
    count = m.get_mineshafts(MC_1_19_4, 12345, 0, 0, 10, 10, out, 10)
    assert count >= 0

def test_is_slime_chunk():
    res = m.is_slime_chunk(12345, 0, 0)
    assert res in [0, 1]

def test_get_end_islands():
    islands = (m.EndIsland * 2)()
    count = m.get_end_islands(islands, MC_1_19_4, 12345, 0, 0)
    assert 0 <= count <= 2


# ==============================================================================
# Section 3: Spawning Viability Diagnostics
# ==============================================================================

def test_is_viable_structure_pos():
    g = m.create_generator(MC_1_19_4)
    m.apply_seed(g, 0, 12345)
    pos = m.Pos()
    if m.get_structure_attempt(OUTPOST, MC_1_19_4, 12345, 0, 0, ctypes.byref(pos)):
        viable = m.is_viable_structure_pos(OUTPOST, g, pos.x, pos.z, 0)
        assert viable in [0, 1]

def test_is_viable_structure_terrain():
    g = m.create_generator(MC_1_19_4)
    m.apply_seed(g, 0, 12345)
    res = m.is_viable_structure_terrain(OUTPOST, g, 0, 0)
    assert res in [0, 1]
    
    # End City check
    g_end = m.create_generator(MC_1_19_4)
    m.apply_seed(g_end, 1, 12345)
    sn = m.SurfaceNoise()
    m.init_surface_noise(sn, 1, 12345)
    res_end = m.is_viable_structure_terrain(END_CITY, g_end, 0, 0, ctypes.byref(sn))
    assert res_end >= 0


# ==============================================================================
# Section 4: Advanced Structural Configuration & Blueprint Properties
# ==============================================================================

def test_get_village_house_list():
    houses = (ctypes.c_int * 10)()
    rnd = m.get_village_house_list(houses, 12345, 0, 0)
    assert isinstance(rnd, int)
    assert all(houses[i] >= 0 for i in range(10))

def test_get_structure_variant():
    sv = m.StructureVariant()
    status = m.get_structure_variant(ctypes.byref(sv), OUTPOST, MC_1_19_4, 12345, 0, 0, 14)
    assert isinstance(status, int)

def test_get_blueprint_piece_lists():
    pieces = (m.Piece * 500)()
    count_fortress = m.get_blueprint_piece_lists(pieces, FORTRESS, 500, MC_1_19_4, 12345, 0, 0)
    assert count_fortress >= 0
    count_end_city = m.get_blueprint_piece_lists(pieces, END_CITY, 500, MC_1_19_4, 12345, 0, 0)
    assert count_end_city >= 0


# ==============================================================================
# Section 5: Unique World Mechanics (Strongholds, Spawn, and Gateways)
# ==============================================================================

def test_stronghold_iteration():
    sh = m.StrongholdIter()
    g = m.create_generator(MC_1_19_4)
    m.apply_seed(g, 0, 12345)
    pos = m.init_first_stronghold(ctypes.byref(sh), MC_1_19_4, 12345)
    assert isinstance(pos.x, int) and isinstance(pos.z, int)
    rem = m.next_stronghold(ctypes.byref(sh), g)
    assert rem >= 0

def test_spawn_queries():
    g = m.create_generator(MC_1_19_4)
    m.apply_seed(g, 0, 12345)
    pos_est = m.estimate_spawn(g)
    assert isinstance(pos_est.x, int) and isinstance(pos_est.z, int)
    pos_exact = m.get_spawn(g)
    assert isinstance(pos_exact.x, int) and isinstance(pos_exact.z, int)

def test_end_gateways():
    gateways = (m.Pos * 20)()
    m.get_fixed_end_gateways(MC_1_19_4, 12345, gateways)
    assert any(gateways[i].x != 0 or gateways[i].z != 0 for i in range(20))
    en = m.EndNoise()
    m.set_end_seed(en, MC_1_19_4, 12345)
    sn = m.SurfaceNoise()
    m.init_surface_noise(sn, 1, 12345)
    dst = m.get_linked_gateway_pos(ctypes.byref(en), ctypes.byref(sn), 12345, m.Pos(100, 100))
    assert isinstance(dst.x, int) and isinstance(dst.z, int)


# ==============================================================================
# Section 6: Climate Noise & Terrain Geometry (Modern 1.18+)
# ==============================================================================

def test_sample_biome_noise():
    bn = m.BiomeNoise()
    m.init_biome_noise(bn, MC_1_19_4)
    m.set_biome_seed(bn, 12345, 0)
    np = (ctypes.c_int64 * 6)()
    biome = m.sample_biome_noise(ctypes.byref(bn), np, 0, 63, 0)
    assert biome >= 0

def test_get_para_range():
    bn = m.BiomeNoise()
    m.init_biome_noise(bn, MC_1_19_4)
    m.set_biome_seed(bn, 12345, 0)
    dpn = ctypes.cast(ctypes.byref(bn), ctypes.POINTER(m.DoublePerlinNoise))
    pmin = ctypes.c_double()
    pmax = ctypes.c_double()
    err = m.get_para_range(dpn, ctypes.byref(pmin), ctypes.byref(pmax), 0, 0, 16, 16)
    assert err == 0
    assert pmin.value <= pmax.value

def test_biome_para_tables():
    ext = m.get_biome_para_extremes(MC_1_19_4)
    assert bool(ext)
    lim = m.get_biome_para_limits(MC_1_19_4, 14)
    assert bool(lim)
    ids = (ctypes.c_char * 256)()
    m.get_possible_biomes_for_limits(ids, MC_1_19_4, lim)
    assert any(ids[i] != b'\x00' for i in range(256))

def test_get_largest_rec():
    ids = (ctypes.c_int * 100)()
    for i in range(100):
        if (i % 10 < 8) and (i // 10 < 8):
            ids[i] = 14
    p0 = m.Pos()
    p1 = m.Pos()
    area = m.get_largest_rec(14, ids, 10, 10, ctypes.byref(p0), ctypes.byref(p1))
    assert area == 64
    assert p0.x == 0 and p0.z == 0 and p1.x == 7 and p1.z == 7

def test_map_approx_height():
    g = m.create_generator(MC_1_19_4)
    m.apply_seed(g, 0, 12345)
    sn = m.SurfaceNoise()
    m.init_surface_noise(sn, 0, 12345)
    y = (ctypes.c_float * 16)()
    ids = (ctypes.c_int * 16)()
    status = m.map_approx_height(y, ids, g, ctypes.byref(sn), 0, 0, 4, 4)
    assert status == 0
    assert any(y[i] > 0 for i in range(16))


# ==============================================================================
# Section 7: Seed Vectors, Filters, & Math Constraints
# ==============================================================================

def test_seed_transformations():
    shadow = m.get_shadow_seed(SEED)
    assert isinstance(shadow, int)
    shifted = m.shift_base_seed(12345, 1, 2)
    assert isinstance(shifted, int)

def test_check_for_biomes():
    g = m.create_generator(MC_1_19_4)
    m.apply_seed(g, 0, 12345)
    cache = (ctypes.c_int * 100)()
    r = m.Range(4, 0, 0, 10, 10, 0, 1)
    bf = m.BiomeFilter()
    m.setup_biome_filter(bf, MC_1_19_4, 0, biomes=[14])
    res = m.check_for_biomes(g, cache, r, 0, 12345, ctypes.byref(bf))
    assert res in [0, 1, 2]

def test_check_for_temps():
    ls = m.LayerStack()
    m.setup_layer_stack(ls, MC_1_16, 0)
    tc = (ctypes.c_int * 9)(*[-1]*9)
    res = m.check_for_temps(ctypes.byref(ls), 12345, 0, 0, 10, 10, tc)
    assert res in [0, 1]

def test_monte_carlo_biomes():
    g = m.create_generator(MC_1_19_4)
    m.apply_seed(g, 0, 12345)
    r = m.Range(4, 0, 0, 10, 10, 0, 1)
    rng = ctypes.c_uint64(12345)
    
    @ctypes.CFUNCTYPE(ctypes.c_int, ctypes.POINTER(m.Generator), ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_void_p)
    def dummy_eval(gen, scale, x, y, z, data):
        return 1
        
    res = m.monte_carlo_biomes(g, r, ctypes.byref(rng), 0.5, 0.95, ctypes.cast(dummy_eval, ctypes.c_void_p))
    assert res in [0, 1]


# ==============================================================================
# Section 8: Functions for the AI
# ==============================================================================

def test_get_seed_spawn_info():
    info = ai.get_seed_spawn_info(SEED, "1.19.4")
    assert isinstance(info, dict)
    assert "spawn_x" in info and "spawn_z" in info
    assert "biome_id" in info and "biome_name" in info
    assert isinstance(info["biome_name"], str)
    assert info["biome_id"] >= 0

def test_locate_structures_near_spawn():
    # Test with village and pillager outpost
    structs = ai.locate_structures_near_spawn(12345, "1.19.4", ["village", "pillager_outpost"], radius=5000)
    assert isinstance(structs, list)
    if structs:
        first = structs[0]
        assert "structure_type" in first
        assert "structure_id" in first
        assert "x" in first and "z" in first
        assert "distance" in first
        # Verify sorting by distance
        distances = [s["distance"] for s in structs]
        assert distances == sorted(distances)

def test_check_vicinity_for_rare_biomes():
    rares = ai.check_vicinity_for_rare_biomes(SEED, "1.19.4", radius=3000)
    assert isinstance(rares, list)
    assert all(isinstance(name, str) for name in rares)
    # Rares should be sorted and unique
    assert rares == sorted(list(set(rares)))

def test_locate_nearest_strongholds():
    strongholds = ai.locate_nearest_strongholds(12345, "1.19.4", count=3)
    assert isinstance(strongholds, list)
    assert len(strongholds) == 3
    for sh in strongholds:
        assert "index" in sh and "x" in sh and "z" in sh and "distance" in sh
    # Verify sorting by distance
    distances = [sh["distance"] for sh in strongholds]
    assert distances == sorted(distances)

def test_check_slime_chunks_at_coordinates():
    res = ai.check_slime_chunks_at_coordinates(12345, 0, 0)
    assert isinstance(res, bool)
    assert res == bool(m.is_slime_chunk(12345, 0, 0))
