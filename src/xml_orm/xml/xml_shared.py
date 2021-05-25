from datetime import datetime, timezone
import os
import requests

from lxml import etree
from lxml.etree import tostring, XMLParser, fromstring


def extract_simple_tags(tree):
    l_tags = [elem.tag for elem in tree.iter()]

    # Remove duplicates
    l_tags = list(set(l_tags))

    simple_tags_dict = {tag.split('}')[-1]: tag for tag in l_tags}

    return simple_tags_dict


def get_namespace_uri(root):
    return root.xpath('namespace-uri(.)')


def get_xpath_unique(tree, s_xpath):
    l_unique = tree.xpath(s_xpath)
    assert len(l_unique) == 1, l_unique
    return l_unique[0]


def get_iter_unique(tree, tag):
    l_unique = list(tree.iter(tag))
    assert len(l_unique) == 1
    return l_unique[0]


def validate_pagexml(element_tree):
    file_xsd = os.path.join(os.path.dirname(__file__), "pagecontent_2013_07_15.xsd")
    if not os.path.exists(file_xsd):
        url_xsd = 'https://www.primaresearch.org/schema/PAGE/gts/pagecontent/2013-07-15/pagecontent.xsd'
        r = requests.get(url_xsd, allow_redirects=True)
        with open(file_xsd, 'wb') as f:
            f.write(r.content)

    xml_validator = etree.XMLSchema(file=file_xsd)

    if xml_validator.validate(element_tree):
        return  # XML file is up to standard

    else:
        error_log = xml_validator.error_log
        print(error_log)

        return error_log


def save_xml(path, root):
    _update_metadata(root, init=True)

    # save the updated xml
    s = _prettify(root)

    with open(path, 'wb') as output:
        output.write(s)

    return


def _prettify(tree):
    """Return a pretty-printed XML string for the Element.
    """

    rough_string = tostring(tree, encoding="utf-8")

    # Fix inconsistent indentations.
    # Parse again
    parser = XMLParser(remove_blank_text=True)
    root_simple = fromstring(rough_string, parser=parser)

    validate_pagexml(root_simple)

    s = tostring(root_simple,
                 encoding="utf-8",
                 pretty_print=True,
                 xml_declaration=True,
                 # standalone=False
                 )

    try:
        fromstring(s)
    except Exception:
        raise ValueError("Not a proper xml anymore", s)

    return s


def _update_metadata(root, creator=None, init=False):
    """

    :param root:
    :param creator:
    :param init: boolean that decides if *creator* and *created* should be overwrited or not.
    :return:
    """
    """
    example:

      <Metadata>
        <Creator>OCCAM</Creator>
        <Created>2020-07-07T15:56:40.547+02:00</Created>
        <LastChange>2020-07-07T15:56:40.547+02:00</LastChange>
      </Metadata>
    """

    if creator is None:
        creator = "OCCAM"

    simple_tags = extract_simple_tags(root)

    key_metadata = "Metadata"
    if key_metadata not in simple_tags.keys():
        p = get_iter_unique(root, simple_tags['PcGts'])

        # Update simple tags
        ns = get_namespace_uri(root)
        simple_tags[key_metadata] = f"{{{ns}}}{key_metadata}"
        simple_tags['Creator'] = f"{{{ns}}}{'Creator'}"
        simple_tags['Created'] = f"{{{ns}}}{'Created'}"
        simple_tags['LastChange'] = f"{{{ns}}}{'LastChange'}"

        m = etree.Element(simple_tags[key_metadata])

        etree.SubElement(m, simple_tags['Creator'])
        etree.SubElement(m, simple_tags['Created'])
        etree.SubElement(m, simple_tags['LastChange'])

        p.insert(0, m)

    _update_field(root, simple_tags["Creator"], creator, init)
    s_time = datetime.now(timezone.utc).astimezone().isoformat()  # e.g. 2020-07-08T14:12:40.135092+02:00
    _update_field(root, simple_tags["Created"], s_time, init)
    _update_field(root, simple_tags["LastChange"], s_time, True)
    return


def _update_field(tree, tag: str, text: str, update: bool):
    t = get_iter_unique(tree, tag)

    if update or (t.text is None):
        t.text = text

    return


def _change_namespace(root, target_namespace):
    # working in bytestring utf-8
    try:
        target_namespace = target_namespace.encode("utf-8")
    except AttributeError:  # already bytes
        pass

    # Set namespace
    s = etree.tostring(root,
                       encoding='utf-8')
    i = s.find(b"xmlns=")
    s0, s1 = s[:i], s[i:]

    s2, _, s4 = s1.split(b'\"', 2)

    s_comb = s0 + b'\"'.join([s2, target_namespace, s4])

    root_target = etree.fromstring(s_comb)

    return root_target
