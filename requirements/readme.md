All requirements for normal use are in `requirements.txt`.

We use a specific version of gunicorn to run the g2p studio in production, and don't want to introduce git as a dependency, so we separate these requirements here into `requirements.prod.txt`.

Requirements recommended for use during development but not needed for running g2p are separated into `requirements.dev.txt`.

Requirements needed for running tests are in `requirements.test.txt`.
