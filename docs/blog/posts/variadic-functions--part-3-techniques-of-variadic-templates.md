---
date: 2019-08-26
categories:
  - C++
authors:
  - kuba
comments: true
---

# Variadic functions – Part 3: Techniques of variadic templates

In the previous article I have shown you how variadic templates can be a type-safe alternative to va_arg macros in
designing the variadic functions. Today I want to show you a few techniques of variadic templates, that can be found in
many codebases.

<!-- more -->

???+ abstract "In this series"

    1. [Variadic functions – Part 1: va_args and friends][part1]
    2. [Variadic functions – Part 2: C++11 variadic templates][part2]
    3. **Variadic functions – Part 3: techniques of variadic templates**

## Recursive variadic templates

This technique has been already covered in the previous post, but let’s keep it anyway for completeness.

```cpp linenums="1"
#include <iostream>

void showRecursive() {}

template <typename T, typename... Args>
void showRecursive(T first, Args... args)
{
    std::cout << "showRecursive: " << first << '\n';
    showRecursive(args...);
}

int main()
{
    showRecursive(1, 2, 3, 4);
    return 0;
}
```

Here we have a slightly different example with only one template. `showRecursive` is a function that prints its
arguments, each in a separate line. As we already know, we have to unpack the first argument from the parameter pack by
explicitly declaring it in the function parameter list. Thus each instantiation of the template will assign its leading
argument to the `first` variable and leave the rest as the remaining pack.

In order to enable the recursion, we call the same function with the expansion of the remaining parameter pack. In every
iteration the argument pack will be shorter by one element. Finally, in the last round `showRecursive` will be called
with an empty pack. To handle this base case we can use a simple overload that takes no arguments (this is why it
doesn’t need to be a template).

The expected result is of course:

```
showRecursive: 1
showRecursive: 2
showRecursive: 3
showRecursive: 4
```

## Non-recursive argument evaluation with `std::initializer_list`

Variadic templates don’t have to be recursive. In fact this approach has several drawbacks:

- it makes the code less readable,
- it potentially generates more code,
- it requires a correct base case (stop condition) implementation.
 
Our preferred way is to iterate over all arguments and pass them one by one to some single argument function (like in
the `for` loop) and ultimately get something like this:

```cpp
func(arg1), func(arg2), ..., func(argN);
```

C++ doesn’t have an explicit way of achieving that. Fortunately, there is an implicit method, that involves usage of the
infamous `std::initializer_list`. Let’s see:

```cpp linenums="1"
#include <initializer_list>
#include <iostream>

template <typename T>
void showImpl(T arg)
{
    std::cout << "showImpl: " << arg << '\n';
}

template <typename... Args>
void showNonRecursive(Args... args)
{
    std::initializer_list<int>{(showImpl(args), 0)...};
}

int main()
{
    showNonRecursive(1, 2, 3, 4);
    return 0;
}
```

The first notable difference in this example is lack of the first unpacked argument. We are not basing out
implementation on the recursion, so it is not needed. Instead the `showNonRecursive` is creating an object of
`std::initializer_list<int>`. The argument of its constructor is particularly interesting:

```cpp
(showImpl(args), 0)...
```

This is a pack expansion, but used on the comma operator expression. Arguments of the comma operator are always
evaluated left-to-right, but the result is equal to the last argument. So in our case the first argument (which is a
call to `showImpl`) is evaluated with the first unpacked value from the parameter pack and `0` is returned as a result
of the comma operator. Then the second unpacked argument is passed to the constructor of the `std::initializer_list` in
the same manner. And again, the result of the operator is `0`. In pseudo-code this operation may be executed like this:

```cpp
std::initializer_list<int>{(showImpl(arg1), 0), (showImpl(arg2), 0), ..., (showImpl(argN), 0)};
```

If we leave only the side effects (results of the expressions), then it may look like this:

```cpp
std::initializer_list<int>{0, 0, ..., 0};
```

This explains, why we used `int` as a template argument in the `std::initializer_list`. In the end, the created object
is not assigned to any variable, so compiler is free to optimize it away (however I didn’t confirmed that it actually
does that).

To sum up, we are creating a fake object only to use the fact, that initializer lists are guaranteed to be evaluated in
order. Since we can’t create an initializer list out of the parameter pack (which could potentially have multiple
types), we use a list of 0s preceded with a demanded function. The glue that makes it work is the comma operator, which
evaluates both `showImpl` and 0, leaving 0 as the side effect.

!!! Note

    For people used to C++98 style or earlier this seems like a cool trick. For newcomers it could look like a hack in a
    language where everything is difficult. I agree – this is a HACK that exploits side effects of the comma operator.
    But let’s not forget, that templates were never intended to be used this way.

## Expression expansion

