class XMLParser:
    def __init__(self):
        self.root = None
        self.current = None
        self.stack = []
    
    def feed(self, data):
        i = 0
        while i < len(data):
            if data[i] == '<':
                i += 1
                if data[i] == '/':
                    i += 1
                    end = data.find('>', i)
                    if end != -1:
                        tag_name = data[i:end].strip()
                        if self.stack:
                            self.current = self.stack.pop()
                        i = end + 1
                else:
                    end = data.find('>', i)
                    if end != -1:
                        tag_text = data[i:end]
                        if tag_text.endswith('/'):
                            tag_text = tag_text[:-1].strip()
                            tag_parts = tag_text.split()
                            tag_name = tag_parts[0]
                            attribs = self._parse_attributes(tag_parts[1:])
                            
                            element = Element(tag_name, attribs)
                            if self.current:
                                self.current.children.append(element)
                            elif not self.root:
                                self.root = element
                        else:
                            tag_parts = tag_text.split()
                            tag_name = tag_parts[0]
                            attribs = self._parse_attributes(tag_parts[1:])
                            
                            element = Element(tag_name, attribs)
                            if not self.root:
                                self.root = element
                            if self.current:
                                self.current.children.append(element)
                            
                            self.stack.append(self.current)
                            self.current = element
                        i = end + 1
            else:
                end = data.find('<', i)
                if end != -1:
                    text = data[i:end].strip()
                    if text and self.current:
                        self.current.text = (self.current.text or '') + text
                    i = end
                else:
                    break
    
    def _parse_attributes(self, attrib_parts):
        attribs = {}
        for part in attrib_parts:
            if '=' in part:
                key, value = part.split('=', 1)
                value = value.strip('"\'').strip()
                attribs[key] = value
        return attribs
    
    def close(self):
        return self.root

class Element:
    def __init__(self, tag, attrib=None):
        self.tag = tag
        self.attrib = attrib or {}
        self.text = None
        self.children = []
    
    def find(self, tag):
        for child in self.children:
            if child.tag == tag:
                return child
        return None
    
    def findall(self, tag):
        return [child for child in self.children if child.tag == tag]
    
    def __getitem__(self, key):
        return self.attrib.get(key)
    
    def __setitem__(self, key, value):
        self.attrib[key] = value
    
    def get(self, key, default=None):
        return self.attrib.get(key, default)

def Element(tag, attrib=None):
    return Element(tag, attrib or {})

def SubElement(parent, tag, attrib=None):
    element = Element(tag, attrib)
    parent.children.append(element)
    return element

def fromstring(text):
    parser = XMLParser()
    parser.feed(text)
    return parser.close()

def parse(file_or_path):
    if hasattr(file_or_path, 'read'):
        content = file_or_path.read()
    else:
        with open(file_or_path, 'r') as f:
            content = f.read()
    
    return fromstring(content)

def tostring(element, encoding='unicode'):
    def _to_string(elem, level=0):
        indent = '  ' * level
        result = [f'{indent}<{elem.tag}']
        
        # Атрибуты
        for key, value in elem.attrib.items():
            result.append(f' {key}="{value}"')
        
        if elem.text or elem.children:
            result.append('>')
            if elem.text:
                result.append(elem.text.strip())
            
            if elem.children:
                result.append('\n')
                for child in elem.children:
                    result.append(_to_string(child, level + 1))
                result.append(indent)
            
            result.append(f'</{elem.tag}>\n')
        else:
            result.append('/>\n')
        
        return ''.join(result)
    
    return _to_string(element).strip()

ElementTree = type('ETree', (), {
    'Element': Element,
    'SubElement': SubElement,
    'parse': parse,
    'fromstring': fromstring,
    'tostring': tostring
})