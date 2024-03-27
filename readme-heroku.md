Our production Heroku deployment is controlled by the following files:
 - `Procfile`: tells Heroku what command to launch in each Dyno;
 - `runtime.txt`: tells Heroku which run-time engine to use (i.e., which version of Python);

   Heroku detects Python by default, but `runtime.txt` lets us specify/bump the version as needed;
 - `requirements.txt`: tells Heroku what our production dependencies
   are.  This is managed by `hatch` now.  You will need to make sure
   the Python version in the `[tool.hatch.envs.prod]` section matches
   the one in `runtime.txt`.  Now you can update the requirements with:

        hatch env remove prod
        rm -f requirements.txt
        hatch env create prod