Parameter expansion can be used in many ways and in different code contexts. In the previous example we have seen that
applying a function on the parameter pack in fact calls this function for every element of the pack. The same can be
done with the single argument operators like incrementing, casting or extracting an address. Below you can find a list
of most interesting use cases for the expression expansion:

| CONTEXT             | EXPANSION                                                                                                                                                                          |
| ------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Function arguments  | `f(sizeof(args)...)` -> `f(sizeof(arg1), sizeof(arg2), ..., sizeof(argN)`                                                                                                          |
| Template arguments  | `print<Param1, Args..., Param2>` -> `print<Param1, Arg1, Arg2, ..., ArgN, Param2>`                                                                                                 |
| Inheritance list    | `template class Derived : public Bases... {}` -> `template <typename Base1, typename Base2, ..., typename BaseN> class Derived : public Base1, public Base2, ..., public BaseN {}` |
| Lambda capture list | `[args...] {}` -> `[arg1, arg2, ..., argN] {}`                                                                                                                                     |

## C++17 fold expressions

C++17 added even more operations, that can be used with the parameter pack. The main idea is to allow using two-argument
operators. [C++17 standard][cpp-standard-fold] specifies 4 acceptable syntax variations for this:

1. unary right fold (`pack op ...`),
2. unary left fold (`... op pack`),
3. binary right fold (`pack op ... op init`),
4. binary left fold (`init op ... op pack`).
 
So our summing example could be implemented using the unary right fold expression like this:

```cpp linenums="1"
#include <iostream>

template <typename... Args>
auto sum(Args... args)
{
    return (args + ...);
}

int main()
{
   std::cout << sum(1, 2, 3, 4) << '\n';
   return 0;
}
```

On the other hand, the “no separate line” variation of the printing example could look like this using the binary left
fold expression:

```cpp linenums="1"
#include <iostream>

template <typename... Args>
void foldPrint(Args... args)
{
    (std::cout << "foldPrint: " << ... << args) << '\n';
}

int main()
{
    foldPrint(1, 2, 3, 4);
    return 0;
}
```

The result of the above code is:

```
foldPrint: 1234
```

Below you can find the list of all acceptable operators in the fold expressions:

```
+   -   *   /   %   ^   &   |   <<   >> 
+=  -=  *=  /=  %=  ^=  &=  |=  <<=  >>=  =
==  !=  <   >   <=  >=  &&  ||  ,    .*   ->*
```

## Usage of the `sizeof...` operator

When using variadic templates you may end up in a situation, where you would like to know how many arguments are
actually passed. Let’s say that you want to store them in a table. How big should it be? `sizeof...()` will tell you:

```cpp linenums="1"
template <typename... Args>
void func(Args... args)
{
    int argsTable[sizeof...(args)] = {args...}; 
    // Some other code.
}
```

This technique is pretty straightforward. `sizeof...` operator called on the parameter pack will tell you the number of
its elements at compile time. It can be used in any context, that requires the compile-time evaluation.

## Perfect forwarding (FYI)

There is one last very important technique called perfect forwarding. It is not limited only to variadic templates, but
in my opinion it brings the most benefits in this context. Its only purpose is to pass (forward) function template
arguments into another function preserving all their properties like qualifiers or value semantics (lvalue, rvalue
etc…). However, it requires more knowledge about universal/forward references (`&&`) and move semantics. It is also very
rarely found in a typical business code, thus I will not cover its details here. Usually, it is exploited in the highly
customizable libraries, where client can specify its own callback functions. STL would be an excellent example of this.
Some of the most popular standard functions and classes that use perfect forwarding are:

- `std::make_shared()` / `std::make_unique()`,
- `std::thread`,
- `std::function`,
- `std::vector::emplace_back()`.

!!! Note

    Even Bjarne Stroustrup was joking (or not), that he can’t write perfect forwarding with confidence without checking
    some details first. Not to mention how little percentage of programmers actually should care about understanding it.
    Herb Sutter mentions this in his ["Back to the Basics! Essentials of Modern C++ Style"][cppcon-herb] talk at CppCon
    2014 (direct link to the quote).

## Summary

I hope that now you know what can be done with variadic templates and how to start using it.
[cppreference][cppreference-param-pack] can be a useful resource when in doubt.

<!-- links -->

[part1]: variadic-functions--part-1-va_args-and-friends.md
[part2]: variadic-functions--part-2-c11-variadic-templates.md
[cpp-standard-fold]: http://eel.is/c++draft/expr.prim.fold
[cppcon-herb]: https://youtu.be/xnqTKD8uD64?list=PLHTh1InhhwT7esTl1bRitiizeEnksGU7J&t=4667
[cppreference-param-pack]: https://en.cppreference.com/w/cpp/language/parameter_pack
