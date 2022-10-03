---
title: "#87: Artificial neural networks: imitating human brain to solve problems like humans"
category: podcast
permalink: /87
tags: machine-learning deep-learning
description: >
    An artificial neural network is a computer algorithm somewhat inspired by our brains.
    Superficially, our brain is a network of neurons connected with each other and communicating via electrical impulses.
    Artificial intelligence experts implemented a similar concept purely in software.
    An artificial neuron is basically a function that takes a set of inputs and has an output.
    Just like the biological one.
    By connecting hundreds of such neurons in a network, we can observe quite _intelligent_ behaviours.
    For example, artificial neural networks can recognize what's in the image.
    Or quite the opposite - generate images from text.
---

{% include player.html spotify_id="08Pens38XZEfGchvaEf41c" youtube_id="TODO" %}

{{ page.description }}

But first things first.
Both inputs and outputs are basically just numbers.
The simplest neuron may take two numbers and return their sum or product.
In that case, the so-called _activation function_ is addition or multiplication respectively.
It's called _activtion_, because it decides whether our neuron "_activates_" with respect to inputs.
In other words, if it produces an output signal.
In practice, the activation function must be nonlinear, for example, logarithmic or exponential.

OK, so how does all this work together?
First of all, neurons are typically organized into a multi-layer network.
The outcome of one layer is propagated to the subsequent layer.
The number of layers and neurons in each layer comes from experimentation.
That's one of the deciding factors, how well the network operates.

The other factor is even more important.
One neuron may receive hundreds of inputs.
The activation function inside that neuron must decide, which inputs are more important than the others.
So, each input has a weight.
With one set of weights, our neural network may recognise cats and dogs.
The same network with different weights may translate from Polish to Chinese.
There may be hundreds of thousands of weights to adjust.
How do we come with them?
The secret is: we don't!

Instead, we create a rather random network that is not capable of doing anything useful.
Then we feed that network with, for example, pictures of cats and dogs.
By the way, a picture 1000 by 1000 pixels is represented as a million input.
One input number per pixel.
Anyway, our network digests that and produces a single number as an output.
That number is garbage because the network is random.
However!
We know what the output was supposed to be.
Let's say `0` for cat and `1` for a dog.
Then the algorithm known as _backpropagation_ adjusts each weight ever so slightly.
The next time the neural network receives a cat image, it is slightly closer to the expected outcome.

This process, known as supervised learning, is repeated for thousands if not millions of inputs.
After many hours of training, the network can recognize cats, tumours, or Chinese poems.

Artificial neural networks are actively studied.
For example **deep neural network** consists of multiple layers to support more complex problems.
**Recurrent neural network** supports the flow of signals in any direction, not only forward.
**Convolutional neural network** adds spatial filtering over input image.
All these techniques allow speech recognition, artificial image generation and more.

Interestingly, artificial neural networks were invented quite some time ago.
But only recent research, combined with growing hardware capabilities, allowed them to grow in significance.

That's it, thanks for listening, bye!

# More materials

* [Artificial neural network](https://en.wikipedia.org/wiki/Artificial_neural_network)
* [Backpropagation](https://en.wikipedia.org/wiki/Backpropagation)
* [Convolutional Neural Networks](https://www.ibm.com/cloud/learn/convolutional-neural-networks)
* [Is it true that a neural network can be represented by just a lot of matrix math? How do you implement one on paper?](https://www.quora.com/Is-it-true-that-a-neural-network-can-be-represented-by-just-a-lot-of-matrix-math-How-do-you-implement-one-on-paper)
* [Text-to-Image Generation with Attention Based Recurrent Neural Networks](https://deepai.org/publication/text-to-image-generation-with-attention-based-recurrent-neural-networks) 
