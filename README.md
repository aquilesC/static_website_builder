# Static Website Builder

This is a very simple static website builder, which I use for building [aquiles.me](https://www.aquiles.me). The idea is to grab a bunch of markdown files and render them as HTML files. 

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

## Core Ideas
I built this static generator so that small notes can quickly find their way online, lowering my barrier to pushing content to a website. Therefore, it all revolves around using plain markdown files (I author them using Obsidian), and compiling using two simple templates: one for the index page and one for each note/article. 

Each note that ends with ``.md`` will be transformed into a folder such as as ``/note/index.html`` and spaces will be transformed to underscores. 

!! warning
    I am not dealing with non-ascii characters in any way, which is a problem for URL's

Each note can have internal links, in which I use the wikilink syntax: ``[[ ]]``. Each link is then appended to the target page, so that lists of backlinks can be built. I find the idea of backlinks crucial for lowering the barrier, since new content can be automatically be shown on older content. 

Also, links to non-existing pages will force the creation of an 'empty' node that only displays backlinks. 

## Extra Markdown
There are some custom solutions embedded into the program. For example, wikilinks parse the presence of ``|`` as a separator for the href. In this way, ``[[target|link]]`` will show up as ``link`` but will be targeted at ``target``. The wikilinks also remove all the spaces and transform them to underscores to be consistent with how I deal with URL's. 

The frontmatter is separated using an initial ``---`` and final ``---``. The keyowrds used for the moment are: ``title`` and ``description``, which are used for the meta tags of the html, ``epistemic``, which adds a note at the top of each article to display the [epistemic status](https://www.aquiles.me/epistemic_status). Other fields are accepted but are not currently used when generating content.

I also make use of ``admonition`` to include images of different widths. The ``style.css`` defines two types of images: medium and small that can be used by inserting something like this in the markdown file:

    !!! image small
	    ![Aquiles Carattino](/Aquiles_Carattino.jpg) 

## Git-based creation and modification dates
Since my working flow is based on git, I use it to compute the creation and modification dates of each file. It is not super accurate, since it measures the moment a file was added to git and not really created on the computer. Normally the offset is lower than a day. This approach seems to give more consistent results than using the operating system's dates, and is compatible with Netlify. 

You can read more on my [about page](https://www.aquiles.me/about).

## License
The code is released under BSD 3 Clause License. See LICENSE for more information. You are free to use and re-distribute, provided that you aknowledge my work. Seems fair enough. 

Of course, if you are trying to learn from the program, or building on it, don't hesitate to reach out at **aqui.carattino@gmail.com** 