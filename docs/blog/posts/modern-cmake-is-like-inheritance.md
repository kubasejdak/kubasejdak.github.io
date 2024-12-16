---
date: 2020-01-18
categories:
  - Tools
tags:
  - CMake
authors:
  - kuba
comments: true
---

# Modern CMake is like inheritance

CMake has been created in 2000 by Bill Hoffman from Kitware. During the last 20 years, as of the time of this
publication, it’s been constantly evolving by adding new features and expanding its support for third-party libraries.
But the most significant additions were released in version 3.0 and are commonly called “Modern CMake”. Despite being
available for more than 5 years, many programmers are still not using them!

Today I will show you one of the greatest “Modern CMake” feature, that behaves almost like C++ inheritance. But before
we get there, let me briefly explain a few fundaments.

<!-- more -->

## Modern CMake = targets + properties

Target is a fundamental concept in CMake. It generally represents one “job” of the building process. Most commonly used
targets are executables and libraries. Let’s see the syntax for creating and using them:

```cmake linenums="1"
add_executable(myExecutable
    main.cpp
)

add_library(libA
    sourceA.cpp
)

add_library(libB
    sourceB.cpp
    sourceB_impl.cpp
)

add_library(libC
    sourceC.cpp
)

target_link_libraries(myExecutable libA)
target_link_libraries(libA libB)
target_link_libraries(libB libC)
```

This is a classic way of creating targets. Here we have an executable called `myExecutable` and three libraries `libA`,
`libB` and `libC`. For now we know, that in order to build `myExecutable` we have to link with `libA`, for building
`libA` we have to link with `libB` and for building `libB` we have to link with `libC`. The last one has no
dependencies.

Let’s keep in mind, that those are not the only possible targets that can be defined in CMake. We can create also custom
targets, whose only role is to invoke some command:

```cmake linenums="1"
add_custom_target(firmware.bin
    COMMAND             ${CMAKE_OBJCOPY} -O binary firmware firmware.bin
    DEPENDS             firmware
    WORKING_DIRECTORY   "${CMAKE_BINARY_DIR}/bin"
)
```

In the snippet above we are defining a custom target named `firmware.bin`, whose only objective is to create a BIN file
from the original executable using GNU objcopy (if you are not familiar with objcopy, then think of this as some
conversion of the binary file). Here we explicitly say, that `firmware.bin` depends on `firmware`. This is natural,
because in order to convert firmware file it must be already built!

!!! note

    We could also skip the line with `DEPENDS` and add `add_dependencies(firmware.bin firmware)` instead as a separate
    statement. But in my opinion, it is less elegant.

Each target can have its own set of properties, that will be used in proper contexts. Here is a list of the most popular
ones:

- compilation flags,
- linking flags,
- preprocessor flags,
- C/C++ standard,
- include directories.

All of the above properties are stored in the special CMake variables and are automatically used by the build system,
when the given target appears in the certain context. For example, include directories property is automatically added
to the compilation flags when the target is being compiled. Linking flags are automatically passed to the linker, when
this target is being linked. You may say, that all these properties are either `CFLAGS` or `LDFLAGS` so there is no need
to extract them into individual entities. But we will see in a moment, that this separation can be quite handy in Modern
CMake projects.

## Setting properties: include directories, preprocessor, compilation and linking flags

Target properties can be set in at least few ways. Before CMake 3.x we could either set raw CMake flags (e.g.
`CMAKE_C_FLAGS`, `CMAKE_LINKER_FLAGS`) or use directory-oriented commands, which set given property for all targets in
the current directory and its subdirectories. Modern CMake introduced a new set of target-oriented commands, which allow
us to set properties for targets individually.

Below you can find a comparison of the old directory-oriented commands and their new recommended alternatives in Modern
CMake:

| DIRECTORY-ORIENTED OLD COMMANDS            | TARGET-ORIENTED NEW COMMANDS                                             |
| ------------------------------------------ | ------------------------------------------------------------------------ |
| `include_directories(<include_path>)`      | `target_include_directories(<target> [VISIBILITY] <include_path>)`       |
| `add_definitions(<preprocessor_flags>)`    | `target_compile_definitions(<target> [VISIBILITY] <preprocessor_flags>)` |
| `set(CMAKE_CXX_FLAGS <compilation_flags>)` | `target_compile_options(<target> [VISIBILITY] <compilation_flags>)`      |
| `set(CMAKE_LINKER_FLAGS <linker_flags>)`   | `target_link_options(<target> [VISIBILITY] <linker_flags>)`              |

