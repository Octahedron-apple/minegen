import ctypes
import os
import sys 
import subprocess

src_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.abspath(os.path.join(src_dir, ".."))
lib_path = os.path.abspath(os.path.join(root_dir, "libcubiomes.so"))
print(f"Loading shared library from: {lib_path}")

def auto_compile():
    """Runs 'make' in the root directory automatically to ensure libcubiomes.so is built."""
    print("Checking/building libcubiomes.so via Makefile...")
    try:
        subprocess.run(
            ["make"], 
            cwd=root_dir, 
            check=True, 
            stdout=subprocess.DEVNULL, 
            stderr=subprocess.PIPE
        )
    except subprocess.CalledProcessError as e:
        print(f"Compilation error while building cubiomes:\n{e.stderr.decode()}", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError:
        print("Error: 'make' command not found. Ensure you are running inside 'nix-shell'.", file=sys.stderr)
        sys.exit(1)

def load_library():
    auto_compile()
    try:
        return ctypes.CDLL(lib_path)
    except OSError as e:
        print(f"Error loading library: {e}", file=sys.stderr)
        sys.exit(1)
# ==============================================================================
# CTypes Structure Definitions
# ==============================================================================

class Pos(ctypes.Structure):
    _fields_ = [
        ("x", ctypes.c_int),
        ("z", ctypes.c_int),
    ]

class Pos3(ctypes.Structure):
    _fields_ = [
        ("x", ctypes.c_int16),
        ("y", ctypes.c_int16),
        ("z", ctypes.c_int16),
        ("sx", ctypes.c_int16),
        ("sy", ctypes.c_int16),
        ("sz", ctypes.c_int16),
    ]

class Range(ctypes.Structure):
    _fields_ = [
        ("scale", ctypes.c_int),
        ("x", ctypes.c_int),
        ("z", ctypes.c_int),
        ("sx", ctypes.c_int),
        ("sz", ctypes.c_int),
        ("y", ctypes.c_int),
        ("sy", ctypes.c_int),
    ]

class EndIsland(ctypes.Structure):
    _fields_ = [
        ("x", ctypes.c_int),
        ("y", ctypes.c_int),
        ("z", ctypes.c_int),
        ("r", ctypes.c_int),
    ]

class StructureConfig(ctypes.Structure):
    _fields_ = [
        ("salt", ctypes.c_int32),
        ("regionSize", ctypes.c_int8),
        ("chunkRange", ctypes.c_int8),
        ("structType", ctypes.c_uint8),
        ("dim", ctypes.c_int8),
        ("rarity", ctypes.c_float),
    ]

class StructureVariant(ctypes.Structure):
    _fields_ = [
        ("abandoned", ctypes.c_uint8, 1),
        ("giant", ctypes.c_uint8, 1),
        ("underground", ctypes.c_uint8, 1),
        ("airpocket", ctypes.c_uint8, 1),
        ("basement", ctypes.c_uint8, 1),
        ("cracked", ctypes.c_uint8, 1),
        ("_pad_bits", ctypes.c_uint8, 2),
        ("size", ctypes.c_uint8),
        ("start", ctypes.c_uint8),
        ("biome", ctypes.c_short),
        ("rotation", ctypes.c_uint8),
        ("mirror", ctypes.c_uint8),
        ("x", ctypes.c_int16),
        ("y", ctypes.c_int16),
        ("z", ctypes.c_int16),
        ("sx", ctypes.c_int16),
        ("sy", ctypes.c_int16),
        ("sz", ctypes.c_int16),
    ]

class Piece(ctypes.Structure):
    pass

Piece._fields_ = [
    ("name", ctypes.c_char_p),
    ("pos", Pos3),
    ("bb0", Pos3),
    ("bb1", Pos3),
    ("rot", ctypes.c_uint8),
    ("depth", ctypes.c_int8),
    ("type", ctypes.c_int8),
    ("next", ctypes.POINTER(Piece)),
]

class StrongholdIter(ctypes.Structure):
    _fields_ = [
        ("pos", Pos),
        ("nextapprox", Pos),
        ("index", ctypes.c_int),
        ("ringnum", ctypes.c_int),
        ("ringmax", ctypes.c_int),
        ("ringidx", ctypes.c_int),
        ("angle", ctypes.c_double),
        ("dist", ctypes.c_double),
        ("rnds", ctypes.c_uint64),
        ("mc", ctypes.c_int),
    ]

# Opaque buffers for stack-allocated structures in C (padded to 64KB for safety)
class Generator(ctypes.Structure):
    _fields_ = [("_data", ctypes.c_byte * 65536)]

class SurfaceNoise(ctypes.Structure):
    _fields_ = [("_data", ctypes.c_byte * 65536)]

class EndNoise(ctypes.Structure):
    _fields_ = [("_data", ctypes.c_byte * 65536)]

class LayerStack(ctypes.Structure):
    _fields_ = [("_data", ctypes.c_byte * 65536)]

class BiomeFilter(ctypes.Structure):
    _fields_ = [("_data", ctypes.c_byte * 65536)]

class BiomeNoise(ctypes.Structure):
    _fields_ = [("_data", ctypes.c_byte * 65536)]

class DoublePerlinNoise(ctypes.Structure):
    _fields_ = [("_data", ctypes.c_byte * 65536)]


# ==============================================================================
# Setup C Function Signatures
# ==============================================================================

def _setup_signatures(lib):
    # Setup helpers
    lib.setupGenerator.argtypes = [ctypes.POINTER(Generator), ctypes.c_int, ctypes.c_uint32]
    lib.setupGenerator.restype = None
    lib.applySeed.argtypes = [ctypes.POINTER(Generator), ctypes.c_int, ctypes.c_uint64]
    lib.applySeed.restype = None
    lib.initSurfaceNoise.argtypes = [ctypes.POINTER(SurfaceNoise), ctypes.c_int, ctypes.c_uint64]
    lib.initSurfaceNoise.restype = None
    lib.setEndSeed.argtypes = [ctypes.POINTER(EndNoise), ctypes.c_int, ctypes.c_uint64]
    lib.setEndSeed.restype = None
    lib.initBiomeNoise.argtypes = [ctypes.POINTER(BiomeNoise), ctypes.c_int]
    lib.initBiomeNoise.restype = None
    lib.setBiomeSeed.argtypes = [ctypes.POINTER(BiomeNoise), ctypes.c_uint64, ctypes.c_int]
    lib.setBiomeSeed.restype = None
    lib.setupBiomeFilter.argtypes = [ctypes.POINTER(BiomeFilter), ctypes.c_int, ctypes.c_uint32, ctypes.POINTER(ctypes.c_int), ctypes.c_int, ctypes.POINTER(ctypes.c_int), ctypes.c_int, ctypes.POINTER(ctypes.c_int), ctypes.c_int]
    lib.setupBiomeFilter.restype = None
    lib.setupLayerStack.argtypes = [ctypes.POINTER(LayerStack), ctypes.c_int, ctypes.c_uint32]
    lib.setupLayerStack.restype = None
    lib.str2mc.argtypes = [ctypes.c_char_p]
    lib.str2mc.restype = ctypes.c_int
    lib.biome2str.argtypes = [ctypes.c_int, ctypes.c_int]
    lib.biome2str.restype = ctypes.c_char_p
    lib.struct2str.argtypes = [ctypes.c_int]
    lib.struct2str.restype = ctypes.c_char_p
    lib.getStructureConfig.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.POINTER(StructureConfig)]
    lib.getStructureConfig.restype = ctypes.c_int

    # Section 1
    lib.getBiomeAt.argtypes = [ctypes.POINTER(Generator), ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int]
    lib.getBiomeAt.restype = ctypes.c_int
    lib.genBiomes.argtypes = [ctypes.POINTER(Generator), ctypes.POINTER(ctypes.c_int), Range]
    lib.genBiomes.restype = ctypes.c_int
    lib.biomeExists.argtypes = [ctypes.c_int, ctypes.c_int]
    lib.biomeExists.restype = ctypes.c_int
    lib.getDimension.argtypes = [ctypes.c_int]
    lib.getDimension.restype = ctypes.c_int
    lib.getCategory.argtypes = [ctypes.c_int, ctypes.c_int]
    lib.getCategory.restype = ctypes.c_int
    lib.getMutated.argtypes = [ctypes.c_int, ctypes.c_int]
    lib.getMutated.restype = ctypes.c_int
    lib.isMesa.argtypes = [ctypes.c_int]
    lib.isMesa.restype = ctypes.c_int
    lib.isOceanic.argtypes = [ctypes.c_int]
    lib.isOceanic.restype = ctypes.c_int
    lib.isShallowOcean.argtypes = [ctypes.c_int]
    lib.isShallowOcean.restype = ctypes.c_int
    lib.isDeepOcean.argtypes = [ctypes.c_int]
    lib.isDeepOcean.restype = ctypes.c_int
    lib.isSnowy.argtypes = [ctypes.c_int]
    lib.isSnowy.restype = ctypes.c_int
    lib.isOverworld.argtypes = [ctypes.c_int, ctypes.c_int]
    lib.isOverworld.restype = ctypes.c_int
    lib.areSimilar.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_int]
    lib.areSimilar.restype = ctypes.c_int

    # Section 2
    lib.getStructurePos.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_uint64, ctypes.c_int, ctypes.c_int, ctypes.POINTER(Pos)]
    lib.getStructurePos.restype = ctypes.c_int
    lib.getMineshafts.argtypes = [ctypes.c_int, ctypes.c_uint64, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.POINTER(Pos), ctypes.c_int]
    lib.getMineshafts.restype = ctypes.c_int
    lib.getEndIslands.argtypes = [ctypes.POINTER(EndIsland), ctypes.c_int, ctypes.c_uint64, ctypes.c_int, ctypes.c_int]
    lib.getEndIslands.restype = ctypes.c_int

    # Section 3
    lib.isViableStructurePos.argtypes = [ctypes.c_int, ctypes.POINTER(Generator), ctypes.c_int, ctypes.c_int, ctypes.c_uint32]
    lib.isViableStructurePos.restype = ctypes.c_int
    lib.isViableStructureTerrain.argtypes = [ctypes.c_int, ctypes.POINTER(Generator), ctypes.c_int, ctypes.c_int]
    lib.isViableStructureTerrain.restype = ctypes.c_int
    lib.isViableEndCityTerrain.argtypes = [ctypes.POINTER(Generator), ctypes.POINTER(SurfaceNoise), ctypes.c_int, ctypes.c_int]
    lib.isViableEndCityTerrain.restype = ctypes.c_int

    # Section 4
    lib.getHouseList.argtypes = [ctypes.POINTER(ctypes.c_int), ctypes.c_uint64, ctypes.c_int, ctypes.c_int]
    lib.getHouseList.restype = ctypes.c_uint64
    lib.getVariant.argtypes = [ctypes.POINTER(StructureVariant), ctypes.c_int, ctypes.c_int, ctypes.c_uint64, ctypes.c_int, ctypes.c_int, ctypes.c_int]
    lib.getVariant.restype = ctypes.c_int
    lib.getFortressPieces.argtypes = [ctypes.POINTER(Piece), ctypes.c_int, ctypes.c_int, ctypes.c_uint64, ctypes.c_int, ctypes.c_int]
    lib.getFortressPieces.restype = ctypes.c_int
    lib.getEndCityPieces.argtypes = [ctypes.POINTER(Piece), ctypes.c_uint64, ctypes.c_int, ctypes.c_int]
    lib.getEndCityPieces.restype = ctypes.c_int

    # Section 5
    lib.initFirstStronghold.argtypes = [ctypes.POINTER(StrongholdIter), ctypes.c_int, ctypes.c_uint64]
    lib.initFirstStronghold.restype = Pos
    lib.nextStronghold.argtypes = [ctypes.POINTER(StrongholdIter), ctypes.POINTER(Generator)]
    lib.nextStronghold.restype = ctypes.c_int
    lib.estimateSpawn.argtypes = [ctypes.POINTER(Generator), ctypes.POINTER(ctypes.c_uint64)]
    lib.estimateSpawn.restype = Pos
    lib.getSpawn.argtypes = [ctypes.POINTER(Generator)]
    lib.getSpawn.restype = Pos
    lib.getFixedEndGateways.argtypes = [ctypes.c_int, ctypes.c_uint64, ctypes.POINTER(Pos)]
    lib.getFixedEndGateways.restype = None
    lib.getLinkedGatewayPos.argtypes = [ctypes.POINTER(EndNoise), ctypes.POINTER(SurfaceNoise), ctypes.c_uint64, Pos]
    lib.getLinkedGatewayPos.restype = Pos

    # Section 6
    lib.sampleBiomeNoise.argtypes = [ctypes.POINTER(BiomeNoise), ctypes.POINTER(ctypes.c_int64), ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.POINTER(ctypes.c_uint64), ctypes.c_uint32]
    lib.sampleBiomeNoise.restype = ctypes.c_int
    lib.getParaRange.argtypes = [ctypes.POINTER(DoublePerlinNoise), ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_double), ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_void_p, ctypes.c_void_p]
    lib.getParaRange.restype = ctypes.c_int
    lib.getBiomeParaExtremes.argtypes = [ctypes.c_int]
    lib.getBiomeParaExtremes.restype = ctypes.POINTER(ctypes.c_int)
    lib.getBiomeParaLimits.argtypes = [ctypes.c_int, ctypes.c_int]
    lib.getBiomeParaLimits.restype = ctypes.POINTER(ctypes.c_int)
    lib.getPossibleBiomesForLimits.argtypes = [ctypes.POINTER(ctypes.c_char), ctypes.c_int, ctypes.POINTER(ctypes.c_int)]
    lib.getPossibleBiomesForLimits.restype = None
    lib.getLargestRec.argtypes = [ctypes.c_int, ctypes.POINTER(ctypes.c_int), ctypes.c_int, ctypes.c_int, ctypes.POINTER(Pos), ctypes.POINTER(Pos)]
    lib.getLargestRec.restype = ctypes.c_int
    lib.mapApproxHeight.argtypes = [ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_int), ctypes.POINTER(Generator), ctypes.POINTER(SurfaceNoise), ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int]
    lib.mapApproxHeight.restype = ctypes.c_int

    # Section 7
    lib.checkForBiomes.argtypes = [ctypes.POINTER(Generator), ctypes.POINTER(ctypes.c_int), Range, ctypes.c_int, ctypes.c_uint64, ctypes.POINTER(BiomeFilter), ctypes.POINTER(ctypes.c_char)]
    lib.checkForBiomes.restype = ctypes.c_int
    lib.checkForTemps.argtypes = [ctypes.POINTER(LayerStack), ctypes.c_uint64, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.POINTER(ctypes.c_int)]
    lib.checkForTemps.restype = ctypes.c_int
    lib.monteCarloBiomes.argtypes = [ctypes.POINTER(Generator), Range, ctypes.POINTER(ctypes.c_uint64), ctypes.c_double, ctypes.c_double, ctypes.c_void_p, ctypes.c_void_p]
    lib.monteCarloBiomes.restype = ctypes.c_int

