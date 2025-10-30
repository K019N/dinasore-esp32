import os
import sys
from custom_parser.xml import ElementTree as ETree
from core import logging


class FBResources:

    def __init__(self, fb_type):
        self.fb_type = fb_type

        # Gets the file path to the python file
        self.py_path = "/dinasore/resources/function_blocks/" + fb_type + ".py"

        # Gets the file path to the fbt (xml) file
        self.fbt_path = "/dinasore/resources/function_blocks/" + fb_type + ".fbt"

    def import_fb(self):
        logging.info('importing fb python file and definition file...')
        root = None
        fb_obj = None

        try:
            module_name = 'resources.function_blocks.' + self.fb_type
            
            module = __import__(module_name, [], [], [''])
            # module = __import__('resources.function_blocks.' + self.fb_type, fromlist=['*'])
            # print("\nAvailable in module:", dir(module), "\n\n")
            # Gets the running fb method
            fb_class = getattr(module, self.fb_type)
            # Instance the fb class
            fb_obj = fb_class()
            # Reads the xml - используем встроенный парсер MicroPython
            try:
                # with open(self.fbt_path, 'r') as file:
                #     file_content = file.read()
                tree = ETree.parse(self.fbt_path)
                root = tree.getroot()
            except ImportError:
                logging.error("no xml")

        except ImportError as error:
            logging.error('can not import the module (check fb_type.py nomenclature)')
            logging.error(str(error))
            # Дополнительная отладочная информация
            logging.error('Module path: resources.function_blocks.{}'.format(self.fb_type))

        except AttributeError as error:
            logging.error('can not find the fb method declaration (check if fb_type.py = def fb_type(...):)')
            logging.error(str(error))

        # except FileNotFoundError as error:
        #     logging.error('can not find the .fbt file (check .fbt name = fb_type.fbt)')
        #     logging.error(str(error))

        except Exception as ex:
            logging.error(str(ex))

        else:
            logging.info('fb definition (xml) imported from: {0}'.format(self.fbt_path))
            logging.info('python file imported from: {0}'.format(self.py_path))

        return root, fb_obj

    def get_xml(self):
        logging.info('getting the xml fb definition...')
        root = None

        try:
            # Reads the xml
            tree = ETree.parse(self.fbt_path)
            # Gets the root element
            root = tree.getroot()
        # except FileNotFoundError as error:
        #     logging.error('can not find the .fbt file (check .fbt name = fb_type.fbt)')
        #     logging.error(str(error))
        except:
            pass
        else:
            logging.info('fb definition (xml) imported from: {0}'.format(self.fbt_path))

        return root

    def exists_fb(self):
        # Verifies if exists the python file
        # exists_py = os.path.isfile(self.py_path)
        # Verifies if exists the fbt file
        # exists_fbt = os.path.isfile(self.fbt_path)

        # if exists_py and exists_fbt:
        #     return True
        # else:
        #     return False
        # fixme!
        return True

