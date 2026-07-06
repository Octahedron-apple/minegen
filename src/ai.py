import ctypes
import sys
from .main import (
    cubiomes,
    create_generator,
    apply_seed,
    get_spawn,
    get_biome_at,
    get_structure_attempt,
    is_viable_structure_pos,
    biome_exists,
    setup_biome_filter,
    check_for_biomes,
    init_first_stronghold,
    next_stronghold,
    is_slime_chunk,
    Pos,
    Range,
    BiomeFilter,
    StrongholdIter,
    StructureConfig,
)

STRUCTURE_TYPES = {
    "feature": 0,
    "desert_pyramid": 1, "desert_temple": 1,
    "jungle_pyramid": 2, "jungle_temple": 2,
    "swamp_hut": 3, "witch_hut": 3,
    "igloo": 4,
    "village": 5,
    "ocean_ruin": 6,
    "shipwreck": 7,
    "monument": 8, "ocean_monument": 8,
    "mansion": 9, "woodland_mansion": 9,
    "pillager_outpost": 10, "outpost": 10,
    "ruined_portal": 11,
    "ruined_portal_nether": 12,
    "ancient_city": 13,
    "buried_treasure": 14, "treasure": 14,
    "mineshaft": 15,
    "desert_well": 16,
    "amethyst_geode": 17, "geode": 17,
    "fortress": 18, "nether_fortress": 18,
    "bastion_remnant": 19, "bastion": 19,
    "end_city": 20,
    "end_gateway": 21,
    "end_island": 22,
    "trail_ruins": 23,
    "trial_chambers": 24,
}

RARE_BIOME_IDS = [
    14,   # Mushroom Fields
    37,   # Badlands / Mesa
    38,   # Wooded Badlands Plateau
    39,   # Badlands Plateau
    125,  # Ice Spikes (old ID)
    126,  # Modified Jungle
    127,  # Modified Jungle Edge
    137,  # Eroded Badlands (old ID) / Ice Spikes
    165,  # Eroded Badlands
    168,  # Bamboo Jungle
    170,  # Soul Sand Valley
    171,  # Crimson Forest
    172,  # Warped Forest
    173,  # Basalt Deltas
    174,  # Dripstone Caves
    175,  # Lush Caves
    183,  # Deep Dark
    185,  # Cherry Grove
    186,  # Pale Garden
]

def _parse_mc_version(mc_version) -> int:
    if isinstance(mc_version, int):
        return mc_version
    if isinstance(mc_version, str):
        val = cubiomes.str2mc(mc_version.encode('utf-8'))
        if val != 0:
            return val
        parts = mc_version.split('.')
        if len(parts) >= 2:
            base = f"{parts[0]}.{parts[1]}"
            val = cubiomes.str2mc(base.encode('utf-8'))
            if val != 0:
                return val
        raise ValueError(f"Unsupported Minecraft version: {mc_version}")
    raise TypeError(f"mc_version must be int or str, got {type(mc_version)}")

def _get_biome_name(mc_ver_int: int, biome_id: int) -> str:
    res = cubiomes.biome2str(mc_ver_int, biome_id)
    if res:
        return res.decode('utf-8')
    return f"biome_{biome_id}"

def _parse_structure_type(stype) -> int | None:
    if isinstance(stype, int):
        return stype
    if isinstance(stype, str):
        if stype.isdigit():
            return int(stype)
        clean_name = stype.lower().strip().replace(" ", "_")
        if clean_name in STRUCTURE_TYPES:
            return STRUCTURE_TYPES[clean_name]
    return None

def _get_structure_dimension(stype: int) -> int:
    if stype in (12, 18, 19, 35):
        return -1
    if stype in (20, 21, 22, 37):
        return 1
    return 0

def get_seed_spawn_info(seed: int, mc_version: str) -> dict:
    """Gets the spawn information for a given seed and Minecraft version."""
    mc_ver_int = _parse_mc_version(mc_version)
    g = create_generator(mc_ver_int)
    apply_seed(g, 0, seed)
    spawn_pos = get_spawn(g)
    biome_id = get_biome_at(g, 1, spawn_pos.x, 63, spawn_pos.z)
    biome_name = _get_biome_name(mc_ver_int, biome_id)
    return {
        "spawn_x": spawn_pos.x,
        "spawn_z": spawn_pos.z,
        "x": spawn_pos.x,
        "z": spawn_pos.z,
        "biome_id": biome_id,
        "biome_name": biome_name,
    }

