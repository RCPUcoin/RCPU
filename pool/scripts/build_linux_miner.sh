#!/bin/bash
set -e
SRCDIR="/root/miner-src-linux"
cd "$SRCDIR"

echo "=== Preparing build environment ==="
# Ensure cpuminer-config.h exists and is Linux compatible (remove Windows-specific content)
ls -la "$SRCDIR/cpuminer-config.h"
ls -la "$SRCDIR/config.h"

# Clean
rm -f *.o minerd minerd-rcpu 2>/dev/null
rm -f RandomX/src/*.o RandomX/src/blake2/*.o 2>/dev/null

echo ""
echo "=== [1/5] Prepare cpuminer-config.h (Linux compatible) ==="
# config.h already has HAVE_* definitions (from previous configure)
cat > /tmp/cpuminer-config-final.h <<'HDR_EOF'
#ifndef CPUMINER_CONFIG_H
#define CPUMINER_CONFIG_H 1
#define PACKAGE_NAME "cpuminer-rcpu"
#define PACKAGE_VERSION "3.0.9"
#define PACKAGE "cpuminer-rcpu"
#define PACKAGE_STRING "cpuminer-rcpu 3.0.9"
#define VERSION "3.0.9"

/* Standard headers */
#define HAVE_STDINT_H 1
#define HAVE_STDBOOL_H 1
#define HAVE_STDLIB_H 1
#define HAVE_STRING_H 1
#define HAVE_SYS_TYPES_H 1
#define HAVE_SYS_STAT_H 1
#define HAVE_UNISTD_H 1
#define HAVE_ENDIAN_H 1
#define HAVE_SYS_ENDIAN_H 0
#define HAVE_SYS_PARAM_H 1
#define HAVE_SYS_SYSCTL_H 1
#define HAVE_SYSLOG_H 1
#define HAVE_ALLOCA_H 0
#define HAVE_STDALIGN_H 1

/* Functions */
#define HAVE_DECL_BE32DEC 0
#define HAVE_DECL_LE32DEC 0
#define HAVE_DECL_BE32ENC 0
#define HAVE_DECL_LE32ENC 0
#define HAVE_ALLOCA 1
#define HAVE_GETOPT_LONG 1
#define HAVE_SYS_SYSINFO 1

/* Libraries */
#define HAVE_LIBCURL 1
#define HAVE_CURL 1
#define HAVE_LIBJANSSON 1
#define HAVE_LIBPTHREAD 1

/* CPU features */
#define HAVE_AVX 1
#define HAVE_AVX2 1
#define HAVE_XOP 1
#define HAVE_AES 1
#define HAVE_SSSE3 1
#define HAVE_SSE2 1
#define __SSE2__ 1
#define __AVX2__ 1
#define __AES__ 1
#define __SSSE3__ 1

/* RandomX */
#define RANDOMX 1
#define RANDOMX_JIT 1

/* OS */
#define __linux__ 1
#define _GNU_SOURCE 1
#define STDC_HEADERS 1

#endif
HDR_EOF
cp /tmp/cpuminer-config-final.h "$SRCDIR/cpuminer-config.h"
echo "  cpuminer-config.h prepared"

echo ""
echo "=== [2/5] Compile jansson (optional) ==="
cd "$SRCDIR/compat/jansson" 2>/dev/null && {
  for f in value.c load.c dump.c hashtable.c strbuffer.c utf.c util.c; do
    [ -f "$f" ] && gcc -c -O2 -fPIC -I. -DHAVE_CONFIG_H $f -o ${f%.c}.o 2>/dev/null || true
  done
  ar rcs libjansson.a *.o 2>/dev/null || true
}
cd "$SRCDIR"
echo "  done"

# CFLAGS / CXXFLAGS - Linux version, no WIN32
COMMON_FLAGS="-I. -I$SRCDIR/RandomX/src -I/usr/include \
  -DRANDOMX -DRANDOMX_JIT -DHAVE_CONFIG_H -D_GNU_SOURCE \
  -DVERSION=\\\"3.0.9\\\" -DPROGNAME=\\\"cpuminer-rcpu\\\" \
  -O2 -maes -mavx2 -mssse3 -fPIC"

