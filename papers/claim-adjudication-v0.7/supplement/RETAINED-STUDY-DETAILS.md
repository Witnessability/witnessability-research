## 8 Retained records of an authorization and effect study

### 8.1 Historical design and retained-record validation

The retained local-study package reports three authorization processes, one executor process, and three readback processes for each of sixteen controlled histories. The original source implements this design; the present audit checks its retained outputs without rerunning that process-based experiment. Two designated actions, A and B, target fresh files in a trial-specific directory. Each action includes a principal, exact target, resource, content, context, and request digest. Sensitivity is a synthetic integer policy attribute: the generator assigns 3 to histories designated authorized and 5 to histories designated unauthorized. The local rule permits values at most 4; this scale encodes the controlled test condition rather than measuring real-world sensitivity. An ALLOW decision establishes permission under that local rule; it does not establish moral authority or permission in an external institution.

The original executor code uses exclusive creation, writes the declared bytes, and calls fsync on the file descriptor. Its readback code inspects the files and compares content digests. The retained readback reports and file contents were checked together; no independent operating-system trace was recovered to attest the historical write or fsync calls. This supports presence of the expected bytes at the readback. It does not establish survival after a host crash, long-term durability, or absence of every other action. For intentionally unperformed actions the controlled directory has no corresponding file at readback; the general proposition that no action ever occurred is not inferred from that absence.

The controller intentionally exercises all four authorization/effect bits (u\_A, u\_B, x\_A, x\_B). This includes actions performed after DENY. The experiment is an observation study and is not an authorization-enforcing service; those controlled violations are labelled in the execution mode. Limiting the experiment to compliant executions would remove precisely the alternative histories needed to examine an authorization-plus-effect claim.

The original code signs reports with ephemeral Ed25519 keys, which do not identify real approving persons or independent organizations. The read-only audit verified all 224 retained signatures and rejected 224 new in-memory changes to their signed target fields. It found 16 request files containing 32 designated actions, 112 record files containing the 224 signed reports, and 16 retained effect files whose bytes matched the corresponding requests and reports. The reported 112 historical subprocess invocations agree with the code's seven-per-history design and the 112 record groups, but were not independently attested by an operating-system execution log. Three negative controls for the audit validator—an invalid signature, a changed signed payload, and a changed manifest digest—were rejected. Verification material, reports, requests, effects, and digest manifests are retained. Private signing keys are not included.

### 8.2 Declared semantic adapter

The finite observer evaluates p = u\_A ∧ x\_A, meaning that the local policy permits A and the expected A file is present at readback. It uses the semantic bits extracted after signature verification and exact target, request, run, and context checks. It does not treat signature bytes as additional truth-bearing coordinates. The three authorization processes agree on their extracted decision pairs; the three readers agree on their extracted effect pairs.

The bound projection keeps the A/B position and yields three copies of the pair (u\_A, u\_B) and three copies of (x\_A, x\_B). The deliberately degraded projection retains only the unordered pair in each report, equivalently its sum. The authentic originals remain available in the archive. This is an observation-adapter change: deleting bindings from a semantic presentation does not alter an original signed message while keeping its signature valid. The adapter simply ceases to use the information required by the exact target claim.

Trial identifiers are random, and the observer's question is normalized to A in the evaluated trial. Ground-truth history labels in the research archive describe experimental conditions and are not additional observer inputs. The distinction matters: an observer given the controller's labelled history table could recover the experimental truth by lookup. Our guarantee concerns the declared semantic observation, not every byte in the research archive or all possible contextual information.

### 8.3 Where simpler analysis succeeds and fails

An authentic ALLOW record alone supports a decision under the local rule. A readback alone supports the observed file content. In the bound presentation their properly scoped conjunction resolves p for all sixteen controlled histories. There is no benefit to claiming that a more elaborate theory was needed for that elementary successful case.

In contrast, histories (1,0,1,0) and (1,0,0,1) produce the same degraded projection: one approval and one effect are present, but their association differs. The first makes p true and the second makes it false. Counting valid signatures, or checking that some authorization and some effect exist, cannot distinguish them. A correct decoder therefore returns UNRESOLVED on that shared observation rather than approving the exact conjunction.

Table 4 reports classes of observations, not probabilities or performance estimates. The bound projection yields sixteen classes: twelve FALSE and four TRUE. The degraded projection yields nine: five FALSE, one TRUE, and three UNRESOLVED. The criterion supplies the opposite-claim pair and the observation equality as an explicit obstruction.

*Table 4. Retained-record study and declared failure interpretations.*

| Presentation and model | Distinct classes at zero faults | Unresolved classes | Margin | One arbitrary domain fault |
| --- | --- | --- | --- | --- |
| Bound, six hypothetically separate domains | 16 | 0 | 3 | Exact in that hypothetical model |
| Bound, one actual host domain | 16 | 0 | 1 | No exact guarantee |
| Unbound, either domain interpretation | 9 | 3 | 0 | Already fails at zero faults |

### 8.4 Concrete repairs and their limits

Restoring checked A/B binding in the adapter removes this zero-fault ambiguity. The repair is concrete at the retained-record analysis level: the bound adapter uses retained target/request/instance fields, whereas the degraded adapter discards the material association. No claim is made that a particular identifier syntax is universally necessary. Any justified binding preserving the relevant distinction can serve the same role.

For common failure, all keys, processes, policies, and files remain under the same host and controlling user. We consequently group the complete report bundle as one actual fault domain. Its opposite-claim margin is one, so tolerance of one arbitrary failure of that host cannot be established. Six signatures do not repair this. By Proposition 1, margin one does not even guarantee detection of a claim-changing substitution under one host failure. Separate process roles and signing keys do not establish administrative independence; the present audit does not independently attest the historical process invocations. The qualitative point that replicas under common control add no independence is not new; it underlies the cross-domain corroboration requirement of HANSARD \[14\]. The retained-record analysis computes margin one for the declared single-host domain model.

The six-domain interpretation in Table 4 is explicitly hypothetical. Under separately controlled, adequately bound report domains the finite benchmark has margin three and satisfies the one-domain threshold. Deploying that interpretation would require evidence of genuinely separate relevant control and observation dependencies. Adding processes or copying the records on the existing host does not supply that evidence. The unit-cost portfolio result in Section 7 is a design calculation, not a measured deployment cost or an executed repair of independence.

