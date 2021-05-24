# pyjintest: A Jinja 2 Tester in Python

Features command-line interface, and optional GUI

Capabilities:

- Lint Jinja 2 templates for Jinja syntax errors
- Render templates with test data and see the results
- Automatically validate the document structure of a template (whether it is valid XML, HTML, or JSON)

Use cases:

- Run against Jinja templates to check for Jinja syntax errors before deployment
- Check that all values are as expected (render the template against a data set)
- Check for structural errors before deployment (valid XML, HTML, JSON output)


## Installation

Clone the repo, go to `jinja2-tester-pygui` and run `pip install .`

### CLI

Use `pyjintest` from anywhere to do testing and linting. If there are errors, they will be reported.

*For linting:*
`pyjintest path\to\template.txt`

This will report what errors there are during linting.

*For rendering*

`pyjintest path\to\somefile.txt --jsondata path\to\input_data.json`
 
This will report any errors during rendering, and if no errors, will print the render.

*For output validation*

Use the `--validate` flag with any of `xml`, `json`, or `html`.

`pyjintest path\to\template.txt --jsondata path\to\input_data.json --validate xml`
