def make_config(hostname, interfaces, border, ospf_pid, ospf_area, asn, vpn):
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
{"" if vpn is None else make_vrf(asn, vpn[hostname])}!
!
no ip domain lookup
no ipv6 cef
!
mpls label protocol ldp
multilink bundle-name authenticated
!
ip tcp synwait-time 5
!
{make_interfaces(hostname, interfaces, vpn)}!
{make_ospf(hostname, interfaces, ospf_pid, ospf_area, vpn)}!
{"" if vpn is None else make_bgp(hostname, interfaces, border, asn, vpn)}!
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


physical_mapping = {}


def make_interfaces(src, interfaces, vpn):
    config = ""
    i = 1
    for dst, int in interfaces[src].items():
        if src == dst:
            config += f"""interface Loopback0\n  ip address {int["addr"]} {int["subnet"].netmask}\n"""
        else:
            if src not in physical_mapping:
                physical_mapping[src] = {}
            physical_mapping[src][dst] = i
            config += f"""interface GigabitEthernet{i}/0\n"""
            vpnid = None
            if vpn is not None:
                for vpni in vpn[src]:
                    if vpni["client"] == dst:
                        vpnid = vpni["vpnid"]
            if vpnid is not None:
                # Rickin & Burst
                config += f""" ip vrf forwarding VPN{vpnid}\n"""
            config += f""" ip address {int["addr"]} {int["subnet"].netmask}\n negotiation auto\n"""
            if int["mpls"]:
                config += " mpls ip\n"
            i += 1
        config += "!\n"
    return config


def make_ospf(src, interfaces, ospf_pid, ospf_area, vpn):
    int = list(interfaces[src].values())[0]
    config = f"""router ospf {ospf_pid}\n router-id {int["addr"]}\n"""
    for dst, int in interfaces[src].items():
        # No ospf with client
        if vpn is None or dst not in map(lambda c: c["client"], vpn[src]):
            config += f""" network {int["addr"]} {int["subnet"].hostmask} area {ospf_area}\n"""
    return config


def make_bgp(src, interfaces, border, asn, vpn):
    int = list(interfaces[src].values())[0]
    config = f"""router bgp {asn}\n bgp router-id {int["addr"]}\n bgp log-neighbor-changes\n"""

    for client in vpn[src]:
        peer = interfaces[client["peer"]][client["peer"]]
        config += f""" neighbor {peer["addr"]} remote-as {asn}\n"""
        config += f""" neighbor {peer["addr"]} update-source Loopback0\n"""

    for copain in border:
        if src != copain:
            config += f""" neighbor {vpn[copain][0]["core_addr"]} remote-as {asn}\n"""

    for client in vpn[src]:
        config += f""" neighbor {interfaces[client["client"]][src]["addr"]} remote-as {client["client_asn"]}\n !\n"""

    # address-family ipv4
    config += f""" address-family ipv4\n"""
    for client in vpn[src]:
        peer = interfaces[client["peer"]][client["peer"]]
        config += f"""  neighbor {peer["addr"]} activate\n"""

    for copain in border:
        if src != copain:
            config += f"""  neighbor {vpn[copain][0]["core_addr"]} activate\n"""

    for client in vpn[src]:
        config += f"""  neighbor {interfaces[client["client"]][src]["addr"]} activate\n"""
    config += """ exit-address-family\n"""

    # address-family vpnv4
    config += f""" address-family vpnv4\n"""
    for client in vpn[src]:
        peer = interfaces[client["peer"]][client["peer"]]
        config += f"""  neighbor {peer["addr"]} activate\n"""
        config += f"""  neighbor {peer["addr"]} send-community extended\n"""
    config += """ exit-address-family\n"""

    for vpni in vpn[src]:
        # address-family vpn
        config += f""" address-family ipv4 vrf VPN{vpni["vpnid"]}\n"""
        client = interfaces[vpni["client"]][src]
        config += f"""  neighbor {client["addr"]} remote-as {vpni["client_asn"]}\n"""
        config += f"""  neighbor {client["addr"]} activate\n"""
        config += """ exit-address-family\n"""

    return config


def make_vrf(src_asn, vpn):
    config = ""
    for client in vpn:
        config += f"""ip vrf VPN{client["vpnid"]}
 rd {src_asn}:{client["vpnid"]}
 route-target export {src_asn}:{client["vpnid"]}
 route-target import {src_asn}:{client["vpnid"]}
"""
    return config
