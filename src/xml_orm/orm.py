"""
# Examples on how to use.
>> xml = PageXML('PATH_TO_PAGE_XML')
>> xml.auto_fix()
>> xml.element_tree.write('PATH_TO_PAGE_XML_FIXED', pretty_print=True)
"""

import os
import warnings
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List

from lxml import etree

from .xml.xml_shared import _change_namespace

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
FILENAME_XSD_PAGE = os.path.join(ROOT, 'xml_orm/xml_schema/pagecontent_2013_07_15.xsd')
FILENAME_XSD_MULTILINGUAL_PAGE = os.path.join(ROOT, 'xml_orm/xml_schema/multilingual_pagecontent_v0_3.xsd')
XML_NAMESPACE = "http://www.w3.org/XML/1998/namespace"

for filename in FILENAME_XSD_PAGE, FILENAME_XSD_MULTILINGUAL_PAGE:
    if not os.path.exists(filename):
        warnings.warn(f"Couldn't find {filename}! Check if added correctly.")


def parse_etree(filename):
    return etree.parse(filename)


class OverlayXML(ABC):
    """
    An abstract class for the different types of xml's that can save the annotated, overlayed text on an image.
    """

    def __init__(self, filename):
        parser = etree.XMLParser(remove_blank_text=True)
        self.element_tree = etree.parse(filename,
                                        parser)

    def get_xmlns(self):
        return self.element_tree.getroot().nsmap.get(None)

    def get_lines_text(self) -> List[str]:
        l_text = self.get_regions_lines_text()
        return [line for region in l_text for line in region]

    def get_regions_text(self) -> List[str]:
        """

        :return:
        """
        # TODO next line might not have to be separated by a space.
        # TODO think off '-'/hyphen, no space and perhaps even remove hyphen!

        l_text = self.get_regions_lines_text()
        return [' '.join(region) for region in l_text]

    @abstractmethod
    def get_regions_lines_text(self) -> List[List[str]]:
        """ Get per text region all the text lines as strings.

        :return:
            a list of the paragraphs/textblocks/textregions,
             with list of all the text lines in it.
        """
        pass

    def write(self, filename):
        # Adds <?xml version="1.0" encoding="UTF-8" standalone="yes"?> header
        self.element_tree.write(filename,
                                xml_declaration=True,
                                encoding="UTF-8",
                                standalone=True,
                                pretty_print=True)

    def to_bstring(self):
        return etree.tostring(self.element_tree,
                              xml_declaration=True,
                              encoding="UTF-8",
                              standalone=True,
                              pretty_print=True)

