---
title: "#7: Speed of light"
permalink: /7
tags: moore cpu cdn ping
description: Speed of light is not as abstract to us, software engineers, as you might think. If you are deploying to the cloud or if you want to squeeze every bit of performance in your app, speed of light holds you back

---

{% include player.html episode_id="36501492" %}

{{ page.description }}

# Distance the light travels during one CPU cycle at 5 GHz

<script src="https://polyfill.io/v3/polyfill.min.js?features=es6"></script>
<script id="MathJax-script" async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>

<p>
    \begin{align}
    c = 3 \cdot 10^8 \mathrm{m \over s} \\
    f = 5 \mathrm{GHz} = 5 \cdot 10^9 \mathrm{Hz}\\
    t = {1 \over f} \\
    s = c \cdot t = {c \over f} \\
    s = { {3 \cdot 10^8 \mathrm{m \over s}} \over 5 \cdot 10^9 \mathrm{1 \over s}} = \\ 
    = {3 \over {5 \cdot 10}}  \mathrm{m} = {30 \over 5} \mathrm{cm} = \\ 
    6 \mathrm{cm}
    \end{align}
</p>

{% include newsletter-input.md %}

</script>