Title: VPN's in 60 seconds
Date: 2017-04-05 17:03
Status: draft
Tags: networking
Slug: vpn-in-a-nutshell

# Motive
With the recent US legislation geared towards dismantling the regulations surrounding carriers and their access to our information, there is more and more need for privacy online. One intermediary solution is to use a VPN. This post makes no attempt to discern if these efforts are  [fruitless](https://asininetech.com/2017/03/28/vpns-are-not-the-solution-to-a-policy-problem/) or [otherwise](https://journal.standardnotes.org/vpns-are-absolutely-a-solution-to-a-policy-problem-3b88af699bcd) but there is value in showing how one could set up a NixOS container that only has access to an arbitrary interface (ie, a virtual tunnel leading to a certain 51st state).


In [the previous post](https://jarmac.org/starting-nix.html), we went over how to modify iproute2's derivation to get routing on multiple interfaces with policy based routing. This step is necessary to get where we want to go: an interface that sends our traffic to Canada without interfering with the routing of the host.


# VPN routing (in 60 seconds or less)
All the IP addresses on a machine's interfaces are associated with a network, a range of addresses it 'knows about'. If a packet is created with a destination in the range an interface knows about, the packet is sent over that interface. But if the destination address is not in these ranges, the packet is sent to the default gateway, with the hope that it knows how to get there. From there, there are more sophisticated routing mechanisms that get the packet where it wants to go.

The way a VPN is usually used is that the remote endpoint creates an encrypted tunnel from us to itself, and pushes routes saying "I know about _all_ addresses except for my own, so send all packets through this tunnel."

Packets sent through the tunnel are actually transformed by the OS into packets being sent entirely to the remote endpoint, so that no matter where they are visiting (provided any of the machine doesn't 'know about' it already), all the packets are sent out our previous default gateway to the remote endpoint. Once they get there, they are changed back into regular packets with the destination we want, unencrypted, and when the server responds, those packets undergo the reverse transformation to get back to our machine.

Alternatively, in crude diagram form:

![Image missing? Let me know ajarara@jarmac.org](/images/vpn-nutshell.jpg)


Situation: We've just clicked share on this gorgeous cat.

1. The computer sends an encrypted packet to the VPN server containing the address and a further encrypted payload (that says "share this cat")
2. The VPN server decrypts the packet, and forwards it to twitter, but can't decrypt the payload (only twitter can do that)
3. twitter.com recieves the request, decrypts the payload, handles the share action and sends an acknowledgement to the VPN server
4. The VPN server recognizes this packet is ours, and sends it back to the machine.

No direct traffic occurs between us and twitter in this scenario. If we hadn't logged in, twitter would have no idea it was us without cooperation with the VPN provider.

