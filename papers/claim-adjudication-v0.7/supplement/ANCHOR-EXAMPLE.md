### 7.5 A separate three-coordinate anchor example

This example instantiates Section 5.2 and is distinct from the two-action benchmark. Let the honest records for claim values 0 and 1 be 000 and 110. The first two coordinates carry data; the last is a reference anchor with honest value 0. A common bit flip gives the four orbits {000,111}, {001,110}, {010,101}, and {011,100}. Thus the honest records are in distinct orbits. Independent coordinate flips instead give one orbit containing all eight records.

The diagonal margin is one: the identity leaves two disagreements, while the common flip turns 110 into 001 and leaves only the anchor disagreement. With one arbitrary domain failure, raw observation 100 is reachable from 000 by changing the first data domain and from 110 by changing the second. The honest orbits are separate at zero faults, but exact adjudication does not tolerate one fault.

For n data domains and k anchor domains in the family of Section 5.2, the margin is min(n,k). The following cases make the separate roles of data multiplicity and anchors explicit; each coordinate is treated as its own failure domain.

| Data domains n | Anchor domains k | Honest records | Diagonal margin | Largest tolerated t | Product margin |
| --- | --- | --- | --- | --- | --- |
| 2 | 1 | 000 / 110 | 1 | 0 | 0 |
| 1 | 2 | 000 / 100 | 1 | 0 | 0 |
| 3 | 3 | 000000 / 111000 | 3 | 1 | 0 |

The retained anchor check considered 26 model/group pairs and 116 cardinality-budget comparisons, including grouped-failure controls; direct observations, the structural criterion, and the threshold agreed in that bounded suite. These checks support this example and its stated general derivation, not an empirical claim about independent anchor deployments. Source and result identities are recorded in SOURCE-PINS.json and the supplement README.

