Title: "Deploying with Nix"
Date: 2017-04-18 19:03
Category: nix
Tags: deploy, functional
Slug: starting-nix


_Edit 6/26/17: The contents of this post are now completely __OUT OF DATE__. It remains here for historical purposes only. This stuff will likely still work, but if you'd like to establish policy based routing on NixOS, I heavily suggest creating a service declaration to modify /etc/iproute2/rt\_tables and scheduling it before networking.service. The new way to modify a derivation is through the use of [overlays](https://nixos.org/nixpkgs/manual/#sec-overlays-install), which was the standard way of overriding packages previously (as discussed on [S/O here](http://stackoverflow.com/a/36011540))._

Nix is awesome. It makes deploying so much fun.

By now I've played with Nix for about 2 weeks, and I've noticed that with learning any new tech there is always a period of utter confusion, where you land deep in S/O questions that answer the wrong questions. In #emacs, there is something called an X-Y problem, addressing directly this.

``` text
<fsbot> alphor: hmm, xyproblem is when you want to do X, and you think
    Y is how, so you ask about Y instead of X. See
    <http://www.perlmonks.org/index.pl?node_id=542341> or
    <http://mywiki.wooledge.org/XyProblem>
```

The problem is that it's difficult to know that someone has encountered the problem before and has set up a convenient interface (or guide) to do it in the tech you're working with. In Nix, it's especially poignant, as that is what Nix is all about: We declare what we want our machine to do, Nix does the heavy lifting.

If that sounds optimistic, know that a _lot_ of work has been done so far to achieve this goal: Nix (and NixOS) has been developed since 2004, and is probably hitting critical mass. #nixos on freenode is very active and helpful. Last week marked the 100,000th commit on nixpkgs, a ports-like repository of derivations. 

I want to use Nix to create a home media center. I've done a machine like this before, running XBMC, a timemachine daemon, nfs, local duplicity, and openvpn providing a (logical) DMZ and dynamic DNS for access. But, configuration of all these services in tandem was a nightmare. Docker helped in terms of providing isolated environments, but it did not reproduce builds. If I broke something, I'd have to rollback to some state and start over. And I broke things often.

I really like the way Nix does things. As long as I don't break networking, I'm free to mess around with my machine as I see fit without risking having to reinstall from scratch. Another big plus: all configuration is local, as in on my machine. No forwarding over SSH, no Dockerfiles in tmux, no littered git repos. Everything for a machine is in exactly one repo, [here](https://github.com/alphor/3asirah).

## New tech ain't easy

Nix has earned its reputation as a difficult paradigm to learn.

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


Easy, right? The hard part isn't that, though. It's creating a new routing table.

# The X-Y Problem

We can't do this:

``` bash
echo 13 eth3 >> /etc/iproute2/rt_tables
```

Because rt_tables isn't there. It's somewhere in /nix/store. How do we modify it after every build? 

We have to modify the derivation. There are a couple of ways to do this. 

## The Mad Way
Let me preface this by making it clear: This is __not__ the right way to do things. Alice returning from Wonderland would faint at the horror I'm about to type here. The correct way follows after this excursion into insanity.

Nix lives on symlinks. It uses them to build environments, to build packages, and to ensure atomic installs. We can find the symlink for iproute2 by first getting the symlink out of our binary:

``` bash
readlink $(type -p ip)
# /nix/store/32bit-hash-snipped-iproute2-4.5.0/bin/ip
```
Then we descend into madness by snipping out the binary path and changing directory to the etc/iproute2 within the derivation.

``` bash
IPROUTE_CONF='$(readlink $(type -p ip) | sed -e 's_/bin/ip_/etc/iproute2/_')
cd $IPROUTE_CONF
```

Hoping the elder gods are pleased with our sacrifice, we move to take our spoils:

``` bash
echo 13 eth3 >> etc/iproute2/rt_tables # Success!
# bash: rt_tables: Read-only file system
```
Wh... what?

![](/images/another-castle.jpg)

## The Reasonable Way

The read only file system is our Y problem. Whether or not making the store world writable is possible (it probably isn't a good idea), there is another solution to our original problem. It's not obvious.

What we want to do is modify the postInstall phase of the iproute derivation.

This is much easier than automating the last step (so that changes persist across reboot), and the manual outlines a [couple ways](http://nixos.org/nixos/manual/index.html#sec-customising-packages) to do this, depending on if we want to modify the derivation as it comes in, or derive a new derivation from the existing one, overwriting the previous.

There is a distinction between these two: the first makes it so that any package that depends on the derivation we are modifying uses the modified derivation. The second essentially creates a new scope where our derivation exists, but if something else depends on the derivation we're messing around with, it will use the stock one.



In this case, I want my routing global and consistent, so I went with the first option:

``` nix
   nixpkgs.config.packageOverrides = pkgs:
     {
     # we use this guide as inspiration
     # https://debian-administration.org/article/377/Routing_for_multiple_uplinks

       iproute = pkgs.stdenv.lib.overrideDerivation pkgs.iproute (attrs: {
         postInstall = ''
           echo 13 eno1 >> $out/etc/iproute2/rt_tables
           echo 14 enp2s0 >> $out/etc/iproute2/rt_tables
         '';
         # if I wanted to append iproute's postInstall phase,
         # I would also concat attrs.postInstall to this.
         # Also note we don't want ${attrs.out} here, explained a paragraph below
         });
     };
   
```

Notice, the assignment is itself a function that takes an argument. In this case, it is pkgs, but I could've named it bananas if I wanted to. Further, overrideDerivation is a function that itself takes a package and a function. This new function, prefixed with attrs: in the code block above, takes the attribute set and returns a new one. This allows me to add in the attributes of the stock derivation, if I wanted to. In this case, iproute doesn't even _have_ a postInstall section, so I do not include it.

Further, I explicitly do not want the $out from attrs, so I don't use ${attrs.out} as that would refer to the stock derivation when I want to refer to the modified one. I tripped up on this as well, but this changes the hash and in a sort of rabbit pulling out the magician trick, we attempt to modify the old derivation, which, for reasons above, just don't work.

# Conclusions

Check the the manual first. While it wasn't difficult to devise my own way, if I wasn't stopped by the file system, I might've done it this way. Sure, it'd work, but it would also necessitate bundling a shell script to do this on rebuild. I would run into the problem of figuring out when this ran, if for example installing something else caused ip's routing table to instantiate before the script ran, suddenly openvpn is down, one of the interfaces is giving me bogus packets, the toast is burning, and I'm on my knees restarting the thing and hoping the problem goes away. 

All in all, though, I'm immensely proud of figuring this out (and I intend to add the dual NIC bit to the manual once I can condense this long commentary into terse, cold instruction). Strangely enough, since the only flag modified is postInstall and thus postCompilation, there is no need for nix to compile it again. Maybe I'd raise an issue, but on the other hand I just love watching all the text scroll by.
