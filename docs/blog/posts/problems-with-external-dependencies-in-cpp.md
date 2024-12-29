---
date: 2020-12-10
categories:
  - Tools
tags:
  - Conan
authors:
  - kuba
comments: true
---

# Problems with external dependencies in C++

Dependencies are usually the most problematic part of the build system (next to the toolchain setup) in programming
projects. In C++ this is especially hard because there is no one standard build system. Many more problems arise if we
target an embedded system. Other programming languages resolve this issue by having one built-in package manager
(usually accompanied by an integrated build system). In C++ we lack both of them, so our lives are much harder.
Fortunately, there are a few third-party package managers which get more and more popular. In this series of posts, I
will try to convince you to start using one of them – Conan.

<!-- more -->

???+ abstract "In this series"

    1. **Problems with external dependencies in C++**
    2. [Introduction to Conan package manager][part2]

## Why do we need a package manager for C++

Before I introduce you to Conan in the next article, let’s try now to define all the problems, that our package manager
should be able to solve, in order to call it “generic” and “usable”. Of course, let’s not expect that it will be a
remedy for everything out of the box. We are looking for a tool, that will provide us with simple mechanisms that can
directly or indirectly address the day-to-day problems that most of us encounter in projects. Here is a list of
immediate issues/concerns that one should look into before making any decision about dependencies or package managers:

1. **getting the sources of the external libraries** – how are we actually going to get the sources of the libraries?
   Should we hardcode the URLs in our build system? Or maybe we should incorporate them into our repository? The former
   makes multiple assumptions about the location, format and availability of the library. The latter option increases
   our codebase, makes it harder to update and de facto turns us into local maintainers of that dependency.
2. **managing versions of the dependencies** – in some cases we need to use a very specific version of the external
   library. For example, we want to use some hot new feature, which is available only in the latest release. How should
   we specify that? How should we manage dependencies of the third-party code which could change from version to
   version? This point is closely related to the next one.
3. **satisfying dependencies of the libraries** – it is quite natural, that our dependencies will have their own
   dependencies. In such a case we would have to meet some preconditions, possibly by installing another set of
   libraries (which could again have dependencies). It is quite easy to get yourself into a loop of relations between
   libraries that is hard to manage or even fully satisfy.
4. **dynamically selecting the required dependencies** – sometimes we can build many applications from the same
   codebase. It is usually the case when we have a lot of common code. In such situation it may happen, that one
   application is using some part of the common code, but the second application is using another one. Both modules can
   have different dependencies and we want to build only what is currently required. We would like to be able to
   dynamically say that dependency A should be installed only while we compile “this” directory and dependency B while
   we compile “that” directory. I have seen projects, in which such selection is not trivial and manually managing it
   can generate a lot of boilerplate code in the build system.
5. **(cross-)compiling the libraries** – if we are working on a PC application, then we don’t have to worry about the
   type of processor that will run our program or other platform-specific things. In the case of embedded systems, we
   must cross-compile every source file that will be used. We need to be able to specify the concrete toolchain and all
   required compilation flags.
6. **customizing/patching dependencies** – in many cases we need to modify a little the external library. For example,
   some of them are not ready for cross-compilation and their build system has to be adjusted. In other cases, it turns
   out, that our dependency is not compiling with our compilation flags (e.g. we have -Werror flag enabled and the
   library is producing warnings or we are using clang compiler and the external code is using GCC-specific extensions).
   The most irritating thing (at least for me) is when I find a perfect library that solves my problem, but it is using
   a different build system than mine. In such situations, we need to adapt it to our needs.
7. **installing compiled dependencies in the host system** – once we compile the external libraries, they have to be
   installed somewhere. There are two options: we either put them in our build directory or install them in the host
   system. The first one will require us to build dependencies every time a build directory is cleaned. The second one
   solves this problem, but installed binaries may be in conflict with the already installed packages in our operating
   system. Also, we may want to distinguish libraries compiled with a different set of flags.
8. **making the whole process easy to use** – it is important to keep it simple for the average programmer to build and
   install the dependencies. If things get complicated, then our coworkers will be frustrated. They will either try to
   remove the dependency and replace it with a self-written code (bad) or will modify a carefully designed build system
   in their own way and thus may complicate it even more (equally bad).
