#!/bin/bash
set -e
MGCC=x86_64-w64-mingw32-gcc-posix
MGXX=x86_64-w64-mingw32-g++-posix
SRC=/root/miner-src-linux
BUILD=/tmp/miner-win
CURLA=/tmp/curl-8.10.1

rm -rf $BUILD && mkdir -p $BUILD
cp $SRC/*.c $SRC/*.h $SRC/*.S $BUILD/ 2>/dev/null || true
cp -r $SRC/RandomX $BUILD/
cp -r $SRC/compat $BUILD/
rm -f $BUILD/RandomX/src/*.o $BUILD/compat/jansson/*.o
cd $BUILD
# Windows config header
cp cpuminer-config-win.h cpuminer-config.h

CFLAGS="-I. -IRandomX/src -Icompat/jansson -I$CURLA/include -DRANDOMX -DRANDOMX_JIT -DHAVE_CONFIG_H -DCURL_STATICLIB -D_WIN32_WINNT=0x0601 -O2 -maes -mavx2 -mssse3 -pthread"

echo "[1/4] jansson..."
cd compat/jansson
for f in value.c load.c dump.c hashtable.c strbuffer.c utf.c; do
  $MGCC -c -O2 -I. $f -o ${f%.c}.o
done
ar rcs libjansson-win.a *.o
cd $BUILD

echo "[2/4] miner C files..."
for f in cpu-miner util sha2 randomx-miner pthread_barrier; do
  echo -n "  $f.c "
  $MGCC -c $CFLAGS $f.c -o $f.o 2>/tmp/werr_$f.log && echo OK || { echo FAIL; head -20 /tmp/werr_$f.log; exit 1; }
done
echo -n "  sha2-x64.S "
$MGCC -c $CFLAGS -x assembler-with-cpp sha2-x64.S -o sha2-x64.o 2>/tmp/werr_sha.log && echo OK || { echo FAIL; head -20 /tmp/werr_sha.log; exit 1; }

echo "[3/4] RandomX..."
cd RandomX/src
for f in aes_hash allocator blake2_generator bytecode_machine cpu dataset \
         instruction instructions_portable randomx soft_aes superscalar \
         virtual_machine vm_compiled vm_compiled_light vm_interpreted \
         vm_interpreted_light jit_compiler_x86 assembly_generator_x86; do
  if [ -f "$f.cpp" ]; then
    echo -n "  $f.cpp "
    $MGXX -c $CFLAGS -fpermissive $f.cpp -o $f.o 2>/tmp/werr_$f.log && echo OK || { echo FAIL; head -10 /tmp/werr_$f.log; exit 1; }
  fi
done
for f in argon2_core argon2_ref argon2_avx2 argon2_ssse3 blake2/blake2b reciprocal virtual_memory; do
  if [ -f "$f.c" ]; then
    obj=$(echo $f | tr '/' '_')
    echo -n "  $f.c "
    $MGXX -c $CFLAGS -fpermissive $f.c -o ${obj%.c}.o 2>/tmp/werr_$obj.log && echo OK || { echo FAIL; head -10 /tmp/werr_$obj.log; exit 1; }
  fi
done
echo -n "  jit_compiler_x86_static.S "
$MGXX -c $CFLAGS -x assembler-with-cpp jit_compiler_x86_static.S -o jit_compiler_x86_static.o 2>/tmp/werr_jit.log && echo OK || { echo FAIL; head -10 /tmp/werr_jit.log; exit 1; }
cd $BUILD

echo "[4/4] linking..."
OBJS="$BUILD/cpu-miner.o $BUILD/util.o $BUILD/sha2.o $BUILD/randomx-miner.o $BUILD/pthread_barrier.o $BUILD/sha2-x64.o"
for f in $BUILD/RandomX/src/*.o; do OBJS="$OBJS $f"; done
$MGXX -o $BUILD/minerd-rcpu.exe $OBJS \
  $CURLA/lib/.libs/libcurl.a $BUILD/compat/jansson/libjansson-win.a \
  -static -static-libgcc -static-libstdc++ -pthread \
  -lws2_32 -lbcrypt -liphlpapi -ladvapi32 2>/tmp/werr_link.log && echo LINK_OK || { echo LINK_FAIL; head -25 /tmp/werr_link.log; exit 1; }
x86_64-w64-mingw32-strip $BUILD/minerd-rcpu.exe 2>/dev/null || true
ls -lh $BUILD/minerd-rcpu.exe
file $BUILD/minerd-rcpu.exe
