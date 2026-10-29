#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Build the reviewed EROFS kernel with pinned Android toolchains; default plan."""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import subprocess


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--android-root', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True, help='Separate kernel output, outside the source checkout')
    ap.add_argument('--jobs', type=int, default=6)
    ap.add_argument('--execute', action='store_true')
    a = ap.parse_args()
    if not 1 <= a.jobs <= 16:
        raise ValueError('Use 1..16 jobs suitable for available RAM')
    root, out = a.android_root.resolve(strict=True), a.out.resolve()
    src = root / 'kernel/xiaomi/cannon'
    source = json.loads((Path(__file__).parent / 'source.json').read_text())
    tree = subprocess.check_output(['git', '-C', str(src), 'rev-parse', 'HEAD^{tree}'], text=True).strip()
    if tree != source['tree'] or subprocess.check_output(['git', '-C', str(src), 'status', '--porcelain']).strip():
        raise RuntimeError('Exact clean optional EROFS tree required')
    if out.is_relative_to(root):
        raise ValueError('Use an independent output directory outside the Android checkout')
    clang = root / 'prebuilts/clang/host/linux-x86/clang-r596125/bin'
    tools = root / 'prebuilts/kernel-build-tools/linux-x86'
    sysroot = root / 'prebuilts/gcc/linux-x86/host/x86_64-linux-glibc2.17-4.8/sysroot'
    for tool in [clang / 'clang', clang / 'ld.lld', Path('/usr/bin/aarch64-linux-gnu-gcc'), Path('/usr/bin/arm-linux-gnueabi-ld.bfd')]:
        if not tool.is_file():
            raise RuntimeError('Required real tool missing: ' + str(tool))
    env = dict(os.environ)
    env['PATH'] = str(clang) + ':' + str(root / 'prebuilts/build-tools/linux-x86/bin') + ':' + env['PATH']
    env['BISON_PKGDATADIR'] = str(root / 'prebuilts/build-tools/common/bison')
    flags = [f'O={out}', 'ARCH=arm64', 'CC=clang', 'LD=ld.lld', 'LLVM_IAS=1', 'LLVM=1',
             'CLANG_TRIPLE=aarch64-linux-gnu-', 'CROSS_COMPILE=/usr/bin/aarch64-linux-gnu-',
             'CROSS_COMPILE_ARM32=/usr/bin/arm-linux-gnueabi-', 'CROSS_COMPILE_COMPAT=/usr/bin/arm-linux-gnueabi-',
             'HOSTCC=clang', 'HOSTCXX=clang++', f'HOSTCFLAGS=--sysroot={sysroot} -I{tools}/include',
             f'HOSTLDFLAGS=--sysroot={sysroot} -Wl,-rpath,{tools}/lib64 -L {tools}/lib64 -fuse-ld=lld --rtlib=compiler-rt',
             f'LEX={root}/prebuilts/build-tools/linux-x86/bin/flex', f'YACC={root}/prebuilts/build-tools/linux-x86/bin/bison',
             f'M4={root}/prebuilts/build-tools/linux-x86/bin/m4', f'PAHOLE={tools}/bin/pahole']
    command = ['make', '-C', str(src), *flags, '-j' + str(a.jobs)]
    targets = ['olddefconfig' if (out / '.config').exists() else 'cannon_defconfig', 'Image.gz']
    print(json.dumps({'source_tree': tree, 'commands': [command + [target] for target in targets],
                      'execute': a.execute, 'phone_operations': []}, indent=2), flush=True)
    if not a.execute:
        return
    out.mkdir(parents=True, exist_ok=True)
    with (out / '.build.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        for target in targets:
            subprocess.run(command + [target], env=env, check=True)
        config = dict(line.split('=', 1) for line in (out / '.config').read_text().splitlines() if line.startswith('CONFIG_') and '=' in line)
        required = ['EROFS_FS', 'EROFS_FS_XATTR', 'EROFS_FS_POSIX_ACL', 'EROFS_FS_SECURITY', 'EROFS_FS_ZIP',
                    'CFI_CLANG', 'SHADOW_CALL_STACK', 'SECURITY_SELINUX', 'KFENCE', 'USERFAULTFD', 'RD_LZ4', 'NET_SCH_TBF',
                    'HID_PLAYSTATION', 'PLAYSTATION_FF', 'CC_IS_CLANG', 'AS_IS_LLVM', 'LD_IS_LLD']
        if any(config.get('CONFIG_' + key) != 'y' for key in required) or config.get('CONFIG_CFI_PERMISSIVE') == 'y':
            raise RuntimeError('Required filesystem/security/FCM configuration missing')
        image = out / 'arch/arm64/boot/Image.gz'
        result = {'status': 'COMPILED_RUNTIME_VALIDATION_REQUIRED', 'source_tree': tree,
                  'kernel': str(image), 'bytes': image.stat().st_size, 'sha256': hashlib.sha256(image.read_bytes()).hexdigest(),
                  'config_sha256': hashlib.sha256((out / '.config').read_bytes()).hexdigest(),
                  'clang': subprocess.check_output([str(clang / 'clang'), '--version'], text=True).splitlines()[0],
                  'linker': subprocess.check_output([str(clang / 'ld.lld'), '--version'], text=True).splitlines()[0]}
        (out / 'erofs-build.json').write_text(json.dumps(result, indent=2) + '\n')
        print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
