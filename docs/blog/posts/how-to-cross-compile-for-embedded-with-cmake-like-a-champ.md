---
date: 2020-10-15
categories:
  - Tools
tags:
  - CMake
authors:
  - kuba
comments: true
---

# How to cross-compile for embedded with CMake like a champ

The power of CMake lies in the fact, that it is both cross-platform in terms of build host and allows cross-compilation
for different targets at the same time. In other words, we can build projects from any platform to any platform as long
as we have proper tools (usually called toolchains). However many people don’t know about this and try to come up with a
sophisticated handmade solution or put complex logic into `CMakeLists.txt` files in order to setup the environment.
Today I’m going to show you how to enable cross-compilation for your project with CMake, basing on the embedded platform
case.

<!-- more -->

!!! note

    Here I use an embedded system example, but the described mechanisms will work for any other platform.

!!! success "Update"

    Examples updated to reflect state in January 2025.

## How CMake manages compiler

Before we can switch to cross-compilation, it is crucial to understand how CMake handles compiler detection, how we can
extract information about current toolchain and what is the target platform.

If you run CMake in the console (or in IDE which shows CMake output) you can usually see, that in the beginning there
are some log messages reporting what is the detected compiler. Below you can find sample output from one of my projects:

```cmake linenums="1"
-- The ASM compiler identification is GNU
-- Found assembler: /opt/toolchains/arm-gnu-toolchain-13.3.rel1-x86_64-arm-none-eabi/bin/arm-none-eabi-gcc
-- The C compiler identification is GNU 13.3.1
-- The CXX compiler identification is GNU 13.3.1
-- Detecting C compiler ABI info
-- Detecting C compiler ABI info - done
-- Check for working C compiler: /opt/toolchains/arm-gnu-toolchain-13.3.rel1-x86_64-arm-none-eabi/bin/arm-none-eabi-gcc - skipped
-- Detecting C compile features
-- Detecting C compile features - done
-- Detecting CXX compiler ABI info
-- Detecting CXX compiler ABI info - done
-- Check for working CXX compiler: /opt/toolchains/arm-gnu-toolchain-13.3.rel1-x86_64-arm-none-eabi/bin/arm-none-eabi-g++ - skipped
-- Detecting CXX compile features
-- Detecting CXX compile features - done
```

Here you can see, that I’m using `arm-none-linux-gnueabihf-gcc` `13.3.1` C compiler and `arm-none-linux-gnueabihf-g++`
`13.3.1` C++ compiler. But how does CMake know which compiler to use? After all, you can have multiple toolchains
installed in your system. The answer is simple: it checks the `CC` and `CXX` environment variables. They define what is
the default compiler in the system. If you manually set `CC` or `CXX` to different values, then CMake will use these new
settings as default compilers. Of course, you may try to set it to something completely rubbish, but CMake will usually
verify if the given compiler is usable. After successful detection, CMake stores info about the current toolchain in the
following variables:

- `CMAKE_C_COMPILER`,
- `CMAKE_CXX_COMPILER`.

They contain paths to the C and C++ compilers respectively. This is usually enough on desktop platforms. In the case of
the embedded systems, we often need also custom linker and assembler. In the more complex projects you may need to
additionally specify binaries to other parts of the toolchain (`size`, `ranlib`, `objcopy`...). All these tools should
be set in the corresponding variables:

- `CMAKE_AR`,
- `CMAKE_ASM_COMPILER`,
- `CMAKE_LINKER`,
- `CMAKE_OBJCOPY`,
- `CMAKE_RANLIB`.

As for the host and target operating systems, CMake stores their names in the following variables:

- [CMAKE_HOST_SYSTEM_NAME][cmakeHostSystemName] – name of the platform, on which CMake is running (host platform). On
major operating systems this is set to the `Linux`, `Windows` or `Darwin` (MacOS) value.
- [CMAKE_SYSTEM_NAME][cmakeSystemName] – name of the platform, for which we are building (target platform). By default,
this value is the same as `CMAKE_HOST_SYSTEM_NAME`, which means that we are building for local platform (no
cross-compilation).

