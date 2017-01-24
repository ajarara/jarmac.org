The Move to Pelican
###################

:date: 2017-01-23 18:19
:category: meta
:tags: pelican , reStructuredText, Markdown, Jekyll
:slug: the-move-to-pelican

I've used Jekyll for a while in college. Let's try Pelican. First I imported all the old posts, and it was incredibly painless to get them posted. The front matter for each post is relatively the same, but one neat thing is that Pelican supports RST or Markdown. The previous posts were written in markdown but with the liquid templating engine. All that was necessary was to change this:

.. code-block:: liquid
		
  {% raw %}{% include piwik %}{% endraw %}


to the same stuff most of us are used to in github.

.. code-block:: markdown
		
  ``` foo
  import foocode
  ```

That was easy.

A couple of benefits I'm really liking so far: make html and make serve very useful, very intuitive tools. `Pelican-mode <https://github.com/qdot/pelican-mode>`_ provides for a great interface, even though the code hasn't been updated in years, the interface still holds. That's comforting.

One other great benefit is the fact that output is entirely agnostic to whether the source file was written with markdown or with restructuredtext. Most people (me included) prefer Markdown, but it is nice to know that I can vomit :math:`\pi/4` at will by writing a post in rst.


Now working on piwik installation and configuration.

