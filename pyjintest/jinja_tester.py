import re
import sys
import argparse
import json
from lxml import etree
import html5lib
from io import StringIO

from jinja2 import (
    Environment,
    TemplateSyntaxError,
    FileSystemLoader,
    UndefinedError,
    Undefined,
    TemplateError,
    StrictUndefined
)


class MismatchedOpeningBracesError(SyntaxError):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class MismatchedClosingBracesError(SyntaxError):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


def render_single_template(file_path, data_dict: dict = None):
    outputText = ''
    error = ''
    # searchpath = '/'.join(file_path.split('/')[0:-1])
    # templateLoader = FileSystemLoader(searchpath=searchpath)
    # templateEnv = Environment(loader=templateLoader)
    # TEMPLATE_FILE = file_path.split('/')[-1]
    jinja2_env = Environment(undefined=StrictUndefined)
    jinja2_tpl_str = ''
    jinja2_tpl     = ''
    with open(file_path, 'r') as src_template:
        jinja2_tpl_str = src_template.read()
        try:
            jinja2_tpl = jinja2_env.from_string(jinja2_tpl_str)
        except Exception as e:
            error += ("[!] Syntax Error in jinja2 template: {0}".format(str(e)))

        try:
            outputText = jinja2_tpl.render(data_dict)
        except (TemplateSyntaxError, UndefinedError, ValueError, TypeError, KeyError) as e:
            error += "[!] Error in your values input field: {0}".format(str(e))
        except Exception as ex:
            error += str(ex) + '. Error: Make sure you linted the template first.'

    return error or outputText


def check_CDATA(tag_list):
    empty_tag_list = []
    for e in tag_list:
        if "><![CDATA[]]></" in e:
            empty_tag_list.append(e)
    return empty_tag_list


class JinjaTemplate():
    """ Lint and render """
    def __init__(self, template_file_path: str):
        self.file = template_file_path
        self.jinja_is_valid = False
        self.output_is_valid = False

    def lint(self) -> str:
        error = ''
        with open(self.file, 'r') as template:
            env = Environment(autoescape=True)
            try:
                contents = template.read()
                env.parse(contents)
                JinjaTemplate.check_mismatched_braces(contents)
                self.jinja_is_valid = True
            except TemplateSyntaxError as ex:
                error = '{} on line # {}'.format(
                    str(ex), ex.lineno
                )
            except MismatchedClosingBracesError as ex:
                error = 'The braces are not closed properly here: {}'.format(str(ex))
            except MismatchedOpeningBracesError as ex:
                error = 'The braces are not opened properly here: {}'.format(str(ex))
            except (MismatchedOpeningBracesError, MismatchedClosingBracesError) as ex:
                error = 'The braces are not closed properly here: {}'.format(str(ex))
            except Exception as ex:
                error = str(ex)
        if not error:
            result = ''
        else:
            result = 'Linting completed but with errors: {}'.format(error)
        return result

    def render(self, data: dict = {}):
        return render_single_template(self.file, data_dict = data)

    @staticmethod
    def validate_html(markup_as_str) -> str:
        result = ''
        parser = html5lib.HTMLParser(strict=True)
        try:
            parser.parse(markup_as_str)
        except html5lib.html5parser.ParseError as ex:
            result = 'Problem with output HTML: {}'.format(str(ex))
        except Exception as ex:
            result = 'General exception: {}'.format(str(ex))
        return result

    @staticmethod
    def validate_xml(markup_as_str) -> str:
        result = ''
        parser = etree.XMLParser()
        try:
            uni_string = markup_as_str.encode('utf-8')
            root = etree.XML(uni_string)
        except etree.XMLSyntaxError as ex:
            result = 'XML syntax error: {}'.format(str(ex))
        except Exception as ex:
            result = 'General exception: {}'.format(str(ex))
        return result

    @staticmethod
    def validate_json(markup_as_str) -> str:
        result = ''
        try:
            json_data = json.loads(markup_as_str)
        except Exception as ex:
            result = 'Validation error: {}'.format(str(ex))
        return result

    @staticmethod
    def validate_markup(markup_as_str, markup_type: str) -> str:
        result = ''
        # is_html = '<html' in markup_as_str
        if markup_type.lower() == 'html':
            result = JinjaTemplate.validate_html(markup_as_str)
        elif markup_type.lower() == 'xml':
            result = JinjaTemplate.validate_xml(markup_as_str)
        elif markup_type.lower() == 'json':
            result = JinjaTemplate.validate_json(markup_as_str)
        else:
            raise Exception("No markup type specified!")
        # print(result)
        return result

    @staticmethod
    def find_empty_tags(template, display_line: str = "show"):
        show_line_empty_tag = re.findall("\d+[)]\s*<.*?>\s*</.*?>", template)
        no_show_empty_tag = re.findall("<.*?>\s*</.*?>", template)
        if display_line == "show":
            empty_tag_list = list([empty for empty in show_line_empty_tag if "CDATA" not in empty])
        else:
            empty_tag_list = list([empty for empty in no_show_empty_tag if "CDATA" not in empty])
        # TODO: Add support for checking inside of CDATA

        if (len(empty_tag_list) != 0):
            print("Double check tags and make sure if the field is in DRS")
            for i, e in enumerate(empty_tag_list):
                print(("{} - {}").format(i + 1, e))

        return sorted(empty_tag_list)

    @staticmethod
    def print_empty_tags(tag_list) -> str:
        return '\n'.join(tag_list)

    @staticmethod
    def check_mismatched_braces(file_contents):
        """ The Jinja linter doesn't check mismatched braces. That IS improper syntax in our book
        At time of invocation, disk file is open """
        mismatched_closing_braces = []
        mismatched_opening_braces = []
        for line in (file_contents.split('\n')):
            # old regex: r'\{\{.*\}[^\}]'
            # new regex: r'\{\{[\[\]'\"\w\s\d\|]+\}[^\}]''
            mismatched_closing_braces = re.findall(
                r"\{\{[\[\]\'\"\w\s\d\|]+\}[^\}]",
                file_contents
            )
            mismatched_opening_braces = re.findall(
                r'[^\{]\{[^\{].*\}\}',
                file_contents
            )
            if any(mismatched_opening_braces):
                raise MismatchedOpeningBracesError(mismatched_opening_braces)
            if any(mismatched_closing_braces):
                raise MismatchedClosingBracesError(mismatched_closing_braces)
        return "BROKEN"