!!! note

    I personally prefer to indent each entry after `[VISIBILITY]` and put each one on a separate line like this:
    ```cmake
    target_include_directories(<target>
        [VISIBILITY]
            <include_path1>
            <include_path2>
    )
    ```

Modern CMake introduced also new keywords, that specify visibility of the given target property: `PRIVATE`, `PUBLIC`,
`INTERFACE`. Their meanings are as follows:

- `PRIVATE` property is only for the internal usage by the property owner,
- `PUBLIC` property is for both internal usage by the property owner and for other targets that use it (link with it),
- `INTERFACE` property is only for usage by other libraries.

This is very similar to the access specifiers in a C++ class! Each of the new commands allow visibility specification.
If none is provided, then `PUBLIC` is assumed. Note, that each command can have multiple properties set at different
visibility level:

```cmake linenums="1"
target_include_directories(<target>
    INTERFACE
        <include_path_1>
        <include_path_2>
        <include_path_3>
    PUBLIC
        <include_path_4>
        <include_path_5>
        <include_path_6>
    PRIVATE
        <include_path_7>
        <include_path_8>
        <include_path_9>
)
```

!!! note

    Targets that don’t produce any binaries (e.g. header-only libraries) can have only `INTERFACE` properties and can
    only use `INTERFACE` linking. This is quite understandable, because there is no “internal” part in such targets, so
    `PRIVATE` keyword doesn’t mean anything.

## Using (linking with) libraries behaves like inheritance

In order to link libraries together we use the expression:

```cmake
target_link_libraries(<TARGET_A> <TARGETS...>)
```

Modern CMake extended this command with the visibility specifier like this:

```
target_link_libraries(<TARGET_A> [VISIBILITY] <TARGETS...>)
```

Again, visibility can be one of `PRIVATE`, `PUBLIC` and `INTERFACE`. If none is provided then `PUBLIC` is used by
default. But what does it mean in terms of linking?

CMake 3.x introduced a very important “side effect” of linking with targets: linked target is passing all its `PUBLIC`
and `INTERFACE` properties to the library that it links with. So for example, if `libA` is linking with `libB` then
`libA` gets all `PUBLIC` and `INTERFACE` properties of `libB`. `PRIVATE` properties are still not accessible. Another
question is: what is the visibility of the newly obtained set of properties (by `libA`)? Answer is simple: it’s the same
as the specifier used in `target_link_libraries()` for that target. So if `libA` links as `PRIVATE` with `libB`, then
all `PUBLIC` and `INTERFACE` properties of `libB` become `PRIVATE` properties of `libA`. Similarly, if it links as
`PUBLIC`, then all `PUBLIC` and `INTERFACE` properties of `libB` become `PUBLIC` in `libA`. The same goes for
`INTERFACE` linking.

Can you see now, that this looks almost identical as inheritance in C++? Private inheritance makes all public and
protected members private in the derived class and public inheritance keeps the visibility unchanged.

In order to understand it better, let’s see some use cases.

## Example 1: avoiding header dependencies

Let’s assume the following directory structure:

```linenums="1"
libA/
    - include/
        - libA/
            - sourceA.h
    - privateHeaderA1.h
    - privateHeaderA2.h
    - sourceA.cpp
libB/
    - include/
        - libB/
            - sourceB.h
    - submodule/
        - submodule.h
        - submodule.cpp
    - privateHeaderB1.h
    - privateHeaderB2.h
    - sourceB.cpp
    - sourceB_impl.h
    - sourceB_impl.cpp
libC/
    - include/
        - libC/
            - sourceC.h
    - privateHeaderC1.h
    - privateHeaderC2.h
    - sourceC.cpp
main.cpp
```

and the following include dependencies in code:

```cpp linenums="1"
// sourceB.cpp

#include "libC/sourceC.h"
#include "submodule.h"

// ...
```

```cpp linenums="1"
// sourceA.h

#include "libB/sourceB.h"

// ...
```

```cpp linenums="1"
// main.cpp

#include "libA/sourceA.h"
#include "libC/sourceC.h"

// ...
```

Also let’s define a rule, that we don't want any library to be able to use "private" headers of the other libraries:
e.g. the code below shouldn’t compile:

```cpp linenums="1"
// main.cpp

#include "privateHeaderC2.h" // should fail as "no such file or directory"
```

This restriction is a good architectural practice, that can keep the code clean from unwanted dependencies. How to make
that compile without a messy config?

