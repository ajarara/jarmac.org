Title: Deploying a macOS Time Machine server in 42 lines of Nix
Date: 2017-04-25 22:04
Category: nixOS
Slug: time-machine

Douglas Adams would be proud.

Time Machine is a proprietary backup program that provides a great interface to a rather expensive physical backup solution. It is installed by default on recent-ish[^1] versions of macOS. Even though the interface is proprietary, the backend is free, open source software. 

[^1]: Anything beyond 10.5 Leopard

All it takes is someone to glue the code together, and a machine with enough disk space:

![3asirah is a small village in Palestine, named for its olive oil industry](/images/time-machine.png)


I did this before using Docker. I don't think Docker, or any container tech, is right for this.

In Docker's case, I had to make sure both it and users had permission to read, write, and execute their stuff. User GIDs needed to be consistent across the host and across the container. Further, Avahi loses its functionality when put in a container unless you have a _very_ creative networking setup. [^2] 

[^2]: I suppose it is possible if you bridged your interface and the Docker bridge (or veth, whatever you're using). This would mean exposing _every_ Docker service to your LAN, as that is what is needed to get broadcast packets to work.

Since we need to break the file system and network encapsulation layers anyway, putting this service in a container makes little sense. Especially since the Nix packaging system is so good at handling the dependency problem. 

The config is short, readable, and all in one file. If you're running NixOS, all you have to do is import the below to get one (changing relevant details like user, directory, allowed hosts, etc.).


``` nix
{ config, pkgs, ... }:
  let
    timeMachineDir = "/backup";
    user = "macUser";
    sizeLimit = "262144";
  in {
  services.avahi = {
    enable = true;
    publish = {
      enable = true;
      userServices = true;
    };
  };
  
  services.netatalk = {
    enable = true;
    extraConfig = ''
      mimic model = TimeCapsule6,106
      log level = default:warn
      log file = /var/log/afpd.log
      hosts allow = 192.168.1.0/24
    [${user}'s Time Machine]
      path = ${timeMachineDir}
      valid users = ${user}
      time machine = yes
      vol size limit = ${sizeLimit}
    '';
  };
  
  # see module in chunks section for an explanation of
  # why I put this in here. Otherwise not strictly necessary.
  users.extraUsers.macUser = { name = "${user}"; group = "users"; };
  systemd.services.macUserSetup = {
    description = "idempotent directory setup for ${user}'s time machine";
    requiredBy = [ "netatalk.service" ];
    script = ''
     mkdir -p ${timeMachineDir}
      chown ${user}:users ${timeMachineDir}
      chmod 0750 ${timeMachineDir}
      '';
  };
  
  networking.firewall.allowedTCPPorts = [ 548 636 ];
}
```
Yes, I counted the line breaks.

# The Module in Chunks
Nix does everything: it pulls in the netatalk and avahi binaries from the cache, opens the right firewall interfaces, and registers and multicasts the service. It just works. If we wanted to add an additional configure flag, we'd set it in `nixpkgs.package.overrides` which expects a function that is passed the old attributes. We could add or filter from that list and make our new configure flags. We could even swap out sources for a new version, preserving everything else. In this case the avahi flag is set, as is SSL. So no need to recompile.

When you set an enable flag for a module, a lot happens. Setting `services.netatalk.enable = true;` allows code to execute in the nixOS implementation of the module. In this case, [here](https://github.com/NixOS/nixpkgs/blob/09a9a472ee783b40c2a3dd287bbe9d3c60f8fc58/nixos/modules/services/network-filesystems/netatalk.nix#L122). This is the basis for having the OS be backed by a functional language, if expressions are special forms, so if the condition fails at build time, there is no need to evaluate the result. Enable usually says 'enable this systemd service'. The enable phase needs pkgs.netatalk to have been evaluated, so it evaluates the derivation, which means pulling it from a cache or if it's not available in the cache compiling it itself.

## Avahi zeroconf

``` nix
  services.avahi = {
    enable = true;
    publish = {
      enable = true;
      userServices = true;
    };
  };
```

Setting up Avahi is simple. It is after all an implementation of the [zero-conf spec](https://en.wikipedia.org/wiki/Zero-configuration_networking#Avahi). The relevant portion that requires some config is enabling user service publishing.[^3]

[^3]: The publish.enable part enables publishing generally. It is not implied by other settings which is a little strange as [setting `publish.userServices` implies `publish.addresses`](https://github.com/NixOS/nixpkgs/blob/e74ea4282a7922fd73655de863315854d322ea8d/nixos/modules/services/networking/avahi-daemon.nix#L132).

With Avahi, the onus is on the program and not the sysadmin to register where their services are at. This allows things to 'just work' on the client machine, as a service registers itself with Avahi, and Avahi multicasts[^4] the connection details out to the broadcast domain.

[^4]: I'm not really sure on the fundamental difference between ipv4 multicasting and ipv6, but Avahi implements mDNS which [does both](https://en.wikipedia.org/wiki/Multicast_DNS#Packet_structure).

But there is _some_ config necessary, and that's to do with what service can register. Enabling netatalk and an admittedly naive `services.avahi.enable = true;` gives an error in the afpd logs complaining of entry group permissions. 'Entry' didn't seem like a directory permissions issue, so like any computer wiz worth their salt I looked it up, and found [the issue](https://bugs.launchpad.net/ubuntu/+source/netatalk/+bug/841772). What is labelled a bug here is actually an optional feature of Netatalk, that the reporter worked around by simply disabling service registration with the -nozeroconf option. 


## netatalk (AKA afpd)

``` nix
  services.netatalk = {
    enable = true;
    
    # the first four lines are appended to the global section.
    # only the stuff after [${user}'s Time Machine] is user specific
    # further, comments MUST be on their own line. see:
    # http://netatalk.sourceforge.net/3.0/htmldocs/afp.conf.5.html
    extraConfig = ''
      # show the icon for the first gen TC
      mimic model = TimeCapsule6,106
      log level = default:warn
      
      # this helped me crack why zeroconf needed non-zero config
      log file = /var/log/afpd.log
      hosts allow = 192.168.1.0/24
      
    # this breaks us out of the global config. 
    [${user}'s Time Machine]
      path = ${timeMachineDir} 
      valid users = ${user}
      time machine = yes
       # in megabytes
      vol size limit = ${sizeLimit}
    '';
  };
```

Netatalk implements the Apple Filing Protocol (afp), which is what Apple uses on their own Time Capsules. The config was easy enough to understand: I lifted it from [an old guide](https://kremalicious.com/ubuntu-as-mac-file-server-and-time-machine-volume/) showing how to do this on stock Ubuntu. What Nix does here is generate a config file and pass the location of it in the store to the relevant netatalk binaries (that are also in the store).

## Filesystem structure
This is admittedly a weak point of Nix.

``` nix
  users.extraUsers.macUser = { name = "${user}"; group = "users"; };
  systemd.services.macUserSetup = {
    description = "idempotent directory setup for ${user}'s time machine";
    requiredBy = [ "netatalk.service" ];
    script = ''
     mkdir -p ${timeMachineDir}
      chown ${user}:users ${timeMachineDir}
      chmod 0750 ${timeMachineDir}
      '';
  };
```
The reason I inline it here is to show the current iteration of what I do to ensure directory structure is set up for services. This only needs to be done once, so one restriction is that any config run 1,000,000 times runs the same as if it is done once.

This... is tricky. As it is now, the service runs each boot. The more the config grows the longer it takes to start up. I could set up a lockfile that represents that the setup service has been set up, but what if the setup service changes? I'd have to go in there and remove the lockfile. An alternative is to do some ctime ([creation time](https://en.wikipedia.org/wiki/Stat_(system_call))) checks and compare them with the service mtime. I'm not all too sure of the semantics of how to handle this with systemd, much less with systemd backed by symlinks, so I'll let the sleeping beast lie on this one.

# Gotchas:
## Credentials
I haven't figured out how to allow people to modify their passwords from the Time Machine client yet. It's possible to set initial[Hashed]Password for a user in NixOS, but this comes with the caveat that [this info is readable by any program (or user).](https://github.com/NixOS/nix/issues/8)

The hash or the password is available in the store in plain text. If a malicious program/actor obtains the password, then it's game over. If a hash is exposed, then hope the password doesn't show up in a dictionary somewhere.

So far I've tried setting users.mutableUsers and an initialHashedPassword in order to prod the Time Machine client to allow client side password changes, but that didn't work. Short of giving clients ssh access (which is not desirable) I'm not sure how else to do it.

So for now I had people enter their own logins into a passwd prompt on my machine. This is more than jarring from a security standpoint, and is probably going to be the next point of improvement. Thankfully the encryption password is set client side.

## userAccountsLookLikeThis
GNU/Linux (rightfully) doesn't allow usernames to have literal spaces in them. Fine by me, but a little jarring when logging in the first time.

## Multi user support?
As of right now all I do is make the changes manually. That is, for each user I create a systemd service and an `afp.conf` entry. It's not hard to imagine a scenario where all I have to do is add a user, directory, and size limit attribute set to a list, nixos-rebuild and the new user is added, but I only have 4 machines that need this. So yes, there is multi user support, but it's mostly manual (and convenient enough).

One big issue is that adding new users requires a reload of the configuration, and thus the daemon, cutting off anyone who is backing up. In an enterprise environment where users are added all the time, this is a serious problem.
## Aren't you forgetting to open UDP for avahi?
[Nope!](https://github.com/NixOS/nixpkgs/blob/07cc3eb0d005938fa44a0580688400f0129efbd7/nixos/modules/services/networking/avahi-daemon.nix#L228) The service declaration does that for me, saving me a whole line.
The only other module I know of that does its own firewall configuration is SSH.

# Addendum: Taking down all server config from GitHub
I've been pushing these commits to a public repo. Of course, like any sane person, I have relevant secrets on a gitignore, but now that I have the names of my family and some aspect of their usage patterns I've decided it is best to take the code down. I'll still post useful[^5] snippets here, and in [this repo](https://github.com/alphor/example-nixos-config). This allows people to get useful material out without having access to private-ish information, which was my intent anyway.

[^5]: This is almost certainly the first post I've written that isn't completely useless.