def main():
    parser = argparse.ArgumentParser("Validate and render Jinja2 templates")
    parser.add_argument(
        'template',
        help='Path to the Jinja template file to be linted, ex: codebase/path/somefile.txt. Checks for basic syntax '
             'errors. Any errors will be reported.'
        )
    parser.add_argument(
        '--jsondata',
        help='When the --jsondata argument is used, the tester will attempt to render the template with the data in '
             'the json file.'
             ' Useful for checking the template for data reference errors, which will be reported.',
        required=False
        )
    parser.add_argument(
        '--validate',
        help='Use this argument to check that the HTML, XML, or JSON structure of the template output is '
             'valid for the document type. JSON data is required to check the render. \n'
             'Accepted values: "json", "html", "xml"',
        required=False
    )
    args = parser.parse_args()

    if args.template and not args.jsondata:
        # lint a single file
        template = JinjaTemplate(args.template)
        template_errors = template.lint()
        if len(template_errors):
            print("Found template syntax errors:")
            sys.exit(template_errors)
        else:
            sys.stdout.write('LINT OK: {}'.format(args.template))
            sys.exit(0)
    elif args.template and args.jsondata and not args.validate:
        with open(args.jsondata) as jsonfile:
            template = JinjaTemplate(args.template)
            data = json.loads(jsonfile.read())
            output = template.render(data)
            if ' Error' in output:
                sys.exit(output)
            else:
                print(output)
                sys.exit()
            # output = render_single_template(args.template, json.load(jsonfile))
        sys.stdout.write(output)
    elif args.template and args.validate and args.jsondata:
        template_input_data = {}
        template = JinjaTemplate(args.template)
        template_errors = template.lint()
        if len(template_errors):
            sys.exit(template_errors)
        try:
            with open(args.jsondata, 'r') as jsonfile:
                template_input_data = json.load(jsonfile)
                # print('Input json is valid')
        except Exception as ex:
            sys.exit('Problem with input json: {}'.format(str(ex)))
        output = template.render(template_input_data)
        if ' Error' in output:
            sys.exit(output)
        errors = JinjaTemplate.validate_markup(output, args.validate)
        if len(errors):
            sys.exit(errors)
        else:
            print("Output structure is valid.")
            sys.exit(0)


if __name__ == "__main__":
    main()
