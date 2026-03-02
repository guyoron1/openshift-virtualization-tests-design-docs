# Openshift-virtualization-tests Test plan

## **VM Disk Resize with dataVolumeTemplates Creates New PVC with Original Size - Quality Engineering Plan**

### **Metadata & Tracking**

| Field | Details |
|:------|:--------|
| **Enhancement(s)** | N/A (Bug fix - no VEP) |
| **Feature in Jira** | [CNV-72096](https://issues.redhat.com/browse/CNV-72096) |
| **Jira Tracking** | Closed Loop: [CNV-72096](https://issues.redhat.com/browse/CNV-72096), Bug: [CNV-69395](https://issues.redhat.com/browse/CNV-69395), Related: [CNV-76065](https://issues.redhat.com/browse/CNV-76065) |
| **QE Owner(s)** | Guohua Ouyang |
| **Owning SIG** | sig-ui |
| **Participating SIGs** | sig-storage |
| **Current Status** | Verified (Fix in CNV v4.18.26, PR [#3162](https://github.com/kubevirt-ui/kubevirt-plugin/pull/3162) merged 2025-11-06) |

**Document Conventions (if applicable):** N/A

### **Feature Overview**

This bug fix addresses a critical data loss scenario in the OpenShift Virtualization web console. When a user resized a VM disk through the console's disk edit modal, the underlying PVC was correctly resized. However, upon restarting the VM, the virt-controller re-provisioned a new PVC based on the original size specified in the `dataVolumeTemplate`, because the UI incorrectly renamed the DataVolume and DataVolumeTemplate entries during edit operations. The root cause was in `src/utils/components/DiskModal/utils/submit.ts`, where the `createDataVolumeName` function was called unconditionally for all disk operations instead of only during disk creation. The fix adds a guard condition (`isCreatingDisk`) so that the DataVolume name is only regenerated when creating a new disk, not when editing an existing one. This prevents the VM from losing track of the resized PVC on restart and eliminates the data loss and orphaned PVC issues. The fix was backported from 4.19 to the release-4.18 branch. Automation for this test was added via GitLab MR [!1148](https://gitlab.cee.redhat.com/cnv-qe/kubevirt-ui/-/merge_requests/1148).

---

### **I. Motivation and Requirements Review (QE Review Guidelines)**

This section documents the mandatory QE review process. The goal is to understand the feature's value, technology, and testability before formal test planning.

#### **1. Requirement & User Story Review Checklist**

| Check | Done | Details/Notes | Comments |
|:------|:-----|:--------------|:---------|
| **Review Requirements** | [x] | Reviewed the relevant requirements. | Bug report CNV-69395 provides clear reproduction steps and expected results. The defect is 100% reproducible when resizing disks defined via dataVolumeTemplates through the UI console. |
| **Understand Value** | [x] | Confirmed clear user stories and understood. Understand the difference between U/S and D/S requirements. **What is the value of the feature for RH customers**. | This fix prevents data loss for customers who resize VM disks through the OpenShift console. Multiple customer support cases were filed, confirming significant customer impact. Without this fix, restarting a VM after disk resize results in a new, smaller PVC being created and all previous data being lost. |
| **Customer Use Cases** | [x] | Ensured requirements contain relevant **customer use cases**. | Customers running production VMs on OCP 4.18 with dataVolumeTemplate-based storage need to resize disks non-disruptively. The primary use case is expanding a VM root disk to accommodate growing data, then restarting the VM without data loss. |
| **Testability** | [x] | Confirmed requirements are **testable and unambiguous**. | Fully testable. Steps: (1) Create VM with dataVolumeTemplate, (2) write data to disk, (3) resize PVC via console disk edit modal, (4) restart VM, (5) verify disk size reflects the resize and data is preserved. |
| **Acceptance Criteria** | [x] | Ensured acceptance criteria are **defined clearly** (clear user stories; D/S requirements clearly defined in Jira). | (1) After resizing a disk defined in dataVolumeTemplates via the console, the VM must restart with the resized PVC. (2) No new PVC with the original size should be created. (3) All data written before the resize must be preserved after restart. (4) No orphaned PVCs should remain on the cluster. |
| **Non-Functional Requirements (NFRs)** | [x] | Confirmed coverage for NFRs, including Performance, Security, Usability, Downtime, Connectivity, Monitoring (alerts/metrics), Scalability, Portability (e.g., cloud support), and Docs. | No performance impact expected. The fix adds a conditional guard to a single assignment operation. Usability is the primary NFR: the disk edit modal must correctly preserve the existing DataVolume name when editing (not creating) a disk. |

#### **2. Technology and Design Review**

| Check | Done | Details/Notes | Comments |
|:------|:-----|:--------------|:---------|
| **Developer Handoff/QE Kickoff** | [x] | A meeting where Dev/Arch walked QE through the design, architecture, and implementation details. **Critical for identifying untestable aspects early.** | Fix developed by Adam Viktora. Root cause analysis by Alexander Wels confirmed the UI was modifying the VM YAML during disk edits, replacing volume names with a `dv-<template_type>-<original_name>` prefix and resetting the size to the default. PR reviewed and approved by upalatucci. |
| **Technology Challenges** | [x] | Identified potential testing challenges related to the underlying technology. | (1) The bug only manifests when the disk is defined via `dataVolumeTemplates` in the VM spec, not when using standalone DataVolumes or PVCs. (2) The resize itself works correctly at the PVC level; the issue is that the UI creates a new DataVolume reference pointing to a different PVC name. (3) A related bug CNV-76065 affects disk resize with HPP storage class where the size displayed in the edit modal is incorrect. |
| **Test Environment Needs** | [x] | Determined necessary **test environment setups and tools**. | Requires an OCP cluster with OpenShift Virtualization, a storage class that supports volume expansion (CSI-based), and the ability to create VMs with dataVolumeTemplates. Playwright test framework is used for UI automation. |
| **API Extensions** | [x] | Reviewed new or modified APIs and their impact on testing. | No API changes. The fix modifies a single conditional expression in the UI's disk submit handler (`submit.ts`). The change adds `isCreatingDisk` and `data.dataVolumeTemplate?.metadata` guards before calling `createDataVolumeName`. |
| **Topology Considerations** | [x] | Evaluated multi-cluster, network topology, and architectural impacts. | Single-cluster topology. The bug is isolated to the kubevirt-plugin UI component. No multi-cluster or network topology considerations. |

### **II. Software Test Plan (STP)**

This STP serves as the **overall roadmap for testing**, detailing the scope, approach, resources, and schedule.

#### **1. Scope of Testing**

This test plan covers the bug fix for VM disk resize when storage is defined via `dataVolumeTemplates` in the OpenShift Virtualization web console. The fix corrects the disk edit submit handler to preserve the existing DataVolume and DataVolumeTemplate names during edit operations, preventing the creation of a new PVC with the original size on VM restart. Testing will validate that disk resizes are preserved across VM restarts, that data integrity is maintained, and that no orphaned PVCs are created.

**Testing Goals**

- **P0:** Verify that resizing a disk defined in dataVolumeTemplates via the console preserves the resize after VM restart
- **P0:** Verify that data written to the disk before resize is preserved after VM restart
- **P0:** Verify that no new PVC with the original size is created after VM restart
- **P1:** Verify that no orphaned PVCs remain on the cluster after the resize and restart cycle
- **P1:** Verify that the console correctly reflects the resized PVC size
- **P1:** Verify that disk resize works correctly for disks not defined via dataVolumeTemplates (regression check)
- **P2:** Verify behavior when resizing disks with different storage classes (HPP, OCS/ODF, NFS)

**Out of Scope (Testing Scope Exclusions)**

| Out-of-Scope Item | Rationale | PM/ Lead Agreement |
|:-------------------|:----------|:-------------------|
| Backend virt-controller reconciliation logic | The fix is entirely in the frontend UI component; virt-controller behavior is unchanged | Out of scope for this fix |
| Online disk resize (hotplug resize while VM is running) | Online resize is a separate feature covered by existing tests (CNV-6793, CNV-6794) in the storage test suite | Covered by existing test suite |
| PVC resize initiated via CLI (oc/kubectl) | The bug is specific to the console UI disk edit modal; CLI-based PVC resize is unaffected | Covered by storage QE |
| Multi-node storage replication behavior | Storage replication during resize is a storage-level concern, not a UI concern | Covered by storage QE |
| Version 4.19+ behavior | The fix was already present in 4.19; this is a backport to 4.18 only | Not applicable |

#### **2. Test Strategy**

| Item | Description | Applicable (Y/N or N/A) | Comments |
|:-----|:------------|:------------------------|:---------|
| Functional Testing | Validates that the feature works according to specified requirements and user stories | Y | Core testing of disk resize via console disk edit modal for VMs with dataVolumeTemplates. Verify PVC size is preserved, data integrity is maintained, and no orphaned PVCs are created after VM restart. |
| Automation Testing | Ensures test cases are automated for continuous integration and regression coverage | Y | Automated via GitLab MR [!1148](https://gitlab.cee.redhat.com/cnv-qe/kubevirt-ui/-/merge_requests/1148) using Playwright for UI tests. Additional tier 2 tests can be developed using pytest in openshift-virtualization-tests. |
| Performance Testing | Validates feature performance meets requirements (latency, throughput, resource usage) | N/A | The fix adds a single conditional check. No performance impact expected. |
| Security Testing | Verifies security requirements, RBAC, authentication, authorization, and vulnerability scanning | N/A | No security changes. RBAC for disk resize is handled by the OCP console framework and Kubernetes RBAC. |
| Usability Testing | Validates user experience, UI/UX consistency, and accessibility requirements. Does the feature require UI? If so, ensure the UI aligns with the requirements | Y | This is a UI fix. Verify that the disk edit modal correctly displays the current disk size, allows resize, and persists the change. Verify the console disk tab reflects the updated size after restart. |
| Compatibility Testing | Ensures feature works across supported platforms, versions, and configurations | Y | Verify fix works on OCP 4.18 with CNV v4.18.26+. Test with multiple storage classes that support volume expansion. |
| Regression Testing | Verifies that new changes do not break existing functionality | Y | Verify disk creation still works (the `createDataVolumeName` function is still called for new disks). Verify disk edit for non-dataVolumeTemplate disks still works. Verify other disk modal operations (delete, detach) are unaffected. |
| Upgrade Testing | Validates upgrade paths from previous versions, data migration, and configuration preservation | N/A | Frontend-only fix with no persistent state changes. Existing VMs with resized PVCs should not be affected. |
| Backward Compatibility Testing | Ensures feature maintains compatibility with previous API versions and configurations | N/A | No API changes. Frontend-only fix. |
| Dependencies | Dependent on deliverables from other components/products? Identify what is tested by which team. | Y | Depends on the storage class supporting volume expansion (allowVolumeExpansion: true). Depends on the kubevirt-plugin console plugin being loaded in the OCP console. |
| Cross Integrations | Does the feature affect other features/require testing by other components? Identify what is tested by which team. | Y | The fix touches the disk submit handler which is shared between create and edit operations. Disk creation workflows should be regression-tested. Storage team should verify that existing online resize tests (CNV-6793, CNV-6794, CNV-6578, CNV-6580) remain unaffected. |
| Monitoring | Does the feature require metrics and/or alerts? | N | No new metrics or alerts required. |
| Cloud Testing | Does the feature require multi-cloud platform testing? Consider cloud-specific features. | N/A | Console UI behavior is platform-independent. Storage class availability varies by cloud provider, but the fix is in the UI layer. |

#### **3. Test Environment**

| Environment Component | Configuration | Specification Examples |
|:----------------------|:--------------|:-----------------------|
| **Cluster Topology** | Multi-node OCP cluster with at least 2 worker nodes | 3-node cluster: 1 control plane + 2 workers |
| **OCP & OpenShift Virtualization Version(s)** | OCP 4.18 with CNV v4.18.26+ | OCP 4.18, CNV 4.18.26 |
| **CPU Virtualization** | Standard x86_64 with hardware virtualization | Intel VT-x or AMD-V enabled |
| **Compute Resources** | Sufficient resources to run VMs with resizable disks | 16 GB RAM per worker node minimum |
| **Special Hardware** | N/A | No special hardware required |
| **Storage** | Storage class with volume expansion support | OCS/ODF, NFS, or any CSI-based storage with `allowVolumeExpansion: true` |
| **Network** | Standard cluster networking | OVN-Kubernetes or OpenShiftSDN |
| **Required Operators** | OpenShift Virtualization operator, CDI (Containerized Data Importer) | HyperConverged CR deployed |
| **Platform** | Any supported OCP platform | Bare metal, IPI, or cloud-provider |
| **Special Configurations** | VMs created with dataVolumeTemplates in the VM spec | RHEL or Fedora guest OS template with dataVolumeTemplate-based disk |

#### **3.1. Testing Tools & Frameworks**

| Category | Tools/Frameworks |
|:---------|:-----------------|
| **Test Framework** | Playwright (UI tests, Tier 1), pytest (Tier 2 / Python) |
| **CI/CD** | OpenShift CI (Prow), Polarion for test case tracking |
| **Other Tools** | oc CLI for PVC/DV verification, Browser DevTools for frontend debugging |

#### **4. Entry Criteria**

The following conditions must be met before testing can begin:

- [ ] Requirements and design documents are **approved and merged**
- [ ] Test environment can be **set up and configured** (see Section II.3 - Test Environment)
- [ ] PR [kubevirt-ui/kubevirt-plugin#3162](https://github.com/kubevirt-ui/kubevirt-plugin/pull/3162) is merged and included in the target CNV build
- [ ] Storage class with `allowVolumeExpansion: true` is available in the test cluster
- [ ] At least one VM template with dataVolumeTemplate-based disk storage is available
- [ ] OCP console with kubevirt-plugin v4.18.26+ is accessible

#### **5. Risks**

| Risk Category | Specific Risk for This Feature | Mitigation Strategy | Status |
|:--------------|:-------------------------------|:--------------------|:-------|
| Timeline/Schedule | Fix is already merged and verified; no timeline risk | Test development can begin immediately against available builds | [x] |
| Test Coverage | The original QE team missed this test scenario when the feature was introduced | Add explicit test scenarios covering disk edit with dataVolumeTemplates; add to CNV UI manual checklist as documented in comments | [x] |
| Test Environment | Storage class must support volume expansion; some storage backends may not support this feature | Document required storage class configuration; test with multiple storage backends where possible | [ ] |
| Untestable Aspects | The exact customer environment conditions (including specific template types and disk naming patterns) may not be fully replicable | Focus on testing the core logic (disk edit preserves DataVolume name) rather than reproducing exact customer configurations | [x] |
| Resource Constraints | UI testing with Playwright requires browser automation infrastructure | Use existing Playwright CI infrastructure in the kubevirt-ui repository | [ ] |
| Dependencies | Related bug CNV-76065 affects disk resize with HPP storage class, showing incorrect size in the edit modal | Track CNV-76065 resolution; test HPP storage class scenarios separately once that fix is available | [ ] |
| Other | Automation MR !1148 for kubevirt-ui covers UI-level testing; additional API-level tests may be needed in openshift-virtualization-tests | Coordinate with storage QE to ensure coverage at both UI and API levels | [ ] |

#### **6. Known Limitations**

- The fix is specific to the release-4.18 branch of kubevirt-plugin. In version 4.19 and later, this bug was already fixed as part of the upstream development.
- Related bug CNV-76065 affects disk resize with HPP storage class, where the size displayed in the edit modal is incorrect (shows 329 instead of 30). This is a separate issue that may affect testing disk resize with HPP storage.
- The fix is a single-line conditional change. While the code change is minimal, the impact is significant: it prevents data loss and orphaned PVCs. Testing must verify both the positive case (resize is preserved) and the negative case (no new PVC is created).
- The automation MR !1148 covers UI-level testing via Playwright. Additional tier 2 end-to-end tests using pytest and the openshift-virtualization-tests framework may be needed to verify data integrity at the storage layer (writing data, resizing, restarting, verifying data).

---

### **III. Test Scenarios & Traceability**

This section links requirements to test coverage, enabling reviewers to verify all requirements are tested.

#### **1. Requirements-to-Tests Mapping**

| Requirement ID | Requirement Summary | Test Scenario(s) | Tier | Priority |
|:---------------|:--------------------|:-----------------|:-----|:---------|
| CNV-72096-REQ-01 | Resized PVC must be preserved after VM restart when disk is defined via dataVolumeTemplates | **TS-01:** Create a VM with a disk defined in dataVolumeTemplates. Start the VM. Navigate to the disk edit modal in the console. Resize the PVC to a larger size. Restart the VM. Verify the VM boots with the resized PVC and the disk capacity inside the guest reflects the new size. **Preconditions:** VM with dataVolumeTemplate-based disk, storage class with allowVolumeExpansion. **Expected:** VM restarts with the resized PVC; disk capacity matches the new size. | Tier 1 | P0 |
| CNV-72096-REQ-02 | Data written to the disk before resize must be preserved after VM restart | **TS-02:** Create a VM with dataVolumeTemplate. Start the VM. Write test data to the disk (create a file with known content and checksum). Resize the PVC via the console. Restart the VM. Verify the test data file exists and its checksum matches the original. **Preconditions:** Running VM with writable filesystem. **Expected:** Data file exists with matching checksum after restart. | Tier 1 | P0 |
| CNV-72096-REQ-03 | No new PVC with original size should be created after VM restart | **TS-03:** Create a VM with dataVolumeTemplate. Start the VM. Note the PVC name and size. Resize the PVC via the console. Restart the VM. List all PVCs in the namespace. Verify no new PVC with the `dv-` prefix and original size exists. Verify the original PVC is still bound to the VM. **Preconditions:** VM with dataVolumeTemplate-based disk. **Expected:** Only the original (resized) PVC exists; no orphaned PVCs. | Tier 1 | P0 |
| CNV-72096-REQ-04 | Console must correctly reflect the resized PVC size on the VM disks tab | **TS-04:** Create a VM with dataVolumeTemplate. Start the VM. Resize the PVC via the console disk edit modal. Navigate to the VM's disk tab. Verify the displayed disk size matches the resized value. Restart the VM. Verify the disk tab still shows the correct resized value. **Preconditions:** VM with dataVolumeTemplate-based disk. **Expected:** Console disk tab shows the resized PVC size both before and after VM restart. | Tier 1 | P1 |
| CNV-72096-REQ-05 | No orphaned (detached) PVCs should remain on the cluster after resize and restart | **TS-05:** Create a VM with dataVolumeTemplate. Start the VM. Resize the PVC via the console. Restart the VM. List all PVCs in the namespace using `oc get pvc`. Verify that only the expected PVCs exist (no orphaned PVCs with old names or sizes). **Preconditions:** VM with dataVolumeTemplate-based disk. **Expected:** No orphaned PVCs in the namespace. | Tier 1 | P1 |
| CNV-72096-REQ-06 | Disk creation via the console must still work correctly (regression) | **TS-06:** Create a VM. Add a new disk via the console disk modal (hot-add or at creation time) using dataVolumeTemplate. Verify the new disk is created with the correct name (using the `dv-` prefix convention for new disks) and size. Start the VM. Verify the new disk is visible inside the guest. **Preconditions:** VM without the target disk. **Expected:** New disk is created with correct naming and size; VM boots successfully with the new disk. | Tier 1 | P1 |
| CNV-72096-REQ-07 | Disk resize works correctly for disks not defined via dataVolumeTemplates | **TS-07:** Create a VM with a standalone DataVolume (not via dataVolumeTemplate). Start the VM. Resize the PVC via the console. Restart the VM. Verify the resize is preserved and no data loss occurs. **Preconditions:** VM with standalone DV-based disk, storage class with volume expansion. **Expected:** Resize is preserved after restart; data integrity maintained. | Tier 1 | P1 |
| CNV-72096-REQ-08 | Disk resize with different storage classes | **TS-08:** Create VMs with dataVolumeTemplate-based disks using different storage classes (OCS/ODF, NFS). For each VM: start, resize PVC via console, restart, verify resize is preserved. **Preconditions:** Multiple storage classes with allowVolumeExpansion available. **Expected:** Resize is preserved across all tested storage classes. | Tier 2 | P1 |
| CNV-72096-REQ-09 | End-to-end disk resize lifecycle with data verification | **TS-09:** Create a VM from an RHEL template with dataVolumeTemplate. Start the VM. Install packages and write significant data to the disk (multiple files, directories). Note disk usage. Resize the PVC via the console to a larger size. Restart the VM. Verify: (1) all files and directories are intact, (2) disk capacity reflects the new size, (3) additional space is available for use, (4) the VM is fully functional after restart. **Preconditions:** RHEL template VM with dataVolumeTemplate. **Expected:** Full data preservation, correct disk capacity, functional VM. | Tier 2 | P0 |
| CNV-72096-REQ-10 | Multiple sequential disk resizes via console | **TS-10:** Create a VM with dataVolumeTemplate. Start the VM. Resize the PVC via the console (first resize). Restart the VM. Verify the first resize is preserved. Resize the PVC again via the console (second resize). Restart the VM again. Verify the second resize is preserved and no orphaned PVCs exist. **Preconditions:** VM with dataVolumeTemplate-based disk, storage class supporting multiple expansions. **Expected:** Both resizes are preserved; no orphaned PVCs after either restart. | Tier 2 | P1 |
| CNV-72096-REQ-11 | Disk resize followed by VM migration preserves data | **TS-11:** Create a VM with dataVolumeTemplate. Start the VM. Write test data. Resize the PVC via the console. Restart the VM. Migrate the VM to another node. Verify the resized disk and data are preserved after migration. **Preconditions:** Multi-node cluster, VM with dataVolumeTemplate, shared storage. **Expected:** Data preserved after resize, restart, and migration. | Tier 2 | P2 |
| CNV-72096-REQ-12 | Disk resize followed by VM snapshot and restore | **TS-12:** Create a VM with dataVolumeTemplate. Start the VM. Write test data. Take a snapshot. Resize the PVC via the console. Restart the VM. Verify the resize is preserved. Restore from the pre-resize snapshot. Verify the VM boots with the original disk size and data from the snapshot. **Preconditions:** Storage class supporting snapshots, VM with dataVolumeTemplate. **Expected:** Resize preserved after restart; snapshot restore returns to original state. | Tier 2 | P2 |

---

### **IV. Sign-off and Approval**

This Software Test Plan requires approval from the following stakeholders:

- **Reviewers:**
  - TBD / @tbd
  - TBD / @tbd
- **Approvers:**
  - TBD / @tbd
  - TBD / @tbd
