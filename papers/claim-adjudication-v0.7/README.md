# Claim Adjudication under Uncertain Binding and Shared Failures

Reproducibility supplement for the preprint by Mikhail A. Sergeev:
[version DOI 10.5281/zenodo.23871213](https://doi.org/10.5281/zenodo.23871213).
The Zenodo deposit contains the paper; this directory supplies its code and retained data separately.

Published PDF SHA-256:
`30900c712a7dec3464a4c43e94dad2f49d3f64d77c176469db4c1ed2cd6f198b`.

From this directory, using Python 3.12 and a virtual environment:

```sh
python -m pip install -r supplement/requirements.txt
python -B supplement/tools/reproduce_all.py --output /tmp/claim-adjudication-results
```

Choose a fresh output directory outside the supplement. The runner refuses existing output paths and disabled assertions. It runs the historical six checks and three expected rejection controls, followed by coalition concealment, ledger projection, search/capture completeness and exhaustive small-group checks. It compares computed JSON with retained expectations; only explicitly named runtime fields are omitted. Results are not blinded or independently authored verification.

`supplement/SOURCE-PINS.json` preserves the historical 180-file inventory. `supplement/RELEASE-PINS.json` covers all current scientific inputs, code, expected results and native records. The portable runner has been updated to check both inventories, so the later additions no longer invalidate the historical inventory. Scientific source files and retained results are unchanged from the paper's supplement. `MANIFEST.json` identifies every published file except itself.

The package validates retained signatures and finite models. It does not rerun the original file-producing experiment, execute Lean or Wolfram, prove the general theorem, or validate real PostgreSQL deployment assumptions. The ledger application is a finite projection. Native source and logs are retained with their stated limits; they do not constitute a complete Lean formalization.

Component licenses and attribution are in [LICENSE-NOTICE.md](LICENSE-NOTICE.md).

Mikhail A. Sergeev is the author of this work, prepared with assistance from AI assistants.