## Setting custom toolchain

When we cross-compile to another platform, we have to specify completely different toolchain both in terms of name and
location of the binaries.

!!! info

    Toolchain name usually contains the so-called target triple, which is in the form of `<arch>-<system>-<abi> `or in a
    longer form `<arch>-<vendor>-<system>-<abi>`, e.g. `arm-linux-gnueabihf`. Typically, local toolchains have symbolic
    links that omit triple in binary name: we use `gcc` instead of the full name `x86_64-linux-gnu-gcc`.

This can be done in two ways:

1. pass values for the toolchain variables from the command line,
2. specify toolchain file.

First option is very explicit thus easy to understand, but big number of arguments makes it harder to use CMake in
terminal:

```bash
cmake .. -DCMAKE_C_COMPILER=<path_to_c_compiler> -DCMAKE_CXX_COMPILER=<path_to_cxx_compiler> -DCMAKE_AR=<path_to_ar> -DCMAKE_LINKER=<path_to_linker> etc...
```

In such a case you would probably want to put it into some kind of script.

Second option is more elegant and is the preferred way of choosing the toolchain. All you need to do is to put toolchain
variables into a separate file (e.g. `<toolchain_name>.cmake`) and set `CMAKE_TOOLCHAIN_FILE` variable to the path of
that file. This can be done both in the command line or in `CMakeLists.txt` before `project()` command:

```bash
cmake .. -DCMAKE_TOOLCHAIN_FILE=<path_to_toolchain_file>
```

or:

```cmake linenums="1"
cmake_minimum_required(VERSION 3.15)

set(CMAKE_TOOLCHAIN_FILE <path_to_toolchain_file>)

project(<project_name> C CXX)
```

In both cases, CMake will not try to detect default system toolchain but will blindly use whatever you provide.

!!! warning "Important"

    It is crucial to set the value of `CMAKE_TOOLCHAIN_FILE` before `project()` is invoked, because `project()` triggers
    toolchain detection and verification.

## Structure of the toolchain file

In fact, toolchain file doesn’t have any structure. You can put anything you want there. But the best practice is to
define at least these settings:

- path to the toolchain binaries (C compiler, C++ compiler, linker, etc.):

```cmake linenums="1"
set(CMAKE_AR                    <path_to_ar>)
set(CMAKE_ASM_COMPILER          <path_to_assembler>)
set(CMAKE_C_COMPILER            <path_to_c_compiler)
set(CMAKE_CXX_COMPILER          <path_to_cpp_compiler)
set(CMAKE_LINKER                <path_to_linker>)
set(CMAKE_OBJCOPY               <path_to_objcopy>)
set(CMAKE_RANLIB                <path_to_ranlib>)
set(CMAKE_SIZE                  <path_to_size>)
set(CMAKE_STRIP                 <path_to_strip>)
```

- name of the target platform (and optionally target processor architecture):

```cmake linenums="1"
set(CMAKE_SYSTEM_NAME           <target_system>)
set(CMAKE_SYSTEM_PROCESSOR      <target_architecture>)
```

- required compilation and linking flags on that particular platform:

```cmake linenums="1"
set(CMAKE_C_FLAGS               <c_flags>)
set(CMAKE_CXX_FLAGS             <cpp_flags>)
set(CMAKE_C_FLAGS_DEBUG         <c_flags_for_debug>)
set(CMAKE_C_FLAGS_RELEASE       <c_flags_for_release>)
set(CMAKE_CXX_FLAGS_DEBUG       <cpp_flags_for_debug>)
set(CMAKE_CXX_FLAGS_RELEASE     <cpp_flags_for_release>)
set(CMAKE_EXE_LINKER_FLAGS      <linker_flags>)
```

- toolchain sysroot settings:

