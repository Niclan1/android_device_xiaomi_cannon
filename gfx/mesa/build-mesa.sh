#!/bin/bash
# Out-of-tree cross build of the Mesa panfrost EGL/GLES driver for Android.
#
# The Android build never runs this: the result is committed under
# prebuilt/<arch>/ and gfx/gfx.mk installs it to /vendor/lib{,64}/egl/. The
# libraries are loaded when ro.hardware.egl=mesa, which libinit sets by default
# on mainline kernels (androidboot.cannon.egl=angle opts out; legacy 4.14 keeps Mali).
#
# usage: build-mesa.sh deps | native | ndk | build <arm64|arm> | all | check-patches
#   deps    python venv (meson, ninja, mako, ...), host LLVM/clang/libclc packages, Mesa sources
#   native  host tools used by the cross build (mesa_clc, panfrost_compile, ...)
#   ndk     Android NDK
#   build   cross-compile one ABI, install it and publish it into prebuilt/<arch>
#   all     everything, both ABIs
#
# env:  GFX_MESA_WORK  work directory (default $HOME/gfx-mesa, about 4 GB)
#       GFX_MESA_JOBS  ninja jobs (default 4; heavy steps run under nice -n 15)
# host: python3 (venv), curl, bsdtar, unzip, zstd, pkg-config, bison, flex and network access
#       on the first run (Arch packages, Mesa tarball, NDK, libdrm/expat meson wraps).
# Every stage is idempotent and skipped when its output already exists.

set -eu

HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
W=${GFX_MESA_WORK:-$HOME/gfx-mesa}
JOBS=${GFX_MESA_JOBS:-4}

MESA_VER=26.2.6
MESA_SHA256=b9436b3e1a8be76fbd4823dc884f90596ab7c6ac5e1867a305e66ffccfb31a92
CAMERA_PATCH=$HERE/patches/0001-cros-nv12-import.patch
YV12_PATCH=$HERE/patches/0002-cros-yv12-import.patch
NDK_VER=r28c
LLVM_VER=23.1.4
API=34

SRC=$W/src/mesa-$MESA_VER
NDK_BIN=$W/ndk/android-ndk-$NDK_VER/toolchains/llvm/prebuilt/linux-x86_64/bin
ARCH_MIRROR=https://fastly.mirror.pkgbuild.com/extra/os/x86_64
ARCH_ARCHIVE=https://archive.archlinux.org/packages
ARCH_PKGS="llvm-$LLVM_VER-1-x86_64 llvm-libs-$LLVM_VER-1-x86_64 clang-$LLVM_VER-1-x86_64
  clang-libs-$LLVM_VER-1-x86_64 libclc-$LLVM_VER-1-x86_64 spirv-llvm-translator-23.1.3-1-x86_64
  spirv-tools-1:1.4.363.0-1-x86_64 spirv-headers-1:1.4.363.0-1-any libdrm-2.4.134-1-x86_64"

trap 'rc=$?; [ "$rc" -eq 0 ] || echo "[build-mesa] failed (exit $rc), see $W/*.log" >&2' EXIT

log() { echo "[build-mesa] $*"; }

fetch_pkg() {
  local f=$1.pkg.tar.zst n=${1%%-[0-9]*}
  [ -s "$f" ] && return 0
  if [ -e "/var/cache/pacman/pkg/$f" ]; then
    cp "/var/cache/pacman/pkg/$f" "$f"
  else
    curl -fsSL -m 900 -o "$f.part" "$ARCH_MIRROR/$f" ||
      curl -fsSL -m 900 -o "$f.part" "$ARCH_ARCHIVE/${n:0:1}/$n/${f//:/%3A}"
    mv "$f.part" "$f"
  fi
}

check_mesa_archive() {
  printf '%s  %s\n' "$MESA_SHA256" "$W/src/mesa-$MESA_VER.tar.xz" | sha256sum -c -
}


