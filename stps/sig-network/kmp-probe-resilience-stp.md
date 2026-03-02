# Openshift-virtualization-tests Test plan

## **KubeMacPool (KMP) Liveness/Readiness Probe Resilience at Scale - Quality Engineering Plan**

### **Metadata & Tracking**

| Field                  | Details                                                                                                   |
|:-----------------------|:----------------------------------------------------------------------------------------------------------|
| **Enhancement(s)**     | [kubemacpool/pull/540](https://github.com/k8snetworkplumbingwg/kubemacpool/pull/540) (introduced probes), [kubemacpool/pull/570](https://github.com/k8snetworkplumbingwg/kubemacpool/pull/570) (fix) |
| **Feature in Jira**    | [CNV-62943](https://issues.redhat.com/browse/CNV-62943) - KMP readinessProbe and livenessProbe too low    |
| **Jira Tracking**      | [CNV-71903](https://issues.redhat.com/browse/CNV-71903) (Closed Loop), [CNV-62943](https://issues.redhat.com/browse/CNV-62943) (Bug), [CNV-66956](https://issues.redhat.com/browse/CNV-66956) (Scale Failure) |
| **QE Owner(s)**        | TBD                                                                                                       |
| **Owning SIG**         | SIG-Network                                                                                               |
| **Participating SIGs** | SIG-Scale                                                                                                 |
| **Current Status**     | Closed Loop - Fix Verified                                                                                |

**Document Conventions (if applicable):** KMP = KubeMacPool, CNV = Container-native Virtualization (OpenShift Virtualization)

### **Feature Overview**

KubeMacPool (KMP) is a component that manages MAC address allocation for virtual machines in OpenShift Virtualization. PR #540 introduced readiness and liveness probes to the KMP manager container to improve health monitoring. However, on production-scale clusters with 200+ namespaces, the probe timer values (initialDelaySeconds: 10/15, periodSeconds: 10/20, failureThreshold: 3) were too aggressive. The KMP pool manager initialization involves iterating over all cluster pods and VMs to build MAC address maps, which takes significantly longer on dense clusters. This caused the liveness probe to kill the container before initialization completed, resulting in CrashLoopBackOff.

The fix (PR #570) decoupled the readiness and liveness probes from the pool manager startup sequence. The controller-runtime now starts immediately and serves the liveness endpoint (`/healthz`) while the pool manager initializes asynchronously. The readiness endpoint (`/readyz`) only returns healthy after the pool manager completes initialization. This ensures the pod is not prematurely killed while still accurately reflecting readiness state.

This closed-loop ticket (CNV-71903) ensures that testing covers the scale scenario that exposed the original defect: clusters with 500+ VM namespaces where KMP must successfully initialize and remain stable.

---

### **I. Motivation and Requirements Review (QE Review Guidelines)**

This section documents the mandatory QE review process. The goal is to understand the feature's value,
technology, and testability before formal test planning.

#### **1. Requirement & User Story Review Checklist**

| Check                                  | Done | Details/Notes                                                                                                                                                                           | Comments |
|:---------------------------------------|:-----|:----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|:---------|
| **Review Requirements**                | [x]  | Reviewed CNV-71903 (closed loop), CNV-62943 (original bug), CNV-66956 (scale failure). Root cause: probe timers too aggressive for scale clusters.                                      | Original bug filed against v4.99.0.rhel9-2317 |
| **Understand Value**                   | [x]  | KMP is critical infrastructure for MAC address management. CrashLoopBackOff blocks CNV upgrades and prevents VM stop/start operations via webhook failure. Direct customer impact.       | Blocks CNV upgrade path; breaks VM lifecycle operations |
| **Customer Use Cases**                 | [x]  | Customers running 500+ VM namespaces on production clusters. KMP must remain stable during and after initialization on dense clusters.                                                  | Verified with 514 namespaces in fix validation |
| **Testability**                        | [x]  | Testable by deploying 500+ VM namespaces and verifying KMP pod stability. Pod restart and VM operations can be validated programmatically.                                              | Scale environment required |
| **Acceptance Criteria**                | [x]  | KMP pod reaches Ready state on clusters with 500+ VM namespaces. Pod does not enter CrashLoopBackOff. VM stop/start operations succeed through KMP webhook.                            | Derived from bug resolution and closed-loop comments |
| **Non-Functional Requirements (NFRs)** | [x]  | **Performance:** KMP must initialize within probe timeout on 500+ ns clusters. **Scalability:** Must support 500+ VM namespaces. **Reliability:** Pod must not crash-loop during init.  | Scale testing up to 500 VM namespaces per closed-loop feedback |

#### **2. Technology and Design Review**

| Check                            | Done | Details/Notes                                                                                                                                           | Comments |
|:---------------------------------|:-----|:--------------------------------------------------------------------------------------------------------------------------------------------------------|:---------|
| **Developer Handoff/QE Kickoff** | [x]  | Closed-loop retro summary provided. Fix decouples controller-runtime startup from pool manager initialization using async goroutine and atomic readiness flag. | [Retro doc linked in Jira comments](https://issues.redhat.com/browse/CNV-71903) |
| **Technology Challenges**        | [x]  | Requires scale environment with 500+ namespaces and VMs. Pool manager iterates all pods/VMs during init - time grows linearly with cluster density.      | CI/test clusters too small to reproduce; real/scale clusters needed |
| **Test Environment Needs**       | [x]  | Bare-metal or large-scale cluster capable of hosting 500+ VM namespaces. Dedicated scale test infrastructure recommended.                               | Automation command documented in Jira: `namespaceCount=500 vmsPerNamespace=1 ./run-workloads.sh per-host-density` |
| **API Extensions**               | [x]  | No new APIs. Changes are to KMP deployment manifests (probe config) and internal health endpoints (`/healthz`, `/readyz`).                               | Webhook endpoint `mutatevirtualmachines.kubemacpool.io` must be functional |
| **Topology Considerations**      | [x]  | Multi-node clusters required for realistic scale testing. Single-node clusters unlikely to reproduce the issue due to lower resource pressure.            | Fix validated on multi-node baremetal cluster |

### **II. Software Test Plan (STP)**

This STP serves as the **overall roadmap for testing**, detailing the scope, approach, resources, and schedule.

#### **1. Scope of Testing**

This test plan covers the verification of KubeMacPool (KMP) pod stability and functionality at scale, specifically ensuring that the liveness and readiness probe configurations do not cause premature pod termination on clusters with high namespace/VM density. The testing validates the fix introduced in PR #570, which decoupled probe health from pool manager initialization.

**Testing Goals**

- Verify KMP pod reaches Ready state on clusters with 500+ VM namespaces without entering CrashLoopBackOff
- Verify KMP pod recovers successfully after manual deletion on dense clusters
- Verify VM lifecycle operations (stop/start) function correctly through KMP webhook on dense clusters
- Verify KMP readiness probe accurately reflects pool manager initialization state
- Verify KMP liveness probe does not terminate the pod during extended initialization
- Verify KMP stability during and after CNV upgrade on dense clusters

**Out of Scope (Testing Scope Exclusions)**

| Out-of-Scope Item | Rationale | PM/ Lead Agreement |
|:-------------------|:----------|:-------------------|
| KMP MAC address allocation logic | Functional correctness of MAC allocation is covered by existing KMP functional tests, not this scale-focused plan | TBD |
| Kubernetes liveness/readiness probe mechanism | Platform-level functionality tested by Kubernetes upstream QE | N/A |
| Network policy interaction with health endpoints | Confirmed not needed per PR #540 review: "Health checks doesn't seem to be blocked by network-policy" | N/A |
| KMP cert-manager container probes | Explicitly excluded from PR #540 scope | N/A |

#### **2. Test Strategy**

| Item                           | Description                                                                                                                                                  | Applicable (Y/N or N/A) | Comments |
|:-------------------------------|:-------------------------------------------------------------------------------------------------------------------------------------------------------------|:------------------------|:---------|
| Functional Testing             | Validates that the feature works according to specified requirements and user stories                                                                        | Y | KMP pod stability, webhook functionality, VM operations at scale |
| Automation Testing             | Ensures test cases are automated for continuous integration and regression coverage                                                                          | Y | Scale workload automation via `run-workloads.sh per-host-density` |
| Performance Testing            | Validates feature performance meets requirements (latency, throughput, resource usage)                                                                       | Y | KMP initialization time on 500+ ns clusters; probe response latency |
| Security Testing               | Verifies security requirements, RBAC, authentication, authorization, and vulnerability scanning                                                              | N/A | No security-related changes in this fix |
| Usability Testing              | Validates user experience, UI/UX consistency, and accessibility requirements. Does the feature require UI? If so, ensure the UI aligns with the requirements | N/A | No UI components |
| Compatibility Testing          | Ensures feature works across supported platforms, versions, and configurations                                                                               | Y | Verify fix across OCP versions where KMP probes are deployed |
| Regression Testing             | Verifies that new changes do not break existing functionality                                                                                                | Y | Ensure probe decoupling does not break normal (small cluster) KMP behavior |
| Upgrade Testing                | Validates upgrade paths from previous versions, data migration, and configuration preservation                                                               | Y | CNV upgrade on dense cluster must not cause KMP CrashLoopBackOff |
| Backward Compatibility Testing | Ensures feature maintains compatibility with previous API versions and configurations                                                                        | N/A | No API changes |
| Dependencies                   | Dependent on deliverables from other components/products? Identify what is tested by which team.                                                             | Y | Depends on KMP upstream (k8snetworkplumbingwg/kubemacpool) delivering the fix |
| Cross Integrations             | Does the feature affect other features/require testing by other components? Identify what is tested by which team.                                           | Y | KMP webhook affects all VM stop/start operations; scale team coordination needed |
| Monitoring                     | Does the feature require metrics and/or alerts?                                                                                                              | Y | Pod restart count and CrashLoopBackOff events should be monitored |
| Cloud Testing                  | Does the feature require multi-cloud platform testing? Consider cloud-specific features.                                                                     | N/A | Issue is cluster-density dependent, not cloud-specific |

#### **3. Test Environment**

| Environment Component                         | Configuration | Specification Examples |
|:----------------------------------------------|:--------------|:-----------------------|
| **Cluster Topology**                          | Multi-node bare-metal cluster | Minimum 3 worker nodes, sufficient to host 500+ VMs |
| **OCP & OpenShift Virtualization Version(s)** | OCP 4.19+, CNV 4.20+ | CNV v4.20.5-7 or later with KMP fix included |
| **CPU Virtualization**                        | Standard | Intel VT-x / AMD-V enabled |
| **Compute Resources**                         | High-density | Sufficient RAM/CPU for 500+ lightweight VMs (1 VM per namespace) |
| **Special Hardware**                          | None | Standard bare-metal or nested virtualization capable hosts |
| **Storage**                                   | Standard CSI provider | Any supported storage class for VM boot disks |
| **Network**                                   | Standard cluster networking | OVN-Kubernetes or OpenShiftSDN |
| **Required Operators**                        | HCO, KubeVirt, CDI, KubeMacPool | All operators deployed via HyperConverged CR |
| **Platform**                                  | Bare-metal preferred | AWS/GCP possible but bare-metal preferred for scale |
| **Special Configurations**                    | 500+ namespaces with 1 VM each | `namespaceCount=500 vmsPerNamespace=1` workload configuration |

#### **3.1. Testing Tools & Frameworks**

| Category           | Tools/Frameworks |
|:-------------------|:-----------------|
| **Test Framework** | Ginkgo v2 + Gomega (Tier 1), pytest (Tier 2) |
| **CI/CD**          | OpenShift CI, Jenkins (scale jobs) |
| **Other Tools**    | `run-workloads.sh per-host-density` (scale workload generator), `virtctl`, `oc` CLI |

#### **4. Entry Criteria**

The following conditions must be met before testing can begin:

- [x] Requirements and design documents are **approved and merged**
- [ ] Test environment can be **set up and configured** (see Section II.3 - Test Environment)
- [ ] KMP fix (PR #570) is included in the CNV build under test
- [ ] Scale cluster with 500+ namespace capacity is provisioned
- [ ] Scale workload tooling (`run-workloads.sh`) is available and validated

#### **5. Risks**

| Risk Category        | Specific Risk for This Feature | Mitigation Strategy | Status |
|:---------------------|:-------------------------------|:--------------------|:-------|
| Timeline/Schedule    | Scale environment provisioning may delay testing | Pre-allocate scale cluster; coordinate with scale team | [ ] |
| Test Coverage        | CI environments too small to reproduce the defect | Dedicated scale job with 500+ namespaces | [ ] |
| Test Environment     | Insufficient hardware for 500+ VM namespaces | Use lightweight VMs (minimal resources per VM) to maximize density | [ ] |
| Untestable Aspects   | Exact timing of probe failures depends on cluster load | Use conservative thresholds; test with worst-case density | [ ] |
| Resource Constraints | Scale tests require significant cluster resources and time | Schedule scale tests in off-peak windows; parallelize where possible | [ ] |
| Dependencies         | KMP upstream fix must be included in CNV build | Track upstream PR #570 merge and downstream rebase | [x] |
| Other                | Node reboot during KMP init may mask probe issues | Include node disruption scenarios in scale tests | [ ] |

#### **6. Known Limitations**

- The defect is only reproducible on clusters with 200+ namespaces; standard CI clusters with fewer than 50 namespaces will not trigger the CrashLoopBackOff condition.
- The exact initialization time for KMP pool manager depends on cluster size, API server responsiveness, and network latency -- probe timer thresholds may need tuning for extremely large clusters (10,000+ VMs).
- CNV-66956 describes a separate but related issue where KMP fails to iterate over all cluster pods at 10K VM scale. This test plan focuses on the probe-related CrashLoopBackOff (CNV-62943/CNV-71903), not the pod iteration failure.

---

### **III. Test Scenarios & Traceability**

This section links requirements to test coverage, enabling reviewers to verify all requirements are tested.

#### **1. Requirements-to-Tests Mapping**

| Requirement ID | Requirement Summary | Test Scenario(s) | Tier | Priority |
|:---------------|:--------------------|:-----------------|:-----|:---------|
| CNV-71903 | KMP pod stability at scale during initialization | Verify KMP pod reaches Ready state with 500+ VM namespaces | Tier 1 (Functional) | P0 |
|  |  | Verify KMP pod does not enter CrashLoopBackOff on dense cluster | Tier 1 (Functional) | P0 |
|  |  | Verify KMP pod restart count remains zero during normal operation at scale | Tier 1 (Functional) | P1 |
|  |  | Verify KMP initialization completes within liveness probe window at scale | Tier 1 (Functional) | P0 |
| CNV-62943 | KMP readiness probe accurately reflects pool manager state | Verify readiness endpoint returns not-ready during pool initialization | Tier 1 (Functional) | P0 |
|  |  | Verify readiness endpoint returns ready after pool initialization completes | Tier 1 (Functional) | P0 |
|  |  | Verify liveness endpoint remains healthy during extended pool initialization | Tier 1 (Functional) | P0 |
|  |  | Verify error when readiness probe fails due to pool manager crash | Tier 1 (Functional) | P1 |
| CNV-71903 | KMP pod recovery after deletion on dense clusters | Verify KMP pod recovers after manual deletion on 500+ ns cluster | Tier 1 (Functional) | P0 |
|  |  | Verify KMP pod reaches Ready within expected time after restart at scale | Tier 1 (Functional) | P1 |
|  |  | Verify failure when KMP pod cannot connect to API server during init | Tier 1 (Functional) | P1 |
| CNV-71903 | VM lifecycle operations function through KMP webhook at scale | Verify VM stop succeeds through KMP webhook on dense cluster | Tier 1 (Functional) | P0 |
|  |  | Verify VM start succeeds through KMP webhook on dense cluster | Tier 1 (Functional) | P0 |
|  |  | Verify webhook rejection when KMP is not ready (during initialization) | Tier 1 (Functional) | P1 |
| CNV-71903 | KMP stability during CNV upgrade on dense clusters | Verify KMP remains stable during CNV upgrade with 500+ VM namespaces | Tier 2 (End-to-End) | P0 |
|  |  | Verify VM operations resume after CNV upgrade completes on dense cluster | Tier 2 (End-to-End) | P1 |
|  |  | Verify KMP pod does not CrashLoopBackOff during rolling upgrade at scale | Tier 2 (End-to-End) | P0 |
| CNV-66956 | KMP stability under node disruption at scale | Verify KMP recovers after node reboot on 500+ ns cluster | Tier 2 (End-to-End) | P1 |
|  |  | Verify KMP handles concurrent VM deletions without crash-looping | Tier 2 (End-to-End) | P1 |
|  |  | Verify KMP pod stability during simulated node upgrade (`oc adm reboot-machine-config-pool`) | Tier 2 (End-to-End) | P1 |

---

### **IV. Sign-off and Approval**

This Software Test Plan requires approval from the following stakeholders:

* **Reviewers:**
  - [TBD / @tbd]
  - [TBD / @tbd]
* **Approvers:**
  - [TBD / @tbd]
  - [TBD / @tbd]
