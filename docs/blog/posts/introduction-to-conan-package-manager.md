---
date: 2021-02-07
categories:
  - Tools
tags:
  - Conan
authors:
  - kuba
comments: true
---

# Introduction to Conan package manager

In the previous article of this series, I have listed several problems that we as developers have to deal with while
using dependencies to external code in our projects. These vary from version management, through cross-compilation
issues, up to the horror of integration with our build system. Linux users are used to the comfort of working with
package managers, which download and install applications and libraries in our host system with simple to use
command-line utilities. It would be very handy to have a tool, that does something similar for libraries in the C++
world. Among many previously mentioned package managers, one has stolen my heart and attention for good –
[Conan][conan].

<!-- more -->

???+ abstract "In this series"

    1. [Problems with external dependencies in C++][part1]
    2. **Introduction to Conan package manager**

!!! warning

    This article is about Conan v1, which is now deprecated.

## High level overview

Conan is a C/C++ package manager written in Python. This doesn’t just mean, that its binary is compiled from Python.
Conan is distributed as a Python package. Also, packages provided by this manager are defined in recipes in a form of
Python classes. This may sound like something not important, but using one of the most popular programming languages in
the world as a language for defining packages provides both tremendous flexibility as well as a very low entry-level for
new users or package creators. I have experienced this myself while I was creating recipes for packages that I was
missing in the existing Conan repository. I could totally focus on describing how to build a given library, rather than
fight with the vocabulary of application-specific config format. Nevertheless, Python is only required if you want to
create new packages. If you only want to download and use any of the existing packages, it can be done in several handy
and easy ways (including Python, if this is what you want).

In general, when we want to download any Conan package, we invoke the package manager with the name of the package.
Conan is first searching registered package repositories for the ones which provide given package name. We can register
multiple package repositories, which may be public or private. Also, we can use one of the existing repositories or we
can set up the whole infrastructure on our own private servers. Of course, that repository needs to support Conan
package protocol.

There are a few ways of installing Conan. The most recommended one is as a Python package. In order to do that, you need
to run the following command (assuming you have both `Python` and `pip` installed):

```bash
pip3 install conan
```

Once done, you will be able to search for packages with the following command:

```bash
conan search <package_name> -r=all
```

## Example: using `fmt` and `nlohmann_json`

In order to quickly present you the typical flow of using Conan, we will try to build a simple C++ app that uses fmt and
[nlohmann_json][json] aka `JSON for modern C++`. Both libraries are header only, but this is not the point right now.
Our current situation is that we don’t have it downloaded anywhere and we do not want to install it as a regular package
in our system. Let’s say, that the reason for that is that we want to use the latest possible version of both
dependencies and our distribution is missing “a few” releases.

In this example, we will try to compile the following file (`main.cpp`):

```cpp linenums="1"
#include <fmt/printf.h>
#include <nlohmann/json.hpp>

int main()
{
    nlohmann::json json = {
        {"pi", 3.14},
        {"happy", true},
        {"name", "Kuba"},
        {"nothing", nullptr},
        {"answer", {
            {"everything", 42}
        }},
        {"list", {1, 2, 3}},
        {"object", {
            {"currency", "PLN"},
            {"value", 100.0}
        }}
    };

    fmt::print("JSON: {}\n", json);
    return 0;
}
```

As we can see, we are first creating a JSON object with the help of `nlohmann_json` library and then we are printing it
with the `fmt` library. We need access to 2 header files of the mentioned libraries. In order to get it, we will create
a conan “requirements” file, which simply lists names of the required dependencies along with their versions and also
specifies how would we like to integrate it with our build system.

Here is the `conanfile.txt` file which is kept in the project root:

```toml linenums="1"
[requires]
nlohmann_json/3.9.1
fmt/7.1.3

[generators]
cmake
```

In the `[requires]` section we list our dependencies and in the `[generators]` section we specify to which build system
Conan should generate integration layer.

Since “our” preferred build system is CMake, then we will of course need simple configuration for that:

