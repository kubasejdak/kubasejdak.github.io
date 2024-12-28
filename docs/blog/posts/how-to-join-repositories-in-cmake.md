---
date: 2020-02-02
categories:
  - Tools
tags:
  - CMake
authors:
  - kuba
comments: true
---

# How to join repositories in CMake

Sometimes there is a need in a project to use directly some other repository (local or external). This means, that we
want to be able to incorporate parts (or all) of sources of the imported repository into our build system. Usually, in
such a case we would also like to track which version is used at a given time.

We can solve this problem in a few ways, e.g. by using:

- git submodules,
- git subtree,
- CMake `FetchContent`,
- CMake `ExternalProject`.

First two are handled by the version control system and the last two are handled by the build system. Each of them has
its own strengths and weaknesses, depending on the current project needs.

Today I want to briefly present how CMake allows joining repositories with its `FetchContent` and `ExternalProject`
modules.

<!-- more -->


## `FetchContent`

!!! info

    `FetchContent` is available since CMake 3.11.

The role of `FetchContent` is to obtain resources from a specified location and make it available to the rest of the
build system. Note, that I used the word “resources” which can mean not only source codes, but also toolchains,
artifacts from other builds, scripts, application icons etc.

Below you can see a typical usage:

```cmake linenums="1"
include(FetchContent)

# 1.
FetchContent_Declare(platform
    GIT_REPOSITORY  https://github.com/kubasejdak-org/platform.git
    GIT_TAG         main
)

# 2.
FetchContent_MakeAvailable(platform)
```

In this example, we are downloading my `platform` repository and using the `main` branch. Here we can see, that it
consists of two parts:

1. define (declare) what should be downloaded and where it is,
2. launch download and make it available (populate) to the rest of the build system.

Note, that `platform` (which I will reference later as `<resource_name>`) is later used as prefix in the related
variables or argument in related functions, so make it meaningful and unique.

Everything happens at the “configure” (generation) stage, once CMake reaches `FetchContent_MakeAvailable(platform)`
command. This is important to remember and understand, because generation step is usually done once and `FetchContent`
can influence this process. `FetchContent_MakeAvailable` command is executed only once for every resource during cmake
configuration. Consider those two functions as the `FetchContent` idiom.

!!! info

    Using `FetchContent` requires including proper module: `include(FetchContent)`.

By default, everything is downloaded into your build directory in a well-defined structure:

```
${CMAKE_CURRENT_BINARY_DIR}/
  - _deps/
    - <resource_name>-build
    - <resource_name>-src
    - <resource_name>-subbuild
```

!!! note

    I’m not exactly sure what is the purpose of the `subbuild` directory. After examining its contents it looks like
    CMake is generating `CMakeLists.txt` files there to implement `FetchContent` in terms of `ExternalProject` command.
    Maybe it was the easiest way of adding `FetchContent`, since `ExternalProject` was already available for a long time
    and can be reused at generation stage with a simple trick.

Once CMake successfully downloads our external content, it sets two variables that can be used in `CMakeLists.txt` to
locate the new data:

- `<resource_name>_SOURCE_DIR` – specifies the location of the downloaded sources,
- `<resource_name>_BINARY_DIR` – specifies where is the default build directory for the downloaded sources.

`FetchContent_MakeAvailable(<resource_name>)` triggers both download and includes that sources to our build system as if
they were already part of our codebase.

From now on, downlo directory is subject to all CMake settings of the main project and from the build system point of
view is treated as the local sources.

## `ExternalProject`

!!! info

    `ExternalProject` is available since CMake 3.0.

`ExternalProject` command is almost identical to `FetchContent` in terms of the purpose and available options with,
except for one extremely important difference: it is launched at build stage. In my opinion it is a crucial drawback
comparing to `FetchContent` because external content is made available to us after our build system is already generated
and all build decisions are already made. There is no way to add sources downloaded with this method into our
compilation stage (or at least not a trivial way).

To compensate this problem, `ExternalProject` allows launching another CMake instance on the downloaded sources and pass
custom command to be used to compile it. Let’s see this in an example:

```cmake linenums="1"
include(ExternalProject)
ExternalProject_Add(platform
    GIT_REPOSITORY  https://github.com/kubasejdak-org/platform.git
    GIT_TAG         main
    CMAKE_ARGS      -DPLATFORM=freertos-arm
)

add_dependencies(<some_target> platform)
```

!!! info

    Using `ExternalProject` requires including proper module: `include(ExternalProject)`.

The snippet above will perform the following actions:

1. It will download specified repository into `platform-src` path (like in `FetchContent`).
2. It will automatically call CMake in `platform-build` passing `-DPLATFORM=freertos-arm`:

```bash
cd platform-build
cmake -DPLATFORM=freertos-arm ../platform-src
```

!!! note

    `FetchContent` offers the same possibility.

Making a dependency to some other target with `add_dependencies(<some_target> platform)` command is required in order to
tell CMake when all that actions should be actually done. With `FetchContent` we didn’t have that problem: generation is
done sequentially in order of parsing `CMakeLists.txt` files. At build stage, CMake is composing a dependency graph of
all defined targets in order to determine in which order all targets should be built. That graph is influenced by two
commands:

- `target_link_libraries()`, where we implicitly say that in order to build one target we need to link with another one
so it would be nice if it was already built,
- `add_dependecies()`, where we explicitly say, that one target should be built before another one (even if they are not
using each other).

Without making an explicit dependency between `ExternalProject` target and `<some_target>` CMake would simply ignore
that step.

To be honest, once `FetchContent` became available in CMake I completely lost the purpose for using `ExternalProject`.