cubiomes = load_library()
_setup_signatures(cubiomes)


# ==============================================================================
# Generator Initialization Helpers
# ==============================================================================

def create_generator(mc_version: int, flags: int = 0) -> Generator:
    """Allocates and initializes a Generator struct for a given Minecraft version and flags."""
    g = Generator()
    cubiomes.setupGenerator(ctypes.byref(g), mc_version, flags)
    return g

def apply_seed(g: Generator, dim: int, seed: int) -> None:
    """Applies a world seed and dimension (-1: Nether, 0: Overworld, 1: End) to a Generator."""
    cubiomes.applySeed(ctypes.byref(g), dim, seed)

def init_surface_noise(sn: SurfaceNoise, dim: int, seed: int) -> None:
    """Initializes SurfaceNoise structure for a given dimension and world seed."""
    cubiomes.initSurfaceNoise(ctypes.byref(sn), dim, seed)

def set_end_seed(en: EndNoise, mc_version: int, seed: int) -> None:
    """Initializes EndNoise structure for a given Minecraft version and world seed."""
    cubiomes.setEndSeed(ctypes.byref(en), mc_version, seed)

def init_biome_noise(bn: BiomeNoise, mc_version: int) -> None:
    """Initializes BiomeNoise structure for a given Minecraft version."""
    cubiomes.initBiomeNoise(ctypes.byref(bn), mc_version)

