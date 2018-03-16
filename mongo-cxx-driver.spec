# aptech spec file for mongo-cxx-driver
#
# Copyright (c) 2018 William N. Braswell, Jr.
# License: CC-BY-SA
# http://creativecommons.org/licenses/by-sa/4.0/
#
# Please, preserve the changelog entries
#
%global gh_owner     mongodb
%global gh_project   mongo-cxx-driver
%global libname      libmongocxx
%global libver       3.2.0
%global bsonver      1.9

%ifarch x86_64
%global with_tests   0%{!?_without_tests:1}
%else
# See https://jira.mongodb.org/browse/CDRIVER-1186
# 32-bit MongoDB support was officially deprecated
# in MongoDB 3.2, and support is being removed in 3.4.
%global with_tests   0%{?_with_tests:1}
%endif

Name:      mongo-cxx-driver
Summary:   Client library written in C++ for MongoDB
Version:   3.2.0
Release:   1%{?dist}
License:   Apache License 2.0
Group:     System Environment/Libraries
URL:       https://github.com/%{gh_owner}/%{gh_project}

Source0:   https://github.com/%{gh_owner}/%{gh_project}/releases/download/%{version}%{?prever:-%{prever}}/%{gh_project}-%{version}%{?prever:-%{prever}}.tar.gz

BuildRequires: autoconf
BuildRequires: automake
BuildRequires: gcc
BuildRequires: libtool
# pkg-config may pull compat-openssl10
BuildRequires: openssl-devel
BuildRequires: pkgconfig(libbson-1.0) > %{bsonver}
BuildRequires: pkgconfig(libsasl2)
BuildRequires: pkgconfig(zlib)
%if 0%{?fedora} >= 26
# pkgconfig file introduce in 1.1.4
BuildRequires: pkgconfig(snappy)
%else
BuildRequires: snappy-devel
%endif
%if %{with_tests}
# WBRASWELL 20180315 2018.074: replace mongodb-server with mongodb-org-server
#BuildRequires: mongodb-server
BuildRequires: mongodb-org-server
BuildRequires: openssl
%endif
BuildRequires: perl-interpreter
# From man pages
BuildRequires: python
BuildRequires: /usr/bin/sphinx-build

BuildRequires: mongo-c-driver

Requires:   %{name}-libs%{?_isa} = %{version}-%{release}
# Sub package removed
#Obsoletes:  %{name}-tools         < 1.3.0
#Provides:   %{name}-tools         = %{version}
#Provides:   %{name}-tools%{?_isa} = %{version}


%description
%{name} is a client library written in C++ for MongoDB.


%package libs
Summary:    Shared libraries for %{name}
Group:      Development/Libraries

%description libs
This package contains the shared libraries for %{name}.


%package devel
Summary:    Header files and development libraries for %{name}
Group:      Development/Libraries
Requires:   %{name}%{?_isa} = %{version}-%{release}
Requires:   pkgconfig

%description devel
This package contains the header files and development libraries
for %{name}.

Documentation: http://api.mongodb.org/c/%{version}/


%prep
%setup -q -n %{gh_project}-%{version}%{?prever:-dev}

%build

cd build

cmake3 -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX=/usr/lib64 ..

: Build MNMLSTC Polyfill... Then INSTALL SYSTEM-WIDE!!!
make %{?_smp_mflags} EP_mnmlstc_core

: Build MongoDB C++ Driver
make %{?_smp_mflags}


# Explicit man target is needed for generating manual pages
# WBRASWELL 20180315 2018.074: NEED FIX, comment out man3 make targer, due to malformed sphinx commands
#make %{?_smp_mflags} doc/man V=1


%install

cd build

: Install MongoDB C++ Driver
make install DESTDIR=%{buildroot}

: Create pkg-config Symlinks
ln -sf %{_libdir}/lib/pkgconfig/%{libname}.pc /usr/share/pkgconfig/%{libname}.pc
ln -sf %{_libdir}/lib/pkgconfig/libbsoncxx.pc /usr/share/pkgconfig/libbsoncxx.pc

#rm %{buildroot}%{_libdir}/*la

#: install examples
#for i in examples/*/*.cpp; do
#  install -Dpm 644 $i %{buildroot}%{_datadir}/doc/%{name}/$i
#done

#: Rename documentation to match subpackage name
#mv %{buildroot}%{_datadir}/doc/%{name} \
#   %{buildroot}%{_datadir}/doc/%{name}-devel


%check
%if %{with_tests}
: Save Test Program

printf "#include <iostream>\n#include <bsoncxx/builder/stream/document.hpp>\n#include <bsoncxx/json.hpp>\n#include <mongocxx/client.hpp>\n#include <mongocxx/instance.hpp>\nint main(int, char**) {\n    mongocxx::instance inst{};\n    mongocxx::client conn{mongocxx::uri{}};\n    bsoncxx::builder::stream::document document{};\n    auto collection = conn[\"testdb\"][\"testcollection\"];\n    document << \"hello\" << \"world\";\n    collection.insert_one(document.view());\n    auto cursor = collection.find({});\n    for (auto&& doc : cursor) {\n        std::cout << bsoncxx::to_json(doc) << std::endl;\n    }\n}" > ./mongocxx_test.cpp

: Compile Test Program

#export PKG_CONFIG_PATH=%{buildroot}/usr/lib64/lib/pkgconfig/
#c++ --std=c++11 mongocxx_test.cpp -o mongocxx_test $(pkg-config --cflags --libs libmongocxx)

c++ --std=c++11 mongocxx_test.cpp -o mongocxx_test -I%{buildroot}/usr/lib64/include/mongocxx/v_noabi -I/usr/lib64/include/bsoncxx/v_noabi/ -I%{buildroot}/usr/lib64/include/bsoncxx/v_noabi -L%{buildroot}/usr/lib64/lib -Wl,-rpath,%{buildroot}/usr/lib64/lib -lmongocxx -lbsoncxx

: Run Test Program
./mongocxx_test

: Cleanup
rm -Rf ./mongocxx_test*

exit $ret
%endif


%post   libs -p /sbin/ldconfig
%postun libs -p /sbin/ldconfig

%files
#%{_bindir}/*

%files libs
#%{!?_licensedir:%global license %%doc}
#%license COPYING
#%license THIRD_PARTY_NOTICES
%{_libdir}/lib/%{libname}.so.*
%{_libdir}/lib/libbsoncxx.so.*

%files devel
#%{_docdir}/%{name}-devel
%{_libdir}/include/bsoncxx
%{_libdir}/include/mongocxx
%{_libdir}/lib/%{libname}.so
%{_libdir}/lib/libbsoncxx.so
%{_libdir}/lib/pkgconfig/%{libname}.pc
%{_libdir}/lib/pkgconfig/libbsoncxx.pc
#/usr/share/pkgconfig/%{libname}.pc
#/usr/share/pkgconfig/libbsoncxx.pc
%{_libdir}/lib/cmake/%{libname}-*
%{_libdir}/lib/cmake/libbsoncxx-*
#%{_mandir}/man3/mongoc*  # WBRASWELL 20180315 2018.074: NEED FIX, comment out man3 directory, due to malformed sphinx commands

%changelog
* Thu Mar 15 2018 Will Braswell <william.braswell@NOSPAM.autoparallel.com> - 3.2.0-1
- Initial package
