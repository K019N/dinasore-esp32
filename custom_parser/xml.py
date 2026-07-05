# simple_xml.py
class XMLParser:
    def __init__(self):
        self.root = None
        self.current = None
        self.stack = []
        self.text_buffer = []  # Буфер для сбора текста
    
    def feed(self, data):
        i = 0
        while i < len(data):
            if data[i] == '<':
                # Сохраняем накопленный текст перед обработкой тега
                self._flush_text_buffer()
                
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
                            self.stack.pop()
                            self.current = self.stack[-1] if self.stack else None
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
                        i = end + 1
            else:
                # Собираем текст в буфер
                end = data.find('<', i)
                if end != -1:
                    text = data[i:end]
                    if text and self.current:
                        self.text_buffer.append(text)
                    i = end
                else:
                    # Остаток данных - текст
                    text = data[i:]
                    if text and self.current:
                        self.text_buffer.append(text)
                    break
    
    def _flush_text_buffer(self):
        """Сохраняет накопленный текст в текущий элемент"""
        if self.text_buffer and self.current:
            text_content = ''.join(self.text_buffer)
            # Если у элемента уже есть текст, добавляем к нему
            if self.current.text:
                self.current.text += text_content
            else:
                self.current.text = text_content
            self.text_buffer = []
    
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
        # Сохраняем оставшийся текст перед завершением
        self._flush_text_buffer()
        return self.root

class ElementClass:
    def __init__(self, tag, attrib=None):
        self.tag = tag
        self.attrib = attrib or {}
        self.text = None  # Текстовое содержимое элемента
        self.children = []  # Дочерние элементы
    
    def __iter__(self):
        """Для итерации по дочерним элементам"""
        return iter(self.children)
    
    def getroot(self):
        """Добавляем метод getroot для совместимости с xml.etree.ElementTree"""
        return self
    
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
    
    @property
    def text_content(self):
        """Возвращает полное текстовое содержимое элемента (включая дочерние)"""
        result = []
        if self.text:
            result.append(self.text)
        for child in self.children:
            result.append(child.text_content)
        return ''.join(result)

def Element(tag, attrib=None):
    return ElementClass(tag, attrib or {})

def SubElement(parent, tag, attrib=None):
    element = Element(tag, attrib)
    parent.children.append(element)
    return element

def fromstring(text):
    if text is None:
        raise ValueError("None passed to fromstring")
    
    # Если это уже Element, просто возвращаем
    if hasattr(text, 'tag') and hasattr(text, 'attrib') and hasattr(text, 'children'):
        return text
    
    # Преобразуем в строку если это байты
    if isinstance(text, bytes):
        text = text.decode('utf-8')
    
    # Гарантируем что это строка
    if not isinstance(text, str):
        text = str(text)
    
    if not text:
        raise ValueError("Empty XML string")
    
    parser = XMLParser()
    parser.feed(text)
    result = parser.close()
    
    if result is None:
        raise ValueError(f"Could not parse XML: {text[:100]}...")
    
    return result

def parse(file_or_path):
    if hasattr(file_or_path, 'read'):
        # Это файловый объект
        content = file_or_path.read()
        # Если content - байты, декодируем
        if isinstance(content, bytes):
            content = content.decode('utf-8')
        return fromstring(content)
    else:
        # Это путь к файлу
        with open(file_or_path, 'r') as f:
            content = f.read()
        return fromstring(content)

def tostring(element, encoding='utf-8'):
    def _to_string(elem, level=0):
        indent = '  ' * level
        result = [f'{indent}<{elem.tag}']
        
        # Атрибуты
        for key, value in elem.attrib.items():
            result.append(f' {key}="{value}"')
        
        has_content = elem.text or elem.children
        if has_content:
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
    
    xml_string = _to_string(element).strip()
    
    if encoding == 'unicode':
        return xml_string
    else:
        return xml_string.encode(encoding)

# Псевдоним для совместимости
ElementTree = type('ETree', (), {
    'Element': Element,
    'SubElement': SubElement,
    'parse': parse,
    'fromstring': fromstring,
    'tostring': tostring
})