def set_biome_seed(bn: BiomeNoise, seed: int, large: int = 0) -> None:
    """Sets the seed for an initialized BiomeNoise structure."""
    cubiomes.setBiomeSeed(ctypes.byref(bn), seed, large)

def setup_biome_filter(bf: BiomeFilter, mc_version: int, flags: int = 0, biomes: list[int] = None, avoid: list[int] = None, special: list[int] = None) -> None:
    """Initializes a BiomeFilter with lists of required, avoided, and special biomes."""
    b_arr, b_len = ((ctypes.c_int * len(biomes))(*biomes), len(biomes)) if biomes else (None, 0)
    a_arr, a_len = ((ctypes.c_int * len(avoid))(*avoid), len(avoid)) if avoid else (None, 0)
    s_arr, s_len = ((ctypes.c_int * len(special))(*special), len(special)) if special else (None, 0)
    cubiomes.setupBiomeFilter(ctypes.byref(bf), mc_version, flags, b_arr, b_len, a_arr, a_len, s_arr, s_len)

def setup_layer_stack(ls: LayerStack, mc_version: int, flags: int = 0) -> None:
    """Initializes a LayerStack structure for versions up to 1.17."""
    cubiomes.setupLayerStack(ctypes.byref(ls), mc_version, flags)


# ==============================================================================
# 1. Biome & Dimension Queries
# ==============================================================================

