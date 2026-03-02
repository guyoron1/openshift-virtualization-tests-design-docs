# Openshift-virtualization-tests Test plan

## **vGPU Documentation Fix: Mediated Device Discovery Procedure - Quality Engineering Plan**

### **Metadata & Tracking**

| Field | Details |
|:------|:--------|
| **Enhancement(s)** | N/A (Documentation fix - no VEP) |
| **Feature in Jira** | [CNV-68261](https://issues.redhat.com/browse/CNV-68261) |
| **Jira Tracking** | Closed Loop: [CNV-68261](https://issues.redhat.com/browse/CNV-68261), Bug: [CNV-67095](https://issues.redhat.com/browse/CNV-67095) |
| **QE Owner(s)** | TBD |
| **Owning SIG** | sig-compute |
| **Participating SIGs** | sig-compute, sig-documentation |
| **Current Status** | Closed (PR merged 2025-10-17, cherrypicked to enterprise-4.19 and enterprise-4.20) |

**Document Conventions (if applicable):** This is a closed-loop documentation bug fix. The test plan validates the corrected vGPU mediated device setup procedure documented in the OpenShift Container Platform virtualization guide.

### **Related GitHub Pull Requests**

| PR Link | Repository | Source Jira Issue | Status | Description |
|:--------|:-----------|:------------------|:-------|:------------|
| [openshift/openshift-docs#100595](https://github.com/openshift/openshift-docs/pull/100595) | openshift/openshift-docs | CNV-67095 | Merged | Rewrites the mediated device creation procedure to include step-by-step node exploration for discovering mdev types, replacing the non-functional `oc get $NODE` command with a working `oc debug` workflow |

### **Feature Overview**

The original OpenShift Virtualization documentation for setting up virtual GPUs (vGPU) via mediated devices contained a procedural dead end at step 3 of the mediated device creation process. The `oc` command specified in step 3 returned no output until the full setup was already complete, making it impossible for users to identify available mediated device types and proceed with configuration.

The fix restructures the documentation to guide users through a node-level exploration workflow using `oc debug` to discover PCI addresses, supported mediated device types, and their display names before configuring the `HyperConverged` CR. This eliminates the circular dependency where the discovery command required the configuration to already be in place.

**Key Changes:**

- Added a multi-step procedure to explore worker nodes via `oc debug node/` and `chroot /host`
- Added commands to navigate `/sys/class/mdev_bus/` to discover PCI addresses of physical GPUs
- Added commands to list supported mediated device types (`mdev_supported_types`) and read their display names
- Restructured the `HyperConverged` CR configuration section with updated examples using discovered values
- Moved the verification step to use `oc get node -o json | jq` to confirm GPU attachment after configuration
- Updated example device types from GRID T4 references to NVIDIA A2 references

---

### **I. Motivation and Requirements Review (QE Review Guidelines)**

This section documents the mandatory QE review process. The goal is to understand the feature's value, technology, and testability prior to formal test planning.

#### **1. Requirement & User Story Review Checklist**

| Check | Done | Details/Notes | Comments |
|:------|:-----|:--------------|:---------|
| **Review Requirements** | [x] | Documentation fix: The vGPU setup procedure must provide a working method to identify available mediated device types on worker nodes before configuring the HyperConverged CR. | Requirements are clearly defined in CNV-67095 bug description and confirmed by QE review on the PR. |
| **Understand Value** | [x] | Customers following the official documentation to set up vGPU/mediated devices were unable to complete the procedure because step 3 returned empty output. This forced customers to manually SSH into nodes and explore sysfs paths without guidance. | Critical documentation usability fix for customers deploying GPU workloads on OpenShift Virtualization. |
| **Customer Use Cases** | [x] | A user attempts to configure vGPU pass-through for VMs by following the official OpenShift documentation. They need to discover which mediated device types are available on their GPU hardware and configure the HyperConverged CR accordingly. | Reported via internal support case. Affects all customers setting up vGPU for the first time. |
| **Testability** | [x] | Testable by following the documented procedure on a cluster with GPU-capable nodes. Each step in the new procedure produces verifiable output. The end-to-end workflow can be validated by confirming mediated devices appear as allocatable resources on nodes. | Requires nodes with NVIDIA GPU hardware supporting mediated devices (GRID/vGPU capable). |
| **Acceptance Criteria** | [x] | (1) The documented procedure provides a working method to discover available mediated device types. (2) Each step produces expected output. (3) The discovered values can be used to successfully configure the HyperConverged CR. (4) After configuration, mediated devices appear as allocatable resources. | QE approval received from reviewer prior to PR merge. |
| **Non-Functional Requirements (NFRs)** | [x] | Documentation accuracy and completeness. No performance, security, or scalability NFRs as this is a documentation-only change. | Docs review and QE review both completed before merge. |

#### **2. Technology and Design Review**

| Check | Done | Details/Notes | Comments |
|:------|:-----|:--------------|:---------|
| **Developer Handoff/QE Kickoff** | [x] | Multiple contributors investigated the issue. Original bug reporter provided the manual workaround (`cat /sys/class/mdev_bus/.../name`). Documentation writer translated this into a structured procedure using `oc debug`. QE reviewed the PR preview. | Review comments from QE captured in CNV-67095 and PR #100595. |
| **Technology Challenges** | [x] | (1) The `oc debug` approach requires `cluster-admin` or equivalent permissions. (2) The sysfs paths (`/sys/class/mdev_bus/`) are specific to the NVIDIA vGPU driver and may differ for other GPU vendors. (3) Node exploration requires the GPU driver to be loaded on the worker node. | Documented procedure is NVIDIA-specific. Other GPU vendors may have different sysfs layouts. |
| **Test Environment Needs** | [x] | Requires OpenShift cluster with at least one worker node containing an NVIDIA GPU that supports mediated devices (GRID/vGPU capable). The NVIDIA GRID driver must be installed. IOMMU must be enabled. | GPU hardware is specialized and may not be available in standard CI environments. |
| **API Extensions** | [x] | No API changes. The fix modifies documentation only. The HyperConverged CR API (`spec.mediatedDevicesConfiguration` and `spec.permittedHostDevices.mediatedDevices`) is unchanged. | Existing API surface. |
| **Topology Considerations** | [x] | Mediated devices are node-specific. Different nodes may have different GPU hardware and therefore different available mediated device types. The procedure must be repeated per node if hardware varies. | Multi-GPU or mixed-GPU clusters require per-node discovery. |

### **II. Software Test Plan (STP)**

This STP serves as the **overall roadmap for testing**, detailing the scope, approach, resources, and schedule.

#### **1. Scope of Testing**

This test plan covers the corrected documentation procedure for discovering and configuring mediated devices (vGPU) on OpenShift Virtualization. Testing validates that the documented steps produce the expected outputs and result in a working vGPU configuration. Since the change is documentation-only, functional testing focuses on verifying the accuracy and completeness of the documented procedure rather than underlying API behavior.

**In Scope:**

- Documented `oc debug` workflow for discovering GPU PCI addresses
- Documented sysfs navigation for listing supported mediated device types
- Documented method for reading mediated device type display names
- HyperConverged CR configuration using discovered values
- Verification command to confirm mediated devices are allocatable
- End-to-end workflow: from node exploration to VM with vGPU attachment

**Testing Goals**

##### **Positive Use Cases (Happy Path)**

- Verify that `oc debug node/<gpu-node>` followed by `chroot /host` provides shell access to the node filesystem
- Verify that navigating to `/sys/class/mdev_bus/` and listing contents reveals PCI addresses of physical GPUs
- Verify that listing `mdev_supported_types` for a PCI address shows available mediated device type identifiers
- Verify that reading the `name` file for a mediated device type returns the display name
- Verify that configuring the HyperConverged CR with discovered `mediatedDeviceTypes`, `mdevNameSelector`, and `resourceName` values results in mediated devices being created
- Verify that the verification command (`oc get node -o json | jq`) shows the configured mediated device as allocatable with a non-zero count
- Verify that a VM configured with the mediated device GPU can be started and the device is available inside the guest

##### **Negative Use Cases (Error Handling and Edge Cases)**

- Verify behavior when no GPU hardware is present on the node (empty `/sys/class/mdev_bus/`)
- Verify behavior when GPU driver is not installed (directory structure may be absent)
- Verify behavior when an invalid mediated device type is specified in the HyperConverged CR
- Verify behavior when `mdevNameSelector` does not match any available device name on the node

**Out of Scope (Testing Scope Exclusions)**

| Out-of-Scope Item | Rationale | PM/Lead Agreement |
|:-------------------|:----------|:-------------------|
| GPU driver installation testing | Driver installation is handled by NVIDIA and documented separately | Out of scope for CNV QE |
| IOMMU enablement testing | IOMMU configuration is a prerequisite covered by platform documentation | Out of scope for CNV QE |
| Non-NVIDIA GPU vendors | The documented procedure uses NVIDIA-specific sysfs paths; other vendors have separate documentation | Not applicable |
| Documentation rendering and formatting | AsciiDoc rendering and Netlify preview validation are handled by the docs team | Docs team responsibility |
| Performance benchmarking of vGPU workloads | vGPU performance is a separate concern from documentation accuracy | Separate test effort |

#### **2. Test Strategy**

| Item | Description | Applicable (Y/N or N/A) | Comments |
|:-----|:------------|:------------------------|:---------|
| Functional Testing | Validates that the documented procedure works end-to-end: from node exploration through mediated device discovery to HyperConverged CR configuration and device allocation verification | Y | Core testing focus. Each documented step is validated for correct output. |
| Automation Testing | Automated verification of the end-to-end vGPU setup workflow using documented commands | Y | Tier 2 (pytest) for end-to-end workflow validation. Tier 1 (Ginkgo) for HyperConverged CR mediated device configuration. |
| Performance Testing | Validates performance of vGPU workloads after configuration | N/A | Documentation fix does not affect performance. vGPU performance testing is a separate effort. |
| Security Testing | Verifies RBAC requirements for `oc debug` and node access | Y | The documented `oc debug` command requires elevated privileges. Verify minimum required RBAC roles. |
| Usability Testing | Validates that the documented procedure is clear, complete, and produces expected outputs at each step | Y | Primary concern for this documentation fix. Steps should be unambiguous and produce the documented example outputs. |
| Compatibility Testing | Ensures the procedure works across supported OCP versions (4.19+) and GPU hardware | Y | Verify on OCP 4.19 and 4.20. Verify with different NVIDIA GPU models that support mediated devices. |
| Regression Testing | Verifies that existing vGPU configurations continue to work after the documentation update | Y | Existing mediated device configurations should not be affected. Verify that previously configured mediated devices remain functional. |
| Upgrade Testing | Validates that mediated device configurations created using the old documentation still work after cluster upgrade | N/A | Documentation change only; no runtime behavior change. |
| Backward Compatibility Testing | Ensures older HyperConverged CR configurations remain valid | N/A | No API changes. Old configurations continue to work. |
| Dependencies | Dependent on NVIDIA GPU hardware, NVIDIA GRID driver, IOMMU enablement | Y | Requires specialized hardware. NVIDIA driver must be installed and loaded on worker nodes. |
| Cross Integrations | Interaction with HyperConverged operator, virt-handler device plugin, and kubevirt device manager | Y | Mediated device creation involves the HCO reconciling the configuration and virt-handler exposing devices to kubelet. |
| Monitoring | Mediated device allocation is visible through node status | N | No new metrics or alerts. Existing node allocatable resources show mediated device counts. |
| Cloud Testing | vGPU pass-through on cloud platforms | N/A | Mediated devices require bare-metal access to physical GPUs. Cloud GPU instances typically do not support nested mediated device creation. |

#### **3. Test Environment**

| Environment Component | Configuration | Specification Examples |
|:----------------------|:--------------|:-----------------------|
| **Cluster Topology** | Multi-node cluster with at least one GPU-capable worker node | 4-node cluster: 3 control plane + 1 GPU worker node |
| **OCP & OpenShift Virtualization Version(s)** | OCP 4.19+ with CNV matching version | OCP 4.19, CNV 4.19.x or OCP 4.20, CNV 4.20.x |
| **CPU Virtualization** | Hardware virtualization enabled with IOMMU support | Intel VT-d or AMD-Vi enabled in BIOS |
| **Compute Resources** | GPU worker node with sufficient memory for VM + vGPU allocation | 32 GB RAM, 16 CPUs on GPU worker node |
| **Special Hardware** | NVIDIA GPU supporting mediated devices (GRID/vGPU capable) | NVIDIA A2, A10, A16, A30, A100, L4, or T4 with vGPU support |
| **Storage** | Standard storage for VM disks | ODF, NFS, or local storage with PV provisioning |
| **Network** | Standard cluster networking | OVN-Kubernetes |
| **Required Operators** | OpenShift Virtualization operator, NVIDIA GPU Operator (optional) | HyperConverged CR, ClusterPolicy CR (if using GPU Operator) |
| **Platform** | Bare metal (required for physical GPU access) | Bare metal with NVIDIA GPU installed |
| **Special Configurations** | IOMMU enabled, NVIDIA GRID driver installed, `mdev_bus` sysfs populated | Kernel parameter `intel_iommu=on` or `amd_iommu=on` |

#### **3.1. Testing Tools & Frameworks**

| Category | Tools/Frameworks |
|:---------|:-----------------|
| **Test Framework** | Ginkgo v2 + Gomega (Tier 1 / Go), pytest (Tier 2 / Python) |
| **CI/CD** | OpenShift CI (Prow), Polarion for test case tracking |
| **Other Tools** | oc CLI, virtctl, jq for JSON parsing, NVIDIA SMI tools for GPU verification |

#### **4. Entry Criteria**

The following conditions must be met before testing can begin:

- [ ] Requirements and design documents are **approved and merged**
- [ ] Test environment can be **set up and configured** (see Section II.3 - Test Environment)
- [ ] PR [openshift/openshift-docs#100595](https://github.com/openshift/openshift-docs/pull/100595) is merged and documentation is published
- [ ] At least one worker node with NVIDIA GPU hardware supporting mediated devices is available
- [ ] NVIDIA GRID driver is installed and loaded on the GPU worker node
- [ ] IOMMU is enabled on the GPU worker node
- [ ] `/sys/class/mdev_bus/` is populated with at least one PCI device directory

#### **5. Risks**

| Risk Category | Specific Risk for This Feature | Mitigation Strategy | Status |
|:--------------|:-------------------------------|:--------------------|:-------|
| Timeline/Schedule | Documentation PR is already merged and published; no timeline risk for test development | Test development can begin immediately | [x] |
| Test Coverage | GPU hardware availability limits the scope of testing across different GPU models | Focus testing on one confirmed GPU model (e.g., NVIDIA L4 or A2); document expected behavior for other models | [ ] |
| Test Environment | Requires bare-metal nodes with physical NVIDIA GPU hardware, which is specialized and limited | Coordinate with lab team for GPU-equipped bare-metal nodes; some steps can be validated with mock sysfs structures | [ ] |
| Untestable Aspects | Cannot test the original broken workflow (old docs) to confirm the regression since documentation has been replaced | Rely on the bug report description and reproduction steps as baseline evidence | [x] |
| Resource Constraints | GPU-equipped nodes are expensive and in limited supply | Share GPU test environments across QE team; batch vGPU-related tests together | [ ] |
| Dependencies | NVIDIA GRID driver must be installed and functional; driver installation issues are outside CNV QE control | Verify driver installation as a precondition check; fail fast if driver is not available | [ ] |
| Other | Procedure is NVIDIA-specific; customers with other GPU vendors may still face discovery challenges | Flag as a known limitation; recommend documentation for other GPU vendors as a follow-up | [ ] |

#### **6. Known Limitations**

- The documented procedure is specific to NVIDIA GPUs with GRID/vGPU support. Other GPU vendors (AMD, Intel) may have different sysfs layouts and discovery procedures.
- The `oc debug` command requires `cluster-admin` or equivalent privileges. Users with restricted RBAC roles may not be able to perform the node exploration steps.
- The sysfs path structure (`/sys/class/mdev_bus/<PCI_ADDR>/mdev_supported_types/`) depends on the GPU driver being loaded. If the driver fails to load, these paths will not exist.
- Different GPU models support different sets of mediated device types. The example output in the documentation (NVIDIA A2-2Q) is specific to the NVIDIA A2 GPU; other models will show different type identifiers and names.
- The procedure does not cover scenarios where multiple GPUs of different models are installed on the same node. Users must repeat the discovery for each PCI address.
- The `resourceName` naming convention (`nvidia.com/NVIDIA_<name_with_underscores>`) is an NVIDIA convention. The documentation does not explain how to derive `resourceName` values for non-NVIDIA devices.

---

### **III. Test Scenarios & Traceability**

This section provides a **high-level overview** of test scenarios mapped to requirements.

#### **1. Requirements-to-Tests Mapping**

| Requirement ID | Requirement Summary | Test Scenario(s) | Tier | Priority |
|:---------------|:--------------------|:-----------------|:-----|:---------|
| REQ-MDEV-001 | Documented `oc debug` workflow provides shell access to worker node filesystem | TS-001: Verify that `oc debug node/<gpu-node>` opens a debug pod and `chroot /host` provides access to the host filesystem including `/sys/class/mdev_bus/` | Tier 2 | P1 |
| REQ-MDEV-002 | `/sys/class/mdev_bus/` listing reveals PCI addresses of physical GPUs | TS-002: Verify that listing `/sys/class/mdev_bus/` on a GPU-equipped node returns one or more PCI address directories matching the format `XXXX:XX:XX.X` | Tier 2 | P1 |
| REQ-MDEV-003 | `mdev_supported_types` directory lists available mediated device types | TS-003: Verify that navigating to a PCI address directory and listing `mdev_supported_types` returns one or more type identifiers (e.g., `nvidia-745`) | Tier 2 | P1 |
| REQ-MDEV-004 | Reading the `name` file for a mediated device type returns its display name | TS-004: Verify that reading `<type>/name` inside `mdev_supported_types` returns a non-empty string representing the GPU profile name (e.g., `NVIDIA A2-2Q`) | Tier 2 | P1 |
| REQ-MDEV-005 | HyperConverged CR can be configured with discovered mediated device type values | TS-005: Verify that adding the discovered device type identifier to `spec.mediatedDevicesConfiguration.mediatedDeviceTypes` and the display name and resource name to `spec.permittedHostDevices.mediatedDevices` is accepted by the HCO | Tier 1 | P1 |
| REQ-MDEV-006 | Mediated devices appear as allocatable resources on the node after HCO configuration | TS-006: Verify that after configuring the HyperConverged CR, running `oc get node <node> -o json \| jq '.status.allocatable'` shows the configured mediated device resource with a non-zero count | Tier 1 | P1 |
| REQ-MDEV-007 | VM can be created with a configured mediated device (vGPU) | TS-007: Verify that a VM spec referencing the mediated device resource name in `spec.domain.devices.gpus` can be created and the VM starts successfully with the device attached | Tier 1 | P1 |
| REQ-MDEV-008 | vGPU device is accessible inside the guest VM | TS-008: Verify that inside a running VM with an attached mediated device, the GPU is visible (e.g., via `lspci` showing an NVIDIA display device) | Tier 2 | P1 |
| REQ-MDEV-009 | Node-specific mediated device type override via `nodeMediatedDeviceTypes` works | TS-009: Verify that specifying `nodeMediatedDeviceTypes` with a `nodeSelector` targeting a specific GPU node overrides the global `mediatedDeviceTypes` for that node | Tier 1 | P2 |
| REQ-MDEV-010 | `resourceName` derivation from `mdevNameSelector` follows naming convention | TS-010: Verify that the `resourceName` value using underscores instead of spaces (e.g., `NVIDIA A2-2Q` becomes `nvidia.com/NVIDIA_A2-2Q`) is correctly recognized by the device plugin | Tier 1 | P2 |
| REQ-MDEV-011 | Behavior when no GPU hardware is present on the node | TS-011: Verify that on a node without GPU hardware, `/sys/class/mdev_bus/` is either empty or absent, and the procedure clearly indicates no GPUs are available | Tier 2 | P2 |
| REQ-MDEV-012 | Invalid mediated device type in HyperConverged CR is handled gracefully | TS-012: Verify that specifying a non-existent mediated device type in `mediatedDeviceTypes` does not cause HCO reconciliation errors and the device simply does not appear as allocatable | Tier 1 | P2 |
| REQ-MDEV-013 | Mismatched `mdevNameSelector` does not allocate devices | TS-013: Verify that when `mdevNameSelector` does not match any available device name on the node, no mediated devices are exposed for that selector | Tier 1 | P2 |
| REQ-MDEV-014 | Verification command confirms device allocation after configuration | TS-014: Verify that the documented verification command (`oc get node <node> -o json \| jq` with nvidia.com filter) correctly filters and displays only GPU-related allocatable resources with non-zero values | Tier 2 | P1 |
| REQ-MDEV-015 | End-to-end workflow: discovery through VM deployment | TS-015: Execute the complete documented workflow from node exploration through HCO configuration to VM creation with vGPU, verifying each step produces the expected output as documented | Tier 2 | P1 |
| REQ-MDEV-016 | Multiple mediated device types can be configured simultaneously | TS-016: Verify that multiple entries in `mediatedDeviceTypes` and `permittedHostDevices.mediatedDevices` can be configured and all specified types appear as allocatable resources | Tier 1 | P2 |

---

### **IV. Sign-off and Approval**

This Software Test Plan requires approval from the following stakeholders:

- **Reviewers:**
  - TBD / @tbd
  - TBD / @tbd
- **Approvers:**
  - TBD / @tbd
  - TBD / @tbd
