# [jarmac.org](http://jarmac.org)
> "But you're not an organization!!"


Aw, shut it.


Relevant parts of nginx.conf
``` bash
$ diff default.conf default.old
24c24
<       root /home/ajarara/_site;
---
>       root /usr/share/nginx/www;
```

As of now, this blog is hosted on an nginx server through apt-get. I want to move it nix management, especially as this server does not scale well at all and the more config I can sanely keep in version control the better.

Further, while I will be using pelican (moving from jekyll, both static site generators), I  will be using piwik, just so I can visualize the reality that I'm posting to /dev/null.