First we have to check each target and determine the include paths that it is “creating”. By this I mean which include
paths belong to this particular target. Then for each path in a given target we have to decide, if it should be
accessible by others (`PUBLIC`) or not (`PRIVATE`). Finally we will use new target-oriented commands to set the include
properties for each library.

```cmake linenums="1"
add_executable(myExecutable
    main.cpp
)
```

```cmake linenums="1"
add_library(libA
    sourceA.cpp
)
target_include_directories(libA
    PUBLIC
        include
)
```

```cmake linenums="1"
add_library(libB
    sourceB.cpp
    submodule/submodule.cpp
)

target_include_directories(libB
    PUBLIC
        include
    PRIVATE
        submodule
)
```

```cmake linenums="1"
add_library(libC
    sourceC.cpp
)

target_include_directories(libC
    PUBLIC
        include
)
```

All these targets have one thing in common: the only `PUBLIC` include path is the `include` directory. This means, that
if other libraries call only `target_link_libraries()` to both get include paths and link with library, then no private
header will ever leak unintentionally outside the containing library.

Now its time to properly link the libraries:

```cmake linenums="1"
target_link_libraries(myExecutable
    PRIVATE
        libA
        libC
)

target_link_libraries(libA
    PUBLIC
        libB
)

target_link_libraries(libB
    PRIVATE
        libC
)
```

Observe the following things:

1. Executable doesn’t need to specify linking type (because nothing can link with exec), but we define it for
consistency.
2. `libA` links publicly with `libB`, because it is using header from `libB` in its own public header. So it has to
provide this path to its clients.
3. `libB` links privately with `libC`, because it is using header from `libC` only in its internal implementation and
its clients shouldn’t even be aware of this.
4. `target_link_libraries()` means in Modern CMake two things: use library (get its properties) at compilation stage and
link with it at linking stage. Hence maybe a bit better name for it would be `target_use_libraries()` but it would break
the backward compatibility.

## Example 2: defining header-only libraries

Sometimes we have to deal with libraries, that don’t produce any binaries. For example, they are just a set of headers
that your application needs to include. In such a case they are called a header-only libraries.

An excellent example would be the [Catch2][catch2] library, which implements the popular C++ testing framework. It
consists of only one file `catch.hpp` which is stored in `catch2` directory. First, it would be convenient for us, to
still have a CMake target that provides path to that file once someone links with it. Secondly, Catch2 allows some
behavior customization via the define directives. For example, we can disable usage of POSIX signals and exceptions in
favor of a call to `std::terminate()`. This is particularly crucial on embedded systems, where we can’t use any of them.
So our target should also be able to detect the environment and provide the proper defines accordingly.

In Modern CMake it could be expressed like this:

```cmake linenums="1"
add_library(catch2 INTERFACE)

target_include_directories(catch2
    INTERFACE
        catch2
)

if (<some_condition_to_detect_embedded_platform>)
    target_compile_definitions(catch2
        INTERFACE
            CATCH_CONFIG_NO_POSIX_SIGNALS
            CATCH_CONFIG_DISABLE_EXCEPTIONS
    )
endif ()
```

Note the usage of `INTERFACE` keyword. When `add_library()` contains the `INTERFACE` specifier, then it tells CMake,
that this target doesn’t produce any binary. In such a case it doesn’t contain any source files.

As mentioned before, all properties of the `INTERFACE` target also have to be marked as `INTERFACE`. This is
understandable, because header-only libraries don’t have any private implementation. Everything is always accessible to
the client. If this is still confusing for you then just remember, that `INTERFACE` target enforces `INTERFACE`
properties. But later linking with such a target can be of any type:

```cmake linenums="1"
add_library(myTestingModule
    source.cpp
)

target_link_libraries(myTestingModule
    PRIVATE
        catch2
)
```

## Summary

CMake provides a new target-oriented way of specifying various compiler options and other properties. Once you link with
a target, you immediately inherit (obtain) its `INTERFACE` and `PUBLIC` properties and make it your own with the access
level specified in the linking command. This mechanism resembles C++ inheritance, thus should be easy to understand.

!!! success "If you are using CMake 3.x and above, then use the this rule as your guide for creating targets:"

    Library designed and built with Modern CMake should provide its clients with everything they need to compile and use
    it, without the need to check its internal implementation.

If you find yourself checking what is the path to the missing include in some library then it means that you are doing
something wrong:

- either CMake configuration of that library is bad,
- or you are trying to access files that are explicitly hidden from you.

<!-- links -->

[catch2]: https://github.com/catchorg/Catch2
