# Static Website Builder

This is a very simple static website builder, which I use for building [aquiles.me](aquiles.me). The idea is to grab a bunch of markdown files and render them as HTML files. 

Building from scratch was easier than trying to adjust existing solutions to my own needs. I a releasing this package mostly to help others learn. 

The template was built using TalwindCSS, and is processed with PostCSS to make it minimal (11kb without compressing). 

## Entry Point
The program can be triggered by running the following command:

```bash
$ brain_dump
```

It assumes the following:

* Content Folder: ``content``
* Template Folder: ``templates``
* Static Folder: ``static``
* Output Folder: ``output``

You can see the [main function](https://github.com/aquilesC/static_website_builder/blob/master/aqui_brain_dump/main.py) to understand what it does.

### Core Ideas
I am trying to lower my barrier to generate content. I realized that the pressure to create complete articles, such as what happens on a blog, blocks my creativity. Thereore, I built this static generator on the ideas of an evergreen digital garden of ideas. Small notes can quickly find their way online. 

This also lowers my barrier to write articles on very diverse topics, such as technical notes, that may be handy to share with colleagues, and thoughts on political issues, such as gender biases, academia, or the role of technology transfer. 

For this, all articles are parsed and a tree of links is built using the wikilink syntax. Only after, articles are rendered and the list of links to each page is available. This allows for a reader to transverse the articles in both directions. I also took care of creating empty pages for articles linked to, but non existen. In this way nodes are visible even if they have no content. 

You can read more on my [about page](https://www.aquiles.me/about).

## License
The code is released under BSD 3 Clause License. See LICENSE for more information. You are free to use and re-distribute, provided that you aknowledge my work. Seems fair enough. 

Of course, if you are trying to learn from the program, or building on it, don't hesitate to reach out. 