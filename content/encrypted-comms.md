Title: Encrypted communication without host service disruption
Date: 2017-04-22 20:47
Tags: nixos, networking
Slug: encrypted-comms

Suppose you're in my shoes: you have a home machine operating as a central point of services for my -- err, your family.

One such service you'd like is the ability to provide anonymity and security for all residents. In order to do this, you need some VPN provider (either self hosted or commercial). 

How would you expose this endpoint to others in the network, so that they can utilize it without losing access to other services that are hosted in the clear?

If I was in your shoes, I would have to ignore the routes pushed by the provider. This breaks things in weird ways, but that's usually the first step to anything interesting.

You can do this by setting `route-nopull` in the openvpn config file. Even though the server still pushes them, the client just ignores them. You can still communicate with the endpoint, but any traffic not directed at the endpoint goes to your regular default gateway. This leads to surprising results:

``` bash
ip addr show enp2s0 | grep inet
# inet 192.168.1.5/24 scope  global enp2s0

ip addr show tun0 | grep inet
# inet 10.1.1.16/16 brd 10.1.255.255 scope global tun0

# ping some host on the same LAN running tcpdump using the interface of tun0
ping -I 10.1.1.16 192.168.1.25
```

On root@192.168.1.25:
``` bash
  tcpdump -i any icmp
  # 18:33:30.148705 IP 10.10.1.16 > 192.168.1.25: ICMP echo request, id 10830, seq 1, length 64
  # 18:33:30.148806 IP 192.168.1.25 > 10.10.1.16: ICMP echo reply, id 10830, seq1, length 64
  # 18:33:30.150079 IP 10.10.1.16 > 192.168.1.25: ICMP 10.10.1.16 protocol 1 port 16982 unreachable, length 36
```

Now I'd love to tell you exactly what shenanigans are going on here. My best guess is that the net-facing interface rejects these packets, but if you stay on the line you'll get ICMP unreachables from addresses beyond the next hop.

The point is, there needs to be some way to keep tunnel traffic and regular traffic separate. And there is!

The first thing you need are tables in '/etc/iproute2/rt_tables'. We've covered how to do this before in the paradigm of NixOS, and in true bleeding edge tech fashion the article is no longer relevant. In fact plans are underway to integrate iproute as a NixOS module, providing for an easier interface to.. er.. interface configuration.

Assuming you have two clean tables labelled normal-table and tunnel-table:
``` bash
# root@server

# this adds the directive that routes all packets sent to
# normal-table has a default-gateway of $lan_gateway
ip route add default via $lan_gateway dev enp2s0 table normal-table

# this says "any packets from this IP address should be handled by
# whatever is in normal-table, AKA the route above.
ip rule add from $lan_local lookup normal-table
```

If you write this into networking.localCommands, make sure to wrap this with a lockfile, otherwise you can't switch into a new configuration after any changes to it.

Implement the same set of commands in the up script of the tunnel:
```
ip route add default via $tunnel_gateway dev tun0 table tunnel-table
ip rule add from $tunnel_local lookup tunnel-table

echo -n "$tunnel_local" >> /tmp/tunnel.addr  # ooh, what could this be?
```

And that's it. All packets originating on the vpn interface get sent to the VPN interface. All packets otherwise are sent to the lan.

# Bonus: static NAT
You.. didn't think I wrote this whole thing to show you four lines of bash, did you? 

The problem I was having that prompted this post was that I wanted certain services to bind to the tunnel IP. However, the IP is not consistent, it's effectively random each boot. I needed to know the address beforehand. Since NixOS modules are _not_ derivations but just regular attribute sets that implement commands, I can't override them like we did in the last post. There was no way around it without rewriting the entire NixOS module into my config and using that instead of the provided one, which would mean I would have to watch for and manually apply all upstream changes.

I could, of course, pull in the changes and merge my tweaks into it, but... that sounds like a Y problem.

Here's the satisfying (NixOS) alternative.
``` nix
  systemd.services.staticAddr = {
    description = "Provide static address to openvpn tunnel";
    # in this case, the bindsTo is moot: when the service comes down 
    # the whole interface comes down anyway.
    bindsTo = [ "openvpn-tunnel.service" ];
    after = [ "openvpn-tunnel.service" ];
    
    # if no service needs this one, it won't be executed. Uncomment the
    # below to have it executed regardless.
    # wantedBy = [ "multi-user.target" ];

```

We can use iptables to 'alias' a static address to the dynamic one, so that to any programs (or clients) on the server, it remains consistent throughout reboot. 


``` nix

       serviceConfig = let
         sh = "${pkgs.stdenv.shell}";
         ip = "${pkgs.iproute}/bin/ip";

         # resist the temptation to use a local address in 127/8.
         # it does not end well: https://serverfault.com/a/416669
         # just choose something that fits your fancy in the other IP classes.
         addr = "10.192.8.1";
         cidr = "/32";
         devName = "tun0";
         iptables = "${pkgs.iptables}/bin/iptables";

         # we could also use an environmental file here, but I don't
         tunAddress = "$(cat /tmp/tun255.addr)";

         # we want a new chain to add the SNAT rule
         # so that when this service goes down we just delete the chain
         # instead of having to flush all of POSTROUTING 
         chainName = "staticAddr";
         mkChain = "${iptables} -t nat -N ${chainName}";
         delChain = "${iptables} -t nat -X ${chainName}";
         # since we have the interface rule set already (check upscript of tunnel)
         # we can just add it to our new address.
         rule = "from ${addr} lookup tun255-table";
         
       in
       {
         # SNAT takes packets headed to one interface and rewrites the source
         # address before forwarding them. So packets that originate from 
         # our static IP actually leave our machine with the dynamic IP.
         ExecStart = ''
           ${sh} -c '${ip} rule add ${rule} && \
             ${ip} addr add ${addr}${cidr} dev ${devName} && \
             ${mkChain} && \
             ${iptables} -t nat -A ${chainName} -s ${addr} -j SNAT --to ${tunAddress} && \
             ${iptables} -t nat -A POSTROUTING -j ${chainName}'
         '';
         ExecStop = ''
           ${sh} -c '${ip} rule del ${rule} && \
             ${ip} addr del ${addr}${cidr} dev ${devName} && \
             ${delChain}'
         '';
         Type = "oneshot";
         RemainAfterExit = true;
       };
     };

  boot.kernel.sysctl = {
    "net.ipvr.conf.tun0.forwarding" = true;
  };
```

Fun fact: iptables chains are the only consistent demonstration of magic observed by researchers.