class PageXML(OverlayXML):
    def __init__(self, *args, b_autofix=False, **kwargs):
        """

        :param args:
        :param b_autofix: Flag to fix some mistakes we found in the XML.
            These mistakes were found by working with CEF eTranslation and PERO-OCR.
            While they cause no serious problems, some components might need a valid XML for further processing.
        :param kwargs:
        """
        super(PageXML, self).__init__(*args, **kwargs)

        if b_autofix:
            self.auto_fix()

    def validate(self):

        xmlschema_doc = etree.parse(FILENAME_XSD_PAGE)
        xmlschema = etree.XMLSchema(xmlschema_doc)

        namespace = {'page-1': 'http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15'}

        # validate against schema
        # https://emredjan.github.io/blog/2017/04/08/validating-xml/
        try:
            if self.element_tree.getroot().nsmap.get(None) not in namespace.values():
                raise TypeError('Not a valid Page XML file (namespace declaration missing)')

            xmlschema.assertValid(self.element_tree)
            print('XML valid, schema validation ok.')

        except etree.DocumentInvalid as err:
            print('Schema validation error, see error_schema.log')
            with open('error_schema.log', 'w') as error_log_file:
                error_log_file.write(str(err.error_log))

            raise err

        except Exception as e:
            print('Unknown error, exiting.')
            raise e

    def auto_fix(self, verbose=1):
        """ Issues with PERO-OCR Page XML
        * CONFIRMED, SOLVED, <?xml version="1.0"?> should be added as a header, solved in the write.
        * CONFIRMED, SOLVED, No metadata
        * CONFIRMED, SOLVED, id's are not allowed to start with a number
        https://www.oreilly.com/library/view/xml-pocket-reference/9780596100506/ch01s02s12.html

        * CONFIRMED, TODO, After translation, spaces are added in <created> and <LastChange>
        * CHECK, TODO, It might be that every text field is translated by eTranslation, if so, Page XML might not be the best format for sending for translation

        :return:
        """

        """
        <Metadata>
        <Creator>prov = Brno University of Technology/Faculty of Information Technology/Michal Hradiš/
            ihradis@fit.vut.cz: name = PERO OCR:
        </Creator>
        <Created>2021-02-10T10:18:50.269+01:00</Created>
        <LastChange>2021-02-10T10:22:53.331+01:00</LastChange>
        </Metadata>
        """
        root = self.element_tree.getroot()

        nsmap = root.nsmap
        PAGE_NAMESPACE = nsmap.get(None)

        METADATA_TAG = _get_tag("Metadata", PAGE_NAMESPACE)
        PAGE_TAG = _get_tag("Page", PAGE_NAMESPACE)

        if not root.findall(METADATA_TAG):  # couldn't find Metadata
            if verbose:
                print('Adding Metadata.')
            metadata_el = etree.Element(METADATA_TAG, nsmap=nsmap)

            creator_el = etree.SubElement(metadata_el, _get_tag("Creator", PAGE_NAMESPACE))
            created_el = etree.SubElement(metadata_el, _get_tag("Created", PAGE_NAMESPACE))
            last_ch_el = etree.SubElement(metadata_el, _get_tag("LastChange", PAGE_NAMESPACE))

            now = datetime.now()

            # expected ~ "2021-02-10T10:18:50.269+01:00"
            # now returns ~ '2021-02-26T17:20:34.110553'
            s_now = now.isoformat()

            creator_el.text = "prov = Brno University of Technology/Faculty of Information Technology/Michal Hradiš/ ihradis@fit.vut.cz: name = PERO OCR:"
            created_el.text = s_now  # "2021-02-10T10:18:50.269+01:00"
            last_ch_el.text = s_now  # "2021-02-10T10:22:53.331+01:00"

            root.insert(0, metadata_el)  # Should be first item

        if 1:  # debug
            etree.tostring(root.findall(METADATA_TAG)[0])

        for el_id in self.element_tree.xpath("//*[@id]"):
            id_v = el_id.attrib['id']
            if not id_v[:1].isalpha():
                if verbose:
                    print("Adding 'i-' to the id.")
                el_id.attrib['id'] = f'i-{id_v}'

        return

    def get_regions_lines_text(self) -> List[List[str]]:
        """

        :return:
            a list of the paragraphs/textblocks/textregions,
             with list of all the text lines in it.
        """

        xmlns = self.get_xmlns()

        l_text_page = []

        for region in self.element_tree.iterfind('.//{%s}TextRegion' % xmlns):
            # region

            l_text_line_paragraph = []

            for unicode_line in region.iterfind(
                    './/{{{xmlns}}}TextLine/{{{xmlns}}}TextEquiv/{{{xmlns}}}Unicode'.format(xmlns=xmlns)):
                # Catches None's to become an empty string.
                # Catch empty (None) text
                text_line = unicode_line.text.strip() if unicode_line.text else ''

                l_text_line_paragraph.append(text_line)

            l_text_page.append(l_text_line_paragraph)

        return l_text_page


class ALTOXML(OverlayXML):
    def get_regions_lines_text(self) -> List[List[str]]:
        """
        From https://github.com/cneud/alto-ocr-text

        :return:
            a list of the paragraphs/textblocks/textregions,
             with list of all the text lines in it.
        """

        namespace = {'alto-1': 'http://schema.ccs-gmbh.com/ALTO',
                     'alto-2': 'http://www.loc.gov/standards/alto/ns-v2#',
                     'alto-3': 'http://www.loc.gov/standards/alto/ns-v3#'}
        # tree = ET.parse(sys.argv[1])
        xmlns = self.element_tree.getroot().tag.split('}')[0].strip('{')
        if xmlns in namespace.values():

            l_text_page = []

            for region in self.element_tree.iterfind('.//{%s}TextBlock' % xmlns):
                # region

                l_text_line_paragraph = []

                for lines in region.iterfind('.//{%s}TextLine' % xmlns):

                    l_text_line = []

                    for line in lines.findall('{%s}String' % xmlns):
                        text_word = line.attrib.get('CONTENT')

                        l_text_line.append(text_word)

                    text_line = ' '.join(l_text_line)

                    l_text_line_paragraph.append(text_line)

                l_text_page.append(l_text_line_paragraph)
        else:
            raise TypeError('Not a valid ALTO file (namespace declaration missing)')

        return l_text_page