```cmake linenums="1"
set(CMAKE_FIND_ROOT_PATH_MODE_PROGRAM     NEVER)
set(CMAKE_FIND_ROOT_PATH_MODE_LIBRARY     ONLY)
set(CMAKE_FIND_ROOT_PATH_MODE_INCLUDE     ONLY)

# Optionally reduce compiler sanity check when cross-compiling.
set(CMAKE_TRY_COMPILE_TARGET_TYPE         STATIC_LIBRARY)
```

Note, that in case of compilation flags I said “required”. By this I mean flags that wouldn’t make sense for any other
platform or any other toolchain (e.g. `-mcpu=cortex-m4 -mfloat-abi=hard`). This way your toolchain file will be very
generic and you will be able to reuse it in different projects and different applications built from the same codebase.

!!! info

    `CMAKE_CXX_FLAGS_DEBUG` and `CMAKE_CXX_FLAGS_RELEASE` have default values (e.g. `-O0 -g`). If you set new values
    (instead of appending them) remember, that you will lose optimization settings and debug symbols.

Setting target platform name and architecture is less important, because it has minimal impact on CMake itself.
Sometimes 3rd party modules depend on them, so it won’t hurt if you set it correctly.

One important thing to remember: if you set `CMAKE_SYSTEM_NAME` manually, CMake will automatically set
`CMAKE_CROSSCOMPILING` to `TRUE` (regardless of the value you set). For example, if you compile from Windows to Windows
and call `set(CMAKE_SYSTEM_NAME Windows)` before `project()`, then `CMAKE_CROSSCOMPILING` will still be `TRUE`.

[CMAKE_FIND_ROOT_PATH_MODE_PROGRAM][cmakeFindRootPathModeProgram],
[CMAKE_FIND_ROOT_PATH_MODE_LIBRARY][cmakeFindRootPathModeLibrary] and
[CMAKE_FIND_ROOT_PATH_MODE_INCLUDE][cmakeFindRootPathModeInclude] are all related to the paths that should be searched
for external packages, libraries and headers. When we are recompiling, it is crucial to tell CMake, to look for all
“standard” components in paths related to the current toolchain.

## Ready to use toolchain file

If you find all the above recommendations and rules still complicated, don’t worry. Here is a complete toolchain file
for the embedded baremetal platform. All you need to do is to provide value for the `BAREMETAL_ARM_TOOLCHAIN_PATH`
variable, pointing to the location of your toolchain (in my case it is
`/opt/toolchains/arm-gnu-toolchain-13.3.rel1-x86_64-arm-none-eabi/bin/`).

