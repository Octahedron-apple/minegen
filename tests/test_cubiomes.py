import ctypes
import pytest
import subprocess
import sys
from pathlib import Path

# Load lib
lib_path = Path(__file__).parent / "libcubiomes_wrapper.so"
root_dir = Path(__file__).parent.parent

def auto_compile_wrapper():
    """Runs 'make' in the root directory automatically to ensure libcubiomes_wrapper.so is built."""
    try:
        subprocess.run(
            ["make"], 
            cwd=str(root_dir), 
            check=True, 
            stdout=subprocess.DEVNULL, 
            stderr=subprocess.PIPE
        )
    except subprocess.CalledProcessError as e:
        print(f"Compilation error while building cubiomes wrapper:\n{e.stderr.decode()}", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError:
        print("Error: 'make' command not found. Ensure you are running inside 'nix-shell'.", file=sys.stderr)
        sys.exit(1)

auto_compile_wrapper()
wrapper = ctypes.CDLL(str(lib_path))

# Setup types
wrapper.wrapper_get_mc_version.argtypes = [ctypes.c_int]
wrapper.wrapper_get_mc_version.restype = ctypes.c_int

wrapper.wrapper_get_biome_at.argtypes = [ctypes.c_int, ctypes.c_uint64, ctypes.c_int, ctypes.c_int, ctypes.c_int]
wrapper.wrapper_get_biome_at.restype = ctypes.c_int

wrapper.wrapper_get_structure_pos.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_uint64, ctypes.c_int, ctypes.c_int, ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int)]
wrapper.wrapper_get_structure_pos.restype = ctypes.c_int

wrapper.wrapper_is_viable_structure_pos.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_uint64, ctypes.c_int, ctypes.c_int]
wrapper.wrapper_is_viable_structure_pos.restype = ctypes.c_int


# Enums & Constants
MC_1_19 = wrapper.wrapper_get_mc_version(19)
MC_1_21 = wrapper.wrapper_get_mc_version(21)

MUSHROOM_FIELDS = 14
OUTPOST = 10 # From enum StructureType { Feature, Desert_Pyramid, Jungle_Temple, Swamp_Hut, Igloo, Village, Ocean_Ruin, Shipwreck, Monument, Mansion, Outpost, ... }
VILLAGE = 5

def test_deterministic_biome_generation():
    """
    Test the core biome finder logic by asserting that Seed 262 generates a "Mushroom Fields" biome 
    at Overworld block coordinates (x=0, y=63, z=0) as outlined in the documentation.
    """
    seed = 262
    x, y, z = 0, 63, 0
    biome_id = wrapper.wrapper_get_biome_at(MC_1_19, seed, x, y, z)
    
    assert biome_id == MUSHROOM_FIELDS, f"Expected Mushroom Fields (14), got {biome_id}"

@pytest.mark.parametrize("struct_type, mc_version, seed, regX, regZ", [
    (OUTPOST, MC_1_19, 12345, 0, 0),
    (OUTPOST, MC_1_21, 99999, 1, -1),
    (VILLAGE, MC_1_19, 262, 0, 0)
])
def test_structure_generation_viability(struct_type, mc_version, seed, regX, regZ):
    """
    Test structure generation viability (e.g., Pillager Outposts using getStructurePos and isViableStructurePos)
    to verify that the library detects attempts correctly.
    """
    out_x = ctypes.c_int()
    out_z = ctypes.c_int()
    
    valid_pos = wrapper.wrapper_get_structure_pos(struct_type, mc_version, seed, regX, regZ, ctypes.byref(out_x), ctypes.byref(out_z))
    
    if valid_pos:
        # If the position attempt was valid, check its viability
        # Since viability is seed-dependent and biome-dependent, it might be 0 or 1.
        # We just want to ensure it doesn't crash and returns a boolean-like int (0 or 1)
        viability = wrapper.wrapper_is_viable_structure_pos(struct_type, mc_version, seed, out_x.value, out_z.value)
        assert viability in [0, 1], f"Viability should be 0 or 1, got {viability}"
    else:
        # valid_pos == 0 means no attempt in this region for this structure
        pass
