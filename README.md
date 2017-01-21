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