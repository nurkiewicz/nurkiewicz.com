---
title: "#47: Terraform: managing infrastructure as code"
category: podcast
redirect_from:
  - /47
tags: hcl infrastructure terraform
description: >
    Terraform is fairly low-level software for managing your infrastructure.
    For instance, it's used to create and provision cloud instances, networks and software.
    Unlike traditional tools in this area, Terraform is _declarative_.
    It means you don't define step-by-step, imperative guides.
    Essentially, scripting your infrastructure with Bash or Python.
    Instead, you define desired, final infrastructure state.
    For example, how many hosts, how they should be connected, what kind of software and packages they should contain.
    Once you apply this configuration, Terraform takes all the necessary steps to fulfill your needs.
    Here's how it works in more detail.
---

{% include player.html spotify_id="15zlML4thKnVVwwBPyhJ1D" youtube_id="fBxyoDzw4o8" %}

{{ page.description }}

The Terraform configuration consists of a bunch of resources.
Each resource describes one infrastructure element.
What kind of elements you can manage?
Well, the official Registry of Terraform plugins, known as providers, has about one thousand entries!
Each provider uses an API to manage the undertlying resource.
For example, you can use AWS provider to provision EC2 instance of a certain size.
The provider uses AWS API to create this instances under the hood.
If you wanted one instance, the providers will create it.
If you later change your mind and ask for a hundred, the provider will create the remaining ninety nine.

There's actually a bit more going on under the hood.
Apart from physically setting up your infrastructure, Terraform keeps everything in special external state file.
The initial invocation creates infrastructure resources.
But subsequent applications are quite different.
The desired state is confronted with the last known state.
Terraform tries really hard to transition from current to desired state with minimal effort.
If updating an existing resource is possible, Terraform does that.
Otherwise, the existing resources is destroyed and recreated.
An example of such destructive action is changing the base image of a virtual machine.
Or moving to another data center.
In the latter case Terraform will provision new VM and tear down the old one.
For us, it's just a single line of code.

Oh, I forgot.
Everything in Terraform is driven by code.
The whole setup in HashiCorp Configuration Language is typically stored in version control.
Every change to the infrastructure is audited and can go through code review.
Moreover, it's a good practice to perform a dry-run of every change before applying it.
This can be achieved with `terraform plan` command-line option.
Terraform will explain what it wants to do with infrastructure.
In other words, what steps need to be taken to get from current to desired step.
If we are comfortable with the changes, we can proceed.

Even much more complex resources can be managed by Terraform.
You need a MongoDB cluster or self-hosted GitLab?
With a few lines of code Terraform will provision them.
Of course, if you later decide to scale up or scale out your Mongo cluster, it's a matter of configuration.
Obviously, Terraform can be parameterized.
Setting up a new staging environment or deploying to a different region is a single switch.

Destroying everything we provisioned is also easy.
After all Terraform knows exactly which resources it created.
Contrast this approach to manually clicking through hundreds upon hundreds of screens in AWS or GCP.
Defining your infrastructure as version-controlled code seems much more manageable.

That's it, thanks for listening, bye!

# More materials

* [Terraform](https://en.wikipedia.org/wiki/Terraform_(software)) on Wikipedia
* [Providers registry](https://registry.terraform.io/browse/providers)
* [What is Terraform? A Quick Overview](https://spacelift.io/blog/what-is-terraform)
