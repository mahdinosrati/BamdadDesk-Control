# Contributing

Use Python 3.12 and `requirements.lock`, then run `python -m pytest -q`. Run `bash -n install.sh manage.sh scripts/install-lib.sh`, `bash tests/test_installer.sh`, and the Docker smoke checks in `.github/workflows/ci.yml` on Linux. Never use real passwords or organization data in fixtures.

Keep changes focused. Preserve existing policy/API compatibility and add a regression test for changed behavior. When changing the option catalog, regenerate `policy-schema.json` and document required client changes. Update English and Persian text together. Retain bundled font attribution.

Submit a pull request describing the problem, behavior changed, test results and limitations. Contributions are under the repository's AGPL-3.0 license. Public deployments of modified versions must comply with that license, including its source availability obligations.
