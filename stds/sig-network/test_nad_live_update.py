"""
Live Update NAD Reference on Running VM Tests

STP Reference: stps/sig-network/nad-live-update-stp.md
Jira: CNV-72329
"""


class TestNADLiveUpdateE2E:
    """
    Tests for live update of NAD reference on a running VM's secondary network interface.

    Markers:
        - tier2

    Preconditions:
        - Two bridge-based NADs deployed on each worker node (nad1, nad2)
        - Running VM with secondary bridge interface on nad1
        - Peer VM running on nad2
        - MAC address and interface name of secondary interface recorded
    """
    __test__ = False

    def test_e2e_nad_change_connectivity(self):
        """
        Test that a VM gains connectivity on the new network after NAD change.

        Preconditions:
            - No connectivity to peer VM on nad2 (baseline)

        Steps:
            1. Patch VM spec to change NAD reference from nad1 to nad2
            2. Wait for update to complete

        Expected:
            - Ping from VM to peer VM on nad2 succeeds with 0% packet loss
        """

    def test_recovery_after_failed_nad_update(self):
        """
        [NEGATIVE] Test that VM recovers after a failed NAD update to a non-existent NAD.

        Steps:
            1. Patch VM spec to change NAD reference to non-existent NAD name
            2. Patch VM spec to change NAD reference to valid nad2

        Expected:
            - Error condition is reported for non-existent NAD
            - VM is "Running" and connected to nad2 after valid change
        """

    def test_hotplug_then_nad_change(self):
        """
        Test that NIC hotplug and NAD change coexist on the same VM.

        Steps:
            1. Hotplug a new bridge interface to the VM
            2. Patch VM spec to change NAD reference on existing secondary interface

        Expected:
            - Hotplugged interface reports valid IP address
            - Original secondary interface is connected to new NAD
        """

