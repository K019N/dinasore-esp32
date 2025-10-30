# simple_xml.py
class XMLParser:
    def __init__(self):
        self.root = None
        self.current = None
        self.stack = []  # Стек для хранения открытых элементов
    
    def feed(self, data):
        i = 0
        data = data.strip()
        while i < len(data):
            if data[i] == '<':
                # Найден тег
                i += 1
                if i < len(data) and data[i] == '/':
                    # Закрывающий тег
                    i += 1
                    end = data.find('>', i)
                    if end != -1:
                        tag_name = data[i:end].strip()
                        # Проверяем, что стек не пуст и тег соответствует
                        if self.stack and self.stack[-1].tag == tag_name:
                            self.current = self.stack.pop()
                        i = end + 1
                else:
                    # Открывающий тег
                    end = data.find('>', i)
                    if end != -1:
                        tag_text = data[i:end]
                        # Проверяем на самозакрывающийся тег
                        if tag_text.endswith('/'):
                            tag_text = tag_text[:-1].strip()
                            self_closure = True
                        else:
                            self_closure = False

                        # Разбираем имя тега и атрибуты
                        tag_parts = tag_text.split()
                        if tag_parts:
                            tag_name = tag_parts[0]
                            attribs = self._parse_attributes(tag_parts[1:])
                            
                            element = Element(tag_name, attribs)
                            
                            if not self.root:
                                self.root = element
                            
                            # Добавляем к текущему родителю, если он есть
                            if self.current:
                                self.current.children.append(element)
                            
                            if not self_closure:
                                # Добавляем текущий элемент в стек и делаем его текущим
                                self.stack.append(element)
                                self.current = element
                            else:
                                # Самозакрывающийся тег - не добавляем в стек
                                pass
                        i = end + 1
            else:
                # Текст
                end = data.find('<', i)
                if end != -1:
                    text = data[i:end].strip()
                    if text and self.current:
                        self.current.text = (self.current.text or '') + text
                    i = end
                else:
                    break
    
    def _parse_attributes(self, attrib_parts):
        """Парсит атрибуты вида key="value" или key='value'"""
        attribs = {}
        current_attr = ''
        for part in attrib_parts:
            current_attr += ' ' + part
            # Проверяем, есть ли закрывающая кавычка
            if current_attr.count('"') % 2 == 0 or current_attr.count("'") % 2 == 0:
                parts = current_attr.strip().split('=', 1)
                if len(parts) == 2:
                    key = parts[0].strip()
                    value = parts[1].strip().strip('"\'')
                    attribs[key] = value
                current_attr = ''
        
        # Обрабатываем оставшиеся атрибуты
        if current_attr.strip():
            parts = current_attr.strip().split('=', 1)
            if len(parts) == 2:
                key = parts[0].strip()
                value = parts[1].strip().strip('"\'')
                attribs[key] = value
        
        return attribs
    
    def close(self):
        return self.root

class ElementClass:
    def __init__(self, tag, attrib=None):
        self.tag = tag
        self.attrib = attrib or {}
        self.text = None
        self.children = []
        
    def __iter__(self):
        """Для итерации по дочерним элементам"""
        return iter(self.children)
    
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
    
    def set(self, key, value):
        self.attrib[key] = value

def Element(tag, attrib=None):
    return ElementClass(tag, attrib or {})

def SubElement(parent, tag, attrib=None):
    element = Element(tag, attrib)
    parent.children.append(element)
    return element

def fromstring(text):
    # Проверяем тип входных данных
    if text is None:
        raise ValueError("None passed to fromstring")
    
    # Если это уже Element, просто возвращаем
    if hasattr(text, 'tag') and hasattr(text, 'attrib'):
        return text
    
    # Преобразуем в строку если это байты или другой тип
    if isinstance(text, bytes):
        text = text.decode('utf-8')
    elif not isinstance(text, str):
        text = str(text)
    
    if not text.strip():
        raise ValueError("Empty XML string")
    
    parser = XMLParser()
    parser.feed(text)
    result = parser.close()
    
    if result is None:
        raise ValueError(f"Could not parse XML: {text[:100]}...")  # Ограничим вывод
    
    return result

def parse(file_or_path):
    if hasattr(file_or_path, 'read'):
        # Это файловый объект
        content = file_or_path.read()
    else:
        # Это путь к файлу
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
                # Экранируем специальные XML символы в тексте
                text = elem.text
                text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                result.append(text)
            
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

# Псевдоним для совместимости
ElementTree = type('ETree', (), {
    'Element': Element,
    'SubElement': SubElement,
    'parse': parse,
    'fromstring': fromstring,
    'tostring': tostring
})