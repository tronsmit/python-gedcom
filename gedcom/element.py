# Python GEDCOM Parser
#
# Copyright (C) 2018 Damon Brodie (damon.brodie at gmail.com)
# Copyright (C) 2018 Nicklas Reincke (contact at reynke.com)
# Copyright (C) 2016 Andreas Oberritter
# Copyright (C) 2012 Madeleine Price Ball
# Copyright (C) 2005 Daniel Zappala (zappala at cs.byu.edu)
# Copyright (C) 2005 Brigham Young University
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#
# Further information about the license: http://www.gnu.org/licenses/gpl-2.0.html

import re as regex
from sys import version_info
import gedcom.tags


class Element:
    """GEDCOM element

    Each line in a GEDCOM file is an element with the format

    level [pointer] tag [value]

    where level and tag are required, and pointer and value are
    optional.  Elements are arranged hierarchically according to their
    level, and elements with a level of zero are at the top level.
    Elements with a level greater than zero are children of their
    parent.

    A pointer has the format @pname@, where pname is any sequence of
    characters and numbers.  The pointer identifies the object being
    pointed to, so that any pointer included as the value of any
    element points back to the original object.  For example, an
    element may have a FAMS tag whose value is @F1@, meaning that this
    element points to the family record in which the associated person
    is a spouse.  Likewise, an element with a tag of FAMC has a value
    that points to a family record in which the associated person is a
    child.

    See a GEDCOM file for examples of tags and their values.
    """

    def __init__(self, level, pointer, tag, value, crlf="\n", multi_line=True):
        """Initialize an element

        You must include a level, a pointer, a tag, and a value.
        Normally initialized by the GEDCOM parser, not by a user.

        :type level: int
        :type pointer: str
        :type tag: str
        :type value: str
        :type crlf: str
        :type multi_line: bool
        """

        # basic element info
        self.__level = level
        self.__pointer = pointer
        self.__tag = tag
        self.__value = value
        self.__crlf = crlf

        # structuring
        self.__children = []
        self.__parent = None

        if multi_line:
            self.set_multi_line_value(value)

    def get_level(self):
        """Return the level of this element
        :rtype: int
        """
        return self.__level

    def get_pointer(self):
        """Return the pointer of this element
        :rtype: str
        """
        return self.__pointer

    def get_tag(self):
        """Return the tag of this element
        :rtype: str
        """
        return self.__tag

    def get_value(self):
        """Return the value of this element
        :rtype: str
        """
        return self.__value

    def set_value(self, value):
        """Set the value of this element
        :type value: str
        """
        self.__value = value

    def get_multi_line_value(self):
        """Return the value of this element including continuations
        :rtype: str
        """
        result = self.get_value()
        last_crlf = self.__crlf
        for element in self.get_child_elements():
            tag = element.get_tag()
            if tag == gedcom.tags.GEDCOM_TAG_CONCATENATION:
                result += element.get_value()
                last_crlf = element.__crlf
            elif tag == gedcom.tags.GEDCOM_TAG_CONTINUED:
                result += last_crlf + element.get_value()
                last_crlf = element.__crlf
        return result

    def __available_characters(self):
        """Get the number of available characters of the elements original string
        :rtype: int
        """
        element_characters = len(self.__unicode__())
        return 0 if element_characters > 255 else 255 - element_characters

    def __line_length(self, line):
        """@TODO Write docs.
        :type line: str
        :rtype: int
        """
        total_characters = len(line)
        available_characters = self.__available_characters()
        if total_characters <= available_characters:
            return total_characters
        spaces = 0
        while spaces < available_characters and line[available_characters - spaces - 1] == ' ':
            spaces += 1
        if spaces == available_characters:
            return available_characters
        return available_characters - spaces

    def __set_bounded_value(self, value):
        """@TODO Write docs.
        :type value: str
        :rtype: int
        """
        line_length = self.__line_length(value)
        self.set_value(value[:line_length])
        return line_length

    def __add_bounded_child(self, tag, value):
        """@TODO Write docs.
        :type tag: str
        :type value: str
        :rtype: int
        """
        child = self.new_child_element(tag)
        return child.__set_bounded_value(value)

    def __add_concatenation(self, string):
        """@TODO Write docs.
        :rtype: str
        """
        index = 0
        size = len(string)
        while index < size:
            index += self.__add_bounded_child(gedcom.tags.GEDCOM_TAG_CONCATENATION, string[index:])

    def set_multi_line_value(self, value):
        """Set the value of this element, adding continuation lines as necessary
        :type value: str
        """
        self.set_value('')
        self.get_child_elements()[:] = [child for child in self.get_child_elements() if
                                        child.get_tag() not in (gedcom.tags.GEDCOM_TAG_CONCATENATION, gedcom.tags.GEDCOM_TAG_CONTINUED)]

        lines = value.splitlines()
        if lines:
            line = lines.pop(0)
            n = self.__set_bounded_value(line)
            self.__add_concatenation(line[n:])

            for line in lines:
                n = self.__add_bounded_child(gedcom.tags.GEDCOM_TAG_CONTINUED, line)
                self.__add_concatenation(line[n:])

    def get_child_elements(self):
        """Return the child elements of this element
        :rtype: list of Element
        """
        return self.__children

    def get_parent_element(self):
        """Return the parent element of this element
        :rtype: Element
        """
        return self.__parent

    def new_child_element(self, tag, pointer="", value=""):
        """Create and return a new child element of this element

        :type tag: str
        :type pointer: str
        :type value: str
        :rtype: Element
        """
        child_element = Element(self.get_level() + 1, pointer, tag, value, self.__crlf)
        self.add_child_element(child_element)
        return child_element

    def add_child_element(self, element):
        """Add a child element to this element

        :type element: Element
        """
        self.get_child_elements().append(element)
        element.set_parent_element(self)

    def set_parent_element(self, element):
        """Add a parent element to this element

        There's usually no need to call this method manually,
        add_child_element() calls it automatically.

        :type element: Element
        """
        self.__parent = element

    def is_individual(self):
        """Check if this element is an individual
        :rtype: bool
        """
        return self.get_tag() == gedcom.tags.GEDCOM_TAG_INDIVIDUAL

    def is_child(self):
        """Check if this element is a child
        :rtype: bool
        """
        if not self.is_individual():
            raise ValueError("Operation only valid for elements with %s tag" % gedcom.tags.GEDCOM_TAG_INDIVIDUAL)
        found_child = False
        for child in self.get_child_elements():
            if child.get_tag() == gedcom.tags.GEDCOM_TAG_FAMILY_CHILD:
                found_child = True
        return found_child

    def is_family(self):
        """Check if this element is a family
        :rtype: bool
        """
        return self.get_tag() == gedcom.tags.GEDCOM_TAG_FAMILY

    def is_file(self):
        """Check if this element is a file
        :rtype: bool
        """
        return self.get_tag() == gedcom.tags.GEDCOM_TAG_FILE

    def is_object(self):
        """Check if this element is an object
        :rtype: bool
        """
        return self.get_tag() == gedcom.tags.GEDCOM_TAG_OBJECT

    # criteria matching

    def criteria_match(self, criteria):
        """Check in this element matches all of the given criteria

        `criteria` is a colon-separated list, where each item in the
        list has the form [name]=[value]. The following criteria are supported:

        surname=[name]
             Match a person with [name] in any part of the surname.
        name=[name]
             Match a person with [name] in any part of the given name.
        birth=[year]
             Match a person whose birth year is a four-digit [year].
        birth_range=[from_year-to_year]
             Match a person whose birth year is in the range of years from
             [from_year] to [to_year], including both [from_year] and [to_year].
        death=[year]
        death_range=[from_year-to_year]

        :type criteria: str
        :rtype: bool
        """

        # Check if criteria is a valid criteria
        try:
            for criterion in criteria.split(':'):
                criterion.split('=')
        except ValueError:
            return False

        match = True

        for criterion in criteria.split(':'):
            key, value = criterion.split('=')
            if key == "surname" and not self.surname_match(value):
                match = False
            elif key == "name" and not self.given_match(value):
                match = False
            elif key == "birth":
                try:
                    year = int(value)
                    if not self.birth_year_match(year):
                        match = False
                except ValueError:
                    match = False
            elif key == "birth_range":
                try:
                    from_year, to_year = value.split('-')
                    from_year = int(from_year)
                    to_year = int(to_year)
                    if not self.birth_range_match(from_year, to_year):
                        match = False
                except ValueError:
                    match = False
            elif key == "death":
                try:
                    year = int(value)
                    if not self.death_year_match(year):
                        match = False
                except ValueError:
                    match = False
            elif key == "death_range":
                try:
                    from_year, to_year = value.split('-')
                    from_year = int(from_year)
                    to_year = int(to_year)
                    if not self.death_range_match(from_year, to_year):
                        match = False
                except ValueError:
                    match = False

        return match

    def surname_match(self, name):
        """Match a string with the surname of an individual
        :type name: str
        :rtype: bool
        """
        (first, last) = self.get_name()
        return regex.search(name, last, regex.IGNORECASE)

    def given_match(self, name):
        """Match a string with the given names of an individual
        :type name: str
        :rtype: bool
        """
        (first, last) = self.get_name()
        return regex.search(name, first, regex.IGNORECASE)

    def birth_year_match(self, year):
        """Match the birth year of an individual
        :type year: int
        :rtype: bool
        """
        return self.get_birth_year() == year

    def birth_range_match(self, from_year, to_year):
        """Check if the birth year of an individual is in a given range
        :type from_year: int
        :type to_year: int
        :rtype: bool
        """
        birth_year = self.get_birth_year()
        if from_year <= birth_year <= to_year:
            return True
        return False

    def death_year_match(self, year):
        """Match the death year of an individual.
        :type year: int
        :rtype: bool
        """
        return self.get_death_year() == year

    def death_range_match(self, from_year, to_year):
        """Check if the death year of an individual is in a given range. Years are integers
        :type from_year: int
        :type to_year: int
        :rtype: bool
        """
        death_year = self.get_death_year()
        if from_year <= death_year <= to_year:
            return True
        return False

    def get_name(self):
        """Return a person's names as a tuple: (first, last)
        :rtype: tuple
        """
        first = ""
        last = ""
        if not self.is_individual():
            return first, last

        # Return the first gedcom.tags.GEDCOM_TAG_NAME that is found.  Alternatively
        # as soon as we have both the gedcom.tags.GEDCOM_TAG_GIVEN_NAME and _SURNAME return those
        found_given_name = False
        found_surname_name = False
        for child in self.get_child_elements():
            if child.get_tag() == gedcom.tags.GEDCOM_TAG_NAME:
                # some GEDCOM files don't use child tags but instead
                # place the name in the value of the NAME tag
                if child.get_value() != "":
                    name = child.get_value().split('/')
                    if len(name) > 0:
                        first = name[0].strip()
                        if len(name) > 1:
                            last = name[1].strip()
                    return first, last
                else:
                    for childOfChild in child.get_child_elements():
                        if childOfChild.get_tag() == gedcom.tags.GEDCOM_TAG_GIVEN_NAME:
                            first = childOfChild.get_value()
                            found_given_name = True
                        if childOfChild.get_tag() == gedcom.tags.GEDCOM_TAG_SURNAME:
                            last = childOfChild.get_value()
                            found_surname_name = True
                    if found_given_name and found_surname_name:
                        return first, last

        # If we reach here we are probably returning empty strings
        return first, last

    def get_gender(self):
        """Return the gender of a person in string format
        :rtype: str
        """
        gender = ""
        if not self.is_individual():
            return gender
        for child in self.get_child_elements():
            if child.get_tag() == gedcom.tags.GEDCOM_TAG_SEX:
                gender = child.get_value()
        return gender

    def is_private(self):
        """Return if the person is marked private in boolean format
        :rtype: bool
        """
        private = False
        if not self.is_individual():
            return private
        for child in self.get_child_elements():
            if child.get_tag() == gedcom.tags.GEDCOM_TAG_PRIVATE:
                private = child.get_value()
                if private == 'Y':
                    private = True
        return private

    def get_birth_data(self):
        """Return the birth tuple of a person as (date, place, sources)
        :rtype: tuple
        """
        date = ""
        place = ""
        sources = []
        if not self.is_individual():
            return date, place, sources
        for child in self.get_child_elements():
            if child.get_tag() == gedcom.tags.GEDCOM_TAG_BIRTH:
                for childOfChild in child.get_child_elements():
                    if childOfChild.get_tag() == gedcom.tags.GEDCOM_TAG_DATE:
                        date = childOfChild.get_value()
                    if childOfChild.get_tag() == gedcom.tags.GEDCOM_TAG_PLACE:
                        place = childOfChild.get_value()
                    if childOfChild.get_tag() == gedcom.tags.GEDCOM_TAG_SOURCE:
                        sources.append(childOfChild.get_value())
        return date, place, sources

    def get_birth_year(self):
        """Return the birth year of a person in integer format
        :rtype: int
        """
        date = ""
        if not self.is_individual():
            return date
        for child in self.get_child_elements():
            if child.get_tag() == gedcom.tags.GEDCOM_TAG_BIRTH:
                for childOfChild in child.get_child_elements():
                    if childOfChild.get_tag() == gedcom.tags.GEDCOM_TAG_DATE:
                        date_split = childOfChild.get_value().split()
                        date = date_split[len(date_split) - 1]
        if date == "":
            return -1
        try:
            return int(date)
        except ValueError:
            return -1

    def get_death_data(self):
        """Return the death tuple of a person as (date, place, sources)
        :rtype: tuple
        """
        date = ""
        place = ""
        sources = []
        if not self.is_individual():
            return date, place
        for child in self.get_child_elements():
            if child.get_tag() == gedcom.tags.GEDCOM_TAG_DEATH:
                for childOfChild in child.get_child_elements():
                    if childOfChild.get_tag() == gedcom.tags.GEDCOM_TAG_DATE:
                        date = childOfChild.get_value()
                    if childOfChild.get_tag() == gedcom.tags.GEDCOM_TAG_PLACE:
                        place = childOfChild.get_value()
                    if childOfChild.get_tag() == gedcom.tags.GEDCOM_TAG_SOURCE:
                        sources.append(childOfChild.get_value())
        return date, place, sources

    def get_death_year(self):
        """Return the death year of a person in integer format
        :rtype: int
        """
        date = ""
        if not self.is_individual():
            return date
        for child in self.get_child_elements():
            if child.get_tag() == gedcom.tags.GEDCOM_TAG_DEATH:
                for childOfChild in child.get_child_elements():
                    if childOfChild.get_tag() == gedcom.tags.GEDCOM_TAG_DATE:
                        date_split = childOfChild.get_value().split()
                        date = date_split[len(date_split) - 1]
        if date == "":
            return -1
        try:
            return int(date)
        except ValueError:
            return -1

    def get_burial(self):
        """Return the burial tuple of a person as (date, place, sources)
        :rtype: tuple
        """
        date = ""
        place = ""
        sources = []
        if not self.is_individual():
            return date, place
        for child in self.get_child_elements():
            if child.get_tag() == gedcom.tags.GEDCOM_TAG_BURIAL:
                for childOfChild in child.get_child_elements():
                    if childOfChild.get_tag() == gedcom.tags.GEDCOM_TAG_DATE:
                        date = childOfChild.get_value()
                    if childOfChild.get_tag() == gedcom.tags.GEDCOM_TAG_PLACE:
                        place = childOfChild.get_value()
                    if childOfChild.get_tag() == gedcom.tags.GEDCOM_TAG_SOURCE:
                        sources.append(childOfChild.get_value())
        return date, place, sources

    def get_census(self):
        """Return list of census tuples (date, place, sources) for an individual
        :rtype: tuple
        """
        census = []
        if not self.is_individual():
            raise ValueError("Operation only valid for elements with %s tag" % gedcom.tags.GEDCOM_TAG_INDIVIDUAL)
        for child in self.get_child_elements():
            if child.get_tag() == gedcom.tags.GEDCOM_TAG_CENSUS:
                date = ''
                place = ''
                sources = []
                for childOfChild in child.get_child_elements():
                    if childOfChild.get_tag() == gedcom.tags.GEDCOM_TAG_DATE:
                        date = childOfChild.get_value()
                    if childOfChild.get_tag() == gedcom.tags.GEDCOM_TAG_PLACE:
                        place = childOfChild.get_value()
                    if childOfChild.get_tag() == gedcom.tags.GEDCOM_TAG_SOURCE:
                        sources.append(childOfChild.get_value())
                census.append((date, place, sources))
        return census

    def get_last_change_date(self):
        """Return the last updated date of a person as (date)
        :rtype: str
        """
        date = ""
        if not self.is_individual():
            return date
        for child in self.get_child_elements():
            if child.get_tag() == gedcom.tags.GEDCOM_TAG_CHANGE:
                for childOfChild in child.get_child_elements():
                    if childOfChild.get_tag() == gedcom.tags.GEDCOM_TAG_DATE:
                        date = childOfChild.get_value()
        return date

    def get_occupation(self):
        """Return the occupation of a person as (date)
        :rtype: str
        """
        occupation = ""
        if not self.is_individual():
            return occupation
        for child in self.get_child_elements():
            if child.get_tag() == gedcom.tags.GEDCOM_TAG_OCCUPATION:
                occupation = child.get_value()
        return occupation

    def is_deceased(self):
        """Check if a person is deceased
        :rtype: bool
        """
        if not self.is_individual():
            return False
        for child in self.get_child_elements():
            if child.get_tag() == gedcom.tags.GEDCOM_TAG_DEATH:
                return True
        return False

    def get_individual(self):
        """Return this element and all of its sub-elements
        :rtype: str
        """
        result = self.__unicode__()
        for child_element in self.get_child_elements():
            result += child_element.get_individual()
        return result

    def __str__(self):
        """:rtype: str"""
        if version_info[0] >= 3:
            return self.__unicode__()
        else:
            return self.__unicode__().encode('utf-8')

    def __unicode__(self):
        """Format this element as its original string
        :rtype: str
        """
        if self.get_level() < 0:
            return ''
        result = str(self.get_level())
        if self.get_pointer() != "":
            result += ' ' + self.get_pointer()
        result += ' ' + self.get_tag()
        if self.get_value() != "":
            result += ' ' + self.get_value()
        result += self.__crlf
        return result
