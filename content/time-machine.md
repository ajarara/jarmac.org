Title: Deploying a macOS Time Machine server in 42 lines of Nix
Date: 2017-04-25 16:41
Category: nixOS
Slug: time-machine

### Douglas Adams would be proud.

Time Machine is a proprietary backup program that provides a great interface to a rather expensive physical backup solution. It is installed by default on recent-ish[^1] versions of macOS.

[^1]: Anything beyond 10.5 Leopard

After some investigation I found that even though the interface is proprietary, the backend is free, open source software. All it takes is someone to glue the code together, and a machine with enough disk space:

![3asirah is a small village in Palestine, named for its olive oil industry](/images/time-machine.png)


I've done this before using Docker, which had its issues, but they weren't Docker-specific:

I had to make sure both Docker and users had permission to read, write, execute their stuff. User GIDs needed to be consistent across the host and across the container. Avahi loses its functionality when put in a container unless you have a _very_ creative networking setup. Since we need to break the file system and network encapsulation layers anyway, this kind of service really doesn't belong in a container. Especially since the Nix packaging system is so good at handling the dependency problem. [^2]

[^2]: It's interesting thinking about containers vs Nix. On the one hand, they both solve the dependency resolution problem. However, that's where they diverge. Stock NixOS doesn't care about other forms of encapsulation. It focuses more so on build management and configuration. In this case NixOS is the clear choice.

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
      mimic model = TimeCapsule6,106  # show the icon for the first gen TC
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
  
  users.extraUsers.macUser = { name = "${user}"; group = "users"; };
  systemd.services.macUserSetup = {
    description = "idempotent directory setup for ${user}'s time machine";
    requiredBy = [ "netatalk.service" ];
    script = ''
     mkdir -p ${timeMachineDir}
      chown ${user}:users ${timeMachineDir}  # making these calls recursive is a switch
      chmod 0750 ${timeMachineDir}           # away but probably computationally expensive
      '';
  };
  
  networking.firewall.allowedTCPPorts = [ 548 636 ];
}
```
Yes, I counted the line breaks.

# How?
Nix does everything: it pulls in netatalk and avahi[^3], opens the right firewall interfaces, and registers and multicasts the service. It just works.

[^3]: Since we're not adding any compile flags, we get to pull the binaries from the nixpkgs cache.

Netatalk implements the Apple Filing Protocol (afp), which is what Apple uses on their own Time Capsules. The config was easy enough to understand: I lifted it from [an old guide](https://kremalicious.com/ubuntu-as-mac-file-server-and-time-machine-volume/) on how to do this on stock Ubuntu. 

In some cases, the NixOS interface for configuration of a service boils down to attribute sets where the maintainer of the module created attribute sets for the things they needed, and extraConfig for all the other cases. I like this, because it allows things to [be implemented gradually](https://news.ycombinator.com/item?id=12337549).

Setting up Avahi is, of course, simple. It is after all an implementation of the [zero-conf spec](https://en.wikipedia.org/wiki/Zero-configuration_networking#Avahi). The relevant portion that requires some config is enabling user service publishing[^4]


[^4]: The publish.enable part enables publishing generally. It is not implied by other settings which is a little strange as [setting `publish.userServices` implies `publish.addresses`](https://github.com/NixOS/nixpkgs/blob/e74ea4282a7922fd73655de863315854d322ea8d/nixos/modules/services/networking/avahi-daemon.nix#L132).

The rest is user and directory management, which are admittedly weak points discussed below.

## Gotchas:
### Credentials
I haven't figured out how to allow people to modify their passwords from the Time Machine client yet. It's possible to set initial[Hashed]Password for a user in NixOS, but this comes with the caveat that [this info is readable by any program (or user).](https://github.com/NixOS/nix/issues/8)

So far I've tried setting users.mutableUsers and an initialHashedPassword in order to prod the Time Machine client to allow client side password changes, but that didn't work. Short of giving clients ssh access (which is not desirable) I'm not sure how else to do it.

So for now I had people enter their own logins into a passwd prompt on my machine. This is more than jarring from a security standpoint, and is probably going to be the next point of improvement. Thankfully the encryption password is set client side.

### userAccountsLookLikeThis
GNU/Linux (rightfully) doesn't allow usernames to have literal spaces in them. Fine by me, but a little jarring when logging in the first time.

### Multi user support?
As of right now all I do is make the changes manually. That is, for each user I create a setup systemd service and an afpd entry. It's not hard to imagine a scenario where all I have to do is add a user, directory, and size limit attribute set to a list, nixos-rebuild and allocate some more, but I only have 4 machines that need this. So yes, there is multi user support, but it's mostly manual (and convenient enough).

Further, adding multiple users requires a reload of the configuration, and thus the daemon. In an enterprise environment where users are added all the time, this is a serious problem.
### Aren't you forgetting to open UDP for avahi?
[Nope!](https://github.com/NixOS/nixpkgs/blob/07cc3eb0d005938fa44a0580688400f0129efbd7/nixos/modules/services/networking/avahi-daemon.nix#L228)
The only other module I know of that does its own firewall configuration is SSH.

### Directory management
Directory management is... uncomfortable on NixOS. While declaring a service isn't all _too_ bad, one problem I can see is that if someone decides to mess around server side with directory permissions, there is no way to recover besides doing it manually (or making the idempotent calls recursive). This is not the case with processes: all the stuff in RAM is ephemeral. I mean it makes sense that Nix, as a a functional language, isn't the best at handling persistent state. 

## Addendum: Taking down all server config from GitHub
I've been pushing these commits to a public repo. Of course, like any sane person, I have relevant secrets on a gitignore, but now that I have the names of my family and some aspect of their usage patterns I've decided it is best to take the code down. I'll still post useful[^5] snippets here, and in repos. This allows people to get useful material out without having access to private-ish information, which was my intent anyway.

[^5]: This is almost certainly the first post I've written that isn't completely useless.
