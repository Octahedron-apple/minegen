CUBIOMES_DIR = ./deps/cubiomes
OUTPUT_LIB  = ./libcubiomes.so
WRAPPER_LIB = ./tests/libcubiomes_wrapper.so

SRCS = $(CUBIOMES_DIR)/biomenoise.c \
       $(CUBIOMES_DIR)/biomes.c \
       $(CUBIOMES_DIR)/finders.c \
       $(CUBIOMES_DIR)/generator.c \
       $(CUBIOMES_DIR)/layers.c \
       $(CUBIOMES_DIR)/noise.c \
       $(CUBIOMES_DIR)/quadbase.c \
       $(CUBIOMES_DIR)/util.c

CC      = gcc
CFLAGS  = -shared -fPIC -fwrapv -O3 -I$(CUBIOMES_DIR)
LDFLAGS = -lm -lpthread

.PHONY: all clean

all: $(OUTPUT_LIB) $(WRAPPER_LIB)

$(OUTPUT_LIB): $(SRCS)
	$(CC) $(CFLAGS) -o $(OUTPUT_LIB) $(SRCS) $(LDFLAGS)

$(WRAPPER_LIB): ./tests/test_wrapper.c $(SRCS)
	$(CC) $(CFLAGS) -o $(WRAPPER_LIB) ./tests/test_wrapper.c $(SRCS) $(LDFLAGS)

clean:
	rm -f $(OUTPUT_LIB) $(WRAPPER_LIB)
