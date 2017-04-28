Title: Deploying a macOS Time Machine server in 42 lines of Nix
Date: 2017-04-27 16:42
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
      set password = yes
    [${user}'s Time Machine]
      path = ${timeMachineDir}
      valid users = ${user}
      time machine = yes
      vol size limit = ${sizeLimit}
    '';
  };
  users.extraUsers.macUser = {
    name = "${user}";
    group = "users";
    initialHashedPassword = "$6$vLd1Li[...]FKTfZ6Ut.";
  };
  systemd.services.macUserSetup = {
    description = "idempotent directory setup for ${user}'s time machine";
    requiredBy = [ "netatalk.service" ];
    script = '' mkdir -p ${timeMachineDir}
                chown ${user}:users ${timeMachineDir}
                chmod 0750 ${timeMachineDir} '';
  };
  networking.firewall.allowedTCPPorts = [ 548 636 ];
}
```
Let's uh...  overlook the fact that the `script` assignment is a bit loose with its concept of lines.


# The Module in Chunks
Nix does everything: it pulls in the netatalk and avahi binaries from the cache, opens the right firewall interfaces, and registers and multicasts the service. It just works. If we wanted to add an additional configure flag, we'd set it in `nixpkgs.package.overrides` which expects a function that is passed the old attributes. We could add or filter from that list and make our new configure flags. We could even swap out sources for a new version, preserving everything else. In this case the avahi flag is set, as is SSL. So no need to recompile.

When you set an enable flag for a module, a lot happens. Setting `services.netatalk.enable = true;` allows code to execute in the nixOS implementation of the module. In this case, [here](https://github.com/NixOS/nixpkgs/blob/09a9a472ee783b40c2a3dd287bbe9d3c60f8fc58/nixos/modules/services/network-filesystems/netatalk.nix#L122). This is the basis for having the OS be backed by a lazy language, if the condition fails at NixOS-build time, there is no need to evaluate the result. Enable usually says 'enable this systemd service'. The enable phase needs pkgs.netatalk to have been evaluated, so it evaluates the derivation, which means pulling it from a cache or compiling it itself.

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

But there is _some_ config necessary, and that's to do with what service can register. Enabling netatalk and an admittedly naive `services.avahi.enable = true;` gives an error in the afpd logs complaining of entry group permissions. 'Entry' didn't seem like a directory permissions issue, so like any computer wiz worth their salt I looked it up, and found [the issue](https://bugs.launchpad.net/ubuntu/+source/netatalk/+bug/841772). This config addresses that.


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
      # this allows users to change their password from the client side
      set password = yes
      
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

In this case, I could've configured the Time Machine directive as [a volume](https://github.com/NixOS/nixpkgs/blob/09a9a472ee783b40c2a3dd287bbe9d3c60f8fc58/nixos/modules/services/network-filesystems/netatalk.nix#L93). That wouldn't give me much beyond having myself and the reader go through how it's mapped to the config, but it is available so I figured it best to link it.

## User declaration

``` nix
  users.extraUsers.macUser = {
    name = "${user}";
    group = "users";
    initialHashedPassword = "$6$vLd1Li[...]FKTfZ6Ut";
  };
```
User configuration is so varied that it might be best just to refer you to the [module itself](https://github.com/NixOS/nixpkgs/blob/77f572f07234e500d0d3aeecd03a2af96cc3da06/nixos/modules/config/users-groups.nix).

One portion that warrants discussion is the password hash. This is output from `mkpasswd -m sha512 <password>` and is convenient if you want to reset the user account (you can do this by just deleting the user the standard unix way, and rebuild the configuration). Make sure users.mutableUsers is true (as of 4/27/17 that is the default).
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
The reason I inline it here is to show the current iteration of what I do to ensure directory structure is set up for services. This only needs to be done once, so one restriction is that any config run 1,000,000 times results in the same as if it is done once.

Of course, the simplest method is to go in there and prep the directory structure by hand, but that just isn't satisfying (although it is idempotent!)

This... is tricky. As it is now, the service runs each boot. The more the config grows the longer it takes to start up. I could set up a lockfile that represents that the setup service has been set up, but what if the setup service changes? I'd have to go in there and remove the lockfile, or change it. An alternative is to do some ctime ([creation time](https://en.wikipedia.org/wiki/Stat_(system_call))) check of the service file and compare them with the service mtime. I'm not all too sure of the semantics of how to handle this with systemd, much less with systemd backed by symlinks, so I'll let the sleeping beast lie on this one.


# Gotchas:
While this is an almost full featured service, there are a couple things that would make this something to really be proud of.
## Credentials
While I figured out how to allow people to modify their passwords from the client, the problem still remains that the hash is readable by any malevolent binary (or user) in the store. Obtaining the hash then makes users susceptible to a dictionary attack (as was pointed out to me on freenode's #nixos by 'clever'). Management of secrets in the store is a [long standing problem](https://github.com/NixOS/nix/issues/8).[^5]

[^5]: Movie executives: "Issue 8" would make for a fantastic thriller title. Just _please_ don't remake Swordfish.

So the point discussed above remains, make the initial password something the user is guilty not changing. Their guilt is worth your sleep.

## userAccountsLookLikeThis
GNU/Linux (rightfully) doesn't allow usernames to have literal spaces in them. Fine by me, but a little jarring when logging in the first time.

## Multi user support?
As of right now all I do is make the changes manually. That is, for each user I create a systemd service and an `afp.conf` entry. It's not hard to imagine a scenario where all I have to do is add a user, directory, and size limit attribute set to a list, nixos-rebuild and the new user is added, but I only have 4 machines that need this. So yes, there is multi user support, but it's mostly manual (and convenient enough).

One big issue is that adding new users requires a reload of the configuration, and thus the daemon, cutting off anyone who is backing up. In an enterprise environment where users are added all the time, this is a serious problem.
## Aren't you forgetting to open UDP for avahi?
[Nope!](https://github.com/NixOS/nixpkgs/blob/07cc3eb0d005938fa44a0580688400f0129efbd7/nixos/modules/services/networking/avahi-daemon.nix#L228) The service declaration does that for me, saving me a whole line.
The only other module I know of that does its own firewall configuration is SSH. This one is a pleasant surprise.


# Addendum: Taking down all server config from GitHub
I've been pushing these commits to a public repo. Of course, like any sane person, I have relevant secrets on a gitignore, but now that I have the names of my family and some aspect of their usage patterns I've decided it is best to take the code down. I'll still post useful[^6] snippets here, and in [this repo](https://github.com/alphor/example-nixos-config). This allows people to get useful material out without having access to private-ish information, which was my intent anyway.

[^6]: This is almost certainly the first post I've written that isn't completely useless.