prepare_yv12_source() {
  local fallback=$SRC/src/util/u_gralloc/u_gralloc_fallback.c
  local header=$SRC/src/util/u_gralloc/u_gralloc_cros_yv12.h
  git -C "$SRC" apply --check "$YV12_PATCH"
  git -C "$SRC" apply "$YV12_PATCH"
  printf '%s  %s\n' "e754c08aad48d60c6f3cd29dab68db477cd9b7fe0db6c75a1c7eca3b10bc816c" "$fallback" | sha256sum -c -
  printf '%s  %s\n' "427a7c4be5b5d43d226c2d3aeac9f1b3487d986ed19f31ba1f2cc3f14f180aa6" "$header" | sha256sum -c -
}

prepare_camera_source() {
  local fallback=$SRC/src/util/u_gralloc/u_gralloc_fallback.c
  local header=$SRC/src/util/u_gralloc/u_gralloc_cros_nv12.h
  check_mesa_archive
  [ -f "$YV12_PATCH" ] || { log "missing YV12 source patch"; exit 1; }
  if printf '%s  %s\n' "e754c08aad48d60c6f3cd29dab68db477cd9b7fe0db6c75a1c7eca3b10bc816c" "$fallback" | sha256sum -c - >/dev/null 2>&1; then
    printf '%s  %s\n' "186b54b18c7d6bab60a3921f562550288e5c507b6239f37bd1652eb44b736cc2" "$header" | sha256sum -c -
    printf '%s  %s\n' "427a7c4be5b5d43d226c2d3aeac9f1b3487d986ed19f31ba1f2cc3f14f180aa6" "$SRC/src/util/u_gralloc/u_gralloc_cros_yv12.h" | sha256sum -c -
    git -C "$SRC" apply --reverse --check "$YV12_PATCH"
    return 0
  fi
  [ -f "$CAMERA_PATCH" ] || { log "missing camera source patch"; exit 1; }
  if printf '%s  %s\n' "b1eae4378163b643232101b820848b33c6fbc8512525e7b2db7665c1bcbc7874" "$fallback" | sha256sum -c - >/dev/null 2>&1; then
    printf '%s  %s\n' "186b54b18c7d6bab60a3921f562550288e5c507b6239f37bd1652eb44b736cc2" "$header" | sha256sum -c -
    git -C "$SRC" apply --reverse --check "$CAMERA_PATCH"
    prepare_yv12_source
    return 0
  fi
  printf '%s  %s\n' "2aff5bd509e852c597b23b152bcbf79a0719980d85a466a4bef6f4c1903e2dce" "$fallback" | sha256sum -c -
  git -C "$SRC" apply --check "$CAMERA_PATCH"
  git -C "$SRC" apply "$CAMERA_PATCH"
  printf '%s  %s\n' "b1eae4378163b643232101b820848b33c6fbc8512525e7b2db7665c1bcbc7874" "$fallback" | sha256sum -c -
  printf '%s  %s\n' "186b54b18c7d6bab60a3921f562550288e5c507b6239f37bd1652eb44b736cc2" "$header" | sha256sum -c -
  prepare_yv12_source
}

