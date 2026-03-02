"""
VM Disk Resize with dataVolumeTemplates Tests

STP Reference: stps/sig-storage/disk-resize-dvt-stp.md
Jira: CNV-72096
"""


class TestDiskResizeDVT:
    """
    Tests for VM disk resize when storage is defined via dataVolumeTemplates.

    Markers:
        - tier2

    Preconditions:
        - OpenShift cluster with OCP 4.18+ and OVN-Kubernetes
        - OpenShift Virtualization CNV v4.18.26+ with fix from PR #3162
        - StorageClass with allowVolumeExpansion: true (CSI-based)
        - CDI operator deployed
        - VM created with disk defined in spec.dataVolumeTemplates
    """

    __test__ = False

    def test_resize_with_different_storage_classes(self):
        """
        Test that disk resize is preserved across different storage classes.

        Preconditions:
            - At least 2 StorageClasses with allowVolumeExpansion: true available
              (e.g., OCS/ODF, NFS)

        Steps:
            1. For each expandable storage class, create a VM with
               dataVolumeTemplate using that storage class
            2. Start the VM and wait for Running phase
            3. Resize PVC to a larger size
            4. Stop and restart VM
            5. Check PVC capacity after restart

        Expected:
            - PVC capacity matches resized value for each storage class
            - No orphaned PVCs with any storage class
        """

    def test_e2e_resize_lifecycle_with_data_verification(self):
        """
        Test that full resize lifecycle preserves data and functionality.

        Preconditions:
            - RHEL guest image template with dataVolumeTemplate available
            - VM created from RHEL template and in Running phase

        Steps:
            1. Write significant test data (multiple files and directories)
            2. Record disk usage and file checksums
            3. Resize PVC to a larger size via API
            4. Stop and restart VM
            5. Verify all file checksums match pre-resize values
            6. Check disk capacity reflects new size inside guest
            7. Write new data to verify additional space is available
            8. Run basic VM operations (network, process management)

        Expected:
            - All files and directories are intact after resize and restart
            - Disk capacity inside guest reflects the new size
            - Additional space is available and writable
            - VM is fully functional after restart
        """

    def test_multiple_sequential_resizes(self):
        """
        Test that multiple sequential disk resizes are preserved.

        Preconditions:
            - VM created with 10Gi dataVolumeTemplate-based disk
            - StorageClass supports multiple sequential volume expansions
            - VM started and in Running phase

        Steps:
            1. Resize PVC from 10Gi to 20Gi
            2. Stop and restart VM
            3. Verify PVC capacity is 20Gi
            4. Resize PVC from 20Gi to 30Gi
            5. Stop and restart VM again
            6. Verify PVC capacity is 30Gi
            7. List PVCs in namespace

        Expected:
            - First resize (20Gi) is preserved after first restart
            - Second resize (30Gi) is preserved after second restart
            - No orphaned PVCs after either restart
        """

    def test_resize_followed_by_migration(self):
        """
        Test that resized disk and data are preserved after VM migration.

        Preconditions:
            - Multi-node cluster with at least 2 worker nodes
            - VM created with dataVolumeTemplate and shared (RWX) storage
            - VM started and in Running phase

        Steps:
            1. Write test data and record SHA-256 checksum
            2. Resize PVC to a larger size
            3. Stop and restart VM
            4. Migrate VM to another node
            5. Verify file checksums after migration
            6. Check PVC capacity after migration

        Expected:
            - Migration completes successfully
            - Data file checksums match after migration
            - Resized disk capacity is maintained after migration
        """

    def test_resize_with_snapshot_and_restore(self):
        """
        Test that resize and snapshot restore interact correctly.

        Preconditions:
            - Storage class with VolumeSnapshot support
            - VolumeSnapshotClass configured for the storage backend
            - VM created with dataVolumeTemplate and started

        Steps:
            1. Write test data and record checksums
            2. Take VM snapshot (pre-resize)
            3. Resize PVC to a larger size
            4. Stop and restart VM
            5. Verify PVC shows resized value
            6. Restore from pre-resize snapshot
            7. Verify VM boots with original disk size
            8. Verify snapshot data is intact

        Expected:
            - Resize is preserved after restart (before restore)
            - Snapshot restore returns VM to pre-resize state
            - PVC capacity matches original size after restore
            - Data from snapshot is intact after restore
        """