9. **(optional) handling compilation on the target platform** – in some rare (or not) cases we need to support building
   the project on the target. In my experience, I had to do this in order to correctly calculate code coverage. Maybe I
   did something wrong, nevertheless, the situation forced me to run a compilation on the board. It was quite
   problematic because my target already had all the dependencies installed in the system. As a consequence build system
   and package manager had to take that into an account and rather use those libraries than compiling them from scratch.

These are only a few of problems that may arise in our projects. Also, once we choose one mechanism for managing the
dependecies, then it will be hard to change it in the future. This is why this topic is important and requires a deep
thought.

## Possible solutions for external dependencies

There are a few solutions for managing the dependencies on the market nowadays. It is good to know them at least
briefly. Below you can find a list of the most popular that I know of:

!!! note

    This list not complete and extremely brief. I have no experience with package managers other than Conan or CMake
    `fetch_content`. Consult the official docs to get more information and have a better overview on available
    solutions.

### CMake `fetch_content`

- Official documentation: [cmake.org][cmakeFetchContent].
- This mechanism is part of the CMake build system (read [this article][joinRepos] to learn more) and doesn’t require
  anything additional to be installed. It is very primitive but quite effective if your dependency is also using CMake
  (non-CMake projects can also be built, but it is less flexible that way).
- It allows you to specify a repository or file to be downloaded. Additionally, you can select a branch or tag in case
  of the git VCS.
- Dependencies are downloaded into the current build directory and can be built just like any other code in your
  project. To be precise, you need to explicitly include them with a `add_subdirectory` command in `CMakeLists.txt`
  file. This allows you to build third-party code with the exact same compilation configuration (toolchain and
  compilation flags) as your codebase. On the other side, CMake treats that code as if it was your code which sometimes
  can cause problems (warnings treated as errors or conflicting CMake variables).

### Hunter

- Official documentation: [hunter.readthedocs.io][hunterDocs].
- Third-party package manager, which is fully dependant on CMake. In fact, Hunter is simply a set of CMake modules that
  manage given dependencies internally via `ExternalProject_Add` command.
- Hunter provides a customization point for building the libraries via the native CMake toolchain file mechanism. This
  is quite clean and nice, but it can be problematic if someone is not using toolchain files or don’t know how they work
  (read [this article][crossCompileChamp] to learn more about toolchain files).
- Using libraries built by Hunter is done in a typical CMake way: after adding some initialization code in the
  beginning, you can call `find_package` to locate the demanded library and use `target_link_libraries` to link against
  it.
- Packages that are supported by Hunter have to be added to the official package repository and usually a bit modified
  in order to cooperate with the package manager. Such libraries are said to be “Hunterized”. It seems, that there is no
  easy way to add custom packages other than through the official package list. This is quite limiting because it
  usually takes time to analyze, review and accept such changes by the package manager maintainers. Also, this is
  dangerous to depend on the work and time of people outside your organization or project. Sometimes you need to make
  changes very quickly (e.g. hotfix for the client) and you can’t have delays on the third-party people side.
- Hunter makes it easy to manage multiple versions and configurations of the same dependency because each build
  directory is stored separately in a specified root path. Thus it is possible to reuse prebuilt packages in all your
  projects.

### vcpkg

- Official documentation: [vcpkg.readthedocs.io][vcpkgDocs].
- Like Hunter, this is a package manager but managed by Microsoft. In order to install it, you have to clone its
  repository and compile it for your local machine. It runs on all major platforms and fully supports CMake by default.
- Installing dependencies is done in a separate step from the command line: `vcpkg install <package_name>`. All files
  and binaries are stored in a user-specified root directory, so packages are not conflicting with the host system.
  However, it is not clear to me, how is vcpkg actually building the code: is it assuming that we are targeting a local
  machine? How should we specify the compiler and compilation flags that should be used during compilation? If you know,
  then please share it in the comments.
- A major drawback (at least for me) is the fact, that in order to use dependencies provided by the vcpkg you need to
  use a special toolchain file from the vcpkg root directory. I don’t have any experience with this package manager
  except for some tutorials and a few personal trials, but it seems that you can’t explicitly use your own toolchain
  file in the project. If that is true then this eliminates vcpkg for my projects.
