import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup, NavigableString, XMLParsedAsHTMLWarning
import warnings
from .base import BaseHandler
import uuid

warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

class BS4NodeWrapper:
    """
    Wraps a BeautifulSoup NavigableString to expose a .text attribute/setter
    compatible with the Translator expects.
    Preserves leading/trailing whitespace to avoid space loss around inline elements.
    """
    def __init__(self, soup_string):
        self.soup_string = soup_string
        # Store original whitespace pattern
        original = str(soup_string)
        stripped = original.strip()
        self._leading_ws = original[:len(original) - len(original.lstrip())]
        self._trailing_ws = original[len(original.rstrip()):]
        self._original = original

    @property
    def text(self):
        # Return just the stripped content for translation
        return str(self.soup_string).strip()

    @text.setter
    def text(self, value):
        # Preserve original whitespace pattern
        if value and value.strip():
            # Reapply the original leading/trailing whitespace
            new_value = self._leading_ws + value.strip() + self._trailing_ws
            self.soup_string.replace_with(new_value)


class EpubHandler(BaseHandler):
    def read_file(self):
        # Use ignore_ncx=True to prevent ebooklib from modifying NCX
        self.book = epub.read_epub(self.file_path, {"ignore_ncx": False})
        self.chapters = []  # Keep track of loaded soup objects to save later
        self.nav_items = []  # Track navigation items separately

    def extract_text(self):
        text_nodes = []
        
        # Iterate over all document items (HTML files inside EPUB)
        for item in self.book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
            # Use lxml parser to better preserve XML structure
            content = item.get_content()
            soup = BeautifulSoup(content, 'lxml-xml')
            
            # If lxml-xml fails (no body), try html.parser
            if soup.find('body') is None and soup.find('html') is None:
                soup = BeautifulSoup(content, 'html.parser')
            
            self.chapters.append((item, soup))
            
            # Find all text strings, excluding scripts, styles, and specific head elements
            for text_elem in soup.find_all(string=True):
                parent_name = text_elem.parent.name if text_elem.parent else None
                
                # Skip script, style, and meta tags
                if parent_name in ['script', 'style', 'meta', '[document]']:
                    continue
                
                # We DO want to translate title tags and nav content
                # Only skip if it's truly empty
                if text_elem.strip():
                    text_nodes.append(BS4NodeWrapper(text_elem))
        
        # Also extract text from navigation items (toc.xhtml, nav.xhtml)
        for item in self.book.get_items_of_type(ebooklib.ITEM_NAVIGATION):
            content = item.get_content()
            soup = BeautifulSoup(content, 'lxml-xml')
            
            if soup.find('body') is None and soup.find('html') is None:
                soup = BeautifulSoup(content, 'html.parser')
            
            self.nav_items.append((item, soup))
            
            # Extract nav text (links in nav)
            for text_elem in soup.find_all(string=True):
                parent_name = text_elem.parent.name if text_elem.parent else None
                
                if parent_name in ['script', 'style', 'meta', '[document]']:
                    continue
                    
                if text_elem.strip():
                    text_nodes.append(BS4NodeWrapper(text_elem))
                    
        return text_nodes

    def apply_translations(self, original_texts, translated_texts):
        # Done via wrapper in-place
        pass

    def _sanitize_toc(self, toc):
        """
        Recursively sanitize TOC entries to ensure all uid values are valid strings.
        This prevents the 'Argument must be bytes or unicode, got NoneType' error.
        """
        if toc is None:
            return
            
        if not isinstance(toc, (list, tuple)):
            toc_list = [toc]
        else:
            toc_list = toc
        
        for i, item in enumerate(toc_list):
            if isinstance(item, epub.Link):
                # Fix None uid on Link objects
                if item.uid is None:
                    item.uid = f"nav_{uuid.uuid4().hex[:8]}"
            elif isinstance(item, tuple) and len(item) >= 2:
                # This is a Section (section_title, list_of_links)
                section = item[0]
                subsections = item[1]
                
                # Fix the section if it's a Link with None uid
                if isinstance(section, epub.Link) and section.uid is None:
                    section.uid = f"nav_{uuid.uuid4().hex[:8]}"
                
                # Recursively sanitize subsections
                if isinstance(subsections, (list, tuple)):
                    self._sanitize_toc(subsections)

    def save_file(self, output_path):
        # Write the modified soups back to the document items
        for item, soup in self.chapters:
            # Encode the modified soup back to bytes
            # Use output_formatter to preserve structure
            content = str(soup)
            # Ensure proper XML declaration if it was there
            if not content.startswith('<?xml'):
                content = '<?xml version="1.0" encoding="utf-8"?>\n' + content
            item.set_content(content.encode('utf-8'))
        
        # Write modified navigation items back
        for item, soup in self.nav_items:
            content = str(soup)
            if not content.startswith('<?xml'):
                content = '<?xml version="1.0" encoding="utf-8"?>\n' + content
            item.set_content(content.encode('utf-8'))
        
        # Ensure TOC is a list/tuple before sanitizing and saving
        if self.book.toc is not None and not isinstance(self.book.toc, (list, tuple)):
            self.book.toc = [self.book.toc]
            
        # Sanitize TOC entries to prevent None uid errors
        self._sanitize_toc(self.book.toc)
            
        # Write the epub - pass options to not regenerate NCX/nav
        epub.write_epub(output_path, self.book, {})
