import io
import json
import os
import unittest

from bs4 import BeautifulSoup

from noteserial.models import Note
from noteserial.parser import Parser

########################################################################################################################
base_dir = os.path.dirname(__file__)
data_folder = os.path.join(base_dir, "data")
TEST_FILEPATH = os.path.join(data_folder, "note_text.txt")


#######################################################################################################################
def write_children(children, _file):
    for child in children:
        _file.write("{indent}{indent_num}: {text}\n".format(indent=" " * child.indent,
                                                            indent_num=child.indent,
                                                            text=child.text or child))
        if child.children:
            write_children(child.children, _file)


########################################################################################################################
def import_file(filepath):
    with io.open(filepath) as _file:
        text = _file.read()
    return text


########################################################################################################################
class TestNote(unittest.TestCase):

    ####################################################################################################################
    @classmethod
    def setUpClass(cls):
        cls.note_text = import_file(TEST_FILEPATH)
        cls.notes = Parser.parse(cls.note_text, title="New Hope Lectures")
        cls.expected_parser_results = open(os.path.join(data_folder, "parser_result.txt")).read().split("\n")

    ####################################################################################################################
    def test_parse(self):
        # todo: rewrite serialize_notes
        actual = serialize_notes(self.notes)
        for a, b in zip(self.expected_parser_results, actual):
            self.assertEqual(a, b, msg="'{}' !=\n'{}'".format(a, b))

    ####################################################################################################################
    def test_html_soup(self):
        html_soup = self.notes.html_soup()
        test_html_filepath = os.path.join(data_folder, "test_serializer.html")
        with open(test_html_filepath, "w") as _file:
            _file.write(html_soup.prettify())
        actual_html = open(test_html_filepath).read()
        actual_soup = BeautifulSoup(actual_html, features="lxml")

        expected_html = open(os.path.join(data_folder, "serializer_result.html")).read()
        expected_soup = BeautifulSoup(expected_html, features="lxml")
        self.assertEqual(expected_soup, actual_soup)
        self.assertEqual(expected_soup.prettify(), actual_soup.prettify())

    ####################################################################################################################
    def test_json(self):
        json_data = self.notes.json(sort_keys=True, indent=4)

        filepath = os.path.join(data_folder, "json_result.json")
        expected_json_data = json.load(open(filepath))
        self.assertEqual(expected_json_data, json_data)

        note_from_json = Note.from_json(json_data)
        actual = serialize_notes(note_from_json)
        self.assertEqual(self.expected_parser_results, actual)

    ####################################################################################################################
    def test_round_trip(self):
        note_tree = Parser.parse(self.note_text, title="New Hope Lectures")
        note_json = note_tree.json()

        note_tree_2 = Note.from_json(note_json)
        self.assertEqual(note_tree.data(), note_tree_2.data())

        note_text_2 = note_tree_2.note_text()
        self.assertEqual(self.note_text, note_text_2)


###################################################################################################################
def serialize_notes(notes):
    """Generates text that models the indent structure and hierarchy of the Note tree.
    :param notes:
    :return: file-type object of text
    """
    filepath = os.path.join(data_folder, "test_parser.txt")
    try:
        os.remove(filepath)
    except:
        pass
    with open(filepath, "a") as _file:
        write_children(notes.children, _file)
    return open(filepath).read().split("\n")
