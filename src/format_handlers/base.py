from abc import ABC, abstractmethod

class BaseHandler(ABC):
    def __init__(self, file_path):
        self.file_path = file_path
        self.content = None
        self.text_nodes = [] # List of objects/nodes that hold text

    @abstractmethod
    def read_file(self):
        """Reads the file and parses its structure."""
        pass

    @abstractmethod
    def extract_text(self):
        """
        Extracts mutable text nodes from the file structure.
        Returns a list of objects/dicts that contain references to the text
        so they can be modified in place.
        """
        pass

    @abstractmethod
    def apply_translations(self, original_texts, translated_texts):
        """
        Replaces the original text with translated text in the file structure.
        """
        pass
    
    @abstractmethod
    def save_file(self, output_path):
        """Saves the modified file structure to a new file."""
        pass
