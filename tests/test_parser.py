from gedcom.element.individual import IndividualElement
from gedcom.element.root import RootElement
from gedcom.parser import Parser


def test_initialization():
    parser = Parser()
    assert isinstance(parser, Parser)


def test_invalidate_cache():
    parser = Parser()
    parser.parse_file('tests/files/Musterstammbaum.ged')

    assert len(parser.get_element_list()) == 396
    assert len(parser.get_element_dictionary()) == 32

    parser.invalidate_cache()

    assert len(parser.get_element_list()) == 396
    assert len(parser.get_element_dictionary()) == 32


def test_get_root_element():
    parser = Parser()
    assert isinstance(parser.get_root_element(), RootElement)


def test_parse_file():
    parser = Parser()

    assert len(parser.get_root_child_elements()) == 0

    parser.parse_file('tests/files/Musterstammbaum.ged')

    assert len(parser.get_root_child_elements()) == 34

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


def test___parse_line():
    # @TODO Add appropriate testing cases
    pass