def get_biome_at(g: Generator, scale: int, x: int, y: int, z: int) -> int:
    """
    Biome ID at Coordinates.
    Inputs: Initialized Generator struct, horizontal scale factor (1 for blocks, 4 for biome scale), coordinates (x, y, z).
    Returns: Integer representing specific BiomeID enum code (or -1/none if evaluation fails).
    """
    return cubiomes.getBiomeAt(ctypes.byref(g), scale, x, y, z)

def gen_biomes_layout(g: Generator, cache: ctypes.POINTER(ctypes.c_int), range_struct: Range) -> int:
    """
    Bulk Biome Area/Volume Layout.
    Inputs: Generator struct, allocated integer array destination buffer (cache), and a Range struct.
    Returns: Integer status flag (0 for absolute generation success) while populating cache buffer.
    """
    return cubiomes.genBiomes(ctypes.byref(g), cache, range_struct)

def biome_exists(mc_version: int, biome_id: int) -> int:
    """
    Version Biome Validation.
    Inputs: Target Minecraft version code (MCVersion enum) and integer biome identifier code.
    Returns: Integer boolean value (1 if biome exists natively within version context, 0 otherwise).
    """
    return cubiomes.biomeExists(mc_version, biome_id)

def get_dimension_and_category(mc_version: int, biome_id: int) -> tuple[int, int]:
    """
    Dimension & Category Rules.
    Inputs: Integer biome identifier code (and MCVersion version flag where category checks are concerned).
    Returns: Tuple of integers (Dimension enum value [-1: Nether, 0: Overworld, 1: End], category archetype integer).
    """
    dim = cubiomes.getDimension(biome_id)
    cat = cubiomes.getCategory(mc_version, biome_id)
    return dim, cat

