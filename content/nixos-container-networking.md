Title: Container networking with NixOS
Date: 2017-04-05 15:49
Tags: nixos networking systemd-nspawn
Status: Draft
Slug: nixos-container-networking

# Containers and Back Again
NixOS provides an interface to systemd-nspawn, a container-like implementation. If you've got systemd, you very likely already have -nspawn. The man page for nspawn [and this (admittedly 3.5 year old) presentation](https://youtu.be/s7LlUs5D9p4?t=381) both warn that the implementation is not for deploying apps meant to be secure. Since I'm still green with containers, I'll stick to using them here, as usage is dead simple.

Nix solves the dependency problem. 
# So let's boot up a web service

``` nix
     systemd.services.myWebApp = {
      description = "A simple greeting";
      wantedBy = [ "multi-user.target" ];
      script = ''
        while true; do echo "Hello, world!" | ${pkgs.netcat}/bin/nc -l -p 12345; done
      '';
    };
    # this next line is to allow other hosts access
    networking.firewall.allowedTCPPorts = [ 12345 ];
```

And now from both within the host and on the lan:
``` bash
curl $server_ip:12345
# Hello, world!
```

This app doesn't _need_ access to our filesystem or any IPC. So let's throw it into a container:


``` nix
```




# __OLDER__
- Motive?
- Here's how nixos works
  - dabble with some idea
  - implement it on your own in some silly mock environment
  - see if there is a nixos interface for your idea.
  - if not, hack away at your own!
  
  - Systemd-nspawn nixos-containers
    - --network-veth option
    providing for full encapsulation of services including filesystem, pid namespacing, and network encapsulation.
  - Declarative vs imperative configuration of a container
    - Seems a strange interface to encourage the imperative style of configuration
    esp as the config itself is itself a nixos attribute
    - private interfaces provide network isolation, but you can prod stuff out using both nc and spiped
      Interestingly enough you can use nc to test if your spiped solution works, which is what I did (neat that a simpler tech allows you to bootstrap to a more robust one)
      `dd if=/dev/urandom bs=32 count=1 of=/tmp/keyfile.key`
      `spiped -d -s '[0.0.0.0]:9999' -t [127.0.0.1]:12345' -k /tmp/keyfile.key`
      `spiped -e -s '[127.0.0.1]:8999' -t [127.0.0.1]:9999 -k /tmp/keyfile.key`
      `echo "Hello world!" | nc -l 12345`
      
      Now hit localhost on 8999, and watch your request go through. The pipes (unlike netcat) are persistent, and we can redo the last command to verify. 
      
    - if you want bidirectional comms then you want a named pipe, using `mkfifo` but unfortunately where to put the pipe (as it is just a file) is an issue. 
    
- NixOS-containers are little more than a wrapper around 

# Outline
 - Simple myWepApp
 ``` nix
     environment.systemPackages = [
        pkgs.netcat
     ];
     systemd.services.myWebApp = {
      description = "A simple greeting";
      wantedBy = [ "multi-user.target" ];
      script = ''
        while true; do echo "Hello, world!" | ${pkgs.netcat}/bin/nc -l -p 12345; done
      '';
    };
 ```
 - Take it a step further and encapsulate it in a container:
 ``` nix
     containers.myWebApp = {
      autoStart = true;
      config = { config, pkgs, ... }:
      {
        environment.systemPackages = [
          pkgs.netcat
        ];
        systemd.services.myWebApp = {
          description = "A simple greeting";
          wantedBy = [ "multi-user.target" ];
          script = ''
            while true; do echo "Hello, world!" | ${pkgs.netcat}/bin/nc -l -p 12345; done
          '';
        };
        networking.firewall.allowedTCPPorts = [ 12345 ];
      };
    };
 ```
 One small nuance here: in this scenario it doesn't matter if you allow the port within the configuration of the container or on the host, they will be merged. This isn't the case if privateNetwork is set, though. At this point the firewall config must be on the host.
 
 - Locally:
 ``` bash
 curl 127.0.0.1:12345
 # Hello, world!
 ```
 - Remote: 
 ``` bash
 curl 192.168.5.151:12345
 # Hello, world!
 ```
 
 - But something bothers me about full network access. In this case it is clearly benign (and systemd-nspawn's man page is quick to add the disclaimer that these containers aren't guaranteed to be secure).
   - Strange that the sole interface to containers is nspawn, not something like rkt. HN and IRC had little to say about it.
     - rkt homepage points to usage in nixos. INVESTIGATE.
       - https://github.com/NixOS/nixpkgs/tree/master/pkgs/applications/virtualization
       - integrated as a module here: https://github.com/NixOS/nixpkgs/blob/fb50cde71e3ffd149faca1a1762c245542a24875/nixos/modules/virtualisation/rkt.nix
       - not documented in the manuals
 - Virtualize network
   - Point out how internet connectivity is lost now
     - This requires NAT!
       - Why is it not working? I can't even get the tagged solns working.
     - NAT makes it difficult to access the resource again.
  - Alternative sol'n
    - remove container abstraction? optional.
    - bind service to localhost and use spiped to forward connections
        - spiped is useful. mandates encryption 
      - is this possible with a networked host behind a NAT?


