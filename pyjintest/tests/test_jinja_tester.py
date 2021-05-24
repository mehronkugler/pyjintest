import os
import unittest

from pyjintest.jinja_tester import (
    MismatchedOpeningBracesError,
    MismatchedClosingBracesError,
    JinjaTemplate
)


class TestLinter(unittest.TestCase):

    cur_path = os.path.dirname(os.path.abspath(__file__))
    test_files = {
        'no_errors': os.path.join(
            cur_path, 'sample_jinja_template_no_errors.html'
        ),
        'html_errors': os.path.join(
            cur_path, 'sample_jinja_template_with_html_errors.html'
        ),
        'jinja_err_open': os.path.join(
            cur_path, 'sample_jinja_errors_opening.html'
        ),
        'jinja_err_close': os.path.join(
            cur_path, 'sample_jinja_errors_closing.html'
        ),
        'jinja_render_no_errors': os.path.join(
            cur_path, 'sample_jinja_template_no_errors__render.html'
        )
    }

    def test_no_errors(self):
        """ Test basic happy path """

        expected = 'Linting completed without errors'
        template = JinjaTemplate(self.test_files['no_errors'])
        errors = template.lint()
        self.assertTrue(len(errors) == 0)

    def test_check_mismatched_braces_close(self):
        """ Check that our exception works as expected """
        with open(self.test_files['jinja_err_close'], 'r') as file:
            with self.assertRaises(MismatchedClosingBracesError):
                JinjaTemplate.check_mismatched_braces(file.read())

    def test_check_mismatched_braces_open(self):
        """ Check that our exception works as expected """
        with open(self.test_files['jinja_err_open'], 'r') as file:
            with self.assertRaises(MismatchedOpeningBracesError):
                JinjaTemplate.check_mismatched_braces(file.read())

    def test_found_jinja_error(self):
        """ Test the jinja error """

        template = JinjaTemplate(self.test_files['jinja_err_open'])
        actual = template.lint()
        self.assertTrue(len(actual))
        self.assertIn('Linting completed but with errors:', actual)

        template = JinjaTemplate(self.test_files['jinja_err_close'])
        actual = template.lint()
        self.assertIn('Linting completed but with errors:', actual)

    def test_rendering_a_template(self):
        """ check rendering a template with known good data """
        test = {
            'test': {
                'title': 'This is a test',
                'description': 'Just your average test',
                'author': 'Nose McTest'
            }
        }
        expected = ''
        with open(self.test_files['jinja_render_no_errors'], 'r') as file:
            expected = file.read().strip()
        template = JinjaTemplate(self.test_files['no_errors'])
        actual = template.render(test).strip()
        self.assertEqual(
            actual, expected
        )

    def test_validating_good_html(self):
        """ Test validating known good HTML """
        test = {
            'test': {
                'title': 'This is a test',
                'description': 'Just your average test',
                'author': 'Nose McTest'
            }
        }
        template = JinjaTemplate(self.test_files['no_errors'])
        render = template.render(test).strip()
        errors = JinjaTemplate.validate_markup(render, 'html')
        self.assertTrue(len(errors) == 0)

    def test_validating_html_bad_render(self):
        """ Test validating bad html """
        test = {
            'test': {
                'title': 'This is a test',
                'description': 'Just your average test',
                'author': 'Nose McTest'
            }
        }
        template = JinjaTemplate(self.test_files['html_errors'])
        render = template.render(test).strip()
        errors = JinjaTemplate.validate_markup(render, 'html')
        self.assertFalse(len(errors) == 0)

    def test_validating_bad_xml(self):
        """ Validate known bad xml """
        with open(os.path.join(self.cur_path, 'invalid_xml.xml'), 'r') as file:
            contents = file.read()
            errors = JinjaTemplate.validate_markup(contents, 'xml')
            self.assertFalse(len(errors) == 0)

    def test_validating_good_json(self):
        """ Validate known good JSON """
        with open(os.path.join(self.cur_path, 'sample_jinja_output_valid_json.json'), 'r') as file:
            contents = file.read()
            errors = JinjaTemplate.validate_markup(contents, 'json')
            self.assertTrue(len(errors) == 0)

    def test_validating_bad_json(self):
        """ Validate known BAD JSON """
        with open(os.path.join(self.cur_path, 'sample_jinja_output_bad_json.json'), 'r') as file:
            contents = file.read()
            errors = JinjaTemplate.validate_markup(contents, 'json')
            self.assertFalse(len(errors) == 0)