def get_mutated_biome(mc_version: int, biome_id: int) -> int:
    """
    Biome Mutation Mapping.
    Inputs: Target game version code and parent integer biome identifier.
    Returns: Integer containing the mutated biome equivalent subtype ID.
    """
    return cubiomes.getMutated(mc_version, biome_id)

def get_environment_flags(mc_version: int, biome_id: int, compare_biome_id: int = -1) -> dict[str, int]:
    """
    Environment Flags (isMesa, isOceanic, etc.).
    Inputs: Integer biome identifier to sample (and optional second biome for similarity comparison).
    Returns: Dictionary mapping environment flag names to boolean integer statements (1 or 0).
    """
    flags = {
        "isMesa": cubiomes.isMesa(biome_id),
        "isOceanic": cubiomes.isOceanic(biome_id),
        "isShallowOcean": cubiomes.isShallowOcean(biome_id),
        "isDeepOcean": cubiomes.isDeepOcean(biome_id),
        "isSnowy": cubiomes.isSnowy(biome_id),
        "isOverworld": cubiomes.isOverworld(mc_version, biome_id),
    }
    if compare_biome_id >= 0:
        flags["areSimilar"] = cubiomes.areSimilar(mc_version, biome_id, compare_biome_id)
    return flags


# ==============================================================================
# 2. Structure Attempt Positions
# ==============================================================================

def get_structure_attempt(stype: int, mc_version: int, seed: int, reg_x: int, reg_z: int, pos: ctypes.POINTER(Pos)) -> int:
    """
    Region Grid Structure Attempt.
    Inputs: StructureType code, MCVersion flag, lower 48 bits of world seed, linear region offsets (reg_x, reg_z), memory reference to Pos output structure.
    Returns: Integer execution boolean flag (0 if attempt impossible, non-zero if valid) while writing absolute coordinates into pos.
    """
    return cubiomes.getStructurePos(stype, mc_version, seed & 0xffffffffffff, reg_x, reg_z, pos)

def get_mineshafts(mc_version: int, seed: int, chunk_x: int, chunk_z: int, chunk_w: int, chunk_h: int, out_pos_array: ctypes.POINTER(Pos), nout: int) -> int:
    """
    Mineshaft Quadrant Mapping.
    Inputs: Target game version identifier, world seed, chunk grid starting points (chunk_x, chunk_z), rectangular sizing (chunk_w, chunk_h), pointer array to write positions into, and allocation limit capacity nout.
    Returns: Integer count totaling how many chunk coordinates generate Mineshafts within boundaries while populating out_pos_array.
    """
    return cubiomes.getMineshafts(mc_version, seed & 0xffffffffffff, chunk_x, chunk_z, chunk_w, chunk_h, out_pos_array, nout)

def is_slime_chunk(seed: int, chunk_x: int, chunk_z: int) -> int:
    """Correct Java-equivalent Slime Chunk Spawning Logic."""
    # 1. Combine seed and chunk coordinates exactly like Java Edition
    # Java precedence: addition happens first, then bitwise XOR at the end
    combined_seed = (
        seed +
        ctypes.c_int32(chunk_x * chunk_x * 0x4c1906).value +
        ctypes.c_int32(chunk_x * 0x5ac0db).value +
        ctypes.c_int32(chunk_z * chunk_z * 0x4307a7).value +
        ctypes.c_int32(chunk_z * 0x5f24f).value ^ 0x3ad8025f
    ) & 0xffffffffffffffff

    # 2. Simulate Java Random Initial Scramble
    multiplier = 0x5DEECE66D
    addend = 0xB
    mask = (1 << 48) - 1
    
    internal_state = (combined_seed ^ multiplier) & mask
    
    # 3. Simulate nextInt(10) step
    internal_state = (internal_state * multiplier + addend) & mask
    bits = internal_state >> 17  # Extract top 31 bits
    
    return 1 if (bits % 10) == 0 else 0

def get_end_islands(islands: ctypes.POINTER(EndIsland), mc_version: int, seed: int, chunk_x: int, chunk_z: int) -> int:
    """
    End Island Tracing.
    Inputs: Two-element array allocation buffer of EndIsland structs, game version, world seed, chunk coordinate locations (chunk_x, chunk_z).
    Returns: Integer value counting total small end islands successfully located (0 to 2) while modifying passed EndIsland structs with location details (x, y, z) and radius magnitude (r).
    """
    return cubiomes.getEndIslands(islands, mc_version, seed, chunk_x, chunk_z)


# ==============================================================================
# 3. Spawning Viability Diagnostics
# ==============================================================================

def is_viable_structure_pos(stype: int, g: Generator, block_x: int, block_z: int, flags: int = 0) -> int:
    """
    Core Biome Structure Spawning Viability.
    Inputs: Target structure type code, pointer to initialized Generator struct context, absolute block coordinate positions (block_x, block_z), structure-specific variant uint32 flags.
    Returns: Integer boolean validation result (1 if environment accommodates structure type, 0 if local biomes cancel spawning).
    """
    return cubiomes.isViableStructurePos(stype, ctypes.byref(g), block_x, block_z, flags)

