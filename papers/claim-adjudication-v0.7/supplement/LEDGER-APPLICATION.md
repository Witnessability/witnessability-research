# Retained ledger application and replay scope

Section 8.2 uses four declared models and projected observations from a retained single-host PostgreSQL 18.6 study. The claim concerns admitted ledger actions in one database incarnation and epoch through its action seal. The business claim is distinct and needs the stated business-to-ledger premise.

## Evidence and provenance

The original archive is 1,691,040 bytes with SHA-256 5223360f08d91ea0f76dd097c989623c51861f67c5ca6643d69d4f4e5f476e3b. It contains 1,915 manifest-listed files plus the manifest. Its recorded source commit is b884e386dd36e381e7fc38323f8986b01a189c56. A selected read-only validation checked that inventory, 18 frozen source/input files and additional context bindings for 11 envelopes. It recomputed 28 finite verdicts and matched three admission refusals to retained results. These counts distinguish the 23 primary ledger cases from eight controls.

The raw archive and operational transcripts are excluded from this selected reader package. The included data/ledger-projection.json contains the four finite models, 31 projected case rows and source snapshot hashes. Those hashes are provenance identifiers; without the raw archive they do not independently authenticate the projection. Three admission refusals are retained as reported outcomes and are not recomputed by the reader replay.

## Reader replay

From the supplement directory:
```sh
python3 -I -B code/replay_ledger.py > ledger-replay.json
python3 -I -B code/search_capture.py > search-capture-replay.json
```

Compare the first result with expected/ledger-projection.json and the second with expected/search-capture.json. The first recomputes 28 verdicts and four margins from the included model data. It does not reproduce archive validation, context admission, signature verification or a native database/checker run.

The exact-ledger model has margin one and a one-domain minimum deciding portfolio at zero faults. The omission model has margin zero and an empty observation shared by opposite claims. The conditional business model has margin zero globally even though an empty record decides business absence under its premise; a nonempty record can concern another action. Without that premise, empty is ambiguous as well. None of these single-domain models tolerates one arbitrary faulty domain.

## Constructed search/capture cases

The second replay uses four histories (B,C,R) satisfying R <= C <= B. These bits represent an action, its source record and a returned record. Search completeness excludes C=1,R=0. Capture completeness excludes B=1,C=0. The conditions are admitted premises, not self-authenticating fields. All eight combinations of a positive return and the two conditions are checked.

An empty return requires both conditions for the action-absence conclusion in this declared model. Either condition alone leaves a displayed opposite-truth pair. A positive, admitted and bound witness refutes absence under the no-false-positive assumption. These are logical premise selections, not independent failure domains or an application of Corollary 3 to new hardware.

The engineering result is a proposed consumer separation of search and capture obligations. No deployed Audit Store, AAR conformance implementation, new PostgreSQL experiment or externally independent validation is claimed.
