#
# spec file for package cargo-auditable
#
# Copyright (c) 2022 SUSE LINUX GmbH, Nuernberg, Germany.
#
# All modifications and additions to the file contributed by third parties
# remain the property of their copyright owners, unless otherwise agreed
# upon. The license for this file, and modifications and additions to the
# file, is the same license as for the pristine package itself (unless the
# license for the pristine package is not an Open Source License, in which
# case the license is the MIT License). An "Open Source License" is a
# license that conforms to the Open Source Definition (Version 1.9)
# published by the Open Source Initiative.

# Please submit bugfixes or comments via http://bugs.opensuse.org/
#
%define _smp_mflags -j1
%define __rustflags -Clink-arg=-Wl,-z,relro,-z,now -C debuginfo=2 -C incremental=false
%define __cargo CARGO_FEATURE_VENDORED=1 RUSTFLAGS="%{__rustflags}" %{_bindir}/cargo
%define __cargo_common_opts %{?_smp_mflags}

Name:           cargo-auditable
Version:        0.5.2~0
Release:        0
Summary:        A tool to embed auditing information in ELF sections of rust binaries
#               If you know the license, put it's SPDX string here.
#               Alternately, you can use cargo lock2rpmprovides to help generate this.
License:        ( (MIT OR Apache-2.0) AND Unicode-DFS-2016 ) AND ( 0BSD OR MIT OR Apache-2.0 ) AND ( Apache-2.0 OR BSL-1.0 ) AND ( Apache-2.0 OR MIT ) AND ( Apache-2.0 WITH LLVM-exception OR Apache-2.0 OR MIT ) AND ( MIT OR Apache-2.0 OR Zlib ) AND ( MIT OR Zlib OR Apache-2.0 ) AND ( Unlicense OR MIT ) AND ( Zlib OR Apache-2.0 OR MIT ) AND MIT
#               Select a group from this link:
#               https://en.opensuse.org/openSUSE:Package_group_guidelines
Group:          Development/Languages/Rust
Url:            https://github.com/rust-secure-code/cargo-auditable
Source0:        %{name}-%{version}.tar.gz
Source1:        vendor.tar.gz
Source2:        cargo_config
# We can't dep on cargo-packaging because we would create a dependency loop.
# BuildRequires:  cargo-packaging
BuildRequires:  cargo
#BuildRequires:  zstd
Requires:       cargo

%description
Know the exact crate versions used to build your Rust executable. Audit binaries for known bugs or
security vulnerabilities in production, at scale, with zero bookkeeping. This works by embedding
data about the dependency tree in JSON format into a dedicated linker section of the compiled
executable.

%define BUILD_DIR "$PWD"/target

%prep
%setup -a1 -n %{name}-%{version}/upstream
mkdir -p .cargo
cp %{SOURCE2} .cargo/config
tar -xzf %{SOURCE1}


%ifarch %arm32
%define SB2_TARGET armv7-unknown-linux-gnueabihf
%endif
%ifarch %arm64
%define SB2_TARGET aarch64-unknown-linux-gnu
%endif
%ifarch %ix86
%define SB2_TARGET i686-unknown-linux-gnu
%endif

%build
# Adopted from https://github.com/sailfishos/gecko-dev/blob/master/rpm/xulrunner-qt5.spec

export CARGO_HOME="%{BUILD_DIR}/cargo"
export CARGO_BUILD_TARGET=%SB2_TARGET

# When cross-compiling under SB2 rust needs to know what arch to emit
# when nothing is specified on the command line. That usually defaults
# to "whatever rust was built as" but in SB2 rust is accelerated and
# would produce x86 so this is how it knows differently. Not needed
# for native x86 builds
export SB2_RUST_TARGET_TRIPLE=%SB2_TARGET
export RUST_HOST_TARGET=%SB2_TARGET

export RUST_TARGET=%SB2_TARGET
export TARGET=%SB2_TARGET
export HOST=%SB2_TARGET
export SB2_TARGET=%SB2_TARGET

%ifarch %arm32 %arm64
export CROSS_COMPILE=%SB2_TARGET

# This avoids a malloc hang in sb2 gated calls to execvp/dup2/chdir
# during fork/exec. It has no effect outside sb2 so doesn't hurt
# native builds.
export SB2_RUST_EXECVP_SHIM="/usr/bin/env LD_PRELOAD=/usr/lib/libsb2/libsb2.so.1 /usr/bin/env"
export SB2_RUST_USE_REAL_EXECVP=Yes
export SB2_RUST_USE_REAL_FN=Yes
export SB2_RUST_NO_SPAWNVP=Yes
%endif

export CC=gcc
export CXX=g++
export AR="ar"
export NM="gcc-nm"
export RANLIB="gcc-ranlib"
export PKG_CONFIG="pkg-config"

unset LIBSSH2_SYS_USE_PKG_CONFIG
%{__cargo} build \
    %{__cargo_common_opts} \
    --offline --release

%install
install -D -d -m 0755 %{buildroot}%{_bindir}
install -m 0755 %{BUILD_DIR}/%{SB2_TARGET}/release/cargo-auditable %{buildroot}%{_bindir}/cargo-auditable

%files
%{_bindir}/cargo-auditable

%changelog