def is_viable_structure_terrain(stype: int, g: Generator, block_x: int, block_z: int, sn: ctypes.POINTER(SurfaceNoise) = None) -> int:
    """
    Isolated Terrain Spawning Viability (Overworld & End).
    Inputs: Target structure identifier code, pointer to Generator context, corresponding block coordinates (block_x, block_z). (End City [stype=37] terrain checks replace generator with explicit pointers to Generator and SurfaceNoise structures).
    Returns: Integer boolean value confirming terrain viability layout compatibility based on continuous noise calculations.
    """
    if stype == 37 and sn is not None:  # End City = 37
        return cubiomes.isViableEndCityTerrain(ctypes.byref(g), sn, block_x, block_z)
    return cubiomes.isViableStructureTerrain(stype, ctypes.byref(g), block_x, block_z)


# ==============================================================================
# 4. Advanced Structural Configuration & Blueprint Properties
# ==============================================================================

def get_village_house_list(houses: ctypes.POINTER(ctypes.c_int), seed: int, chunk_x: int, chunk_z: int) -> int:
    """
    Retro Village House Lists.
    Inputs: Integer array destination buffer allocated to size of HOUSE_NUM elements (10), world seed, and village attempt origin chunk locations (chunk_x, chunk_z).
    Returns: uint64_t variable containing mutated post-generation random object seed state, while filling provided output array with specific piece distributions.
    """
    return cubiomes.getHouseList(houses, seed, chunk_x, chunk_z)

def get_structure_variant(sv: ctypes.POINTER(StructureVariant), stype: int, mc_version: int, seed: int, block_x: int, block_z: int, biome_id: int) -> int:
    """
    Structural Component Variant & Properties.
    Inputs: Pointer target memory block to StructureVariant struct, structure type, version, world seed, absolute block positions (block_x, block_z), and local generated block BiomeID code.
    Returns: Integer status flag while writing detailed structural specifications into StructureVariant bitfields and fields.
    """
    return cubiomes.getVariant(sv, stype, mc_version, seed, block_x, block_z, biome_id)

def get_blueprint_piece_lists(pieces: ctypes.POINTER(Piece), stype: int, max_pieces: int, mc_version: int, seed: int, chunk_x: int, chunk_z: int) -> int:
    """
    Component Blueprint Piece Lists (Nether Fortress / End City).
    Inputs: Pointer buffer allocated to hold multiple Piece structures, maximum capacity size cap integer, version indices, world seed, and originating structural chunk locations (chunk_x, chunk_z).
    Returns: Integer counting absolute total number of structural blueprint modules spawned, while linking data directly into provided array buffer.
    """
    if stype == 35:  # Fortress = 35
        return cubiomes.getFortressPieces(pieces, max_pieces, mc_version, seed, chunk_x, chunk_z)
    elif stype == 37:  # End_City = 37
        return cubiomes.getEndCityPieces(pieces, seed, chunk_x, chunk_z)
    return 0


# ==============================================================================
# 5. Unique World Mechanics (Strongholds, Spawn, and Gateways)
# ==============================================================================

def init_first_stronghold(sh: ctypes.POINTER(StrongholdIter), mc_version: int, s48: int) -> Pos:
    """
    Stronghold Chronological Path Finding (Initialization).
    Inputs: Target pointer to blank StrongholdIter struct tracker, version identifier, and 48-bit seed value.
    Returns: Pos struct mapping estimated non-biome block coordinate footprint of first stronghold ring while filling out internal iterator variables.
    """
    return cubiomes.initFirstStronghold(sh, mc_version, s48 & 0xffffffffffff)

def next_stronghold(sh: ctypes.POINTER(StrongholdIter), g: Generator) -> int:
    """
    Stronghold Chronological Path Finding (Sequential tracking).
    Inputs: Initialized pointer to StrongholdIter and pointer reference to Generator engine context.
    Returns: Integer detailing remaining strongholds left to calculate globally while mutating iterator's pos parameter to precise biome-verified locations.
    """
    return cubiomes.nextStronghold(sh, ctypes.byref(g))

def estimate_spawn(g: Generator, rng: ctypes.POINTER(ctypes.c_uint64) = None) -> Pos:
    """
    Spawn Point Identification (Estimation).
    Inputs: Pointer to compiled Generator structure (and optional random pointer reference address uint64_t *rng for generic estimations).
    Returns: Pos struct containing absolute horizontal block coordinates (x, z) representing estimated starting guess coordinate.
    """
    return cubiomes.estimateSpawn(ctypes.byref(g), rng)

def get_spawn(g: Generator) -> Pos:
    """
    Spawn Point Identification (Exact Biome-Checked).
    Inputs: Pointer to compiled Generator structure.
    Returns: Pos struct containing absolute horizontal block coordinates (x, z) representing slow biome-checked grass/podzol validation location.
    """
    return cubiomes.getSpawn(ctypes.byref(g))