# __ OLD __
# Draft
NixOS provides a declarative interface to systemd-nspawn, which is systemd's implementation of the oh-so-hot container tech. Politics aside (which naturally arises for any program satisfying `/^systemd-/`), nspawn's very easy to use. ${DISCLAIMER}
One thing it does not provide for, however, is virtualization of the network. To do this, pass [--network-veth](https://www.freedesktop.org/software/systemd/man/systemd-nspawn.html), but now you've lost a whole lot. In order to communicate with the host, you must provide routes. This is precisely what docker does: create a virtual interface on the host, route an entire subnet (172.17.0.0/16) out that interface, and configure all hosts to point to it:
``` bash
docker run -ti alpine sh  # alpine image has iproute2 baked in
# inside the container
ip addr
# 1: lo: <snipped>
# 18: eth0@if19: <BROADCAST,MULTICAST,UP,LOWER_UP,M-DOWN> mtu 1500 qdisc noqueue state UP 
#     link/ether 02:42:ac:11:00:02 brd ff:ff:ff:ff:ff:ff
#     inet 172.17.0.2/16 scope global eth0
#        valid_lft forever preferred_lft forever
#     inet6 fe80::42:acff:fe11:2/64 scope link 
#        valid_lft forever preferred_lft forever
ip route
# default via 172.17.0.1 dev eth0 
# 172.17.0.0/16 dev eth0  src 172.17.0.2 
```
nspawn does not do this. By default, it utilizes the network already set up on the host, and thus can [listen on privileged ports](http://nixos.org/nixos/manual/index.html#sec-declarative-containers). Providing --network-veth removes access to all interfaces and even virtualizes the loopback interface, providing an interface on the host, and an interface in the container. Security paranoia notwithstanding, this container is now a discrete host.

NixOS declarative container configuration is delightful:
``` nix
   containers.host = {
     autoStart = true;
     privateNetwork = true;
     localAddress = "10.171.1.2";
     hostAddress = "10.171.1.1";
     config = { config, pkgs, ... }:
     {
       services.nginx.enabled = true;
       services.nginx.config = '' ... '';
     };
   };
```

This snippet does (almost) precisely what docker does for you: generate a container with the addresses you give it and provide routes to and from the interface.
The difference here is that docker generates one interface on the host, and all containers communicate with the same interface. This is probably done so that communication between them is simple(r).

However, attempts to reach other interfaces fail:
``` bash
nixos-container root-login host
# within the container

ping -c 4 192.168.5.151

# PING 192.168.5.151 (192.168.5.151) 56(84) bytes of data.
# 
# --- 192.168.5.151 ping statistics ---
# 4 packets transmitted, 0 received, 100% packet loss, time 3097ms
```

What's going on here?
 - What's this article's scope?
   - Container networking?
     - Docker style networking setup?
     
   - NAT through an openvpn provider?
   - spiped as a solution to network encapsulation?
 - Figure out the networking problem. The tags aren't right.
 - Sleep well.

# Draft
- Breaking the rules
  - Add the openvpn directive 
  - Go over [here](https://community.openvpn.net/openvpn/wiki/IgnoreRedirectGateway).
  - Utilization of 10.0.0.0/8 space.
  - Nat breaks this 
  - NAT to the day. 
# Breaking the rules

Most VPN providers send their customers a config file ending in .ovpn or .conf. Add ```route-nopull``` to this file. When this directive is set, the openvpn client reading the file will ignore all routes pushed by our provider, but will still set up the connection. This means any communication between us and someone else won't be sent to the provider, but will behave normally. 

This seems like what we want, at this point we should be able to send and recieve packets from our machine to the remote endpoint (aka peer). But since we ignored the routes put forth by the server, trying to connect beyond it won't work:

``` bash
# where 10.30.0.2 is the IP address of our end of the tunnel
ping -c4 -I 10.30.0.2 example.com
```

Suppose you owned example.com. If you listened on the external interface for 
CONTINUE HERE.

# wait for d/o to come back up to test
Will fail. In fact, if this machine wasn't behind a NAT, example.com would get these packets and have no idea what to do with them.

% insert picture of delivery here. To: Stomach, From: Mouth ?%


Set up policy based routing on the VPN interface.
after messing about a ton with bridges and GRE tunnels, I reached for NAT.
Set up NAT
possibly allude to how tcpdump saved my skin loads of times.
Set up a privateNetwork
Set up a service controlling the container binding it to the interface (optionally), but it should be after.
admit defeat Type/RemainAfterExit dancing

Show it works

the nixos/systemd integration made it very easy to do what I wanted. There are some strange quirks (anything in the serviceConfig attrib set is not camel case anymore) but they are minor.

A couple of pain points:
difficult to tell if nat is up and working. if it doesn't work, then we're bleeding out traffic. see if we can modify the service file to do this.
difficult to tell if 