- Incorporating dependencies managed by vcpkg is done exactly like in Hunter: `find_package` + `target_link_libraries` –
  clean and easy.
- Only libraries that are registered in the official vcpkg package repository can be used. This has a very similar
  limitation as with Hunter: we depend on other people’s time and will. However, since Microsoft is behind this, then we
  can expect better support than usual. Also, it is said that Microsoft is running regular CI jobs with all registered
  packages in order to maintain quality and quickly detect problems.

### Conan 

- Official documentation: [docs.conan.io][conanDocs].
- A package manager written in Python. Available in multiple forms, but the most recommended one is through a pip
  package.
- It has very good integration with multiple build systems like CMake, Makefiles and Visual Studio. In the case of the
  first one, packages can be used via specially created Conan targets for each library or with a well-known
  `find_package` command.
- Dependencies can be built and installed both from the command line or directly from the CMake. The first method
  expects a simple config file similar to pip’s `requirements.txt` file.
- All binaries are stored in a per-user cache, allowing to reuse the prebuilt packages across compilations and projects.
- Conan is able to build external dependencies that use the most popular build systems like CMake, Autotools
  (Makefiles), Visual Studio and Meson. Of course, it is up to the maintainer of the Conan package config (aka recipe)
  to correctly set up the build process, but Conan provides all the required tools to do that. Regardless of which build
  framework is used, we can quite easily reason about building the library and then (separately) reason about making a
  binding out of its binary output. This is possible because for Conan these are two not related phases. In other words,
  it is possible to use the external library which is using Makefiles and generate an integration layer to your CMake
  project.
- Packages have to be registered in a package repository, but fortunately, you can freely add your own and register them
  in a self-hosted or public repository for binaries. This is a huge benefit because you can maintain your own package
  repository with your own package recipes even on your company’s server. Usually, you don’t need to keep a local copy
  of the third-party code, because Conan packages should only tell the package manager where to get the sources and how
  to build them. Additionally, you can apply custom patches in between.

### Yocto SDK

- Official documentation [yoctoproject.org][yoctoDocs].
- This mechanism is different from the previous ones, but since I’m actively using it recently I decided to mention it
  here. It comes from the Yocto Project, which is a Linux distribution generator/builder. It allows you to specify what
  should be included in your final Linux image and for which platform it should be cross-compiled. Yocto SDK is a set of
  libraries + toolchain that can be used by application developers to cross-compile applications that should be deployed
  later into that image. It creates for you the same environment, that your application will meet on the target
  (libraries, tools, etc).
- SDK installation is done with a Bash script and it simply installs all the packages and tools that your app can link
  against in the development environment. It also provides you with a complete cross-toolchain and sets up all required
  environment variables. If your build system is relying on the `CC` and `CXX` variables to detect the compiler, then
  you won’t have to change anything.
- Integration with CMake is done with a specially generated toolchain file.
- SDK is usually generated in one of the build stages of the Yocto image. Adding new packages or changing their versions
  is done by simply running the Yocto build again and reinstalling the SDK. As a consequence, your build environment
  will always reflect the newest target image, that will host your application.

## Summary

Each of these package managers has advantages and disadvantages. It really depends on your needs and resources. I
personally have the biggest (but still relatively small) experience with Conan. It served me well for the last year and
allowed me to incorporate external libraries into my projects, which would never be possible otherwise within given time
constraints. Mainly because of their lack of support for cross-compilation. With Conan, it was quite easy to adjust them
without making a local copy of the package. In the next articles, I will try to present how Conan works and what are its
main advantages and how I use it in my CMake projects.

<!-- links -->

[part2]: introduction-to-conan-package-manager.md
[cmakeFetchContent]: https://cmake.org/cmake/help/latest/module/FetchContent.html
[joinRepos]: how-to-join-repositories-in-cmake.md/#fetchcontent 
[hunterDocs]: https://hunter.readthedocs.io/en/latest/index.html
[crossCompileChamp]: how-to-cross-compile-for-embedded-with-cmake-like-a-champ.md
[vcpkgDocs]: https://vcpkg.readthedocs.io/en/latest/
[conanDocs]: https://docs.conan.io/en/latest/
[yoctoDocs]: https://www.yoctoproject.org/docs/2.1/sdk-manual/sdk-manual.html