def get_fixed_end_gateways(mc_version: int, seed: int, src_array: ctypes.POINTER(Pos)) -> None:
    """
    End Gateway Matrix Tracing (Fixed Ring).
    Inputs: Game version inputs, world seed variables, and 20-element target destination allocation buffer array of Pos structs.
    Returns: None (modifies passed 20-element array in place with sequential block locations).
    """
    cubiomes.getFixedEndGateways(mc_version, seed, src_array)

def get_linked_gateway_pos(en: ctypes.POINTER(EndNoise), sn: ctypes.POINTER(SurfaceNoise), seed: int, src: Pos) -> Pos:
    """
    End Gateway Link Tracing (Linked Destinations).
    Inputs: Pointers to active EndNoise and SurfaceNoise instances, seed, and source coordinate pair Pos instance.
    Returns: Complete Pos coordinate structure tracking exact destination point mapping out in outer End islands.
    """
    return cubiomes.getLinkedGatewayPos(en, sn, seed, src)


# ==============================================================================
# 6. Climate Noise & Terrain Geometry (Modern 1.18+)
# ==============================================================================

def sample_biome_noise(bn: ctypes.POINTER(BiomeNoise), np: ctypes.POINTER(ctypes.c_int64), x: int, y: int, z: int, dat: ctypes.POINTER(ctypes.c_uint64) = None, sample_flags: int = 0) -> int:
    """
    Raw Climate Parameter Vectors.
    Inputs: Pointer reference to configured BiomeNoise instance, 6-element allocation array buffer of int64_t, absolute spatial coordinates (x, y, z), optional internal tracking reference dat, and flag modifiers.
    Returns: Integer corresponding to final resolved BiomeID while modifying provided int64_t *np array with raw Perlin values (Temperature, Humidity, Continentalness, Erosion, Shift, Weirdness).
    """
    return cubiomes.sampleBiomeNoise(bn, np, x, y, z, dat, sample_flags)

def get_para_range(para: ctypes.POINTER(DoublePerlinNoise), pmin: ctypes.POINTER(ctypes.c_double), pmax: ctypes.POINTER(ctypes.c_double), x: int, z: int, w: int, h: int, data: ctypes.c_void_p = None, func: ctypes.c_void_p = None) -> int:
    """
    Climate Noise Map Scans (getParaRange).
    Inputs: Pointer to continuous noise parameter stream (DoublePerlinNoise), double pointers mapping output destination spaces (pmin, pmax), bounding box boundaries (x, z, w, h), arbitrary validation tracking context address pointer, optional gradient callback hook.
    Returns: Integer execution error status parameter while updating destination double memory pointers directly with calculated min/max noise ranges.
    """
    return cubiomes.getParaRange(para, pmin, pmax, x, z, w, h, data, func)

def get_biome_para_extremes(mc_version: int) -> ctypes.POINTER(ctypes.c_int):
    """
    Global Version Climate Table Caps.
    Inputs: Version parameters.
    Returns: Constant integer pointer referencing internal multidimensional lookup matrices representing standard min/max multi-noise parameters.
    """
    return cubiomes.getBiomeParaExtremes(mc_version)

def get_biome_para_limits(mc_version: int, biome_id: int) -> ctypes.POINTER(ctypes.c_int):
    """
    Global Biome Climate Table Caps.
    Inputs: Version parameters, alongside target biome identification integers.
    Returns: Constant integer pointer referencing internal lookup matrices representing structural generation caps or min/max multi-noise parameters.
    """
    return cubiomes.getBiomeParaLimits(mc_version, biome_id)

def get_possible_biomes_for_limits(ids: ctypes.POINTER(ctypes.c_char), mc_version: int, limits: ctypes.POINTER(ctypes.c_int)) -> None:
    """
    Climate Subset Synthesis.
    Inputs: 256-element byte-array (char ids[256]), game version code, fixed 6x2 multi-dimensional integer limits constraint array tracking user noise criteria thresholds.
    Returns: None (modifies passed char ids[256] lookup table in place by setting indices to non-zero values for any capable biome ID).
    """
    cubiomes.getPossibleBiomesForLimits(ids, mc_version, limits)

def get_largest_rec(match: int, ids: ctypes.POINTER(ctypes.c_int), sx: int, sz: int, p0: ctypes.POINTER(Pos), p1: ctypes.POINTER(Pos)) -> int:
    """
    Footprint Geometry Finders (getLargestRec).
    Inputs: Target matching integer biome code, constant pointer to existing calculated block layout array, layout grid size bounds (sx, sz), pointer addresses targeting memory for two Pos coordinates (p0, p1).
    Returns: Integer defining total surface area footprint found while modifying p0 and p1 pointers with coordinate corner parameters of largest unbroken rectangle cluster found.
    """
    return cubiomes.getLargestRec(match, ids, sx, sz, p0, p1)

