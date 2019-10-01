The contents of this directory are for building and running Docker images for PIVT deployment and testing.

- **Dockerfile**: Creates a development PIVT image to run on a development workstation.

- **Dockerfile.prod**: Creates a production PIVT image.

- **Dockerfile.unittest**: Creates a unit testing image.

- **Dockerfile.functest**: Creates a functional testing image meant to be the "tester", running tests against a separate running PIVT container (built using Dockerfile.prod).

- **build.sh**: Builds a PIVT image.

- **start.sh**: Starts a PIVT container.

- **stop.sh**: Stops a running PIVT container.

- **restart.sh**: Runs `stop.sh` and `start.sh`.

- **build-run.sh**: Runs `build.sh` and `restart.sh`.

- **unit-test.sh**: Builds a unit testing image with the PIVT code and required unit testing dependencies, then runs it. Removed container and image when done.

- **func-test.sh**: Builds a PIVT image, a PIVT functional testing image, and runs them. Removed containers and images when done.

- **build-functest-local.sh**: Builds a functional testing image for repeated use. Used for developing functional tests.

- **run-functest-local.sh**: Runs functional testing image to execute functional tests against an already running PIVT container. Used for developing functional tests.

- **splunk_etc directories**: These directories contain Splunk config files for use in a production PIVT image and a PIVT image meant for functional testing.
