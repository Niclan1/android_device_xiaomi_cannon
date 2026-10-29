/* Copyright (C) 2026 The LineageOS Project
 * SPDX-License-Identifier: Apache-2.0
 *
 * MTK libpkm embeds libpcap 1.8's three-argument interface enumeration caller.
 * Current libpcap has an opaque list and a required extra-flags callback. Use
 * its real enumerator; preserve the old caller's filter and basic flags.
 */
#include <errno.h>
#include <pcap-int.h>

/* Exact private layout from the pinned libpcap pcap.c, checked by our tests.
 * Keep it local: no platform header/API or global libpcap change is required.
 */
struct pcap_if_list {
    pcap_if_t *beginning;
};

static int retain_legacy_flags(const char *name, bpf_u_int32 *flags, char *errbuf) {
    (void)name;
    (void)flags;
    (void)errbuf;
    /* The old ABI has no extra-flags provider. The real enumerator already
     * derives LOOPBACK/UP/RUNNING from getifaddrs; leave those unchanged.
     */
    return 0;
}

int pcap_findalldevs_interfaces(pcap_if_t **output, char *errbuf,
                              int (*check_usable)(const char *)) {
    struct pcap_if_list devices = {0};
    if (!output || !errbuf || !check_usable) {
        errno = EINVAL;
        return -1;
    }
    int result = pcapint_findalldevs_interfaces(&devices, errbuf, check_usable,
                                               retain_legacy_flags);
    if (result < 0) {
        pcap_freealldevs(devices.beginning);
        devices.beginning = NULL;
    }
    *output = devices.beginning;
    return result;
}