echo ""
echo "=== [3/5] Compile C source files (gcc) ==="
cd "$SRCDIR"
gcc -c $COMMON_FLAGS cpu-miner.c -o cpu-miner.o 2>&1 | head -30
gcc -c $COMMON_FLAGS util.c -o util.o 2>&1 | head -20
gcc -c $COMMON_FLAGS sha2.c -o sha2.o 2>&1 | head -20
gcc -c $COMMON_FLAGS randomx-miner.c -o randomx-miner.o 2>&1 | head -20
gcc -c $COMMON_FLAGS pthread_barrier.c -o pthread_barrier.o 2>&1 | head -20
gcc -c $COMMON_FLAGS -x assembler-with-cpp sha2-x64.S -o sha2-x64.o 2>&1 | head -20
echo "  .o files: "
ls -la *.o 2>/dev/null || true

echo ""
echo "=== [4/5] Compile RandomX C++ source files (g++) ==="
cd RandomX/src
# RandomX C++ sources
for f in aes_hash allocator blake2_generator bytecode_machine cpu dataset \
         instruction instructions_portable randomx soft_aes superscalar \
         virtual_machine vm_compiled vm_compiled_light vm_interpreted \
         vm_interpreted_light jit_compiler_x86 assembly_generator_x86; do
  if [ -f "$f.cpp" ]; then
    echo -n "  $f.cpp "
    g++ -c $COMMON_FLAGS -fpermissive $f.cpp -o $f.o 2>/tmp/err_$f.log && echo "OK" || { echo "FAIL:"; cat /tmp/err_$f.log | head -5; }
  fi
done
# RandomX C sources
for f in argon2_core argon2_ref argon2_avx2 argon2_ssse3 blake2/blake2b reciprocal virtual_memory; do
  if [ -f "$f.c" ]; then
    obj=$(echo $f | tr '/' '_')
    echo -n "  $f.c -> ${obj%.c}.o "
    g++ -c $COMMON_FLAGS -fpermissive $f.c -o ${obj%.c}.o 2>/tmp/err_$obj.log && echo "OK" || { echo "FAIL:"; cat /tmp/err_$obj.log | head -5; }
  fi
done
# ASM
echo -n "  jit_compiler_x86_static.S "
g++ -c $COMMON_FLAGS -x assembler-with-cpp jit_compiler_x86_static.S -o jit_compiler_x86_static.o 2>/tmp/err_asm.log && echo "OK" || { echo "FAIL:"; cat /tmp/err_asm.log | head -5; }
cd "$SRCDIR"
echo "  RandomX .o files: "
ls RandomX/src/*.o 2>/dev/null | wc -l

echo ""
echo "=== [5/5] Linking ==="
OBJS=""
for f in cpu-miner.o util.o sha2.o randomx-miner.o pthread_barrier.o sha2-x64.o; do
  [ -f "$SRCDIR/$f" ] && OBJS="$OBJS $SRCDIR/$f"
done
for f in $SRCDIR/RandomX/src/*.o; do
  [ -f "$f" ] && OBJS="$OBJS $f"
done
echo "  linking $(echo $OBJS | wc -w) object files..."

# Prefer system librandomx.so (already in /usr/local/lib)
LINK_RANDOMX="-L/usr/local/lib -lrandomx -Wl,-rpath,/usr/local/lib"

g++ -o "$SRCDIR/minerd-rcpu" $OBJS \
  $LINK_RANDOMX \
  -L/usr/lib/x86_64-linux-gnu -lcurl -ljansson -lpthread -lcrypto -lssl -lm -lstdc++ -lpthread 2>&1 | tail -40

if [ -f "$SRCDIR/minerd-rcpu" ]; then
  strip "$SRCDIR/minerd-rcpu" 2>/dev/null || true
  echo ""
  echo "=== Build successful! ==="
  ls -lh "$SRCDIR/minerd-rcpu"
  file "$SRCDIR/minerd-rcpu"
else
  echo "=== Linking failed ==="
  exit 1
fi
