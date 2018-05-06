Stepik-CLI
==========

CLI for Stepik.

Usage
-----

Consult `man/` for documentation on how to use this program.

It is recommended to pipe the output into `column -t -s '\t'`, where '\t'
is a literal tab. This way, the output isn't a mess but a nice-looking
table.

Building
--------

Install all the packages from `requirements.txt`, for example, by running

    pip install -r requirements.txt

Then **stepik** can be launched with `python -m stepik` if it is visible from
the python environment. The simplest way to make python see the `stepik/`
directory is to be in the root directory of the project.
