### Production environment on Heroku

Our production Heroku deployment is controlled by the following files:
 - `Procfile`: tells Heroku what command to launch in each Dyno;
 - `.python-version`: tells Heroku which run-time engine to use (i.e., which version of Python);
 - `requirements.txt`: tells Heroku what our production dependencies are;
 - `bin/post_compile`: Heroku builds run this after doing `pip install -r requirements.txt`.

### Updating dependencies

Our dependencies are declared in `pyproject.toml`. This is where changes should be made first.

`requirements.txt` is the generated "lock" file that Heroku uses. To update it,
follow these steps on a **Linux** machine to match the Heroku context:

 - Install `hatch` with `pip install hatch hatch-pip-compile`, or use
   `uvx --with hatch-pip-compile hatch` instead of just `hatch`.

 - Make sure `[tool.hatch.envs.prod]` is configured correctly, e.g., with the
   desired Python version, i.e., the same major.minor as found in `.python-version`.

 - Regenerate `requirements.txt`:

       hatch env remove prod
       rm requirements.txt
       hatch env create prod

It is also possible to edit `requirements.txt` manually, e.g., to handle a
critical vulnerability report, but an occasional full rebuild is a good idea to
keep things up to date.
