# Openshift-virtualization-tests Test plan

## **Live Update of NAD Reference on Running VM - Quality Engineering Plan**

### **Metadata & Tracking**

- **Enhancement(s):** [VEP #140: Live Update NAD Reference](https://github.com/kubevirt/enhancements/blob/main/veps/sig-network/hotpluggable-nad-ref.md)
- **Feature Tracking:** [VIRTSTRAT-560](https://issues.redhat.com/browse/VIRTSTRAT-560)
- **Epic Tracking:** [CNV-72329](https://issues.redhat.com/browse/CNV-72329)
- **QE Owner(s):** TBD
- **Owning SIG:** sig-network
- **Participating SIGs:** sig-network

**Document Conventions (if applicable):** N/A

### **Feature Overview**

This feature allows VM administrators to change the NetworkAttachmentDefinition (NAD) reference on a running VM's secondary network interface without requiring a VM restart. The `LiveUpdateNADRef` feature gate controls this capability (enabled by default downstream). Updating the `networkName` field in the VM spec results in the VM connecting to the new network with minimal service disruption. Guest interface properties such as MAC address and interface name are preserved. The feature is scoped to secondary networks using bridge binding only.

---

### **I. Motivation and Requirements Review (QE Review Guidelines)**

This section documents the mandatory QE review process. The goal is to understand the feature's value, technology, and testability before formal test planning.

#### **1. Requirement & User Story Review Checklist**

- [ ] **Review Requirements**
  - Reviewed the relevant requirements.
  - VEP #140 merged (kubevirt/enhancements#138, 2025-12-18).
- [ ] **Understand Value and Customer Use Cases**
  - Confirmed clear user stories and understood.
  - Understand the difference between U/S and D/S requirements.
  - **What is the value of the feature for RH customers**.
  - Ensured requirements contain relevant **customer use cases**.
  - Enables network reassignment (e.g., VLAN change) without VM restart. Primary use case: VM admin swaps guest uplink between networks (e.g., VLAN change) with minimal service disruption. VEP #140 user story covers this.
- [ ] **Testability**
  - Confirmed requirements are **testable and unambiguous**.
  - Testable via API patching and network connectivity checks.
- [ ] **Acceptance Criteria**
  - Ensured acceptance criteria are **defined clearly** (clear user stories; D/S requirements clearly defined in Jira).
  - NAD reference change takes effect without restart, VM connects to new network, bridge binding only. Feature gate controls availability. CNV-78912 (user feedback visibility) still in progress.
- [ ] **Non-Functional Requirements (NFRs)**
  - Confirmed coverage for NFRs, including Performance, Security, Usability, Downtime, Connectivity, Monitoring (alerts/metrics), Scalability, Portability (e.g., cloud support), and Docs.
  - No new scalability or performance constraints.

#### **2. Known Limitations**

- Only bridge binding type is supported for NAD reference live update. Other binding types (SR-IOV, macvtap, passt) are not supported.
- Non-migratable VMs cannot use this feature; the update mechanism requires migratable VM configuration.
- Brief network connectivity interruption is expected during NAD reference change. Seamless connectivity is explicitly not a goal.
- Guest network configuration (IP address, routes) is not automatically updated after the NAD swap; the VM owner must handle guest-side reconfiguration if needed.
- In-place NAD swapping (without migration) is not supported, even on clusters with Dynamic Networks Controller.
- Users/UI/e2e tests cannot currently tell if the network change was applied (CNV-78912 mitigation in progress).

#### **3. Technology and Design Review**

- [ ] **Developer Handoff/QE Kickoff**
  - A meeting where Dev/Arch walked QE through the design, architecture, and implementation details. **Critical for identifying untestable aspects early.**
  - QE kickoff should be scheduled during feature design phase. CNV-78912 (user feedback mitigation) should be discussed.
- [ ] **Technology Challenges**
  - Identified potential testing challenges related to the underlying technology.
  - NAD name normalization (namespace-qualified vs. unqualified) can cause false update triggers. Pod `network-status` annotation parsing treats malformed annotations as empty NAD name.
- [ ] **Test Environment Needs**
  - Determined necessary **test environment setups and tools**.
  - See Section II.3 - Test Environment for detailed requirements.
- [ ] **API Extensions**
  - Reviewed new or modified APIs and their impact on testing.
  - No new API fields. Existing `spec.networks[].multus.networkName` becomes live-updatable. New feature gate: `LiveUpdateNADRef`.
- [ ] **Topology Considerations**
  - Evaluated multi-cluster, network topology, and architectural impacts.
  - Both source and target nodes must have the target NAD's network infrastructure (bridge available). Non-migratable VMs cannot use this feature.

### **II. Software Test Plan (STP)**

This STP serves as the **overall roadmap for testing**, detailing the scope, approach, resources, and schedule.

#### **1. Scope of Testing**

Testing covers the ability to change the NAD reference on a running VM's secondary network interface without restart. This includes verifying that the NAD change results in the VM connecting to the new network, that the feature is controlled by the `LiveUpdateNADRef` feature gate, and that existing network operations are not disrupted.

**Testing Goals**

- **P0:** Verify that changing the NAD reference on a running VM results in the VM being connected to the new network without restart
- **P0:** Verify that the `LiveUpdateNADRef` feature gate controls whether NAD changes are applied live or require restart
- **P0:** Verify that the VM maintains its guest interface properties (MAC address, interface name) after the NAD change
- **P1:** Verify correct behavior when the target NAD does not exist
- **P1:** Verify that existing NIC hotplug/unplug operations are not affected when the feature gate is enabled

**Out of Scope (Testing Scope Exclusions)**

- [ ] Migrating between CNI types -- *Rationale:* VEP #140 explicit non-goal -- *PM/Lead Agreement:* Name/Date
- [ ] Changing the network binding/plugin -- *Rationale:* VEP #140 explicit non-goal -- *PM/Lead Agreement:* Name/Date
- [ ] Seamless network connectivity during NAD reference change -- *Rationale:* Brief interruption is expected; VEP #140 explicit non-goal -- *PM/Lead Agreement:* Name/Date
- [ ] NAD change on non-migratable VMs -- *Rationale:* Feature requires migratable VM configuration; VEP #140 explicit non-goal -- *PM/Lead Agreement:* Name/Date
- [ ] Guest network reconfiguration after NAD swap -- *Rationale:* User responsibility; VEP #140 explicit non-goal -- *PM/Lead Agreement:* Name/Date
- [ ] In-place NAD swapping via DNC -- *Rationale:* VEP #140 design avoids in-place swap to prevent DNC conflicts -- *PM/Lead Agreement:* Name/Date

#### **2. Test Strategy**

**Functional**

- [x] **Functional Testing** -- Validates that the feature works according to specified requirements and user stories
  - *Details:* NAD reference change workflow, feature gate behavior, connectivity verification
- [x] **Automation Testing** -- Confirms test automation plan is in place for CI and regression coverage (all tests are expected to be automated)
  - *Details:* Upstream e2e tests in PR #16412 provide foundation; downstream in Ginkgo (tier 1) and pytest (tier 2)
- [x] **Regression Testing** -- Verifies that new changes do not break existing functionality
  - *Details:* Code changes affect VM controller sync, migration evaluator, and restart-required detection -- all shared with existing network features

**Non-Functional**

- [ ] **Performance Testing** -- Validates feature performance meets requirements (latency, throughput, resource usage)
  - *Details:* N/A -- Migration performance covered by existing migration test suites; no new performance-sensitive code paths
- [ ] **Scale Testing** -- Validates feature behavior under increased load and at production-like scale (e.g., large number of VMs, nodes, or concurrent operations)
  - *Details:* N/A
- [ ] **Security Testing** -- Verifies security requirements, RBAC, authentication, authorization, and vulnerability scanning
  - *Details:* N/A -- No new RBAC roles, API endpoints, or security boundaries
- [ ] **Usability Testing** -- Validates user experience and accessibility requirements
  - *Details:* N/A -- Feature is API-driven; no UI changes
- [ ] **Monitoring** -- Does the feature require metrics and/or alerts?
  - *Details:* N/A -- No new metrics or alerts; existing migration metrics apply

**Integration & Compatibility**

- [x] **Compatibility Testing** -- Ensures feature works across supported platforms, versions, and configurations
  - *Details:* Verify coexistence with existing NIC hotplug/unplug and link state management operations. Disabling the feature gate must restore previous behavior (NAD changes require restart).
- [ ] **Upgrade Testing** -- Validates upgrade paths from previous versions, data migration, and configuration preservation
  - *Details:* N/A -- Feature is a one-time operation (patching a VM spec field) gated behind a new feature gate with no persistent state migration
- [ ] **Dependencies** -- Blocked by deliverables from other components/products. Identify what we need from other teams before we can test.
  - *Details:* N/A -- No team delivery dependencies; Multus CNI and bridge CNI are pre-existing platform infrastructure
- [x] **Cross Integrations** -- Does the feature affect other features or require testing by other teams? Identify the impact we cause.
  - *Details:* Shares code paths with NIC hotplug/unplug and live migration; regression verification needed

**Infrastructure**

- [ ] **Cloud Testing** -- Does the feature require multi-cloud platform testing? Consider cloud-specific features.
  - *Details:* N/A -- Feature operates at the KubeVirt layer; no cloud-specific considerations

#### **3. Test Environment**

- **Cluster Topology:** Multi-node cluster with at least 2 schedulable worker nodes (3-node cluster: 1 control plane + 2 workers)
- **OCP & OpenShift Virtualization Version(s):** OCP 4.22 with OpenShift Virtualization 4.22 (OCP 4.22, CNV 4.22)
- **CPU Virtualization:** Standard virtualization-enabled nodes (Intel VT-x or AMD-V enabled)
- **Compute Resources:** Sufficient resources for live migration, source + target VM memory (16 GB RAM per worker node minimum)
- **Special Hardware:** N/A
- **Storage:** Shared storage for live migration, RWX PVCs or LiveMigrate-compatible storage (OCS/ODF, NFS, or iSCSI with RWX support)
- **Network:** Multiple bridge-based NetworkAttachmentDefinitions on each worker node (Two bridge NADs with different bridges, e.g., br-1, br-2)
- **Required Operators:** OpenShift Virtualization operator, Multus CNI (default in OCP) (HyperConverged CR)
- **Platform:** Bare metal or nested virtualization with migration support (Bare metal preferred)
- **Special Configurations:** `WorkloadUpdateMethods=LiveMigrate`, `VMRolloutStrategy=LiveUpdate`, feature gate `LiveUpdateNADRef` enabled (HyperConverged CR with LiveMigrate workload update strategy)

#### **3.1. Testing Tools & Frameworks**

- **Test Framework:**
- **CI/CD:**
- **Other Tools:**

#### **4. Entry Criteria**

The following conditions must be met before testing can begin:

- [ ] Requirements and design documents are **approved and merged**
- [ ] Test environment can be **set up and configured** (see Section II.3 - Test Environment)
- [ ] Feature implementation is merged and included in the target build
- [ ] `LiveUpdateNADRef` feature gate is available in KubeVirt configuration
- [ ] CNV-78912 (user feedback mitigation) design is finalized and its impact on testability is assessed

#### **5. Risks**

- [ ] **Test Coverage**
  - Risk: NAD name normalization logic (namespace-qualified vs. unqualified) may produce edge cases not covered by upstream tests
  - Mitigation: Add dedicated test scenarios for namespace-qualified NAD name pairs; reviewer flagged this in PR
- [ ] **Test Environment**
  - Risk: N/A
  - Mitigation: N/A
- [ ] **Untestable Aspects**
  - Risk: User feedback issue (CNV-78912): users/UI/e2e tests cannot currently tell if the network change was applied
  - Mitigation: Track CNV-78912 resolution; adjust tests once mitigation design is finalized
- [ ] **Resource Constraints**
  - Risk: N/A
  - Mitigation: N/A
- [ ] **Dependencies**
  - Risk: N/A
  - Mitigation: N/A
- [ ] **Other**
  - Risk: Missing or misconfigured target NAD may cause unbounded retry loop; no retry limit is enforced on NAD reference change (flagged in PR review)
  - Mitigation: Validate behavior when target NAD does not exist; confirm error reporting and absence of infinite retry; escalate to development if retry is unbounded

---

### **III. Test Scenarios & Traceability**

This section links requirements to test coverage, enabling reviewers to verify all requirements are tested.

#### **1. Requirements-to-Tests Mapping**

- **[CNV-72329]** -- As a VM admin, I want to change the NAD on a running VM and connect to the new network
  - *Test Scenario:* Verify VM is reachable on new network
  - *Priority:* P0
- **[CNV-72329]** -- As a VM admin, I want to change the NAD on a running VM and connect to the new network (E2E)
  - *Test Scenario:* Verify VM has connectivity on new network and loses connectivity on old network
  - *Priority:* P0
- **[CNV-72329]** -- As a VM admin, I want the feature gate to control whether NAD changes are applied live
  - *Test Scenario:* Verify NAD change requires restart when feature gate is disabled
  - *Priority:* P0
- **[CNV-72329]** -- As a VM admin, I want the feature gate to control whether NAD changes are applied live (E2E)
  - *Test Scenario:* Verify NAD change requires VM restart end-to-end when feature gate is disabled
  - *Priority:* P0
- **[CNV-72329]** -- As a VM admin, I want guest interface properties preserved after NAD change
  - *Test Scenario:* Verify MAC address and interface name are preserved
  - *Priority:* P0
- **[CNV-72329]** -- As a VM admin, I want graceful handling when target NAD does not exist
  - *Test Scenario:* Verify error is reported for non-existent NAD
  - *Priority:* P1
- **[CNV-72329]** -- As a VM admin, I want graceful handling when target NAD does not exist (E2E)
  - *Test Scenario:* Verify VM recovers after failed NAD update
  - *Priority:* P1
- **[CNV-72329]** -- As a VM admin, I want NAD changes applied without triggering a VM restart
  - *Test Scenario:* Verify VM does not restart after NAD change
  - *Priority:* P1
- **[CNV-72329]** -- As a VM admin, I want non-NAD network changes to still require restart
  - *Test Scenario:* Verify non-NAD property change still requires restart
  - *Priority:* P2
- **[CNV-72329]** -- As a VM admin, I want existing NIC hotplug to work with the feature gate enabled
  - *Test Scenario:* Verify NIC hotplug/unplug works with feature gate enabled
  - *Priority:* P1
- **[CNV-72329]** -- As a VM admin, I want existing NIC hotplug to work with the feature gate enabled (E2E)
  - *Test Scenario:* Verify NIC hotplug and NAD change both succeed on same VM
  - *Priority:* P2
- **[CNV-72329]** -- As a VM admin, I want namespace-qualified NAD names to work
  - *Test Scenario:* Verify NAD change works with namespace-qualified names
  - *Priority:* P2
- **[CNV-72329]** -- As a VM admin, I want the VM spec to reflect the NAD change
  - *Test Scenario:* Verify VMI spec shows updated NAD after change
  - *Priority:* P1
- **[CNV-72329]** -- As a VM admin, I want existing network features to continue working
  - *Test Scenario:* Verify SR-IOV and bridge hotplug are not regressed
  - *Priority:* P1

---

### **IV. Sign-off and Approval**

This Software Test Plan requires approval from the following stakeholders:

* **Reviewers:**
  - [Name / @github-username]
  - [Name / @github-username]
* **Approvers:**
  - [Name / @github-username]
  - [Name / @github-username]
