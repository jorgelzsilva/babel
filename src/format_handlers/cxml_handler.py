from lxml import etree
from .base import BaseHandler

class TailNode:
    """Wrapper to treat an element's tail text as a translatable node."""
    def __init__(self, element):
        self.element = element
    
    @property
    def text(self):
        return self.element.tail
    
    @text.setter
    def text(self, value):
        self.element.tail = value

class CXMLHandler(BaseHandler):
    def read_file(self):
        self.parser = etree.XMLParser(remove_blank_text=False)
        self.tree = etree.parse(self.file_path, self.parser)
        self.root = self.tree.getroot()

    def extract_text(self):
        """
        Extracts all text nodes from the XML.
        Returns a list of 'Node' objects (Elements or TailNodes).
        """
        if self.root is None:
            return []
            
        text_nodes = []
        for elem in self.root.iter():
            # 1. Element Text
            if elem.text and elem.text.strip():
                text_nodes.append(elem)
            
            # 2. Element Tail (Mixed content)
            # The tail attribute holds the text that follows the element's closing tag,
            # but is before the next sibling's opening tag.
            if elem.tail and elem.tail.strip():
                text_nodes.append(TailNode(elem))
            
        return text_nodes

    def apply_translations(self, original_texts, translated_texts):
        pass

    def save_file(self, output_path):
        self.tree.write(output_path, encoding='utf-8', xml_declaration=True, pretty_print=False)