```cmake linenums="1"
set(CMAKE_SYSTEM_NAME               Generic)
set(CMAKE_SYSTEM_PROCESSOR          arm)

# Without that flag CMake is not able to pass test compilation check
set(CMAKE_TRY_COMPILE_TARGET_TYPE   STATIC_LIBRARY)

set(CMAKE_AR                        ${BAREMETAL_ARM_TOOLCHAIN_PATH}/bin/arm-none-eabi-ar)
set(CMAKE_ASM_COMPILER              ${BAREMETAL_ARM_TOOLCHAIN_PATH}/bin/arm-none-eabi-gcc)
set(CMAKE_C_COMPILER                ${BAREMETAL_ARM_TOOLCHAIN_PATH}/bin/arm-none-eabi-gcc)
set(CMAKE_CXX_COMPILER              ${BAREMETAL_ARM_TOOLCHAIN_PATH}/bin/arm-none-eabi-g++)
set(CMAKE_LINKER                    ${BAREMETAL_ARM_TOOLCHAIN_PATH}/bin/arm-none-eabi-ld)
set(CMAKE_OBJCOPY                   ${BAREMETAL_ARM_TOOLCHAIN_PATH}/bin/arm-none-eabi-objcopy CACHE INTERNAL "")
set(CMAKE_RANLIB                    ${BAREMETAL_ARM_TOOLCHAIN_PATH}/bin/arm-none-eabi-ranlib CACHE INTERNAL "")
set(CMAKE_SIZE                      ${BAREMETAL_ARM_TOOLCHAIN_PATH}/bin/arm-none-eabi-size CACHE INTERNAL "")
set(CMAKE_STRIP                     ${BAREMETAL_ARM_TOOLCHAIN_PATH}/bin/arm-none-eabi-strip CACHE INTERNAL "")
set(CMAKE_GCOV                      ${BAREMETAL_ARM_TOOLCHAIN_PATH}/bin/arm-none-eabi-gcov CACHE INTERNAL "")

set(COMMON_FLAGS                    "-Wno-psabi --specs=nosys.specs -fdata-sections -ffunction-sections -Wl,--gc-sections")
set(CMAKE_C_FLAGS                   "${COMMON_FLAGS} ${APP_C_FLAGS} " CACHE INTERNAL "")
set(CMAKE_CXX_FLAGS                 "${COMMON_FLAGS} -fno-exceptions ${APP_CXX_FLAGS}" CACHE INTERNAL "")

set(CMAKE_C_FLAGS_DEBUG             "-Os -g" CACHE INTERNAL "")
set(CMAKE_C_FLAGS_RELEASE           "-Os -DNDEBUG" CACHE INTERNAL "")
set(CMAKE_CXX_FLAGS_DEBUG           "${CMAKE_C_FLAGS_DEBUG}" CACHE INTERNAL "")
set(CMAKE_CXX_FLAGS_RELEASE         "${CMAKE_C_FLAGS_RELEASE}" CACHE INTERNAL "")

set(CMAKE_FIND_ROOT_PATH_MODE_PROGRAM NEVER)
set(CMAKE_FIND_ROOT_PATH_MODE_LIBRARY ONLY)
set(CMAKE_FIND_ROOT_PATH_MODE_INCLUDE ONLY)
```

This toolchain file is part of a more generic project called `platform`, where you can find many operating
system/compiler settings for various platforms. As for the date of publishing this article, it supports the following
configurations:

- (native) Linux (`gcc-11`, `gcc-13`, `clang-14`, `clang-18`),
- (cross) Linux ARM (`aarch64-none-linux-gnu-gcc-11`, `aarch64-none-linux-gnu-gcc-13`,
  `aarch64-none-linux-gnu-clang-14`, `aarch64-none-linux-gnu-clang-18`),
- (cross) baremetal ARM (`arm-none-eabi-gcc`, `arm-none-eabi-clang`),
- (cross) FreeRTOS ARM (`arm-none-eabi-gcc`, `arm-none-eabi-clang`).

## Download platform

`platform` project provides users with bootstrap (startup) code for each supported platform and toolchain file for that
platform with a wide selection of compilers. Feel free to check and use it in your project. Once you understand how it
works and its motivation, you will wonder how did you live without it.

<div class="grid cards" markdown>

- :simple-github: **[platform]**

    ---

    C/C++ application bootstrap layer for various hardware/OS platforms

</div>

## Summary

I hope this article will be helpful to you. Cross-compilation in CMake is easy and in most cases depends only on a
proper toolchain file. Once provided, everything else should be platform agnostic. If you have many conditional CMake
code in your project, consider extending toolchain file to hide all the OS/compiler differences there. You’re welcome!

<!-- links -->

[cmakeHostSystemName]: https://cmake.org/cmake/help/latest/variable/CMAKE_HOST_SYSTEM_NAME.html
[cmakeSystemName]: https://cmake.org/cmake/help/latest/variable/CMAKE_SYSTEM_NAME.html
[cmakeFindRootPathModeProgram]: https://cmake.org/cmake/help/latest/variable/CMAKE_FIND_ROOT_PATH_MODE_PROGRAM.html
[cmakeFindRootPathModeLibrary]: https://cmake.org/cmake/help/latest/variable/CMAKE_FIND_ROOT_PATH_MODE_LIBRARY.html
[cmakeFindRootPathModeInclude]: https://cmake.org/cmake/help/latest/variable/CMAKE_FIND_ROOT_PATH_MODE_INCLUDE.html
[platform]: https://github.com/kubasejdak-org/platform
