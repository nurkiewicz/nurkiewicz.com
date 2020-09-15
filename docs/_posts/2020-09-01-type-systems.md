---
title: "#14: Static, Dynamic, Strong and Weak Type Systems"
permalink: /14
tags: type-systems ruby powershell python java c# groovy
description: >
    When choosing or learning a new programming language, type system should be your first question.
    How strict is that language when types don't really match?
    Will there be a conservative, slow and annoying compiler?
    Or maybe a fast feedback loop, often resulting in crashes at runtime?
    And also, is the language runtime trusting you know what you are doing, even if you don't?
    Or maybe it's babysitting you, making it hard to write fast, low-level code?
    Believe it or not, I just described static, dynamic, weak and strong typing.

---

{% include player.html episode_id="3ryE77MvuGwE08S9q6jv6n" %}

{{ page.description }}

# Example of typing system in Python

```
Python 3.8.5 (default, Jul 21 2020, 10:48:26)
[Clang 11.0.3 (clang-1103.0.32.62)] on darwin
Type "help", "copyright", "credits" or "license" for more information.
```


```python
>>> x = "abc"
>>> y = 123
>>> x + y
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
TypeError: can only concatenate str (not "int") to str
>>> x = 7
>>> x + y
130```

# More materials

* [Type system](https://en.wikipedia.org/wiki/Type_system)
* [Strong and weak typing](https://en.wikipedia.org/wiki/Strong_and_weak_typing)

{% include newsletter-input.md %}
