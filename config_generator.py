def make_config(hostname, interfaces, mpls, ospf_pid, ospf_area, asn, bgp):
    return f"""!
version 15.2
service timestamps debug datetime msec
service timestamps log datetime msec
!
hostname {hostname}
!
boot-start-marker
boot-end-marker
!
no aaa new-model
no ip icmp rate-limit unreachable
ip cef
!
no ip domain lookup
no ipv6 cef
!
{"mpls label protocol ldp" if mpls else ""}
multilink bundle-name authenticated
!
ip tcp synwait-time 5
!
{"" if bgp is not None else ""}
{make_interfaces(hostname, interfaces, mpls)}
{make_ospf(interfaces, ospf_pid, ospf_area)}
{make_bgp(interfaces, asn, bgp)}
!
ip forward-protocol nd
!
no ip http server
no ip http secure-server
!
control-plane
!
line con 0
 exec-timeout 0 0
 privilege level 15
 logging synchronous
 stopbits 1
line aux 0
 exec-timeout 0 0
 privilege level 15
 logging synchronous
 stopbits 1
line vty 0 4
 login
!
end
"""


def make_interfaces(src, interfaces, mpls):
    config = ""
    i = 1
    for dst, (ip, subnet) in interfaces.items():
        if src == dst:
            config += f"""interface Loopback0\n  ip address {ip} {subnet.netmask}"""
        else:
            config += f"""interface GigabitEthernet{i}/0\n ip address {ip} {subnet.netmask}\n negotiation auto"""
            if mpls:
                config += "\n mpls ip"
        config += "\n!\n"
        i += 1
    return config


def make_ospf(interfaces, ospf_pid, ospf_area):
    (ip, subnet) = list(interfaces.values())[0]
    config = f"router ospf {ospf_pid}\n router-id {ip}\n"
    for _, (ip, subnet) in interfaces.items():
        config += f" network {ip} {subnet.hostmask} area {ospf_area}\n"
    return config


def make_bgp(interfaces, asn, bgp):
    (ip, subnet) = list(interfaces.values())[0]
    config = f"router bgp {asn}\n bgp router-id {ip}\n bgp log-neighbor-changes"

    return config
