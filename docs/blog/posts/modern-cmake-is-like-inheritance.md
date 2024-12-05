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
    INTERFACE <include_path_1> <include_path_2> <include_path_3>
    PUBLIC <include_path_4> <include_path_5> <include_path_6>
    PRIVATE <include_path_7> <include_path_8> <include_path_9>
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

Example 1: avoiding header dependencies

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

=== ":octicons-file-code-16: `sourceB.cpp`"

    ```cpp linenums="1"
    #include "libC/sourceC.h"
    #include "submodule.h"

    // ...
    ```

=== ":octicons-file-code-16: `sourceA.h`"

    ```cpp linenums="1"
    #include "libB/sourceB.h"

    // ...
    ```

=== ":octicons-file-code-16: `main.cpp`"

    ```cpp linenums="1"
    #include "libA/sourceA.h"
    #include "libC/sourceC.h"

    // ...
    ```

Also let’s define a rule, that we don't want any library to be able to use "private" headers of the other libraries:
e.g. the code below shouldn’t compile:

=== ":octicons-file-code-16: `main.cpp`"

    ```cpp linenums="1"
    #include "privateHeaderC2.h" // should fail as "no such file or directory"
    ```