```cmake linenums="1"
cmake_minimum_required(VERSION 3.15)

project(conan_example CXX)

add_compile_options(-std=c++17)

include(${CMAKE_BINARY_DIR}/conanbuildinfo.cmake)
conan_basic_setup()

add_executable(conan_example
    main.cpp
)

target_link_libraries(conan_example
    PRIVATE
        ${CONAN_LIBS}
)
```

The final project structure is as follows:

```bash
conan_example/
 ├── build
 ├── CMakeLists.txt
 ├── conanfile.txt
 └── main.cpp
```

In order to build the project we need to perform the following steps:

1. install dependencies with Conan,
2. generate build system with CMake,
3. compile project with make (on Linux machine).

### 1. Installing dependencies with Conan

Installing dependencies using `conanfile.txt` method is very simple: execute `conan install <path>` from build
directory. `<path>` should point to the location of the `conanfile.txt` file (in our example it is in the project root
(one level up).

```bash linenums="1"
kuba@chimera:~/projects/conan_example/build$ conan install ..
Configuration:
[settings]
arch=x86_64
arch_build=x86_64
build_type=Release
compiler=gcc
compiler.libcxx=libstdc++11
compiler.version=10
os=Linux
os_build=Linux
[options]
[build_requires]
[env]
AR=gcc-ar-10
AS=gcc-10
CC=gcc-10
CXX=g++-10
LD=ld
OBJCOPY=objcopy
RANLIB=gcc-ranlib-10
SIZE=size
STRIP=strip
nlohmann_json/3.9.1: Not found in local cache, looking in remotes…
nlohmann_json/3.9.1: Trying with 'conan-center'…
Downloading conanmanifest.txt completed [0.10k]                                          
Downloading conanfile.py completed [2.43k]                                               
Downloading conan_export.tgz completed [0.24k]                                           
Decompressing conan_export.tgz completed [0.00k]                                         
nlohmann_json/3.9.1: Downloaded recipe revision 0
conanfile.txt: Installing package
Requirements
    fmt/7.1.3 from 'conan-center' - Cache
    nlohmann_json/3.9.1 from 'conan-center' - Downloaded
Packages
    fmt/7.1.3:b173bbda18164d49a449ffadc1c9e817f49e819d - Cache
    nlohmann_json/3.9.1:d1091b2ed420e6d287293709a907ae824d5de508 - Download
Installing (downloading, building) binaries…
nlohmann_json/3.9.1: Retrieving package d1091b2ed420e6d287293709a907ae824d5de508 from remote 'conan-center' 
Downloading conanmanifest.txt completed [0.17k]                                          
Downloading conaninfo.txt completed [0.38k]                                              
Downloading conan_package.tgz completed [143.93k]                                        
Decompressing conan_package.tgz completed [0.00k]                                        
nlohmann_json/3.9.1: Package installed d1091b2ed420e6d287293709a907ae824d5de508
nlohmann_json/3.9.1: Downloaded package revision 0
fmt/7.1.3: Already installed!
conanfile.txt: Generator cmake created conanbuildinfo.cmake
conanfile.txt: Generator txt created conanbuildinfo.txt
conanfile.txt: Generated conaninfo.txt
conanfile.txt: Generated graphinfo
```

Here we can see a few interesting things.

At the beginning (lines 2-23) Conan is showing the configuration that will be used to build a given set of dependencies.
Of course, in the case of header-only libraries, it doesn’t matter, but the same scheme will be used for any other
library. This configuration includes architecture and operating system for both host and target platform (should be the
same if not cross-compiling). We can also see environment variables and paths/names to the toolchain binaries. This
config dump is very helpful while debugging problems. In fact, this configuration is exactly what is specified by the
user in the Conan [profile](#profiles).

Later, Conan is installing dependencies one by one. First, it is trying to locate a given package in the local cache. In
case of the `nlohmann_json/3.9.1` library, I haven’t installed it before, so there was no such entry in the cache. In
such a situation, Conan is checking registered remotes one by one for the one which provides the given package. Here the
`conan-center` remote (the main and registered by default Conan remote) is the one that was selected. After that, the
package is downloaded and stored in the cache. By package I mean the meta data (recipe), like `conanfile.py` (line 27)
which is the main description of how to build a given library.

Just before executing the build, Conan is once again explicitly showing what packages were selected (along with their
unique ids) and where they were located – cache or remotes (lines 32-37). Finally, it starts building, which in case of
the header only libraries results in simply downloading and putting files into the proper cache location.

In the end, Conan is generating an integration layer for our build system, as it was specified in the `[generators]`
section of the `conanfile.txt` file. In our case, it is creating files that we will have to include in our
`CMakeLists.txt` in order for CMake to properly locate libraries installed into the Conan cache (lines 47-50). In
particular, the most important file for us will be the `conanbuildinfo.cmake` (see snippet with `CMakeLists.txt` lines
7-8).

### 2. Generating build system with CMake

Now is the time to launch CMake. We do this in a typical way – nothing fancy here.

```bash linenums="1"
kuba@chimera:~/projects/conan_example/build$ cmake ..
-- The CXX compiler identification is GNU 10.2.0
-- Detecting CXX compiler ABI info
-- Detecting CXX compiler ABI info - done
-- Check for working CXX compiler: /usr/bin/c++ - skipped
-- Detecting CXX compile features
-- Detecting CXX compile features - done
-- Conan: Adjusting output directories
-- Conan: Using cmake global configuration
-- Conan: Adjusting default RPATHs Conan policies
-- Conan: Adjusting language standard
-- Current conanbuildinfo.cmake directory: /home/kuba/projects/conan_example/build
-- Conan: Compiler GCC>=5, checking major version 10
-- Conan: Checking correct version: 10
-- Configuring done
-- Generating done
-- Build files have been written to: /home/kuba/projects/conan_example/build
```

Assuming that we correctly installed dependencies with Conan, included the `conanbuildinfo.cmake` file and called
`conan_basic_setup()` (defined in `conanbuildinfo.cmake`) there should be some confirmation logs about Conan in the
CMake output (lines 8-14).

Note, that the CMake generator creates a variable `CONAN_LIBS` which groups all the CMake targets that represent
installed dependencies. The only thing that we need to do is to use this helper variable in the
`target_link_libraries()` command (`CMakeLists.txt` – lines 14-16).

!!! note

    This example is extremely simple and definitely not sufficient for every use/project. Putting all dependencies into
    one variable (`CONAN_LIBS`) is something that I personally never used while working with Conan. There are other,
    more flexible ways of doing so, which will be discussed in the next articles.

### Compile project with make (on Linux machine)

Finally, we can build application with the native toolset:

```bash linenums="1"
kuba@chimera:~/projects/conan_example/build$ make
Scanning dependencies of target conan_example
[ 50%] Building CXX object CMakeFiles/conan_example.dir/main.cpp.o
[100%] Linking CXX executable bin/conan_example
[100%] Built target conan_example
```

The output of the program is like we expect:

```bash
JSON: {"answer":{"everything":42},"happy":true,"list":[1,2,3],"name":"Kuba","nothing":null,"object":{"currency":"PLN","value":100.0},"pi":3.14}
```

## Custom settings

Conan’s advantage over many existing package managers is that it allows us to customize many different settings that can
relate to tools we want to use, target platform or even from where packages should be searched and downloaded.
Everything that user can customize is cleanly organized in specific configuration files. They usually have easy to
understand text format (like JSON or INI-ish). You can edit it manually (if you know the syntax) or use Conan commands
to modify them for you. The latter option is quite handy if you need to adjust configs automatically in the Continous
Integration system.

There are two user-specific types of options that typically you want to adjust: profiles and remotes. Below you can find
more info about each of them.

### Profiles

Conan profiles are the heart of the user configuration for Conan. They specify many different variables, that Conan will
use during the building process:

- names/paths of the toolchain,
- metadata of the host and target platforms,
- environment variables,
- package-specific options (options that are provided by concrete package creator, e.g. “include tests” or “enable
  feature A”).

Many of the above options can be either set globally or for the given package (e.g. use higher optimization for `spdlog`
package).

This feature itself is very powerful, because you can create as many profiles as you want and give them some meaningful
name which will reflect the contents. For example, you can have a profile which allows compilation with GCC, clang, with
full debug mode, with high optimization, profile which is used to cross-compile for Raspberry Pi etc.

Even more possibilities are achievable by composing profiles together. So if you have a profile that only specifies
compiler (e.g. GCC or clang), a separate one which selects build mode (debug or release) and finally separate specific
for the operating system (e.g. Windows and Linux) then you can combine them together by simply listing their names in
the command line, for example:

```bash
conan install .. -pr gcc-10 -pr debug -pr linux
```

I personally define one profile per concrete toolchain (which includes target operating system). Here is my profile for
the GCC 10 compiler (named `gcc-10`):

```toml linenums="1"
[settings]
 os=Linux
 os_build=Linux
 arch=x86_64
 arch_build=x86_64
 compiler=gcc
 compiler.version=10
 compiler.libcxx=libstdc++11
 build_type=Release
 [options]
 [build_requires]
 [env]
 AR=gcc-ar-10
 AS=gcc-10
 CC=gcc-10
 CXX=g++-10
 OBJCOPY=objcopy
 RANLIB=gcc-ranlib-10
 SIZE=size
 STRIP=strip
 ```

As you can see above, in the `[settings]` section I am defining metadata for the platform (operating system,
architecture, build type and compiler type). In `[options]` and `[build_requires]` I do not specify anything
package-related, because this profile is generic – it only selects proper toolchain). In the `[env]` section I specify
well-known variables that are used by all popular build systems. This way, it doesn’t matter if the given package is
compiled using autotools or CMake – it simply uses given variables.

Below you can find a list of my personal profiles:

```bash
kuba@chimera:~$ conan profile list
 arm-linux-gnueabihf-clang-11
 arm-linux-gnueabihf-gcc-10
 arm-none-eabi-gcc-10
 clang-11
 default
 gcc-10
```

Each profile is kept as a separate file in `~/.conan/profiles/<profile_name>`. During the first usage Conan will detect
your current operating system setup and generate a `default` profile for you. `default` profile is used by default if
you do not specify any other in the command line (or in other way).

### Remotes

[Remotes][remotes] are another user-specific settings that you may want to modify. They are simply the names and URLs of
the Conan servers that are used to search for the packages. As it was shown with the `fmt` and `nlohmann_json` example,
every time a package is installed, Conan is searching registered remotes one by one and checking if any of them is
providing given package in a specified version.

By default, the only registered remote is the [conan-center][conanCenter], which is the main official Conan repository.
Every day Conan maintainers are adding there new packages and updating the existing ones.

However, you can register remotes owned by other people, organizations or even your company. It doesn’t matter if given
server is public or private. As long as you have access rights then you are good to go. So in other words, Conan is a
perfect choice for corporations, that need to keep their stuff private but still provide a central place for their
packages. I have registered my own repository to keep packages, that maybe are not generic enough to upload to the
official repository, but are very useful for me. I also use it as a testing ground for packages that may eventually land
in the `conan-center` once I test them enough.

Here is the list of remotes registered on my machine:

```bash
kuba@chimera:~$ conan remote list
 conan-center: https://conan.bintray.com [Verify SSL: True]
 bincrafters: https://api.bintray.com/conan/bincrafters/public-conan [Verify SSL: True]
 kubasejdak: https://api.bintray.com/conan/kubasejdak/public-conan [Verify SSL: True]
```

Conan servers are holding two types of data: package recipes (metadata) and prebuilt binaries. In a typical workflow,
Conan is first checking the local cache for the package and then the registered remotes. But not always downloading
package from a registry must result in compilation on the client machine. Sometimes package maintainers create prebuilt
binaries for the most popular configurations and upload them to the remotes. Conan is checking if the currently selected
profile (mentioned above) has a corresponding prebuilt package on the server. If yes, then it downloads the binary and
saves you time. However, you can force Conan to always compile dependencies on your machine.

## Installing packages

Conan packages can be installed in at least three different ways:

1. manually,
2. automatically with `conanfile.txt`,
3. automatically with CMake wrapper.

Each of them has its purpose, but usually you will use either `conanfile.txt` or CMake wrapper. This is because you
typically what to automate dependency installation while you are building your project. Let’s see a brief overview of
what you can do in each of these ways.

### Manual installation from command line

Manual package installation means that you explicitly [invoke Conan][conanInstall] to install explicitly defined set of
libraries in the command line. A simple example would be as follows:

```bash
conan install opencv/4.5.1@
```

Here we want to install `opencv` package in version `4.5.1`. We didn’t specify any profile so Conan will use the default
one. We also didn’t specify any generator, so no build system integration will be generated. This looks simple. It is an
easy way to experiment, check your own packages or test out different libraries.

That command can be extended to include package-specific settings, required profile or generator that we want to use:

```bash
conan install opencv/4.5.1@ -o opencv:with_png=False -o opencv:with_tiff=False -o opencv:with_gtk=False -pr gcc-10 -g cmake
```

That line can quickly expand if we compose multiple profiles, libraries and options. Not to mention, that you can
override specific settings from selected profiles. You will quickly realize, that this is not a way for production code.
However, if you are experimenting or looking for a proper library to include in your project then this is the quickest
way of getting started.

### Automatic installation with `conanfile.txt`

Conan is supporting the idea taken from Python package manager (`pip`), which allows putting all requirements and
options into a single file – the [conanfile.txt][conanfile]. The above example with `opencv` could look like this in
`conanfile.txt`:

```toml linenums="1"
[requires]
opencv/4.5.1

[generators]
cmake

[options]
opencv:with_png=False
opencv:with_tiff=False
opencv:with_gtk=False
```

Here we have a bit more readable format than in the command line, because of the separate sections for each setting.
However, the biggest advantage of this, is that you can put all these configurations in a file and have it under the
control of the VCS. This way you will always have the correct set of dependencies for the currently checked-out code.

You can also have a set of files that contain different libraries. This way, by feeding Conan with a different path to
the `conanfile.txt` you can install another set of packages. It may be helpful if you build many applications from the
same codebase. Usually, each application has its own set of dependencies.

### Automatic installation with CMake wrapper

The canonical (recommended) way of using Conan is via the `conanfile.txt` configuration. This is fine as long as your
dependencies are not dynamically changing. It can happen if you have, for example, a library that can be built in
different configurations. And each config may require a separate set of dependencies. Let’s look at this simple example:

```bash
mylib/
 ├── CMakeLists.txt
 ├── module_a
 │   └── NetworkBackend.cpp # requires "libcurl" library
 └── module_b
     └── DatabaseBackend.cpp # requires "sqlite3" library
```

Here we have a directory structure for the `mylib` library which consists of two submodules: `module_a` and `module_b`.
The first one is related to some network stuff so it needs `libcurl` in its implementation. The second one operates on a
local database and requires `sqlite3` library. User application, which links with `mylib`, can either compile it with
`module_a`, or `module_b` or both. How can we instruct Conan to actually co-operate with CMake and install only was is
needed in the given setup?

If this example is still not convincing, then imagine that there are hundreds of such modules that internally can also
be built from different parts depending on other settings. Also, we may have some parts of code in our library which are
platform-specific and require libraries only for that platform. We do not want to be caught in a situation, where Conan
is trying to install Linux libraries on Windows.

At the top of it, the application (which is only using the `mylib` library) can have its own dependencies. So we have a
lot of potential sources of libraries to be installed. And the final set of packages depends on the build system. If you
remember the first example with `fmt` and `nlohmann_json`, you know that the order of steps is as follows:

1. install dependencies,
2. launch CMake,
3. compile.

In our situation, CMake has to be launched first. But even that is not enough, because CMake may want to verify that
libraries that we want to use are actually available. So Conan needs to install the libraries before CMake is finished.
Impossible to solve? No, there is a handy solution – [cmake-conan][cmakeConan] wrapper.

This script is a CMake file containing helper functions to actually execute Conan from CMake. This way, you can collect
dependencies in a list as CMake parses your project. Then, in the end you can call Conan from the build system and
install all libraries at once. Alternatively, you can install ad-hoc dependencies in the `CMakeLists.txt` file, which
actually needs it. The second approach is much better because you can both guarantee that you install only what is
actually used and you can use well-known CMake mechanisms (like `find_library`) that require the library to be installed
apriori.

Here is a very simple example of how `cmake-conan` wrapper can be used:

```cmake linenums="1"
include(conan.cmake) # This it the actual cmake-conan wrapper file.

conan_cmake_run(
    REQUIRES opencv/5.4.1
    OPTIONS opencv:with_png=False opencv:with_tiff=False opencv:with_gtk=False
)
```

`conan_cmake_run()` is actually calling Conan command and waiting for the result. Since you can use CMake variables in
that call, this mechanism povides tremendous flexibility in defining which packages should be installed.

!!! success "Note"

    I am personally using yet another approach, based on the CMake wrapper. Details will be explained in the next
        article in the series.

## Conan cache

As I mentioned before, Conan creates a local cache for all downloaded and built packages for future reusing. Typically,
it is located in `$HOME/.conan/data` directory. Below you can see sample cache state from my computer:

```bash
kuba@chimera:~$ tree .conan/data/ -L 5 -d
 .conan/data/
 ├── catch2
 │   ├── 2.13.2
 │   │   └── _
 │   │       └── _
 │   │           ├── export
 │   │           └── package
 │   └── 2.13.3
 │       └── _
 │           └── _
 │               ├── dl
 │               ├── export
 │               ├── locks
 │               └── package
 ├── fmt
 │   └── 7.1.3
 │       └── _
 │           └── _
 │               ├── dl
 │               ├── export
 │               ├── locks
 │               └── package
 ├── grpc
 │   └── 1.24.3
 │       └── kubasejdak
 │           └── stable
 │               ├── build
 │               ├── export
 │               ├── export_source
 │               ├── locks
 │               ├── package
 │               └── source
 ├── libgpiod
 │   └── 1.4.3
 │       └── kubasejdak
 │           └── stable
 │               ├── build
 │               ├── export
 │               ├── export_source
 │               ├── locks
 │               ├── package
 │               └── source
 └── nlohmann_json
     └── 3.9.1
         └── _
             └── _
                 ├── dl
                 ├── export
                 ├── locks
                 └── package
```

Each installed package in each version has its own subdirectory there. Conan is first checking if the given dependency
is already in the cache, before downloading the recipe. Knowledge about the cache and its structure is very helpful when
you are creating your own packages.

## Summary

Conan is a powerful package manager for C and C++. It’s true, that at first many things may seem complicated or
overwhelming. But this is the cost of introducing something new. I can only say, that in time using this tool will
become very easy and you will be quickly tempted to add new packages yourself, once you find any which is not already
provided by the official repository.

In the next article I will focus more on cross-compilation and I will show how I use Conan in my CMake projects. For
that, I am using a little modified version of the `cmake-conan` wrapper. Stay tuned!

<!-- links -->

[part1]: problems-with-external-dependencies-in-cpp.md
[conan]: https://conan.io/
[json]: https://github.com/nlohmann/json
[profiles]: https://docs.conan.io/1/reference/profiles.html
[remotes]: https://docs.conan.io/1/uploading_packages/remotes.html
[conanCenter]: https://conan.io/center/
[conanInstall]: https://docs.conan.io/1/reference/commands/consumer/install.html
[conanfile]: https://docs.conan.io/1/reference/conanfile_txt.html
[cmakeConan]: https://github.com/conan-io/cmake-conan
