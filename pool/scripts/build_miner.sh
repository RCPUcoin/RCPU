#!/bin/bash
set -e
SRCDIR=/root/miner-src-linux
cd "$SRCDIR"
echo "=== RCPU cpuminer Linux build (manual gcc/g++) ==="
echo ""

# Clean
rm -f *.o minerd minerd-rcpu 2>/dev/null
rm -f RandomX/src/*.o RandomX/src/blake2/*.o 2>/dev/null

# Build flags (Linux version: no Windows-specific macros)
COMMON_FLAGS="-I. -I$SRCDIR/RandomX/src -I$SRCDIR/compat/jansson \
  -DRANDOMX -DRANDOMX_JIT -DHAVE_CONFIG_H \
  -DVERSION=\"3.0.9\" -DPROGNAME=\"cpuminer-rcpu\" \
  -O2 -maes -mavx2 -mssse3 -fPIC"

# Step 1: System jansson doesn't need self-compile, use system library directly
# If you need to self-compile jansson:
echo "[1/4] Compile jansson static library..."
cd "$SRCDIR/compat/jansson"
for f in value.c load.c dump.c hashtable.c strbuffer.c utf.c util.c; do
  [ -f "$f" ] && gcc -c -O2 -fPIC -I. $f -o ${f%.c}.o 2>/dev/null || true
done
ar rcs libjansson.a *.o 2>/dev/null || true
cd "$SRCDIR"
echo "  done"

# Step 2: Compile C source files
echo "[2/4] Compile C source files (gcc)..."
gcc -c $COMMON_FLAGS cpu-miner.c -o cpu-miner.o
gcc -c $COMMON_FLAGS util.c -o util.o
gcc -c $COMMON_FLAGS sha2.c -o sha2.o
gcc -c $COMMON_FLAGS randomx-miner.c -o randomx-miner.o
gcc -c $COMMON_FLAGS pthread_barrier.c -o pthread_barrier.o
gcc -c $COMMON_FLAGS -x assembler-with-cpp sha2-x64.S -o sha2-x64.o
echo "  done"

# Step 3: Compile RandomX C++ source files
echo "[3/4] Compile RandomX C++ source files (g++)..."
cd RandomX/src
for f in aes_hash allocator blake2_generator bytecode_machine cpu dataset \
         instruction instructions_portable randomx soft_aes superscalar \
         virtual_machine vm_compiled vm_compiled_light vm_interpreted \
         vm_interpreted_light jit_compiler_x86 assembly_generator_x86; do
  if [ -f "$f.cpp" ]; then
    g++ -c $COMMON_FLAGS -fpermissive $f.cpp -o $f.o 2>&1 | tail -3
  fi
done
# C source files
for f in argon2_core argon2_ref argon2_avx2 argon2_ssse3 blake2/blake2b \
         reciprocal virtual_memory; do
  if [ -f "$f.c" ]; then
    g++ -c $COMMON_FLAGS -fpermissive $f.c -o ${f//\//_}.o 2>&1 | tail -3
  fi
done
# Assembly
g++ -c $COMMON_FLAGS -x assembler-with-cpp jit_compiler_x86_static.S -o jit_compiler_x86_static.o
cd "$SRCDIR"
echo "  done"

# Step 4: Linking
echo "[4/4] Linking to generate minerd..."
OBJS=""
for f in cpu-miner.o util.o sha2.o randomx-miner.o pthread_barrier.o sha2-x64.o; do
  OBJS="$OBJS $SRCDIR/$f"
done
for f in RandomX/src/*.o; do
  [ -f "$f" ] && OBJS="$OBJS $SRCDIR/$f"
done
# Prefer linking system librandomx.so (if exists)
LINK_RANDOMX=""
if [ -f /usr/local/lib/librandomx.so ]; then
  LINK_RANDOMX="-L/usr/local/lib -lrandomx -Wl,-rpath,/usr/local/lib"
  echo "  Using system librandomx.so"
else
  echo "  Using compiled RandomX object files"
fi

g++ -o "$SRCDIR/minerd-rcpu" $OBJS \
  $LINK_RANDOMX \
  -L/usr/lib/x86_64-linux-gnu -lcurl -ljansson -lpthread -lcrypto -lssl -lm -lstdc++ 2>&1 | tail -30

if [ -f "$SRCDIR/minerd-rcpu" ]; then
  strip "$SRCDIR/minerd-rcpu"
  echo ""
  echo "=== Build successful! ==="
  ls -lh "$SRCDIR/minerd-rcpu"
  file "$SRCDIR/minerd-rcpu"
else
  echo "=== Linking failed ==="
  exit 1
fi
