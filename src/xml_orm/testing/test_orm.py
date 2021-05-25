import os
import unittest
import warnings

from lxml import etree

from xml_orm.orm import parse_etree, PageXML, ALTOXML, XLIFFPageXML

ROOT_TEST = os.path.join(os.path.dirname(__file__))

FILENAME_PAGE_XML = {
    0: os.path.join(ROOT_TEST, 'example_files/KB_JB840_1919-04-01_01_0_fixed.xml'),
    1: os.path.join(ROOT_TEST, 'example_files/transkribus/KB_JB840_1919-04-01_01_0.xml'),
}[0]
FILENAME_MULTILANG_XML = os.path.join(ROOT_TEST, 'example_files/KB_JB840_1919-04-01_01_0_fixed_NL_EN.xml')

FILENAME_PAGE_XML_NONVALID = os.path.join(ROOT_TEST, 'example_files/KB_JB840_1919-04-01_01_0.xml')
FILENAME_ALTO = os.path.join(ROOT_TEST, 'example_files/alto/KB_JB840_1919-04-01_01-00001.xml')

# Sanity check
for filename in (FILENAME_PAGE_XML,
                 FILENAME_MULTILANG_XML,
                 FILENAME_PAGE_XML_NONVALID,
                 FILENAME_ALTO):
    if not os.path.exists(filename):
        warnings.warn(f"Couldn't find {filename}! Check if added correctly.", UserWarning)


class TestJoinXML(unittest.TestCase):
    """
    Test the translation on real data from KBR
    """

    def test_(self):
        xml_tree = parse_etree(FILENAME_PAGE_XML)  # read xml
        xml_tree_trans = parse_etree(FILENAME_MULTILANG_XML)  # read xml

        page_xml = PageXML(FILENAME_PAGE_XML)
        page_xml_trans = PageXML(FILENAME_MULTILANG_XML)

        with self.subTest('page xml'):
            page_xml.validate()

        with self.subTest('multilingual page xml'):
            page_xml_trans.validate()

        # xml = XMLTranslator(xml_tree)
        # xml_trans = XMLTranslator(xml_tree_trans)

        return

    # def test_quality(self):
    #
    #     # Zip over the text fields.

    def test_auto_fix(self):
        """ We found out the Page XML produced by PERO-OCR does not always seem to be valid. We'll try to solve this.

        :return:
        """

        xml = PageXML(FILENAME_PAGE_XML_NONVALID)
        xml.auto_fix()

        with self.subTest('Validation should be ok now:'):
            xml.validate()

        b = 0
        if b:  # Save
            xml.write(FILENAME_PAGE_XML)

        return


class TestPageXML(unittest.TestCase):

    def setUp(self) -> None:

        self.filename = FILENAME_PAGE_XML

    def test_page_fix(self):

        FILENAME = r"G:\My Drive\OCCAM\media\gold_standard\BRIS\layout_model\GoldStandard\19154766-page0.xml"

        FILENAME_FIXED = os.path.splitext(FILENAME)[0] + '_fixed.xml'

        page_xml = PageXML(FILENAME)

        try:
            page_xml.validate()
        except Exception as e:
            print(e)
            page_xml.auto_fix()
            page_xml.validate()

        finally:
            page_xml.write(FILENAME_FIXED)

        # page_xml.auto_fix()
        # page_xml.write()

    def test_page_to_txt(self):

        FILENAME_RAWTEXT = os.path.splitext(self.filename)[0] + '_rawtext.txt'

        page_xml = PageXML(self.filename)

        l_text = page_xml.get_regions_lines_text()
        b_debug = False
        if b_debug:
            print(l_text)

        l_text_lines = page_xml.get_lines_text()

        with open(FILENAME_RAWTEXT, 'w') as filehandle:
            for listitem in l_text_lines:
                filehandle.write('%s\n' % listitem)

    def test_get_regions_text(self):

        FILENAME_RAWREGIONS = os.path.splitext(self.filename)[0] + '_rawtextregions.txt'

        page_xml = PageXML(self.filename)
        l_regions = page_xml.get_regions_text()

        with open(FILENAME_RAWREGIONS, 'w') as filehandle:
            for listitem in l_regions:
                filehandle.write('%s\n' % listitem)


class TestALTOXML(unittest.TestCase):
    def setUp(self) -> None:

        self.FILENAME = FILENAME_ALTO

    def test_alto_to_txt(self):
        FILENAME_RAWTEXT = os.path.splitext(FILENAME_ALTO)[0] + '_rawtext.txt'

        alto_xml = ALTOXML(self.FILENAME)

        l_text = alto_xml.get_regions_lines_text()
        b_debug = False
        if b_debug:
            print(l_text)

        l_text_lines = alto_xml.get_lines_text()

        with open(FILENAME_RAWTEXT, 'w') as filehandle:
            for listitem in l_text_lines:
                filehandle.write('%s\n' % listitem)

    def test_get_regions_text(self):

        FILENAME_RAWREGIONS = os.path.splitext(self.FILENAME)[0] + '_rawtextregions.txt'

        alto_xml = ALTOXML(self.FILENAME)

        l_regions = alto_xml.get_regions_text()

        with open(FILENAME_RAWREGIONS, 'w') as filehandle:
            for listitem in l_regions:
                filehandle.write('%s\n' % listitem)


class TestXLIFFPageXML(unittest.TestCase):

    def setUp(self) -> None:
        self.filename = FILENAME_PAGE_XML

    def test_init(self):

        xml = XLIFFPageXML(self.filename)

        etree.dump(xml.element_tree.getroot())

        return

    def test_validate(self):
        xml = XLIFFPageXML(self.filename)

        etree.dump(xml.element_tree.getroot())

        xml.validate()

    def test_join(self):
        return

    def test_integration(self):
        """
        Do a full integration test of the Translation + XML
        Open XML, translate and add to the XML.

        :return:
        """

        return
