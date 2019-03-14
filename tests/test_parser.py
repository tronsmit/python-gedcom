from gedcom.parser import Parser


def test_initialization():
    parser = Parser()
    assert isinstance(parser, Parser)
