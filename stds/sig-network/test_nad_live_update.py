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
        - OpenShift cluster with OCP 4.22+ and OVN-Kubernetes
        - OpenShift Virtualization 4.22+
        - Multi-node cluster with 2+ schedulable worker nodes
        - Shared RWX storage for live migration
        - Two bridge-based NADs deployed on each worker node (nad1, nad2)
        - WorkloadUpdateMethods=LiveMigrate, VMRolloutStrategy=LiveUpdate
        - Running VM with secondary bridge interface on nad1
        - Peer VM running on nad2
        - MAC address and interface name of secondary interface recorded

    """
    __test__ = False

    def test_e2e_nad_change_connectivity(self):
        """
        Test that a VM gains connectivity on the new network after NAD change.

        Steps:
            1. Verify no connectivity to peer VM on nad2 (baseline)
            2. Patch VM spec to change NAD reference from nad1 to nad2
            3. Wait for update to complete

        Expected:
            - Ping from VM to peer VM on nad2 succeeds with 0% packet loss
        """

    def test_feature_gate_disabled_requires_restart(self):
        """
        Test that NAD change requires restart when feature gate is disabled.

        Preconditions:
            - LiveUpdateNADRef feature gate disabled

        Steps:
            1. Patch VM spec to change NAD reference
            2. Restart the VM

        Expected:
            - VM reports RestartRequired condition after NAD change
            - VM is "Running" on new network after restart
        """

    def test_post_update_peer_connectivity(self):
        """
        Test that VM can communicate with peer VM on the new network after NAD change.

        Steps:
            1. Patch VM spec to change NAD reference from nad1 to nad2
            2. Wait for update to complete
            3. Execute ping from VM to peer VM

        Expected:
            - Ping succeeds with 0% packet loss
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

    def test_multiple_sequential_nad_changes(self):
        """
        Test that multiple sequential NAD changes each produce correct connectivity.

        Preconditions:
            - Three bridge NADs deployed (nad1, nad2, nad3)

        Steps:
            1. Patch VM NAD from nad1 to nad2, wait for update
            2. Patch VM NAD from nad2 to nad3, wait for update
            3. Patch VM NAD from nad3 to nad1, wait for update

        Expected:
            - Ping to peer on nad2 succeeds after first change
            - Ping to peer on nad3 succeeds after second change
            - Ping to peer on nad1 succeeds after third change
        """
