#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-2.0-only
set -euo pipefail

root=$(pwd -P)
here=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
kernel="$root/kernel/xiaomi/cannon"
out=${1:?Usage: bash build-kernel.sh ABSOLUTE_NEW_OUTPUT_DIRECTORY}
[[ "$out" == /* && -d "$kernel" && ! -e "$out" ]]
dtc=${DTC_EXT:-"$root/out/host/linux-x86/bin/dtc"}
if [[ ! -x "$dtc" ]]; then
    echo "Build the Android host dtc first (m dtc), or set DTC_EXT explicitly." >&2
    exit 1
fi
dtc=$(realpath -- "$dtc")

clang="$root/prebuilts/clang/host/linux-x86/clang-r596125"
kbt="$root/prebuilts/kernel-build-tools/linux-x86"
tools="$root/prebuilts/build-tools/linux-x86"
export PATH="$clang/bin:$root/prebuilts/tools-lineage/linux-x86/bin:$tools:$root/prebuilts/rust-toolchain/linux-x86/1.93.1/bin:$root/prebuilts/clang-tools/linux-x86/bin:/usr/local/bin:/usr/bin:/bin"
export LD_LIBRARY_PATH="$clang/lib64${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
export HIP_PATH=none
export PERL5LIB="$root/prebuilts/tools-lineage/common/perl-base"
export BISON_PKGDATADIR="$root/prebuilts/build-tools/common/bison"
mkdir -- "$out"
cp -- "$here/kernel.config" "$out/.config"
mk() {
    "$tools/make" -j4 \
        HOSTCFLAGS=" -I$kbt/include" \
        HOSTLDFLAGS=" -Wl,-rpath,$kbt/lib64 -L $kbt/lib64 -fuse-ld=lld --rtlib=compiler-rt" \
        LLVM=1 LLVM_IAS=1 LZ4="$kbt/bin/lz4" \
        LEX="$tools/flex" YACC="$tools/bison" M4="$tools/m4" \
        PAHOLE="$kbt/bin/pahole" \
        LIBCLANG_PATH="$root/prebuilts/clang/host/linux-x86/clang-r584948b/lib" \
        CLANG_AUTOFDO_PROFILE="$kernel/gki/aarch64/afdo/kernel.afdo" \
        DTC_EXT="$dtc" -C "$kernel" O="$out" ARCH=arm64 \
        CLANG_TRIPLE=aarch64-linux-gnu- CC=clang LD=ld.lld "$@"
}
mk olddefconfig
if ! cmp -s -- "$here/kernel.config" "$out/.config"; then
    echo "Regenerated configuration differs; review the toolchain/configuration." >&2
    exit 1
fi
mk Image.gz mediatek/mt6853-cannong.dtb
