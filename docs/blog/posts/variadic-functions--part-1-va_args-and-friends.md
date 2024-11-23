---
date: 2019-05-22
categories:
  - C++
authors:
  - kuba
---

# Variadic functions – Part 1: `va_args` and friends

From time to time there is a need to write a function, that accepts an unspecified number of arguments. In C++ we have
multiple ways of handling this depending on the context, use case and available language features. But the oldest and
still most commonly used mechanism is the `va_arg`.

You think nothing can surprise you? Let’s bet.

<!-- more -->

???+ abstract "In this series"

    1. **Variadic functions – Part 1: va_args and friends**
    2. [Variadic functions – Part 2: C++11 variadic templates](variadic-functions--part-2-c11-variadic-templates.md)
    3. [Variadic functions – Part 3: techniques of variadic templates](variadic-functions--part-3-techniques-of-variadic-templates.md)

## `va_arg` in a nutshell

[Variadic function](https://en.cppreference.com/w/cpp/utility/variadic) by definition takes a variable number of
arguments. C and C++ provide a builtin way of expressing this in the argument list by using the ellipsis (`...`).

Here is a function, that accepts two doubles and an unknown number of other arguments:

```cpp linenums="1"
void compute(double a, double b, int count...)
{
    // Some operations...
}
```

In the example we provide an additional information to the function – number of arguments that are hidden behind the
trailing ellipsis. It looks like an optional hint to the function implementer, but in fact it is required by the [C
standard](http://www.open-std.org/jtc1/sc22/wg14/www/docs/n2346.pdf) ([C++ refers](http://eel.is/c++draft/cstdarg.syn)
to C on this matter).

Valid usage of `va_args` in C++ requires that:

- ellipsis must be last in the arguments list,
- last named parameter must define the count of variadic arguments,
- ellipsis can be preceded with an optional comma.

!!! note

    C++ added an optional comma before the ellipsis to be compatible with C, where comma is obligatory.

The standard library provides the [<cstdarg>](https://en.cppreference.com/w/cpp/header/cstdarg) header with the
following tools to work with the variadic arguments:

- `va_list` – helper type, that represents the variadic arguments list,
- `va_start()` – initializes the `va_list` object in the current function,
- `va_arg()` – extracts the next variadic argument,
- `va_end()` – destroys the `va_list` object.

The `va_list` type is implementation-defined and shouldn’t be accessed directly. Its only purpose is to be used by the
`va_*` macros family. The exact definition is usually provided by a builtin in the compiler and depends on the CPU and
ABI (Application Binary Interface), which defines the calling convention (how arguments are passed from caller to the
callee).

!!! example "For the curious"

    Here are two example implementations found in the wild:

    – pointer to the stack ([old Apple kernel implementation](https://opensource.apple.com/source/xnu/xnu-792.13.8/EXTERNAL_HEADERS/stdarg.h)),<br>
    – custom structure ([System V AMD64 ABI specification](https://software.intel.com/sites/default/files/article/402129/mpx-linux64-abi.pdf)).

`va_start()` macro initializes the `va_list` object using the number of expected variadic arguments. It is required to
be called before any access to the variable arguments.

The central role of the happy variadic family plays the `va_arg()` function macro. It is used to extract the argument of
the given type from the current parameters list’s head. We can visualize this process as casting the varargs pointer to
the demanded type and moving it later by the size of the type.

`va_end()` macro destroys the helper object and has to be called in the same function as the corresponding `va_start()`
call. It also must be called before any redefinition of there `va_list` type.

Here is a complete example of a valid variadic function usage:

```cpp linenums="1"
#include <cstdarg>

int sum(int count, ...)
{
    int sum = 0;
    va_list args;
    va_start(args, count);

    for (int i = 0; i < count; ++i) {
        int num = va_arg(args, int);
        sum += num;
    }

    va_end(args);
    return sum;
}

int main()
{
    return sum(4, 6, 7, 8, 9);
}
```

Feel free to play and inspect this example on different platforms and compilers using [Compiler
Explorer](https://godbolt.org/z/nD5OAZ).

## Default type promotion

There is one interesting process that happens behind the scenes when using variadic arguments. The C standard states,
that all unnamed arguments that are part of the variadic list are subject to the default type promotion. It means, that
all variadic arguments are converted in the following way:

- `std::nullptr_t` is converted to `void*`,
- `float` arguments are converted to `double`,
- `bool`, `char`, `short` and unscoped enumerations are converted to `int` or wider integer types.

It is really important to remember, because it’s not obvious. For example: if you pass `char` or `bool`, you still have
to extract an `int`! Here is an example:

```cpp linenums="1"
#include <cstdarg>
 
void func2(int count…)
{
    va_list ap; 
    va_start(ap, count);

    auto b = static_cast<bool>(va_arg(ap, int));

    va_end(ap);
}
 
void func()
{
    func2(1, true);
}
```

## Sources of the undefined behavior

Variadic arguments from `<cstdarg>` is a simple mechanism. However, it is easy to introduce some serious bugs to your
program if you are not careful. Here is the list of rules to obey to avoid the UB while using `va_args`:

- Do not pass parameters count to `va_args` by reference.
- Always define variadic arguments count to be the last named parameter (right before the ellipsis).
- Do not use `va_list` before calling `va_start()` first.
- Do not use `va_list` after calling `va_end()`.
- Do not call `va_end()` in a different function that corresponding `va_start()`.
- Do not call `va_start()` on the previously initialized object without calling `va_end()` first.
- Do not call `va_arg()` more times than the actual number of arguments.
- Do not call `va_arg()` with the incorrect type.

!!! warning "Remember"

    It doesn’t matter that you checked the violated rule and it works. It is just luck.

## Static analysis

Variadic arguments are operating directly on the stack arguments, so no wonder why this API has so many constraints. But
fear not! Your favorite compiler is here to help. It turns out, that both GCC and Clang have the default `-Wvarargs`
warning enabled. They can check if you are providing the number of hidden arguments in the arguments list, if this
parameter is right before the ellipsis and if by any chance you are passing a reference to the `va_start` macro.

It is also checked by the popular static analyzers: clang-tidy and Parasoft C/C++ Static Analyzer.

## Alternatives to `va_arg`

Presented `va_arg` mechanism from `<cstdarg>` is no the only way to implement the variadic functions. In specific use
cases you can use other alternatives:

function overloads – handy in a situation, where there are not that many combinations of the arguments and they are
handled in a different way, function accepting a container of arguments (e.g. `std::vector`, `std::array` or
`std::initializer_list`) – this approach can be used only if arguments share a common type. Of course, we can use the
type erasure technique (`std::any`, `std::variant`), but it will add another layer to the solution making it harder to
understand, variadic templates – which will be discussed in the second part of this article.

## Conclusion

Variadic functions with `va_arg` support have both pros and cons. They give you freedom and flexibility in handling
particular tasks. But also they require a strict contract between the caller and the callee, which is hard to maintain.
They are not type safe (only rely on the contract) and can lead to undefined behavior. There are multiple
recommendations to avoid it (e.g. [C++ Core
Guidelines](https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines#f55-dont-use-va_arg-arguments) and [SEI CERT
C++ Coding
Standard](https://wiki.sei.cmu.edu/confluence/display/cplusplus/DCL50-CPP.+Do+not+define+a+C-style+variadic+function)),
which I agree with. However I you have no other option or you have to use an API that already takes the `va_args` – be
careful and RTFM!
