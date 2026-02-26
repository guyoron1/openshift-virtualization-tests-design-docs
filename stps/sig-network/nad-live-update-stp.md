# Openshift-virtualization-tests Test plan

## **Live Update of NAD Reference on Running VM - Quality Engineering Plan**

### **Metadata & Tracking**

| Field | Details |
|:-----------------------|:------------------------------------------------------------------|
| **Enhancement(s)** | [VEP #140: Live Update NAD Reference](https://github.com/kubevirt/enhancements/blob/main/veps/sig-network/hotpluggable-nad-ref.md) |
| **Feature in Jira** | [CNV-72329](https://issues.redhat.com/browse/CNV-72329) |
| **Jira Tracking** | Epic: [CNV-72329](https://issues.redhat.com/browse/CNV-72329), Parent: [VIRTSTRAT-560](https://issues.redhat.com/browse/VIRTSTRAT-560) |
| **QE Owner(s)** | TBD |
| **Owning SIG** | sig-network |
| **Participating SIGs** | sig-network |
| **Current Status** | Draft |

**Document Conventions (if applicable):** N/A

### **Feature Overview**

This feature allows VM administrators to change the NetworkAttachmentDefinition (NAD) reference on a running VM's secondary network interface without requiring a VM restart. When the `LiveUpdateNADRef` feature gate is enabled, updating the `networkName` field in the VM spec takes effect transparently. After the update, the VM is connected to the new network while guest interface properties such as MAC address and interface name are preserved. The feature is scoped to secondary networks using bridge binding only.

---

### **I. Motivation and Requirements Review (QE Review Guidelines)**

This section documents the mandatory QE review process. The goal is to understand the feature's value, technology, and testability before formal test planning.

#### **1. Requirement & User Story Review Checklist**

| Check | Done | Details/Notes | Comments |
|:---------------------------------------|:-----|:----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|:---------|
| **Review Requirements** | [ ] | Reviewed the relevant requirements. | VEP #140 merged (kubevirt/enhancements#138, 2025-12-18). |
| **Understand Value** | [ ] | Confirmed clear user stories and understood. <br/>Understand the difference between U/S and D/S requirements<br/> **What is the value of the feature for RH customers**. | Enables network reassignment (e.g., VLAN change) without VM downtime, preserving workload continuity. |
| **Customer Use Cases** | [ ] | Ensured requirements contain relevant **customer use cases**. | Primary use case: VM admin swaps guest uplink between networks (e.g., VLAN change) with minimal service disruption. VEP #140 user story covers this. |
| **Testability** | [ ] | Confirmed requirements are **testable and unambiguous**. | Testable via API patching and network connectivity checks. |
| **Acceptance Criteria** | [ ] | Ensured acceptance criteria are **defined clearly** (clear user stories; D/S requirements clearly defined in Jira). | NAD reference change takes effect without restart, VM connects to new network, bridge binding only. Feature gate controls availability. CNV-78912 (user feedback visibility) still in progress. |
| **Non-Functional Requirements (NFRs)** | [ ] | Confirmed coverage for NFRs, including Performance, Security, Usability, Downtime, Connectivity, Monitoring (alerts/metrics), Scalability, Portability (e.g., cloud support), and Docs. | No new scalability or performance constraints. |

#### **2. Technology and Design Review**

| Check | Done | Details/Notes | Comments |
|:---------------------------------|:-----|:--------------------------------------------------------------------------------------------------------------------------------------------------------|:---------|
| **Developer Handoff/QE Kickoff** | [ ] | A meeting where Dev/Arch walked QE through the design, architecture, and implementation details. **Critical for identifying untestable aspects early.** | QE kickoff should be scheduled during feature design phase. CNV-78912 (user feedback mitigation) should be discussed. |
| **Technology Challenges** | [ ] | Identified potential testing challenges related to the underlying technology. | NAD name normalization (namespace-qualified vs. unqualified) can cause false update triggers. Pod `network-status` annotation parsing treats malformed annotations as empty NAD name. |
| **Test Environment Needs** | [ ] | Determined necessary **test environment setups and tools**. | See Section II.3 - Test Environment for detailed requirements. |
| **API Extensions** | [ ] | Reviewed new or modified APIs and their impact on testing. | No new API fields. Existing `spec.networks[].multus.networkName` becomes live-updatable. New feature gate: `LiveUpdateNADRef`. |
| **Topology Considerations** | [ ] | Evaluated multi-cluster, network topology, and architectural impacts. | Both source and target nodes must have the target NAD's network infrastructure (bridge available). Non-migratable VMs cannot use this feature. |

### **II. Software Test Plan (STP)**

This STP serves as the **overall roadmap for testing**, detailing the scope, approach, resources, and schedule.

#### **1. Scope of Testing**

Testing covers the ability to change the NAD reference on a running VM's secondary network interface without restart. This includes verifying that the NAD change results in the VM connecting to the new network, that the feature is controlled by the `LiveUpdateNADRef` feature gate, and that existing network operations are not disrupted.

**Testing Goals**

- **P0:** Verify that changing the NAD reference on a running VM results in the VM being connected to the new network without restart
- **P0:** Verify that the `LiveUpdateNADRef` feature gate controls whether NAD changes are applied live or require restart
- **P1:** Verify that the VM maintains its guest interface properties (MAC address, interface name) after the NAD change
- **P1:** Verify correct behavior when the target NAD does not exist
- **P1:** Verify that existing NIC hotplug/unplug operations are not affected when the feature gate is enabled
- **P2:** Verify that multiple sequential NAD changes each result in correct network connectivity

**Out of Scope (Testing Scope Exclusions)**

| Out-of-Scope Item | Rationale | PM/ Lead Agreement |
|:-------------------|:----------|:-------------------|
| Migrating between CNI types | VEP #140 explicit non-goal | [ ] Name/Date |
| Changing the network binding/plugin | VEP #140 explicit non-goal | [ ] Name/Date |
| Seamless network connectivity during NAD reference change | Brief interruption is expected; VEP #140 explicit non-goal | [ ] Name/Date |
| NAD change on non-migratable VMs | Feature requires migratable VM configuration; VEP #140 explicit non-goal | [ ] Name/Date |
| Guest network reconfiguration after NAD swap | User responsibility; VEP #140 explicit non-goal | [ ] Name/Date |
| In-place NAD swapping via DNC | VEP #140 design avoids in-place swap to prevent DNC conflicts | [ ] Name/Date |

#### **2. Test Strategy**

| Item | Description | Applicable (Y/N or N/A) | Comments |
|:-------------------------------|:-------------------------------------------------------------------------------------------------------------------------------------------------------------|:------------------------|:---------|
| Functional Testing | Validates that the feature works according to specified requirements and user stories | Y | NAD reference change workflow, feature gate behavior, connectivity verification |
| Automation Testing | Ensures test cases are automated for continuous integration and regression coverage | Y | Upstream e2e tests in PR #16412 provide foundation; downstream in Ginkgo (tier 1) and pytest (tier 2) |
| Performance Testing | Validates feature performance meets requirements (latency, throughput, resource usage) | N/A | Migration performance covered by existing migration test suites; no new performance-sensitive code paths |
| Security Testing | Verifies security requirements, RBAC, authentication, authorization, and vulnerability scanning | N/A | No new RBAC roles, API endpoints, or security boundaries |
| Usability Testing | Validates user experience, UI/UX consistency, and accessibility requirements. Does the feature require UI? If so, ensure the UI aligns with the requirements | N/A | Feature is API-driven; no UI changes |
| Compatibility Testing | Ensures feature works across supported platforms, versions, and configurations | Y | Verify coexistence with existing NIC hotplug/unplug and link state management operations |
| Regression Testing | Verifies that new changes do not break existing functionality | Y | Code changes affect VM controller sync, migration evaluator, and restart-required detection — all shared with existing network features |
| Upgrade Testing | Validates upgrade paths from previous versions, data migration, and configuration preservation | N/A | Feature is a one-time operation (patching a VM spec field) gated behind a new feature gate with no persistent state migration |
| Backward Compatibility Testing | Ensures feature maintains compatibility with previous API versions and configurations | Y | Disabling the feature gate must restore previous behavior (NAD changes require restart) |
| Dependencies | Dependent on deliverables from other components/products? Identify what is tested by which team. | N/A | No team delivery dependencies; Multus CNI and bridge CNI are pre-existing platform infrastructure |
| Cross Integrations | Does the feature affect other features/require testing by other components? Identify what is tested by which team. | Y | Shares code paths with NIC hotplug/unplug and live migration; regression verification needed |
| Monitoring | Does the feature require metrics and/or alerts? | N/A | No new metrics or alerts; existing migration metrics apply |
| Cloud Testing | Does the feature require multi-cloud platform testing? Consider cloud-specific features. | N/A | Feature operates at the KubeVirt layer; no cloud-specific considerations |

#### **3. Test Environment**

| Environment Component | Configuration | Specification Examples |
|:----------------------------------------------|:--------------|:-----------------------|
| **Cluster Topology** | Multi-node cluster with at least 2 schedulable worker nodes | 3-node cluster (1 control plane + 2 workers) |
| **OCP & OpenShift Virtualization Version(s)** | OCP 4.22 with OpenShift Virtualization 4.22 | OCP 4.22, CNV 4.22 |
| **CPU Virtualization** | Standard virtualization-enabled nodes | Intel VT-x or AMD-V enabled |
| **Compute Resources** | Sufficient resources for live migration (source + target VM memory) | 16 GB RAM per worker node minimum |
| **Special Hardware** | N/A | N/A |
| **Storage** | Shared storage for live migration (RWX PVCs or LiveMigrate-compatible storage) | OCS/ODF, NFS, or iSCSI with RWX support |
| **Network** | Multiple bridge-based NetworkAttachmentDefinitions on each worker node | Two bridge NADs with different bridges (e.g., br-1, br-2) |
| **Required Operators** | OpenShift Virtualization operator, Multus CNI (default in OCP) | HyperConverged CR |
| **Platform** | Bare metal or nested virtualization with migration support | Bare metal preferred |
| **Special Configurations** | `WorkloadUpdateMethods=LiveMigrate`, `VMRolloutStrategy=LiveUpdate`, feature gate `LiveUpdateNADRef` enabled | HyperConverged CR with LiveMigrate workload update strategy |

#### **3.1. Testing Tools & Frameworks**

| Category | Tools/Frameworks |
|:-------------------|:-----------------|
| **Test Framework** | |
| **CI/CD** | |
| **Other Tools** | |

#### **4. Entry Criteria**

The following conditions must be met before testing can begin:

- [ ] Requirements and design documents are **approved and merged**
- [ ] Test environment can be **set up and configured** (see Section II.3 - Test Environment)
- [ ] Feature implementation is merged and included in the target build
- [ ] `LiveUpdateNADRef` feature gate is available in KubeVirt configuration
- [ ] CNV-78912 (user feedback mitigation) design is finalized and its impact on testability is assessed

#### **5. Risks**

| Risk Category | Specific Risk for This Feature | Mitigation Strategy | Status |
|:---------------------|:-------------------------------|:--------------------|:-------|
| Timeline/Schedule | PR #16412 is open with active review; merge timeline may affect test development | Begin test development using upstream e2e tests as reference; track PR status | [ ] |
| Test Coverage | NAD name normalization logic (namespace-qualified vs. unqualified) may produce edge cases not covered by upstream tests | Add dedicated test scenarios for namespace-qualified NAD name pairs; reviewer flagged this in PR | [ ] |
| Test Environment | N/A | N/A | [ ] |
| Untestable Aspects | User feedback issue (CNV-78912): users/UI/e2e tests cannot currently tell if the network change was applied | Track CNV-78912 resolution; adjust tests once mitigation design is finalized | [ ] |
| Resource Constraints | N/A | N/A | [ ] |
| Dependencies | N/A | N/A | [ ] |
| Other | Missing or misconfigured target NAD may cause unbounded retry loop; no retry limit is enforced on NAD reference change (flagged in PR review) | Validate behavior when target NAD does not exist; confirm error reporting and absence of infinite retry; escalate to development if retry is unbounded | [ ] |

#### **6. Known Limitations**

- Only bridge binding type is supported for NAD reference live update. Other binding types (SR-IOV, macvtap, passt) are not supported.
- Non-migratable VMs cannot use this feature; the update mechanism requires migratable VM configuration.
- Brief network connectivity interruption is expected during NAD reference change. Seamless connectivity is explicitly not a goal.
- Guest network configuration (IP address, routes) is not automatically updated after the NAD swap; the VM owner must handle guest-side reconfiguration if needed.
- In-place NAD swapping (without migration) is not supported, even on clusters with Dynamic Networks Controller.
- Users/UI/e2e tests cannot currently tell if the network change was applied (CNV-78912 mitigation in progress).

---

### **III. Test Scenarios & Traceability**

This section links requirements to test coverage, enabling reviewers to verify all requirements are tested.

#### **1. Requirements-to-Tests Mapping**

| Requirement ID | Requirement Summary | Test Scenario(s) | Tier | Priority |
|:---------------|:--------------------|:-----------------|:-----|:---------|
| CNV-72329 | NAD reference can be changed on a running VM without restart | Verify NAD reference change takes effect and VM connects to new network | Tier 1 | P0 |
| | | Verify end-to-end NAD change workflow including connectivity on new network and loss of connectivity on old network | Tier 2 | P0 |
| | Feature gate controls whether NAD changes are applied live | Verify VM requires restart after NAD change when feature gate is disabled | Tier 1 | P0 |
| | | Verify feature gate disabled behavior end-to-end: VM requires restart after NAD change | Tier 2 | P0 |
| | VM maintains guest interface properties after NAD change | Verify MAC address and interface name are preserved after NAD reference change | Tier 1 | P1 |
| | VM connects to correct network after NAD change | Verify post-update network connectivity on new NAD via peer VM communication | Tier 2 | P1 |
| | Non-existent NAD reference is handled gracefully | Verify behavior when NAD reference is changed to a non-existent NAD | Tier 1 | P1 |
| | | Verify VM state and recovery after failed update attempt due to non-existent target NAD | Tier 2 | P1 |
| | As an admin, I can modify the VM's NAD reference without triggering a restart | Verify VM stays running without restart after NAD-only change | Tier 1 | P1 |
| | Backward compatibility: non-NAD network property changes are unaffected by this feature | Verify that changing non-NAD properties (e.g., binding type) still requires VM restart even with feature gate enabled | Tier 1 | P2 |
| | Existing NIC hotplug operations are unaffected by feature gate | Verify bridge interface hotplug/unplug continues to work correctly when feature gate is enabled | Tier 1 | P1 |
| | | Verify NIC hotplug followed by NAD change both complete correctly on the same VM | Tier 2 | P2 |
| | Multiple sequential NAD changes produce correct results | Verify multiple NAD reference changes in sequence each result in correct connectivity | Tier 2 | P2 |
| | Namespace-qualified NAD names are handled correctly | Verify NAD reference change works with namespace-qualified NAD names (e.g., `namespace/nad-name`) | Tier 1 | P2 |
| | VM spec reflects NAD reference change after update | Verify that VM spec NAD reference change is propagated to VMI spec networks after update | Tier 1 | P1 |
| | Existing network feature behavior is not regressed | Verify that existing SR-IOV and bridge hotplug triggers continue to produce correct conditions | Tier 1 | P1 |

---

### **IV. Sign-off and Approval**

This Software Test Plan requires approval from the following stakeholders:

* **Reviewers:**
  - [Name / @github-username]
  - [Name / @github-username]
* **Approvers:**
  - [Name / @github-username]
  - [Name / @github-username]
