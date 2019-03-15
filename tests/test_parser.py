from gedcom.element.individual import IndividualElement
from gedcom.parser import Parser


def test_initialization():
    parser = Parser()
    assert isinstance(parser, Parser)


def test_parse_file():
    parser = Parser()
    parser.parse_file('tests/files/Musterstammbaum.ged')

    individuals_in_root_child_elements = 0
    individuals_in_element_list = 0

    for element in parser.get_root_child_elements():
        if isinstance(element, IndividualElement):
            individuals_in_root_child_elements += 1

    for element in parser.get_element_list():
        if isinstance(element, IndividualElement):
            individuals_in_element_list += 1

    assert individuals_in_root_child_elements == 20
    assert individuals_in_element_list == 20
    assert len(parser.get_root_child_elements()) == 34