def locate_structures_near_spawn(seed: int, mc_version: str, structure_types: list[str], radius: int = 3000) -> list[dict]:
    """Locates structures near spawn for a given seed and Minecraft version."""
    mc_ver_int = _parse_mc_version(mc_version)
    g_overworld = create_generator(mc_ver_int)
    apply_seed(g_overworld, 0, seed)
    spawn_pos = get_spawn(g_overworld)
    
    generators = {0: g_overworld}
    results = []
    
    for stype_str in structure_types:
        stype = _parse_structure_type(stype_str)
        if stype is None:
            continue
            
        dim = _get_structure_dimension(stype)
        if dim not in generators:
            g_dim = create_generator(mc_ver_int)
            apply_seed(g_dim, dim, seed)
            generators[dim] = g_dim
        g = generators[dim]
        
        sconf = StructureConfig()
        if cubiomes.getStructureConfig(stype, mc_ver_int, ctypes.byref(sconf)) and sconf.regionSize > 0:
            region_blocks = sconf.regionSize * 16
        else:
            region_blocks = 512
            
        min_x = spawn_pos.x - radius
        max_x = spawn_pos.x + radius
        min_z = spawn_pos.z - radius
        max_z = spawn_pos.z + radius
        
        reg_x_min = min_x // region_blocks
        reg_x_max = max_x // region_blocks
        reg_z_min = min_z // region_blocks
        reg_z_max = max_z // region_blocks
        
        pos = Pos()
        for rx in range(reg_x_min, reg_x_max + 1):
            for rz in range(reg_z_min, reg_z_max + 1):
                if get_structure_attempt(stype, mc_ver_int, seed, rx, rz, ctypes.byref(pos)):
                    dx = pos.x - spawn_pos.x
                    dz = pos.z - spawn_pos.z
                    dist = (dx*dx + dz*dz) ** 0.5
                    if dist <= radius:
                        if is_viable_structure_pos(stype, g, pos.x, pos.z, 0):
                            results.append({
                                "structure_type": stype_str,
                                "structure_id": stype,
                                "x": pos.x,
                                "z": pos.z,
                                "distance": round(dist, 2),
                            })
                            
    results.sort(key=lambda item: item["distance"])
    return results

def check_vicinity_for_rare_biomes(seed: int, mc_version: str, radius: int = 3000) -> list[str]:
    """Checks the vicinity of the spawn point for rare biomes."""
    mc_ver_int = _parse_mc_version(mc_version)
    g = create_generator(mc_ver_int)
    apply_seed(g, 0, seed)
    spawn_pos = get_spawn(g)
    
    scale = 16
    rx = (spawn_pos.x - radius) // scale
    rz = (spawn_pos.z - radius) // scale
    rw = (2 * radius) // scale + 1
    rh = (2 * radius) // scale + 1
    r = Range(scale, rx, rz, rw, rh, 0, 1)
    
    found_names = []
    bf = BiomeFilter()
    
    for biome_id in RARE_BIOME_IDS:
        if not biome_exists(mc_ver_int, biome_id):
            continue
        setup_biome_filter(bf, mc_ver_int, 0, biomes=[biome_id])
        if check_for_biomes(g, None, r, 0, seed, ctypes.byref(bf)) > 0:
            name = _get_biome_name(mc_ver_int, biome_id)
            if name not in found_names:
                found_names.append(name)
                
    found_names.sort()
    return found_names

def locate_nearest_strongholds(seed: int, mc_version: str, count: int = 3) -> list[dict]:
    """Locates the nearest strongholds to the spawn point."""
    mc_ver_int = _parse_mc_version(mc_version)
    g = create_generator(mc_ver_int)
    apply_seed(g, 0, seed)
    spawn_pos = get_spawn(g)
    
    sh = StrongholdIter()
    init_first_stronghold(ctypes.byref(sh), mc_ver_int, seed)
    
    strongholds = []
    max_check = min(max(count + 6, 12), 128)
    for i in range(max_check):
        rem = next_stronghold(ctypes.byref(sh), g)
        dx = sh.pos.x - spawn_pos.x
        dz = sh.pos.z - spawn_pos.z
        dist = (dx*dx + dz*dz) ** 0.5
        strongholds.append({
            "index": len(strongholds) + 1,
            "x": sh.pos.x,
            "z": sh.pos.z,
            "distance": round(dist, 2),
        })
        if rem <= 1:
            break
            
    strongholds.sort(key=lambda item: item["distance"])
    res = strongholds[:count]
    for idx, item in enumerate(res, 1):
        item["index"] = idx
    return res

def check_slime_chunks_at_coordinates(seed: int, chunk_x: int, chunk_z: int) -> bool:
    """Answers granular player questions like, "Is my base perimeter a slime chunk?" """
    return bool(is_slime_chunk(seed, chunk_x, chunk_z))
