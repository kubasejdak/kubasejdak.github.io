---
date: 2019-07-31
categories:
  - C++
authors:
  - kuba
comments: true
---

# Variadic functions – Part 2: C++11 variadic templates

In the previous article, we have seen an old C-style way of defining the variadic functions – via va_args macros. We
have also learned their weaknesses: runtime cost, strict contract between caller and the callee and lack of type safety.
Not to mention the problem of default type promotion!

Fortunately, standards committee thought this through and equipped us in C++11 with variadic templates. Let’s check them
out.

<!-- more -->

???+ abstract "In this series"

    1. [Variadic functions – Part 1: va_args and friends][part1]
    2. **Variadic functions – Part 2: C++11 variadic templates**
    3. [Variadic functions – Part 3: techniques of variadic templates][part3]

## Syntax & definitions

First, let’s start with a basic _hello world_ of variadic templates:

```cpp linenums="1"
#include <iostream>

template <typename T>
T sum(T arg)
{
    return arg;
}

template <typename T, typename... Args>
T sum(T first, Args... args)
{
    return first + sum(args...);
}

int main(int argc, char* argv[])
{
    auto result = sum(1, 3, 5, 7);
    std::cout << result << '\n';
    return 0;
}
```

The output of this program is of course:

```
16
```

We have two template functions: first taking single parameter and second taking… exactly what? There are three syntax
changes compared to the regular templates, that make the second function “variadic”:

```cpp
typename... Args
```

which is called **template parameter pack**, then there is:

```cpp
Args... args
```

which is called **function parameter pack** and finally:

```cpp
args...
```

which is called **pack expansion**.

[Template parameter pack][cppreference-param-pack] defines a list of unspecified (possibly different) types that will be
used to instantiate this template function. Function parameter pack is using the same list of types to create the
function argument list. The notion of ellipsis in this context is similar to that known from the `va_args` functions.
The difference and real strength of variadic templates comes in the argument expansion.

!!! Note

    The reason for having the first argument explicitly stated and having an overload will be explained later.

## Parameter pack expansion

When compiler sees an ellipsis in the template it automatically expands the expression that uses it into a
comma-separated list according to the context. In our example we have three different places where `...` is used. Let’s
see in pseudo-code how compiler might unpack them:

| CONTEXT                 | EXPANSION                                                           |
| ----------------------- | ------------------------------------------------------------------- |
| Template parameter pack | `typename... Args` -> `Arg1, Arg2, Arg3, ..., ArgN`                 |
| Function parameter pack | `Args... args` -> `Arg1 arg1, Arg2 arg3, Arg3 arg3, ..., ArgN argN` |
| Pack expansion          | `sum(args...)` -> `sum(arg1, arg2, arg3, ..., argN)`                |

!!! Note

    **And now the best of it**:

    1. All happens at compile time (**no runtime cost and allows optimizations**)!
    2. All types are preserved (**ensuring type safety**)!
    3. We still haven’t used any specific type (**no strict contract between caller and callee**)!

That makes variadic templates superior to `va_arg` in almost every aspect. However, the drawback of this solution is a
different approach to implementing the function. This requires a bit of a mindset switch and time to get used to it.

## Example explanation

And now is the time to explain the implementation of our adding function. The idea is to use the recursion, extract the
first parameter from the argument pack in each call and pass the rest to the next iteration. We add the first unpacked
argument to the result of the remaining recursion. This process is repeated until the argument pack has only one
element. Then we call the function overload that expects a single template argument. This overload prevents further
recursion and is often called the “base case”. You can find the analogy to the popular `Factorial<N>` example. Finally
this call:

```cpp
auto result = sum(1, 3, 5, 7);
```

might result in the following expansion steps made by the compiler:

```cpp
auto result = sum(1, 3, 5, 7);    // 1) variadic case
auto result = 1 + sum(3, 5, 7);   // 2) variadic case
auto result = 1 + 3 + sum(5, 7);  // 3) variadic case
auto result = 1 + 3 + 5 + sum(7); // 4) base case
auto result = 1 + 3 + 5 + 7;      // 5) full expansion
```

## Implementation notes

I said earlier that variadic templates eliminate the strict contract between the called function and its client. This is
true to some extent. In C-style variadic functions _strict contract_ means, that function author must specify the exact
list of acceptable types along with its order (either in docs or by other parameter like format string). Any difference
between implementation and the call-side might lead to undefined behavior.

In case of variadic templates, then only requirement for the caller is to provide the types that support operations used
on them within the template body. In our case it is addition. So in other words, we require that for every pair of types
from the template parameter pack there is a well-defined `operator+()`.

!!! Note

    One possible way of ensuring this is to use the [concepts][cppreference-constraints] from C++20 aka
    [named requirements][cppreference-named-req].

## Instantiating template with list of different types

Arguments don’t have to be all of the same type in the template parameter list. We only require the `+` operation to be
valid for every pair. So the following call is perfectly valid:

```cpp
sum(true, 0, 4.6, 3.14f);
```

But the result is quite unexpected:

```
1
```

The problem lies in the result type of our template. Lets add some logging to better understand the situation:

```cpp linenums="1"
#include <iostream>
#include <typeinfo>

template <typename T>
T sum(T arg)
{
    return arg;
}

template <typename T, typename... Args>
T sum(T first, Args... args)
{
    return first + sum(args...);
}

int main(int argc, char* argv[])
{
    auto result = sum(true, 0, 4.6, 3.14f);
    std::cout << typeid(result).name() << ": " << result << '\n';
    return 0;
}
```

We have added type name of the result to the output. Now the program prints:

```
b: 1
```

This means, that the result variable is `bool`. The reason for that, is because our first template instantiation has
`bool` as the first argument. At that moment the return value is also `bool`. And this is the type used in type
deduction for the `result` variable. The recursion works as expected, but the return values are casted to `bool` which
can hold only `0` and `1` values.

In C++14 we can ask the compiler to deduce the correct type for us by changing the return types to `auto`.

```cpp linenums="1"
#include <iostream>
#include <typeinfo>

template <typename T>
auto sum(T arg)
{
    return arg;
}

template <typename T, typename... Args>
auto sum(T first, Args... args)
{
    return first + sum(args...);
}

int main(int argc, char* argv[])
{
    auto result = sum(true, 0, 4.6, 3.14f);
    std::cout << typeid(result).name() << ": " << result << '\n';
    return 0;
}
```

Now the result is as expected:

```
d: 8.74
```

## Going further

Recursion is not the only technique used with variadic templates. Our toolbox contains also:

- expression expansion,
- creative trick (read “hack”) with `std::initializer_list`,
- [C++17 fold expressions][cppreference-fold],
- `sizeof...` operator.

But all of that will be covered in the next article. Stay tuned.

<!-- links -->

[part1]: variadic-functions--part-1-va_args-and-friends.md
[part3]: variadic-functions--part-3-techniques-of-variadic-templates.md
[cppreference-param-pack]: https://en.cppreference.com/w/cpp/language/parameter_pack
[cppreference-constraints]: https://en.cppreference.com/w/cpp/language/constraints
[cppreference-named-req]: https://en.cppreference.com/w/cpp/named_req
[cppreference-fold]: https://en.cppreference.com/w/cpp/language/fold
