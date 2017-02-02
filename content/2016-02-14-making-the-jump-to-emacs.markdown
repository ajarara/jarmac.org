layout: post
title:  "Making the Jump to Emacs"
date:   2016-02-14 21:49:51 -0500
category: $editor

## Why I Started With Vim

I first got into development after I had developed an interest in networking. I was used to tools that did one job and did it very very well: ssh, less, grep, man and vim, usually in some remote session. However at one point, I realized that for every development site, I had to push out my .vimrc, make sure vundle was working, send over .bashrc and .tmux.conf... It was starting to get ridiculous. I decided it was best to make edits on my own machine, and then push them out using scp/rsync only. I didn't know it yet, but it's what most development environments (especially ones that use version control) do to manage both complexity and collaboration. I still needed to choose an editor, though. 

Vim stood out to me as the most useful. However, vim was right out of reach. For those who still remember the time that they launched vim and had no idea how to even quit, you recognize what I'm about to talk about. There's a curve to learning any individual utility, a tool like a hammer or a package manager. Anyone familiar with either knows that there are things that can be done with these tools that are near impossible to do without: try updating every application you have installed using only a hammer.

However, most tools aren't intuitive. We've seen other people use hammers, but what if I give you a tool that you probably haven't seen before?

![Seems like this picture's missing. Let me know at ajarara@jarmac.org]({{ site.url }}/assets/esd-wrist-strap.jpg)

(Looking at the file name is cheating, by the way)

It's used to prevent electrostatic discharge when working on the internals of computers. It's not strictly necessary, but it's really nice to have. It's also not intuitive to use. I've had to stop people trying to put the clamp straight on the motherboard once I tell them what it does, and that might've been something I would have done had I not looked into it.

The point is, that the tools we have available have some payoff hidden beyond some technical know how. And the resources at getting you started may come with a manual of its own (looking at you, emacs in-line help system).

While vim did require me to learn an entirely new mode of editing, I firmly believe that it helped significantly. After you learn what modal editing is, how to set marks for quick reference, and how to do conditional text editing (like replacing a variable name in a big file with a more descriptive one globally), you start to see why vim is touted as the best editor. That's the first leap. Then you start looking for ways to go beyond 'basic' functionality with plugins, and then you take the second leap: configuration files, vundle, and vimscript. This is where I was before I decided to jump ship.

When I installed emacs, I knew that evil-mode was the way to go. I tried following the tutorial, and found the key bindings weird and unintuitive. I knew I was happy with vim's keybindings, so I decided to keep them, using evil-mode. I just... uh, needed to figure out how to install evil-mode.

## How I did it

Well the good thing about emacs is that [their wiki is phenomenal](https://www.emacswiki.org/emacs/Evil). The instructions there don't read like TVTropes where you have to know everything to know anything. Once I had that installed, I wanted to test it out, but I realized I didn't have any idea how to start editing a file. After going through the [emacswiki site map](https://www.emacswiki.org/emacs/SiteMap), I found out the important stuff.

One thing I dearly missed almost immediately was shell access. I had it to some extent, (:! worked but would behave weirdly with prompts), but I also missed tmux. Tmux deserves its own post (it completely invalidates vimsplit), but for now it will have to be happy with me just praising it. So I looked up how to get a hold of a terminal emulator, how to get comfortable with quick buffer swapping, and I was set.

There were two options: ansi-term and terminal. I discovered ansi-term first, and use that, but there may not be a difference. Both are a little different (and require an escape sequence C-c to use emacs commands, C-c C-c still interrupts any programs, though) but they read .bashrc and in my case, run tmux just fine. It's a little crazy using both C-b and C-x to work with a buffer system nested inside a buffer system, but there's no conflicts that I've found, and everything works as it should. One issue that I've had is that I tend to navigate to the file I want to edit and use vim. At this point, I'm inside a vim session inside of a tmux pane inside of a tmux session inside of an emacs session. And everything works just fine! I just need to drop that habit.

There was a lot of other intermediary frustrations, and frustrations that I'm still dealing with now, (if you go traverse a big enough directory tree, for example, you get quickly overwhelmed with the number of directory buffers you have when you list them all out) but for the most part I am now as comfortable with emacs as I am with vim. And really, when I say that, I mean I've replaced my editing environment with something that was sane to configure.

## On to the good things
Do you have a text file that you put notes into for reminders? ```M-x remember``` pops up a buffer, you type in what you want to remember, hit C-c C-c and then remember appends it to a notefile in your .emacs.d for later reading. It even saves the current directory you were in. That is especially useful for when you're describing a bug in data or code.

Further, org mode. While I haven't personally haven't tried it yet, I'm really excited about just how powerful it can be. For example it extends M-x remember with useful metadata that allows you to categorize notes and access them independently. The google talk (voiced by the person that wrote org-mode back in 2003) mentions that it only requires the use of two keys to do all sorts of organization: shift and tab, which is music to my keychord ears. It can be used for note taking with inline LaTeX, has column formatting, priorities, and subheadings. Yet another package that has huge payoff for some initial investment.

Once I feel truly comfortable with emacs I may come back and edit this article (there are jekyll-emacs packages ready to use, jekyll is the blogging software) with additional notes.

