#include "../deps/cubiomes/generator.h"
#include "../deps/cubiomes/finders.h"
#include "../deps/cubiomes/biomes.h"

#ifdef __cplusplus
extern "C" {
#endif

// Returns the MC version constant for a given minor version (e.g. 19 for 1.19)
int wrapper_get_mc_version(int minor) {
    switch (minor) {
        case 7: return MC_1_7;
        case 8: return MC_1_8;
        case 9: return MC_1_9;
        case 12: return MC_1_12;
        case 16: return MC_1_16;
        case 17: return MC_1_17;
        case 18: return MC_1_18;
        case 19: return MC_1_19;
        case 20: return MC_1_20;
        case 21: return MC_1_21;
        default: return MC_NEWEST;
    }
}

// 1. Get Biome at block coordinates
int wrapper_get_biome_at(int mc_version, uint64_t seed, int x, int y, int z) {
    Generator g;
    setupGenerator(&g, mc_version, 0);
    applySeed(&g, 0, seed); // 0 = Overworld
    return getBiomeAt(&g, 1, x, y, z);
}

// 2. Structure generation pos and viability
int wrapper_get_structure_pos(int struct_type, int mc_version, uint64_t seed, int regX, int regZ, int *out_x, int *out_z) {
    Pos p;
    if (getStructurePos(struct_type, mc_version, seed, regX, regZ, &p)) {
        if (out_x) *out_x = p.x;
        if (out_z) *out_z = p.z;
        return 1;
    }
    return 0;
}

int wrapper_is_viable_structure_pos(int struct_type, int mc_version, uint64_t seed, int x, int z) {
    Generator g;
    setupGenerator(&g, mc_version, 0);
    applySeed(&g, 0, seed);
    return isViableStructurePos(struct_type, &g, x, z, 0);
}

#ifdef __cplusplus
}
#endif
