# Openshift-virtualization-tests Test plan

## **Prevent VM Live Migration Between Different CPU Vendors (AMD/Intel) - Quality Engineering Plan**

### **Metadata & Tracking**

| Field | Details |
|:------|:--------|
| **Enhancement(s)** | N/A (Bug fix - no VEP) |
| **Feature in Jira** | [CNV-72354](https://issues.redhat.com/browse/CNV-72354) |
| **Jira Tracking** | Closed Loop: [CNV-72354](https://issues.redhat.com/browse/CNV-72354), Bug: [CNV-71957](https://issues.redhat.com/browse/CNV-71957) |
| **QE Owner(s)** | TBD |
| **Owning SIG** | sig-compute |
| **Participating SIGs** | sig-compute, sig-node |
| **Current Status** | Verified (Fix in CNV v4.21.0, PR merged 2025-12-05) |

### **Related GitHub Pull Requests**

| PR Link | Repository | Source Jira Issue | Status | Description |
|:--------|:-----------|:------------------|:-------|:------------|
| [kubevirt/kubevirt#16060](https://github.com/kubevirt/kubevirt/pull/16060) | kubevirt/kubevirt | CNV-71957 | Merged | Prevent VM migration between different CPU vendors by adding CPU vendor label matching to the migration controller target pod node selector |
| [kubevirt/kubevirt#16059](https://github.com/kubevirt/kubevirt/pull/16059) | kubevirt/kubevirt | CNV-71957 | Closed (superseded by #16060) | Initial approach to prevent cross-vendor migration via launcher pod label selector |

---

### **I. Motivation and Requirements Review (QE Review Guidelines)**

This section documents the mandatory QE review process. The goal is to understand the feature's value, technology, and testability prior to formal test planning.

#### **Root Cause Analysis**

Live migration of VMs between nodes with different CPU vendors (AMD and Intel) causes a guest kernel panic. The root cause is that KVM paravirtualized hypercall instructions differ between vendors:

- **AMD**: Uses `vmmcall` instruction (opcode `0F 01 D9`)
- **Intel**: Uses `vmcall` instruction (opcode `0F 01 C1`)

When a VM boots on an AMD host, the guest kernel sets `X86_FEATURE_VMMCALL` and uses the `vmmcall` instruction for KVM hypercalls. After live migration to an Intel host, the guest kernel still executes `vmmcall`, which causes a protection fault (error code `0x3`) on the Intel hypervisor, leading to a kernel panic in `kvm_kick_cpu()` via `__pv_queued_spin_unlock_slowpath`.

The crash manifests 9-15 minutes after migration when PV spinlock unlock operations trigger the hypercall. The crash was confirmed on RHEL 8 (kernel 4.18.0-553.x) and Alma 9 (kernel 5.14.0-570.x) guests.

The issue was enabled by KubeVirt's node labeling: AMD nodes had `cpu-model-migration.node.kubevirt.io/SandyBridge: "true"` set because they could emulate those CPU features, allowing VMs with `nodeSelector: cpu-model.node.kubevirt.io/SandyBridge` to be scheduled on AMD nodes despite the cross-vendor incompatibility.

#### **1. Requirement & User Story Review Checklist**

| Check | Done | Details/Notes | Comments |
|:------|:-----|:--------------|:---------|
| **Review Requirements** | [x] | Bug fix requirement: Prevent VMs from being live-migrated between nodes with different CPU vendors (Intel vs AMD). The migration controller must enforce CPU vendor affinity. | Requirements clearly defined in CNV-71957 and confirmed through kernel dump analysis. |
| **Understand Value** | [x] | Prevents guest kernel panics caused by cross-vendor VM migration. Without this fix, customers with mixed AMD/Intel clusters experience intermittent VM crashes 9-15 minutes after live migration. | Critical bug fix for production environments with heterogeneous CPU architectures. |
| **Customer Use Cases** | [x] | Customer had a mixed cluster with Intel (Cascadelake-Server) and AMD (EPYC-Milan) worker nodes. VMs configured with SandyBridge CPU model were migrated from AMD to Intel nodes, causing kernel panics. | Reported via customer support case. Affected multiple VMs across different guest OS types. |
| **Testability** | [x] | Testable by setting up a cluster with nodes labeled with different CPU vendor labels and attempting live migration. The fix should prevent migration from completing when source and target nodes have different CPU vendors. | Verification was performed by QE on CNV v4.21.0 build with mixed AMD/Intel nodes. |
| **Acceptance Criteria** | [x] | (1) VMs on AMD nodes cannot be migrated to Intel nodes, and vice versa. (2) VMs on same-vendor nodes can be migrated successfully. (3) Migration failure is reported clearly when cross-vendor migration is attempted. (4) CPU vendor label is propagated to the target pod node selector during migration. | Verified by QE: AMD-to-Intel migration fails; Intel-to-Intel migration succeeds. |
| **Non-Functional Requirements (NFRs)** | [x] | No performance impact for same-vendor migrations. No new metrics or alerts introduced. The fix adds a single label lookup during migration target pod creation, which has negligible overhead. | Existing migration monitoring and alerting remains applicable. |

#### **2. Technology and Design Review**

| Check | Done | Details/Notes | Comments |
|:------|:-----|:--------------|:---------|
| **Developer Handoff/QE Kickoff** | [x] | Fix was developed by Daniel Sionov (dasionov) based on initial investigation by Barak Mordehai. Reviewed and approved by xpivarc and Barakmor1. Root cause analysis provided by Lucas Oakley (SBR-Kernel) and Peter Xu (KVM). | Comprehensive root cause analysis documented in CNV-71957 comments. |
| **Technology Challenges** | [x] | (1) CPU vendor detection relies on node labels (`cpu-vendor.node.kubevirt.io/Intel` or `cpu-vendor.node.kubevirt.io/AMD`). If labels are missing, the fix gracefully degrades (no vendor constraint applied). (2) Decentralized migration path must also be handled, using source state node selectors. | Node labeling by virt-handler is critical for the fix to function. |
| **Test Environment Needs** | [x] | Requires a cluster with nodes from at least two different CPU vendors (Intel and AMD), or the ability to simulate this via node labels. Each vendor must have at least one schedulable worker node. | Mixed-vendor clusters may be difficult to provision in standard CI environments; label simulation may be necessary. |
| **API Extensions** | [x] | No new API fields. Uses existing `CPUModelVendorLabel` constant (`cpu-vendor.node.kubevirt.io/`). The fix adds vendor label to the target pod's `NodeSelector` map during migration. Also adds vendor label inclusion to `getNodeSelectorsFromNodeName()` for decentralized migration. | Minimal API surface change. |
| **Topology Considerations** | [x] | Affects any cluster with mixed CPU vendors. Single-vendor clusters are unaffected. The fix applies to both centralized and decentralized migration paths. | In mixed-vendor clusters, the pool of eligible migration target nodes is reduced to same-vendor nodes only. |

### **II. Software Test Plan (STP)**

This STP serves as the **overall roadmap for testing**, detailing the scope, approach, resources, and schedule.

#### **1. Scope of Testing**

This test plan covers the bug fix that prevents VM live migration between nodes with different CPU vendors (AMD vs Intel). The fix adds CPU vendor label matching to the migration controller's target pod node selector, ensuring VMs can only migrate to nodes with the same CPU vendor as the source node. Testing will validate the migration constraint enforcement, same-vendor migration compatibility, and edge cases around label presence and absence.

**In Scope:**

- CPU vendor label-based migration constraint enforcement
- Same-vendor migration continues to work (Intel-to-Intel, AMD-to-AMD)
- Cross-vendor migration is blocked (AMD-to-Intel, Intel-to-AMD)
- Migration failure behavior and error reporting for cross-vendor attempts
- Decentralized migration path vendor constraint enforcement
- Behavior when CPU vendor labels are missing from nodes
- Node labeler correctly assigns CPU vendor labels
- Interaction with existing host-model CPU label matching
- Existing node-labeller e2e test updates (CPU vendor label verification)

#### **2. Testing Goals**

##### **Positive Use Cases (Happy Path)**

- Verify that a VM on an Intel node can be successfully migrated to another Intel node
- Verify that a VM on an AMD node can be successfully migrated to another AMD node
- Verify that the CPU vendor label from the source node is added to the target pod's node selector during migration
- Verify that the migration controller correctly extracts the CPU vendor label from the source node's labels
- Verify that existing host-model CPU label matching continues to function alongside vendor label matching
- Verify that nodes are correctly labeled with `cpu-vendor.node.kubevirt.io/Intel` or `cpu-vendor.node.kubevirt.io/AMD` by the node labeler

##### **Negative Use Cases (Error Handling & Edge Cases)**

- Verify that a VM on an AMD node cannot be migrated to an Intel node (migration fails)
- Verify that a VM on an Intel node cannot be migrated to an AMD node (migration fails)
- Verify graceful behavior when source node has no CPU vendor label (no vendor constraint applied, migration proceeds)
- Verify that migration target pod already having a CPU vendor label in its node selector is not overridden
- Verify behavior when all same-vendor nodes are unavailable (migration should fail with scheduling error)

#### **3. Non-Goals (Testing Scope Exclusions)**

| Non-Goal | Rationale | PM/Lead Agreement |
|:---------|:----------|:-------------------|
| Kernel-level KVM hypercall validation | Kernel crash root cause is well understood and confirmed; testing at the guest kernel level is outside CNV QE scope | Out of scope for CNV QE |
| Performance benchmarking of migration with vendor check | The vendor label lookup adds negligible overhead; no performance regression expected | Not required |
| Non-x86 architectures (ARM, s390x) | CPU vendor label applies only to x86 (amd64) nodes; non-x86 nodes do not get vendor labels | Architecture-specific; not applicable |
| Cross-vendor VM start (without migration) | VMs can start on either vendor's nodes; the fix only constrains migration, not initial placement | By design |
| BIOS/firmware-level CPU feature validation | Feature emulation at the QEMU/KVM level is outside the scope of this fix | Covered by separate KVM testing |

#### **4. Test Strategy**

##### **A. Types of Testing**

| Item (Testing Type) | Applicable (Y/N or N/A) | Comments |
|:--------------------|:------------------------|:---------|
| **Functional Testing** | Y | Core testing of cross-vendor migration blocking, same-vendor migration success, vendor label propagation to target pod node selector, and decentralized migration path. |
| **Automation Testing** | Y | All test scenarios will be automated using Ginkgo v2 (tier 1) and pytest (tier 2). Upstream unit tests already added in PR #16060. |
| **Performance Testing** | N/A | Single label lookup during migration has negligible overhead. No performance-sensitive code paths introduced. |
| **Security Testing** | N/A | No new RBAC roles, no new API endpoints. Existing node label and migration RBAC controls apply. |
| **Usability Testing** | N/A | No UI changes. Migration failure is reported through existing VMI migration status. |
| **Compatibility Testing** | Y | Verify fix works on OCP 4.18+ with CNV 4.21.0+. Verify on both bare-metal and cloud-provider (IPI) clusters with mixed CPU vendors. |
| **Regression Testing** | Y | Verify that same-vendor migrations are not negatively impacted. Verify existing migration test suites pass without regression. Verify node-labeller correctly assigns vendor labels. |
| **Upgrade Testing** | Y | Verify behavior when upgrading from a CNV version without the vendor check to one with it. Existing VMs should have vendor constraint applied on next migration. |
| **Backward Compatibility Testing** | N/A | Fix is a constraint addition; no backward-compatible behavior to preserve. Old behavior (allowing cross-vendor migration) is the bug. |

##### **B. Potential Areas to Consider**

| Item | Description | Applicable (Y/N or N/A) | Comment |
|:-----|:------------|:------------------------|:--------|
| **Dependencies** | Dependent on deliverables from other components/products? | Y | Depends on virt-handler node labeling to set `cpu-vendor.node.kubevirt.io/` labels correctly. Depends on KubeVirt migration controller for target pod creation. |
| **Monitoring** | Does the feature require metrics and/or alerts? | N | No new metrics or alerts. Failed migrations are already tracked by existing migration metrics. |
| **Cross Integrations** | Does the feature affect other features/require testing by other components? | Y | Interacts with: (1) Node labeler (must set vendor labels), (2) Migration controller (adds vendor label to target pod), (3) Host-model CPU migration (existing label-based migration constraints), (4) Decentralized migration (vendor label in source state). |
| **UI** | Does the feature require UI? | N | No UI changes. Migration failures are visible through standard VM/VMI status. |

#### **5. Test Environment**

| Environment Component | Configuration | Specification Examples |
|:----------------------|:--------------|:-----------------------|
| **Cluster Topology** | Multi-node cluster with worker nodes from at least 2 CPU vendors | 5-node cluster: 1 control plane + 2 Intel workers + 2 AMD workers |
| **OCP & OpenShift Virtualization Version(s)** | OCP 4.18+ with CNV v4.21.0+ | OCP 4.18, CNV 4.21.0 |
| **CPU Virtualization** | Mixed vendor nodes with hardware virtualization enabled | Intel VT-x (Cascadelake-Server or newer) and AMD-V (EPYC-Milan or newer) |
| **Compute Resources** | Sufficient resources for live migration on each vendor's nodes | 16 GB RAM per worker node minimum |
| **Special Hardware** | Nodes with different CPU vendors (Intel and AMD) or ability to simulate via labels | Bare metal with mixed CPU vendors preferred |
| **Storage** | Shared storage for live migration (RWX PVCs) | OCS/ODF, NFS, or iSCSI with RWX support |
| **Network** | Standard cluster networking supporting live migration | OVN-Kubernetes or OpenShift SDN |
| **Required Operators** | OpenShift Virtualization operator | HyperConverged CR |
| **Platform** | Bare metal (preferred for real mixed-vendor testing) or IPI cloud with mixed instance types | Bare metal with Intel + AMD nodes |
| **Special Configurations** | Worker nodes must have `cpu-vendor.node.kubevirt.io/` labels set by virt-handler | Labels are automatically set by the node labeler component |

#### **5.5. Testing Tools & Frameworks**

| Category | Tools/Frameworks |
|:---------|:-----------------|
| **Test Framework** | Ginkgo v2 + Gomega (Tier 1 / Go), pytest (Tier 2 / Python) |
| **CI/CD** | OpenShift CI (Prow), Polarion for test case tracking |
| **Other Tools** | kubectl/oc CLI for node label inspection, virtctl for VM management and migration triggering |

#### **6. Entry Criteria**

The following conditions must be met before testing can begin:

- PR [kubevirt/kubevirt#16060](https://github.com/kubevirt/kubevirt/pull/16060) is merged and included in the target build
- Test cluster has worker nodes with at least two different CPU vendors (Intel and AMD), or nodes with simulated vendor labels
- Nodes are correctly labeled with `cpu-vendor.node.kubevirt.io/Intel` or `cpu-vendor.node.kubevirt.io/AMD`
- At least 2 schedulable worker nodes per CPU vendor for same-vendor migration testing
- Shared storage is available for live migration support
- KubeVirt migration controller is operational and migrations can be triggered

#### **7. Risks and Limitations**

| Risk Category | Specific Risk for This Feature | Mitigation Strategy | Status |
|:--------------|:-------------------------------|:--------------------|:-------|
| Timeline/Schedule | Fix is already merged and verified; no timeline risk for test development | Test development can begin immediately against available builds | [x] |
| Test Coverage | Mixed-vendor clusters may be difficult to provision in CI environments | Use node label simulation (manually labeling nodes) to test vendor constraint logic; supplement with real mixed-vendor testing on dedicated hardware | [ ] |
| Test Environment | Requires both Intel and AMD nodes in the same cluster, which is not standard CI configuration | Coordinate with lab team for mixed-vendor bare-metal cluster access; use label manipulation for CI testing | [ ] |
| Untestable Aspects | Actual kernel panic reproduction requires cross-vendor migration on unpatched builds, which is destructive and unreliable (intermittent 9-15 minute window) | Do not attempt to reproduce the kernel panic; focus on verifying the prevention mechanism (migration blocked) | [x] |
| Resource Constraints | Mixed-vendor clusters require additional hardware resources | Share mixed-vendor test environments across QE team; schedule test runs during off-peak hours | [ ] |
| Dependencies | Vendor labels must be correctly set by virt-handler node labeler; if labeling is broken, the fix is ineffective | Include node labeler verification in test scenarios; verify labels exist before testing migration constraints | [ ] |
| Other | Label simulation testing may not catch all real-world edge cases | Supplement with at least one test run on real mixed-vendor hardware | [ ] |

#### **8. Known Limitations**

- The fix relies on `cpu-vendor.node.kubevirt.io/` node labels being present. If these labels are missing from nodes (e.g., due to node labeler issues), the vendor constraint is not enforced and cross-vendor migration may still occur.
- The fix does not apply to non-x86 architectures. Nodes with `kubernetes.io/arch` other than `amd64` do not receive CPU vendor labels.
- The fix does not prevent VMs from being initially scheduled on a different-vendor node. Only live migration is constrained.
- The fix does not address other potential cross-vendor incompatibilities beyond the KVM hypercall instruction mismatch (e.g., CPU feature differences, TSC frequency mismatches).
- In clusters where all nodes have the same CPU vendor, the fix has no observable effect (vendor label is still added to the target pod but does not restrict scheduling).

---

### **III. Test Scenarios & Traceability**

This section provides a **high-level overview** of test scenarios mapped to requirements.

#### **1. Requirements-to-Tests Mapping**

| Requirement ID | Requirement Summary | Test Scenario(s) | Test Type(s) | Priority |
|:---------------|:--------------------|:-----------------|:-------------|:---------|
| REQ-VENDOR-001 | VMs must not be migrated between nodes with different CPU vendors | TS-001: Verify that migration from an AMD node to an Intel node fails with appropriate error | Tier 1 (Functional), Tier 2 (E2E) | P1 |
| REQ-VENDOR-002 | VMs must not be migrated between nodes with different CPU vendors (reverse direction) | TS-002: Verify that migration from an Intel node to an AMD node fails with appropriate error | Tier 1 (Functional), Tier 2 (E2E) | P1 |
| REQ-VENDOR-003 | Same-vendor migration (Intel-to-Intel) must continue to work | TS-003: Verify that a VM on an Intel node can be successfully migrated to another Intel node | Tier 1 (Functional), Tier 2 (E2E) | P1 |
| REQ-VENDOR-004 | Same-vendor migration (AMD-to-AMD) must continue to work | TS-004: Verify that a VM on an AMD node can be successfully migrated to another AMD node | Tier 1 (Functional), Tier 2 (E2E) | P1 |
| REQ-VENDOR-005 | CPU vendor label from source node is added to target pod node selector | TS-005: Verify that the target pod created during migration has the source node's CPU vendor label in its nodeSelector | Tier 1 (Functional) | P1 |
| REQ-VENDOR-006 | Decentralized migration respects CPU vendor constraint | TS-006: Verify that decentralized migration extracts vendor label from source state node selectors and applies it to the target pod | Tier 1 (Functional) | P1 |
| REQ-VENDOR-007 | Graceful behavior when CPU vendor label is missing from source node | TS-007: Verify that when the source node has no `cpu-vendor.node.kubevirt.io/` label, migration proceeds without vendor constraint (backward compatibility) | Tier 1 (Functional) | P1 |
| REQ-VENDOR-008 | Existing vendor label in template pod is not overridden | TS-008: Verify that if the template pod already has a CPU vendor label in its nodeSelector, the migration controller does not override it | Tier 1 (Functional) | P2 |
| REQ-VENDOR-009 | Node labeler assigns CPU vendor labels correctly on x86 nodes | TS-009: Verify that all x86 (amd64) worker nodes have `cpu-vendor.node.kubevirt.io/Intel` or `cpu-vendor.node.kubevirt.io/AMD` label set by the node labeler | Tier 1 (Functional) | P1 |
| REQ-VENDOR-010 | Node labeler does not assign CPU vendor labels on non-x86 nodes | TS-010: Verify that non-amd64 nodes do not have `cpu-vendor.node.kubevirt.io/` labels | Tier 1 (Functional) | P2 |
| REQ-VENDOR-011 | `getNodeSelectorsFromNodeName` includes CPU vendor label | TS-011: Verify that the host-model migration node selector extraction includes CPU vendor labels alongside host-model CPU labels and required feature labels | Tier 1 (Functional) | P1 |
| REQ-VENDOR-012 | Migration failure is clearly reported in VMI migration status | TS-012: Verify that when cross-vendor migration is blocked, the VMI migration object shows a Failed phase with clear indication of scheduling constraint | Tier 2 (E2E) | P2 |
| REQ-VENDOR-013 | VM stability after failed cross-vendor migration attempt | TS-013: Verify that after a cross-vendor migration attempt fails, the VM continues running on its original node without disruption | Tier 2 (E2E) | P1 |
| REQ-VENDOR-014 | Multiple migration attempts respect vendor constraint | TS-014: Verify that repeated migration attempts on a VM in a mixed-vendor cluster consistently enforce the vendor constraint | Tier 2 (E2E) | P2 |
| REQ-VENDOR-015 | Upgrade path: VMs on pre-fix builds get vendor constraint on next migration | TS-015: After upgrading from a CNV version without vendor checks to one with them, verify that existing VMs have the vendor constraint applied on their next migration | Tier 2 (E2E) | P2 |
| REQ-VENDOR-016 | Interaction with host-model CPU label migration constraints | TS-016: Verify that both CPU vendor labels and host-model CPU labels are applied to the target pod's nodeSelector, and both constraints are enforced during migration | Tier 1 (Functional) | P2 |

---

### **IV. Sign-off and Approval**

This Software Test Plan requires approval from the following stakeholders:

- **Reviewers:**
  - TBD / @tbd
  - TBD / @tbd
- **Approvers:**
  - TBD / @tbd
  - TBD / @tbd