class XLIFFPageXML(PageXML):
    """
    To allow multilingual layout models.
    We suggest a combination of XLIFF with Page XML: Page for the layout model and XLIFF for the multilingual annotations.
    """

    # def get_regions_lines_text(self) -> List[List[str]]:
    #     pass # TODO

    def __init__(self, filename):
        """
        We probably start from the regular Page XML and then allow to add other languages.
        """

        super(XLIFFPageXML, self).__init__(filename)

    @classmethod
    def from_page(cls, filename, source_lang=None):
        # TODO auto detect source_lang

        xml = cls(filename)

        # TODO change nsmap!

        xml.element_tree = _change_namespace(xml.element_tree, "urn:occam:multilingual_pagecontent:0.3").getroottree()

        xmlns = xml.get_xmlns()
        for i_r, text_reg in enumerate(xml.element_tree.iterfind('.//{%s}TextRegion' % xmlns)):
            for i_l, text_line in enumerate(text_reg.iterfind('.//{%s}TextLine' % xmlns)):

                for text_equiv in text_line.iterfind('.//{%s}TextEquiv' % xmlns):

                    e_unicode = list(text_equiv.iterfind('.//{%s}Unicode' % xmlns))[0]

                    l_trans_unit = list(text_equiv.iterfind('.//{%s}trans-unit' % xmlns))
                    if l_trans_unit:
                        trans_unit = l_trans_unit[0]
                    else:
                        trans_unit = etree.SubElement(text_equiv, _get_tag("trans-unit", xmlns),
                                                      id=f'r{i_r:03d}-l{i_l:03d}')

                    l_source = list(text_equiv.iterfind('.//{%s}source' % xmlns))
                    if l_source:
                        source = l_source[0]
                    else:

                        attrib = {_get_tag("lang", XML_NAMESPACE): source_lang}

                        source = etree.SubElement(trans_unit, _get_tag("source", xmlns),
                                                  attrib)

                        e_unicode_text = e_unicode.text
                        source.text = e_unicode_text.strip() if e_unicode_text else ''

        return xml

    def add_targets(self, l_target_text, lang_target):
        """
        Add other languages.

        :return:
        """

        xmlns = self.get_xmlns()

        l_text_equiv = self.element_tree.iterfind('.//{%s}TextEquiv' % xmlns)

        for text_equiv, target_text in zip(l_text_equiv, l_target_text):
            l_trans_unit = list(text_equiv.iterfind('.//{%s}trans-unit' % xmlns))
            trans_unit = l_trans_unit[0]

            attrib = {_get_tag("lang", XML_NAMESPACE): lang_target}
            target = etree.SubElement(trans_unit, _get_tag("target", xmlns),
                                      attrib)

            target.text = target_text

        return

    def validate(self):

        # TODO make this load

        warnings.warn('Not implemented yet', UserWarning)
        return
        xmlschema_doc = etree.parse(FILENAME_XSD_MULTILINGUAL_PAGE)
        xmlschema = etree.XMLSchema(xmlschema_doc)

        # validate against schema
        # https://emredjan.github.io/blog/2017/04/08/validating-xml/
        try:
            xmlschema.assertValid(self.element_tree)
            print('XML valid, schema validation ok.')

        except etree.DocumentInvalid as err:
            print('Schema validation error, see error_schema.log')
            with open('error_schema.log', 'w') as error_log_file:
                error_log_file.write(str(err.error_log))

            raise err

        except Exception as e:
            print('Unknown error, exiting.')
            raise e


def _get_tag(tag, namespace):
    return f'{{{namespace}}}{tag}'