def map_approx_height(y: ctypes.POINTER(ctypes.c_float), ids: ctypes.POINTER(ctypes.c_int), g: Generator, sn: ctypes.POINTER(SurfaceNoise), x: int, z: int, w: int, h: int) -> int:
    """
    Volumetric Surface Terrain Mapping.
    Inputs: Allocated destination float array pointer buffer (y), companion integer array buffer pointer to trace biomes simultaneously (ids), pointer variables referencing active Generator and SurfaceNoise engines, spatial coordinate tracking boundaries (x, z, w, h).
    Returns: Integer status metric while writing absolute terrain block surface elevation profiles sequentially into provided float *y matrix array.
    """
    return cubiomes.mapApproxHeight(y, ids, ctypes.byref(g), sn, x, z, w, h)


# ==============================================================================
# 7. Seed Vectors, Filters, & Math Constraints
# ==============================================================================

def get_shadow_seed(seed: int) -> int:
    """
    Shadow Seed Transformation.
    Inputs: Single uint64_t variable tracking original target world seed.
    Returns: uint64_t parameter representing corresponding sibling mathematical shadow seed.
    """
    val = (-7379792620528906219 - seed) & 0xffffffffffffffff
    return ctypes.c_int64(val).value

def shift_base_seed(base_seed: int, reg_x: int, reg_z: int) -> int:
    """
    Shifting Base Seeds.
    Inputs: 48-bit base seed parameter, alongside linear chunk region step indices (reg_x, reg_z).
    Returns: uint64_t transposed seed variable mapping matching structure clusters back to local world origin coordinate layout.
    """
    return (base_seed - reg_x * 341873128712 - reg_z * 132897987541) & 0xffffffffffff

def check_for_biomes(g: Generator, cache: ctypes.POINTER(ctypes.c_int), range_struct: Range, dim: int, seed: int, filter_ptr: ctypes.POINTER(BiomeFilter), stop_flag: ctypes.POINTER(ctypes.c_char) = None) -> int:
    """
    Pre-Generation Filter Verification.
    Inputs: Pointer to Generator context, working integer buffer pointer cache, boundary Range instance, chosen dimension ID (-1, 0, 1), full 64-bit world seed, pointer to set up BiomeFilter validation checklist, atomic stop loop pointer flag.
    Returns: Integer status flag mapping structural suitability profiles (0: failed checklist entirely, 1: matching layout completed, 2: partially completed optimization pass).
    """
    return cubiomes.checkForBiomes(ctypes.byref(g), cache, range_struct, dim, seed, filter_ptr, stop_flag)

def check_for_temps(ls: ctypes.POINTER(LayerStack), seed: int, x: int, z: int, w: int, h: int, tc: ctypes.POINTER(ctypes.c_int)) -> int:
    """
    Layer Stack Temperature Scans (checkForTemps).
    Inputs: Pointer to active historic layered engine (LayerStack), world seed, spatial mapping indices (x, z, w, h), fixed 9-element constraint verification array tc[9] setting precise temperature thresholds.
    Returns: Integer boolean evaluation flag (1 if environmental ratios across layer components satisfy all climatic checklist steps, 0 if dropped).
    """
    return cubiomes.checkForTemps(ls, seed, x, z, w, h, tc)

def monte_carlo_biomes(g: Generator, range_struct: Range, rng: ctypes.POINTER(ctypes.c_uint64), coverage: float, confidence: float, eval_func: ctypes.c_void_p = None, data: ctypes.c_void_p = None) -> int:
    """
    Stochastic Ratios Check (monteCarloBiomes).
    Inputs: Pointer reference targeting Generator instance, target boundary mapping Range struct, pointer referencing tracking seed variable address, double coverage minimum, double confidence tolerance, callback evaluation function point, generic user context data pointer.
    Returns: Integer boolean variable (1 if sampling paths indicate target environment meets coverage distributions across defined confidence criteria scales, 0 if fails).
    """
    return cubiomes.monteCarloBiomes(ctypes.byref(g), range_struct, rng, coverage, confidence, eval_func, data)


if __name__ == "__main__":
    print("\n--- Testing Cubiomes Python Interface ---")
    MC_1_19_4 = 33
    seed = 262
    
    # Test 1: Initialize Generator and query biome at (0, 63, 0)
    g = create_generator(MC_1_19_4)
    apply_seed(g, 0, seed)
    biome = get_biome_at(g, 1, 0, 63, 0)
    print(f"Biome at Overworld (0, 63, 0) for seed {seed}: {biome} (Expected 14 for Mushroom Fields)")
    
    # Test 2: Shadow Seed
    shadow = get_shadow_seed(seed)
    print(f"Shadow seed for {seed}: {shadow}")
    
    # Test 3: Slime Chunk check at (0, 0)
    slime = is_slime_chunk(seed, 0, 0)
    print(f"Is chunk (0, 0) a slime chunk for seed {seed}? {'Yes' if slime else 'No'}")
    
    print("All interface functions loaded and verified successfully!")
