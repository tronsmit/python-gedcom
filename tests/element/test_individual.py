from gedcom.element.element import Element
from gedcom.element.individual import IndividualElement
import gedcom.tags


def test_initialization():
    individual_element = IndividualElement(level=-1, pointer="", tag=gedcom.tags.GEDCOM_TAG_INDIVIDUAL, value="")
    assert isinstance(individual_element, Element)
    assert isinstance(individual_element, IndividualElement)


def test_get_all_names():
    element = IndividualElement(level=0, pointer="@I5@", tag="INDI", value="")
    element.new_child_element(tag="NAME", value="First /Last/")
    element.new_child_element(tag="SEX", value="M")
    birth = element.new_child_element(tag="BIRT", value="")
    birth.new_child_element(tag="DATE", value="1 JAN 1900")
    element.new_child_element(tag="NAME", value="Second /Surname/")

    all_names = element.get_all_names()
    assert len(all_names) == 2
