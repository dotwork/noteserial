import json
import os
import re
from collections import namedtuple

from bs4 import BeautifulSoup

########################################################################################################################
base_dir = os.path.dirname(__file__)

########################################################################################################################
NoteAttrs = namedtuple("NoteAttrs", "indent_neg_1 indent_0 indent_4 indent_gte_8 is_upper is_numbered")
BASE_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title></title>
</head>
<body></body>
</html>
"""


########################################################################################################################
class Note(object):

    ####################################################################################################################
    body = NoteAttrs(indent_neg_1=True, indent_0=False, indent_4=False,
                     indent_gte_8=False, is_upper=False, is_numbered=False)
    h1 = NoteAttrs(indent_neg_1=False, indent_0=True, indent_4=False,
                   indent_gte_8=False, is_upper=True, is_numbered=False)
    h2 = NoteAttrs(indent_neg_1=False, indent_0=True, indent_4=False,
                   indent_gte_8=False, is_upper=False, is_numbered=False)
    h3 = NoteAttrs(indent_neg_1=False, indent_0=False, indent_4=False,
                   indent_gte_8=True, is_upper=True, is_numbered=False)
    olli = NoteAttrs(indent_neg_1=False, indent_0=False, indent_4=False,
                     indent_gte_8=True, is_upper=False, is_numbered=True)
    olh3 = NoteAttrs(indent_neg_1=False, indent_0=False, indent_4=True,
                     indent_gte_8=False, is_upper=False, is_numbered=True)
    ulli = NoteAttrs(indent_neg_1=False, indent_0=False, indent_4=False,
                     indent_gte_8=True, is_upper=False, is_numbered=False)
    p = NoteAttrs(indent_neg_1=False, indent_0=False, indent_4=True,
                  indent_gte_8=False, is_upper=False, is_numbered=False)
    tag_dict = {
        body: "body",
        h1: "h1",
        h2: "h2",
        h3: "h3",
        olli: "li",
        olh3: "li",
        ulli: "li",
        p: "p",
    }
    continue_punctuation = ",;"

    ####################################################################################################################
    def __init__(self, text="", is_root=False, is_ol=False, is_ul=False):
        self.parent = None
        self.children = []
        self.is_root = is_root
        self.is_ol = is_ol
        self.is_ul = is_ul
        if text:
            self.indent, self.text = self.parse_text_and_indent(text)
            self.is_upper = text.upper() == text
            self.is_numbered = self.text.startswith("# ")
            if self.is_numbered:
                self.text = self.strip_hash(self.text)
            self.continues = False
            if self.text:
                self.continues = self.text_continues()
        else:
            self.text = text
            self.is_upper = False
            self.is_numbered = False
            self.indent = -1
            self.continues = False
        self.tag_attrs = NoteAttrs(
            indent_neg_1=self.indent == -1,
            indent_0=self.indent == 0,
            indent_4=self.indent == 4,
            indent_gte_8=self.indent >= 8,
            is_upper=self.is_upper,
            is_numbered=self.is_numbered
        )
        self.html = None

    ####################################################################################################################
    @staticmethod
    def parse_text_and_indent(text):
        indent = 0 if text else -1
        while text.startswith(" "):
            indent += 1
            text = text[1:]
        return indent, text

    ####################################################################################################################
    @staticmethod
    def strip_hash(text):
        return re.search("^#\s*(.+)$", text).group(1)

    ####################################################################################################################
    def text_continues(self):
        assert len(self.text) >= 2, "Expected text at least two letters long. Got '{}'".format(self.text)
        return any([self.text[-2:] == "..",
                    self.text[-1] in self.continue_punctuation])

    ####################################################################################################################
    def append_text(self, text):
        _x_, text = self.parse_text_and_indent(text)
        self.text = " ".join((self.text, text))

    ####################################################################################################################
    def serialize_note(self, note):
        if note.is_ul:
            tag_name = "ul"
        elif note.is_ol:
            tag_name = "ol"
        else:
            tag_name = self.tag_dict[note.tag_attrs]

        tag = self.html.new_tag(tag_name)
        if note.text:
            tag.string = note.text
        return tag

    ####################################################################################################################
    def html_soup(self):
        ################################################################################################################
        def serialize(notes, parent_tag):
            for note in notes:
                tag = self.serialize_note(note)
                parent_tag.append(tag)
                serialize(note.children, parent_tag=tag)

        self.html = BeautifulSoup(BASE_HTML, features="lxml")
        if self.is_root and self.text:
            title = self.html.find("title")
            title.string = self.text

        body = self.html.find("body")
        serialize(self.children, parent_tag=body)
        return self.html

    ####################################################################################################################
    @classmethod
    def from_json(cls, json_data):
        note = Note()
        for attr, value in json_data.items():
            if attr == "tag_attrs":
                indent_neg_1, indent_0, indent_4, indent_gte_8, is_upper, is_numbered = value
                tag_attrs = NoteAttrs(indent_neg_1, indent_0, indent_4, indent_gte_8, is_upper, is_numbered)
                setattr(note, attr, tag_attrs)
            elif attr != "children":
                setattr(note, attr, value)
            else:
                for child_data in value:
                    child_note = Note.from_json(child_data)
                    child_note.parent = note
                    note.children.append(child_note)
        return note

    ####################################################################################################################
    @classmethod
    def from_json_str(cls, json_str):
        json_data = json.loads(json_str)
        return cls.from_json(json_data)

    ####################################################################################################################
    def json(self, sort_keys=False, indent=None):
        data = self.data()
        json_str = json.dumps(data, sort_keys=sort_keys, indent=indent)
        return json.loads(json_str)

    ####################################################################################################################
    def data(self):
        data_dict = self.__dict__.copy()
        data_dict.pop("parent")
        data_dict.pop("html")

        child_data = []
        for child in self.children:
            child_data.append(child.data())

        data_dict["children"] = child_data
        return data_dict

    ####################################################################################################################
    def traverse(self):
        def _traverse(child_notes):
            for note in child_notes:
                yield note
                yield from _traverse(note.children)

        return _traverse(self.children)

    ####################################################################################################################
    def note_text(self):
        parts = []
        for note in self.traverse():
            if note.tag_attrs in (note.h1, note.h2) and parts and parts[-1] != "\n":
                parts.append("\n")
            if note.text:
                text = "{indent}{hash}{text}".format(indent=" " * note.indent,
                                                     hash="# " if note.is_numbered else "",
                                                     text=note.text)
                parts.append(text)

        note_text = "\n".join(parts).replace("\n\n\n", "\n\n")
        if note_text.startswith("\n"):
            note_text = note_text[1:]

        # todo: clean up Note.note_text
        return note_text

    ####################################################################################################################
    def __str__(self):
        if self.text:
            return self.text[:18]
        elif self.is_ul:
            return "<ul>"
        elif self.is_ol:
            return "<ol>"
        elif not self.children:
            "<root>"
        else:
            raise Exception("Unknown Note type. {}".format(self.__dict__))


# todo: if startswith "*", make into note (<em><strong>Note:</strong>...text...</em>)
# todo: use <br> or line spacing to make paragraphs less spacious