stage_deps() {
  local p f
  mkdir -p "$W/arch-pkgs" "$W/arch-root" "$W/src"

  if [ ! -x "$W/venv/bin/meson" ]; then
    python3 -m venv "$W/venv"
    "$W/venv/bin/pip" install -q meson ninja mako pyyaml packaging setuptools ply
  fi

  if [ ! -e "$W/arch-root/.extracted-$LLVM_VER" ]; then
    for p in $ARCH_PKGS; do
      (cd "$W/arch-pkgs" && fetch_pkg "$p")
      bsdtar -xf "$W/arch-pkgs/$p.pkg.tar.zst" -C "$W/arch-root" 2>/dev/null || true
    done
    [ -x "$W/arch-root/usr/bin/llvm-config" ] || { log "LLVM packages did not extract"; exit 1; }
    # the packages hardcode /usr in their pkg-config files
    for f in "$W"/arch-root/usr/lib/pkgconfig/*.pc "$W"/arch-root/usr/share/pkgconfig/*.pc; do
      sed -i "s|=/usr|=$W/arch-root/usr|g" "$f"
    done
    touch "$W/arch-root/.extracted-$LLVM_VER"
  fi

  if [ ! -f "$SRC/meson.build" ]; then
    curl -fsSL -m 900 -o "$W/src/mesa-$MESA_VER.tar.xz" "https://archive.mesa3d.org/mesa-$MESA_VER.tar.xz"
    check_mesa_archive
    tar -xf "$W/src/mesa-$MESA_VER.tar.xz" -C "$W/src"
  fi
  prepare_camera_source
}

stage_native() {
  if [ -x "$W/native/bin/mesa_clc" ] && [ -x "$W/native/bin/panfrost_compile" ]; then
    log "native tools present"
    return 0
  fi
  cd "$W"
  export PATH=$W/venv/bin:$W/arch-root/usr/bin:$PATH
  export LD_LIBRARY_PATH=$W/arch-root/usr/lib
  export PKG_CONFIG_PATH=$W/arch-root/usr/lib/pkgconfig:$W/arch-root/usr/share/pkgconfig
  printf "[binaries]\nllvm-config = '%s'\n" "$W/arch-root/usr/bin/llvm-config" > native.ini
  rm -rf build-native
  meson setup build-native "$SRC" --native-file native.ini --prefix="$W/native" \
    -Dbuildtype=release -Dplatforms= -Dgallium-drivers= -Dvulkan-drivers= \
    -Dglx=disabled -Degl=disabled -Dgbm=disabled -Dgles1=disabled -Dgles2=disabled -Dopengl=false \
    -Dllvm=enabled -Dshared-llvm=enabled -Dmesa-clc=enabled -Dinstall-mesa-clc=true \
    -Dprecomp-compiler=enabled -Dinstall-precomp-compiler=true -Dtools=panfrost \
    -Dpanfrost-rust=false -Dvalgrind=disabled -Dlibunwind=disabled -Dlmsensors=disabled \
    > cfg-native.log 2>&1
  nice -n 15 ninja -C build-native -j"$JOBS" > build-native.log 2>&1
  nice -n 15 meson install -C build-native >> build-native.log 2>&1
}

stage_ndk() {
  if [ -x "$NDK_BIN/clang" ]; then
    log "NDK present"
    return 0
  fi
  mkdir -p "$W/ndk"
  nice -n 15 curl -fsSL -m 1800 -o "$W/android-ndk-$NDK_VER-linux.zip" \
    "https://dl.google.com/android/repository/android-ndk-$NDK_VER-linux.zip"
  nice -n 15 unzip -q "$W/android-ndk-$NDK_VER-linux.zip" -d "$W/ndk"
}

# The driver must only link what the sphal namespace can resolve (LLNDK and
# vendor-available libraries); anything else would make EGL initialisation fail.
check_needed() {
  local bad
  bad=$("$NDK_BIN/llvm-readelf" -d "$1" | sed -n 's/.*(NEEDED).*\[\(.*\)\]/\1/p' |
    grep -v -x -E 'libc\.so|libm\.so|libdl\.so|liblog\.so|libz\.so|libsync\.so|libnativewindow\.so|libhardware\.so|libgallium_dri\.so' || true)
  if [ -n "$bad" ]; then
    log "$1 links libraries that are not reachable from sphal: $bad"
    exit 1
  fi
}

publish() {
  local arch=$1 dest=$2 out=$HERE/prebuilt/$1 f src
  mkdir -p "$out"
  for f in libEGL_mesa.so libGLESv1_CM_mesa.so libGLESv2_mesa.so libgallium_dri.so; do
    src=$(find "$dest" -name "$f" -type f | head -n 1)
    [ -n "$src" ] || { log "$f was not installed under $dest"; exit 1; }
    check_needed "$src"
    install -m 0644 "$src" "$out/$f"
  done
  printf 'mesa %s\nndk %s (api %s)\ngallium panfrost, static libdrm/expat, EGL/GLES suffix _mesa\n' \
    "$MESA_VER" "$NDK_VER" "$API" > "$out/BUILDINFO"
  printf 'source_sha256 %s\ncamera_patch_sha256 %s\n' "$MESA_SHA256" \
    "$(sha256sum "$CAMERA_PATCH" | cut -d ' ' -f 1)" >> "$out/BUILDINFO"
  printf 'yv12_patch_sha256 %s\n' "$(sha256sum "$YV12_PATCH" | cut -d ' ' -f 1)" >> "$out/BUILDINFO"
  ls -l "$out"
}

stage_build() {
  local arch=$1 triple family cpu libdir reconf=
  case $arch in
    arm64) triple=aarch64-linux-android$API; family=aarch64; cpu=armv8; libdir=lib64 ;;
    arm)   triple=armv7a-linux-androideabi$API; family=arm; cpu=armv7; libdir=lib ;;
    *)     echo "unknown arch '$arch' (arm64 or arm)" >&2; exit 2 ;;
  esac
  local bd=$W/build-$arch dest=$W/dist-$arch

  cd "$W"
  export PATH=$W/native/bin:$W/venv/bin:$W/arch-root/usr/bin:$PATH
  export LD_LIBRARY_PATH=$W/arch-root/usr/lib
  unset PKG_CONFIG_PATH
  mkdir -p cross-pc
  cat > "cross-$arch.ini" <<EOF
[constants]
ndk = '$NDK_BIN/'

[binaries]
ar = ndk + 'llvm-ar'
c = [ndk + '$triple-clang']
cpp = [ndk + '$triple-clang++', '-fno-exceptions', '-fno-unwind-tables', '-fno-asynchronous-unwind-tables', '--start-no-unused-arguments', '-static-libstdc++', '--end-no-unused-arguments']
c_ld = 'lld'
cpp_ld = 'lld'
strip = ndk + 'llvm-strip'
pkg-config = 'pkg-config'

[host_machine]
system = 'android'
cpu_family = '$family'
cpu = '$cpu'
endian = 'little'

[properties]
needs_exe_wrapper = true
pkg_config_libdir = ['$W/cross-pc']
EOF

  [ -e "$bd/build.ninja" ] && reconf=--reconfigure
  meson setup $reconf "$bd" "$SRC" --cross-file "cross-$arch.ini" --prefix=/vendor -Dlibdir="$libdir" \
    -Dbuildtype=release -Dstrip=true -Db_ndebug=true \
    -Dplatforms=android -Dplatform-sdk-version="$API" -Dandroid-stub=true -Dandroid-libbacktrace=disabled \
    -Degl=enabled -Dgles1=enabled -Dgles2=enabled -Dopengl=false -Dglx=disabled -Dgbm=disabled \
    -Degl-lib-suffix=_mesa -Dgles-lib-suffix=_mesa \
    -Dgallium-drivers=panfrost -Dvulkan-drivers= -Dllvm=disabled \
    -Dmesa-clc=system -Dprecomp-compiler=system -Dpanfrost-rust=false \
    -Dallow-fallback-for=libdrm -Dlibdrm:default_library=static -Dexpat:default_library=static \
    -Dvalgrind=disabled -Dlibunwind=disabled -Dlmsensors=disabled -Dperfetto=false \
    > "cfg-$arch.log" 2>&1
  nice -n 15 ninja -C "$bd" -j"$JOBS" > "build-$arch.log" 2>&1
  rm -rf "$dest"
  meson install -C "$bd" --no-rebuild --destdir "$dest" > "install-$arch.log" 2>&1
  publish "$arch" "$dest"
}

case ${1:-} in
  check-patches) prepare_camera_source ;;
  deps)   stage_deps ;;
  native) stage_deps; stage_native ;;
  ndk)    stage_ndk ;;
  build)  stage_deps; stage_native; stage_ndk; stage_build "${2:?arch: arm64 or arm}" ;;
  all)    stage_deps; stage_native; stage_ndk; stage_build arm64; stage_build arm ;;
  *)      echo "usage: $0 deps | native | ndk | build <arm64|arm> | all | check-patches" >&2; exit 2 ;;
esac
