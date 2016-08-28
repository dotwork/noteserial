from noteserial.models import Note


####################################################################################################################
class Parser(object):

    ####################################################################################################################
    def __init__(self, text):
        self.text = text
        self.indent_queue = []
        self.notes = None

    ####################################################################################################################
    @classmethod
    def parse(cls, text, title=None):
        parser = Parser(text)
        note = Note(is_root=True, text=title)
        parser.notes = note
        parser.indent_queue.append(note)

        lines = parser.text.split("\n")

        for line in lines:
            if line:
                if note.continues:
                    note.append_text(line)
                    if not note.text_continues():
                        note.continues = False
                else:
                    note = Note(line)
                    parser.handle_if_list(note)
                    parser.append_to_parent(note)

        return parser.notes

    ####################################################################################################################
    def insert_new_list_element(self, note):
        list_element = Note(is_ol=note.is_numbered, is_ul=not note.is_numbered)
        list_element.indent = note.indent - 2
        self.append_to_parent(list_element)

    ####################################################################################################################
    def handle_if_list(self, note):
        is_list_element = note.indent > 4 or note.is_numbered
        if not is_list_element:
            return

        last_element = self.indent_queue[-1]
        last_element_is_list_item = last_element.indent > 4 or last_element.is_numbered
        if not last_element_is_list_item or note.indent > last_element.indent:
            self.insert_new_list_element(note)

    ####################################################################################################################
    def append_to_parent(self, note):
        element = self.indent_queue.pop()
        if note.indent > element.indent:
            if element.indent == 0:
                parent = self.notes
                self.indent_queue = [self.notes]
            else:
                self.indent_queue.append(element)
                parent = element
        else:
            while note.indent < element.indent:
                element = self.indent_queue.pop()
            parent = element

        note.parent = parent
        parent.children.append(note)
        self.indent_queue.append(note)
