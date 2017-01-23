title:  "setxkbmap madness"
date:   2016-02-09 17:28:51 -0500
categories: desktop linux

I recently came across an article off [Economy of Effort][econofeffort] about keeping your pinky happy by swapping around caps lock with control. This is not new to most people, and is easy to do with [Karabiner][karabiner] for OS X. Unfortunately my last Macbook is back home, and also terribly, terribly old (if anyone else has the black 2006, you paid $200 extra for the paint job and some extra RAM, life is tough).

[econofeffort]: http://www.economyofeffort.com/2014/08/11/beyond-ctrl-remap-make-that-caps-lock-key-useful/
[karabiner]: https://pqrs.org/osx/karabiner/

Running GNU/Linux, there are two main options to modifying your key layout: xmodmap and setxkbmap. Both are shipped with a standard Fedora installation, and the guide linked above uses setxkbmap. Unfortunately, I found that after sending my computer to sleep, caps lock reverted to its usual behavior, and I had to pop a terminal to source .profile. Alternatively, I could bind a key to source it, but I had three issues with that:

First, I would have to remember to press the key binding every time my laptop locked.

Second, if I forgot and I hit caps lock expecting control, I would have to hit caps lock before I hit the keybinding, otherwise it simply would not fire.

Third, .profile was in fact being sourced. I knew this because I used xev to look at the keycodes and found that the other relevant line in the guide was indeed being applied.

``` bash
xcape -e 'Caps_Lock=Escape'
```

So setxkbmap was the culprit here. I tried figuring out a way to make it work, but found myself yearning for xmodmap's simple config. Yeah, it wasn't powerful, but it worked consistently. Here are the contents of my .xmodmap:

``` bash
!swapping caps to control
remove Lock = Caps_Lock
remove Control = Control_L
keysym Control_L = Caps_Lock
keysym Caps_Lock = Control_L
add Lock = Caps_Lock
add Control = Control_L
```

I couldn't get xcape to work with xmodmap until I realized that xcape was being called after xmodmap did its thing. This was enough to make me try the following in my .profile instead:

``` bash
xcape -e 'Control_L=Escape'
```

And it worked. And man is it awesome on my pinky.