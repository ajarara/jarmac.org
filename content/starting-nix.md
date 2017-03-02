Title: "Deploying with Nix"
Date: 2017-03-02 13:16
Category: nix
Tags: deploy functional
Slug: starting-nix


Nix is awesome. It makes deploying so much fun.

By now I've been playing with Nix for about 2 weeks. With learning any new tech there is always a period of utter confusion, where you land deep in S/O questions that answer the wrong questions. In #emacs, there is something called an X-Y problem, addressing directly this.

``` text
<fsbot> alphor: hmm, xyproblem is when you want to do X, and you think
    Y is how, so you ask about Y instead of X. See
    <http://www.perlmonks.org/index.pl?node_id=542341> or
    <http://mywiki.wooledge.org/XyProblem>
```

The problem is that it's difficult to know that someone has encountered the problem before and has set up a convenient interface (or guide) to do it in the tech you're working with. In Nix, it's especially poignant, as that is what nix is about: You declare what you want your machine to do, Nix handles the heavy lifting.

If that sounds optimistic, know that a _lot_ of work has been done so far, it's been developed since 2004, and is probably hitting critical mass. #nixos on freenode is very active and helpful. Last week marked the 100,000th commit on nixpkgs, a ports-like repository of derivations. 

I want to use Nix to create a home media center. I've done a machine like this before, running XBMC, a timemachine daemon, nfs, local duplicity, and openvpn providing a DMZ and dynamic DNS for access. But, configuration of all these services in tandem was a nightmare. Docker helped in terms of providing isolated environments, but it did not reproduce builds. If I broke something, I'd have to rollback to some state and start over. And I broke things often.

I really like the way Nix does things. As long as I don't break networking, I'm free to mess around with my machine as I see fit without risking having to reinstall from scratch. Another big plus: all configuration is local, as in on my machine. No forwarding over SSH, no Dockerfiles in tmux, no littered git repos. Everything for a machine is in exactly one repo, [here](github.com/alphor/3asirah).


But Nix has earned its reputation as a difficult technology to learn.

The first hurdle in setting up a home media server was getting openvpn working _just_ right. To do that, we want to dedicate a NIC just to openvpn traffic, and to do that, we need to set up routing with dual NICs. [This S/O question](http://serverfault.com/a/487911) shows how to do it the traditional way.

In order to declare this, first we have to set up our interfaces like so:

``` nix
   # this is our openvpn interface
   networking.interfaces.eno1.ip4 = [ {
     address = "192.168.5.155";
     prefixLength = 24;
   } ];
   
   networking.interfaces.enp2s0.ip4 = [ {
     address = "192.168.5.151";
     prefixLength = 24;
   } ];
```


Easy, right? The hard part isn't that. It's creating a new routing table.

We can't do this:

``` bash
echo 13 eth3 >> /etc/iproute2/rt_tables
```

Instead, we have to modify the derivation. There are a couple of ways to do this. First is to find iproute in the store, and do it directly to the file itself. This is not the right way to do it at all, but it'll probably work, provided you have the permissions for it. But for sure it will disappear on rebuild of your system. Instead, what you want to do is modify the postInstall phase of iproute to do the things you want.

This is much easier than automating the last step, and the manual outlines a [couple ways](http://nixos.org/nixos/manual/index.html#sec-customising-packages) to do this, depending on if you want to modify the derivation as it comes in, or derive a new derivation from the existing one, overwriting the previous.

There is a distinction between these two: the first makes it so that any package that depends on the derivation yoyu are modifying uses the modified derivation. The second essentially creates a new scope where your derivation exists, but if something else depends on the derivation you're messing around with, it will use the stock one.

In this case, I want my routing global and consistent, so I went with the first option:

``` nix
   nixpkgs.config.packageOverrides = pkgs:
     {
     # We have two interfaces. However, since our default gateway only
     # goes through enp2s0, once the second interface is enabled weird
     # routing issues occur, causing all packets to be dropped. Here's
     # how to fix this with iproute2.

     # first we override the derivation provided by nixpkgs. 
     # since openvpn more than likely depends on iproute2, we should
     # override it globally. to do this, we apply our changes to the
     # attr set of pkgs. as shown here:
     # http://nixos.org/nixos/manual/index.html#sec-customising-packages

     # the reason we need to modify the derivation is because we need to
     # modify rt_tables to add an id number for the uplinks.
     # we use this guide as inspiration
     # https://debian-administration.org/article/377/Routing_for_multiple_uplinks

       iproute = pkgs.stdenv.lib.overrideDerivation pkgs.iproute (attrs: {
         postInstall = ''
           echo 13 eno1 >> $out/etc/iproute2/rt_tables
           echo 14 enp2s0 >> $out/etc/iproute2/rt_tables
         '';
         });
     };
   
```

Notice, the assignment is itself a function that takes an argument. In this case, it is pkgs, but I could've named it bananas if I wanted to. Further, overrideDerivation is a function that itself takes a package and a function. This new function, prefixed with attrs: in the code block above, takes the attribute set and returns a new one. This allows me to add in the attributes of the stock derivation, if I wanted to. In this case, iproute doesn't even _have_ a postInstall section, so I do not include it.

Further, I explicitly do not want the $out from attrs, so I don't use ${attrs.out} as that would refer to the stock derivation when I want to refer to the modified one. I tripped up on this as well, but this changes the hash and in a sort of rabbit pulling out the magician trick, you attempt to modify the old derivation, which doesn't work.

All in all, though, I'm immensely proud of figuring this out (and I intend to add this to the manual once I can condense this long commentary). Strangely enough, since the only flag modified is postInstall and thus postCompilation, there is no need for nix to compile it again. Maybe I'd raise an issue, but on the other hand I just love watching all the text scroll by.