## Customization

Both `FetchContent` and `ExternalProject` are highly customizable. Moreover, most of the options are available in both
of them. Let’s see some examples along with short comments on usage.

### Download methods

Both commands support the following download types:

- Git,
- SVN,
- CVS,
- Mercurial,
- HTTP.

Each method has a typical set of settings you would normally expect, like branch name, commit/revision number, URL etc.
I have personally used only Git in this context.

While doing so, for a long time I have specified `main` branch as the content source. The problem with such declaration
is that every time something changes in the content’s upstream, it immediately gets populated to the places that use it.
In my case, I had a few “utility” repositories, that were reused with `FetchContent` in highly active product
repositories. For sure, using branch name relieves you from remembering to update `FetchContent` declaration in every
repository once a change is introduced. But on the other side, if you are doing some breaking change, then it can create
a lot of chaos. Especially if you have an active team. Trust me, you don’t want to hear all those complaints. So instead
of branch name, specify tag or commit hash. The only drawback of this approach is that you need to remember to update
that hash whenever necessary. It is also not obvious at first sight if the changed hash is newer or older in history
without checking the Git log.

```cmake linenums="1"
include(FetchContent)
FetchContent_Declare(platform
    GIT_REPOSITORY  https://github.com/kubasejdak-org/platform.git
    GIT_TAG         ee3ce49227e809aa3ef0f6270b4c996b4808cddf
)

FetchContent_MakeAvailable(platform)
```

### Fetching without network

Most fetching methods naturally assume, that you have an Internet/Intranet connection to your remote content. However
there are situations, where you are totally offline (business trips, network problems, etc). This could literally block
your work.

Fortunately there are two options you can use to work without connection to the upstream:

- using local content copy on you hard drive (e.g. clone of the repo done while connection was still available),
- forcing CMake to not try updating (checking for changes) of the content already downloaded by the previous
`FetchContent`/`ExternalProject` run.

In the first case, you can simply replace repository URL with a path to the local repository copy. It works very well.
The only observable difference is the fact that content will not be physically copied into you build directory – CMake
will use the existing files that you are pointing to. This should hardly ever be an issue.

In the second case, you rely on the fact that you have successfully run `FetchContent`/`ExternalProject` at least once.
Every time CMake is processing it, it checks if the content is up-to-date. In the offline scenario that check will
result in an error. You can explicitly ask CMake to skip that part by adding additional parameter –
`UPDATE_DISCONNECTED` with value `ON`:

```cmake linenums="1"
include(FetchContent)
FetchContent_Declare(platform
    GIT_REPOSITORY        https://github.com/kubasejdak/platform.git
    GIT_TAG               origin/master
    UPDATE_DISCONNECTED   ON
)

FetchContent_MakeAvailable(platform)
```

Note, that this will not skip downloading content for the first time. It will also not update your content if you have a
healthy connection.

!!! success "Hint"

    Local directory turned out to be the perfect solution if you need to make changes in fetched repository and check if
    it breaks dependent projects. It would be really annoying to do this using Git (it could generate a lot of trash
    commits).

### Choosing the right place to run `FetchContent`

`FetchContent` runs at the generation stage, so choosing the place where it is declared determines which parts of the
build system could interact with the fetched content.

For example, `FetchContent` can be run before `project()` function (both declare and make available statements). This
could allow you to setup custom toolchain (via `CMAKE_TOOLCHAIN_FILE`) which is downloaded from the company’s server.

### Specifying subdirectory of referenced content

If you need to get to the specific directory, then you have to do it by hand, e.g. my HAL project requires, that clients
should use only lib directory, while root path is used to launch tests, generate documentation etc.:

```cmake linenums="1"
include(FetchContent)
FetchContent_Declare(hal    
    GIT_REPOSITORY        https://github.com/kubasejdak-org/hal.git
    GIT_TAG               v1.5b
    SOURCE_SUBDIR         lib
)

FetchContent_MakeAvailable(hal)
```

I also like to put FetchContent commands in the separate files called `<resource_name>.cmake` and include them in other
`CMakeLists.txt` where needed:

```cmake linenums="1"
# cmake/platform.cmake

include(FetchContent)
FetchContent_Declare(platform
    GIT_REPOSITORY        https://github.com/kubasejdak-org/platform.git
    GIT_TAG               main
)

FetchContent_MakeAvailable(platform)
```

```cmake linenums="1"
# cmake/osal.cmake

include(FetchContent)
FetchContent_Declare(osal
    GIT_REPOSITORY        https://github.com/kubasejdak-org/osal.git
    GIT_TAG               main
)

FetchContent_MakeAvailable(osal)
```

```cmake linenums="1"
# cmake/hal.cmake

include(FetchContent)
FetchContent_Declare(hal
    GIT_REPOSITORY        https://github.com/kubasejdak/hal.git
    GIT_TAG               main
)

FetchContent_MakeAvailable(hal)
```

```cmake linenums="1"
# Root CMakeLists.txt

# ...

include(cmake/platform.cmake)
include(cmake/osal.cmake)
include(cmake/hal.cmake)

# ...
```

## Summary

There are at least a few ways how you can join repositories in your source code. CMake offers `FetchContent` at
generation stage and `ExternalProject` at build stage. Each comes with a rich set of options, which you can check in the
[official docs][external-project]. Choose the right method for your specific case. In most cases `FetchContent` would
suit you better.

If you liked this article, then please share it on the social media you use. It will greatly increase the chance that
someone else will benefit from it. It will also motivate me to write more and better articles in the future.

<!-- links -->

[external-project]: https://cmake.org/cmake/help/latest/module/ExternalProject.html
