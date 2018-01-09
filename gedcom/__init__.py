# Python GEDCOM Parser
#
# Licensed under the [GNU General Public License v2](http://www.gnu.org/licenses/gpl-2.0.html)
#
# Python GEDCOM
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

__all__ = ["Gedcom", "Element", "GedcomParseError"]

# Global imports
import re as regex
from sys import version_info


class Gedcom:
    """Parses and manipulates GEDCOM 5.5 format data

    For documentation of the GEDCOM 5.5 format, see:
    http://homepages.rootsweb.ancestry.com/~pmcbride/gedcom/55gctoc.htm

    This parser reads and parses a GEDCOM file.
    Elements may be accessed via:
      - a list (all elements, default order is same as in file)
      - a dict (only elements with pointers, which are the keys)
    """

    def __init__(self, file_path):
        """Initialize a GEDCOM data object. You must supply a GEDCOM file"""
        self.__element_list = []
        self.__element_dictionary = {}
        self.invalidate_cache()
        self.__top_element = Element(-1, "", "TOP", "")
        self.__parse(file_path)

    def invalidate_cache(self):
        """Cause element_list() and element_dict() to return updated data

        The update gets deferred until each of the methods actually gets called.
        """
        self.__element_list = []
        self.__element_dictionary = {}

    def element_list(self):
        """Return a list of all the elements in the GEDCOM file

        By default elements are in the same order as they appeared in the file.

        This list gets generated on-the-fly, but gets cached. If the database
        was modified, you should call invalidate_cache() once to let this
        method return updated data.

        Consider using root() or records() to access the hierarchical GEDCOM
        tree, unless you rarely modify the database.
        """
        if not self.__element_list:
            for element in self.records():
                self.__build_list(element, self.__element_list)
        return self.__element_list

    def element_dict(self):
        """Return a dictionary of elements from the GEDCOM file

        Only elements identified by a pointer are listed in the dictionary.
        The keys for the dictionary are the pointers.

        This dictionary gets generated on-the-fly, but gets cached. If the
        database was modified, you should call invalidate_cache() once to let
        this method return updated data.
        """
        if not self.__element_dictionary:
            self.__element_dictionary = {element.get_pointer(): element for element in self.records() if
                                         element.get_pointer()}

        return self.__element_dictionary

    def root(self):
        """Returns a virtual root element containing all logical records as children

        When printed, this element converts to an empty string.
        """
        return self.__top_element

    def records(self):
        """Return a list of logical records in the GEDCOM file

        By default, elements are in the same order as they appeared in the file.
        """
        return self.root().get_child_elements()

    # Private methods

    def __parse(self, file_path):
        """Open and parse file path as GEDCOM 5.5 formatted data"""
        gedcom_file = open(file_path, 'rb')
        line_number = 1
        last_element = self.__top_element
        for line in gedcom_file:
            last_element = self.__parse_line(line_number, line.decode('utf-8'), last_element)
            line_number += 1

    def __parse_line(self, line_num, line, last_element):
        """Parse a line from a GEDCOM 5.5 formatted document

        Each line should have the following (bracketed items optional):
        level + ' ' + [pointer + ' ' +] tag + [' ' + line_value]
        """
        ged_line_regex = (
            # Level must start with nonnegative int, no leading zeros.
                '^(0|[1-9]+[0-9]*) ' +
                # Pointer optional, if it exists it must be flanked by '@'
                '(@[^@]+@ |)' +
                # Tag must be alphanumeric string
                '([A-Za-z0-9_]+)' +
                # Value optional, consists of anything after a space to end of line
                '( [^\n\r]*|)' +
                # End of line defined by \n or \r
                '([\r\n]{1,2})'
        )
        if regex.match(ged_line_regex, line):
            line_parts = regex.match(ged_line_regex, line).groups()
        else:
            error_message = ("Line %d of document violates GEDCOM format" % line_num +
                             "\nSee: http://homepages.rootsweb.ancestry.com/" +
                             "~pmcbride/gedcom/55gctoc.htm")
            raise SyntaxError(error_message)

        level = int(line_parts[0])
        pointer = line_parts[1].rstrip(' ')
        tag = line_parts[2]
        value = line_parts[3][1:]
        crlf = line_parts[4]

        # Check level: should never be more than one higher than previous line.
        if level > last_element.get_level() + 1:
            error_message = ("Line %d of document violates GEDCOM format" % line_num +
                             "\nLines must be no more than one level higher than " +
                             "previous line.\nSee: http://homepages.rootsweb." +
                             "ancestry.com/~pmcbride/gedcom/55gctoc.htm")
            raise SyntaxError(error_message)

        # Create element. Store in list and dict, create children and parents.
        element = Element(level, pointer, tag, value, crlf, multi_line=False)

        # Start with last element as parent, back up if necessary.
        parent_element = last_element

        while parent_element.get_level() > level - 1:
            parent_element = parent_element.parent_element()

        # Add child to parent & parent to child.
        parent_element.add_child_element(element)

        return element

    def __build_list(self, element, element_list):
        """Recursively add Elements to a list containing elements"""
        element_list.append(element)
        for child in element.get_child_elements():
            self.__build_list(child, element_list)

    # Methods for analyzing individuals and relationships between individuals

    def marriages(self, individual):
        """Return list of marriage tuples (date, place) for an individual"""
        marriages = []
        if not individual.is_individual():
            raise ValueError("Operation only valid for elements with INDI tag")
        # Get and analyze families where individual is spouse.
        families = self.families(individual, "FAMS")
        for family in families:
            for family_data in family.get_child_elements():
                if family_data.get_tag() == "MARR":
                    for marriage_data in family_data.get_child_elements():
                        date = ''
                        place = ''
                        if marriage_data.get_tag() == "DATE":
                            date = marriage_data.get_value()
                        if marriage_data.get_tag() == "PLAC":
                            place = marriage_data.get_value()
                        marriages.append((date, place))
        return marriages

    def marriage_years(self, individual):
        """Return list of marriage years (as int) for an individual"""
        dates = []
        if not individual.is_individual():
            raise ValueError("Operation only valid for elements with INDI tag")
        # Get and analyze families where individual is spouse.
        families = self.families(individual, "FAMS")
        for family in families:
            for child in family.get_child_elements():
                if child.get_tag() == "MARR":
                    for childOfChild in child.get_child_elements():
                        if childOfChild.get_tag() == "DATE":
                            date = childOfChild.get_value().split()[-1]
                            try:
                                dates.append(int(date))
                            except ValueError:
                                pass
        return dates

    def marriage_year_match(self, individual, year):
        """Check if one of the marriage years of an individual matches the supplied year. Year is an integer."""
        years = self.marriage_years(individual)
        return year in years

    def marriage_range_match(self, individual, year1, year2):
        """Check if one of the marriage year of an individual is in a given range. Years are integers."""
        years = self.marriage_years(individual)
        for year in years:
            if year1 <= year <= year2:
                return True
        return False

    def families(self, individual, family_type="FAMS"):
        """Return family elements listed for an individual

        family_type can be FAMS (families where the individual is a spouse) or
        FAMC (families where the individual is a child). If a value is not
        provided, FAMS is default value.
        """
        if not individual.is_individual():
            raise ValueError("Operation only valid for elements with INDI tag.")
        families = []
        element_dict = self.element_dict()
        for child in individual.get_child_elements():
            is_family = (child.get_tag() == family_type and
                         child.get_value() in element_dict and
                         element_dict[child.get_value()].is_family())
            if is_family:
                families.append(element_dict[child.get_value()])
        return families

    def get_ancestors(self, individual, anc_type="ALL"):
        """Return elements corresponding to ancestors of an individual

        Optional anc_type. Default "ALL" returns all ancestors, "NAT" can be
        used to specify only natural (genetic) ancestors.
        """
        if not individual.is_individual():
            raise ValueError("Operation only valid for elements with INDI tag.")
        parents = self.get_parents(individual, anc_type)
        ancestors = parents
        for parent in parents:
            ancestors = ancestors + self.get_ancestors(parent)
        return ancestors

    def get_parents(self, individual, parent_type="ALL"):
        """Return elements corresponding to parents of an individual

        Optional parent_type. Default "ALL" returns all parents. "NAT" can be
        used to specify only natural (genetic) parents.
        """
        if not individual.is_individual():
            raise ValueError("Operation only valid for elements with INDI tag.")
        parents = []
        families = self.families(individual, "FAMC")
        for family in families:
            if parent_type == "NAT":
                for family_member in family.get_child_elements():
                    if family_member.get_tag() == "CHIL" and family_member.get_value() == individual.get_pointer():
                        for child in family_member.get_child_elements():
                            if child.get_value() == "Natural":
                                if child.get_tag() == "_MREL":
                                    parents = (parents +
                                               self.get_family_members(family, "WIFE"))
                                elif child.get_tag() == "_FREL":
                                    parents = (parents +
                                               self.get_family_members(family, "HUSB"))
            else:
                parents = parents + self.get_family_members(family, "PARENTS")
        return parents

    def find_path_to_ancestor(self, desc, anc, path=None):
        """Return path from descendant to ancestor"""
        if not desc.is_individual() and anc.is_individual():
            raise ValueError("Operation only valid for elements with IND tag.")
        if not path:
            path = [desc]
        if path[-1].get_pointer() == anc.get_pointer():
            return path
        else:
            parents = self.get_parents(desc, "NAT")
            for parent in parents:
                potential_path = self.find_path_to_ancestor(parent, anc, path + [parent])
                if potential_path:
                    return potential_path
        return None

    def get_family_members(self, family, mem_type="ALL"):
        """Return array of family members: individual, spouse, and children

        Optional argument `mem_type` can be used to return specific subsets.
        "ALL": Default, return all members of the family
        "PARENTS": Return individuals with "HUSB" and "WIFE" tags (parents)
        "HUSB": Return individuals with "HUSB" tags (father)
        "WIFE": Return individuals with "WIFE" tags (mother)
        "CHIL": Return individuals with "CHIL" tags (children)
        """
        if not family.is_family():
            raise ValueError("Operation only valid for elements with FAM tag.")
        family_members = []
        element_dict = self.element_dict()
        for child_element in family.get_child_elements():
            # Default is ALL
            is_family = (child_element.get_tag() == "HUSB" or
                         child_element.get_tag() == "WIFE" or
                         child_element.get_tag() == "CHIL")
            if mem_type == "PARENTS":
                is_family = (child_element.get_tag() == "HUSB" or
                             child_element.get_tag() == "WIFE")
            elif mem_type == "HUSB":
                is_family = (child_element.get_tag() == "HUSB")
            elif mem_type == "WIFE":
                is_family = (child_element.get_tag() == "WIFE")
            elif mem_type == "CHIL":
                is_family = (child_element.get_tag() == "CHIL")
            if is_family and child_element.get_value() in element_dict:
                family_members.append(element_dict[child_element.get_value()])
        return family_members

    # Other methods

    def print_gedcom(self):
        """Write GEDCOM data to stdout"""
        from sys import stdout
        self.save_gedcom(stdout)

    def save_gedcom(self, open_file):
        """Save GEDCOM data to a file"""
        if version_info[0] >= 3:
            open_file.write(self.root().get_individual())
        else:
            open_file.write(self.root().get_individual().encode('utf-8'))


class GedcomParseError(Exception):
    """Exception raised when a GEDCOM parsing error occurs"""

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


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

        You must include a level, pointer, tag, and value.
        Normally initialized by the GEDCOM parser, not by a user.
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
        """Return the level of this element"""
        return self.__level

    def get_pointer(self):
        """Return the pointer of this element"""
        return self.__pointer

    def get_tag(self):
        """Return the tag of this element"""
        return self.__tag

    def get_value(self):
        """Return the value of this element"""
        return self.__value

    def set_value(self, value):
        """Set the value of this element"""
        self.__value = value

    def get_multi_line_value(self):
        """Return the value of this element including continuations"""
        result = self.get_value()
        last_crlf = self.__crlf
        for e in self.get_child_elements():
            tag = e.get_tag()
            if tag == 'CONC':
                result += e.get_value()
                last_crlf = e.__crlf
            elif tag == 'CONT':
                result += last_crlf + e.get_value()
                last_crlf = e.__crlf
        return result

    def __available_characters(self):
        """Get the number of available characters of the elements original string"""
        element_characters = len(self.__unicode__())
        return 0 if element_characters > 255 else 255 - element_characters

    def __line_length(self, line):
        total_characters = len(line)
        available_characters = self.__available_characters()
        if total_characters <= available_characters:
            return total_characters
        spaces = 0
        while spaces < available_characters and line[available_characters - spaces - 1] == ' ':
            spaces = spaces + 1
        if spaces == available_characters:
            return available_characters
        return available_characters - spaces

    def __set_bounded_value(self, value):
        line_length = self.__line_length(value)
        self.set_value(value[:line_length])
        return line_length

    def __add_bounded_child(self, tag, value):
        child = self.new_child_element(tag)
        return child.__set_bounded_value(value)

    def __add_concatenation(self, string):
        index = 0
        size = len(string)
        while index < size:
            index = index + self.__add_bounded_child('CONC', string[index:])

    def set_multi_line_value(self, value):
        """Set the value of this element, adding continuation lines as necessary"""
        self.set_value('')
        self.get_child_elements()[:] = [child for child in self.get_child_elements() if
                                        child.get_tag() not in ('CONC', 'CONT')]

        lines = value.splitlines()
        if lines:
            line = lines.pop(0)
            n = self.__set_bounded_value(line)
            self.__add_concatenation(line[n:])

            for line in lines:
                n = self.__add_bounded_child('CONT', line)
                self.__add_concatenation(line[n:])

    def get_child_elements(self):
        """Return the child elements of this element"""
        return self.__children

    def get_parent_element(self):
        """Return the parent element of this element"""
        return self.__parent

    def new_child_element(self, tag, pointer='', value=''):
        """Create and return a new child element of this element"""
        child_element = Element(self.get_level() + 1, pointer, tag, value, self.__crlf)
        self.add_child_element(child_element)
        return child_element

    def add_child_element(self, element):
        """Add a child element to this element"""
        self.get_child_elements().append(element)
        element.set_parent_element(self)

    def set_parent_element(self, element):
        """Add a parent element to this element

        There's usually no need to call this method manually,
        add_child_element() calls it automatically.
        """
        self.__parent = element

    def is_individual(self):
        """Check if this element is an individual"""
        return self.get_tag() == "INDI"

    def is_family(self):
        """Check if this element is a family"""
        return self.get_tag() == "FAM"

    def is_file(self):
        """Check if this element is a file"""
        return self.get_tag() == "FILE"

    def is_object(self):
        """Check if this element is an object"""
        return self.get_tag() == "OBJE"

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
        birthrange=[year1-year2]
             Match a person whose birth year is in the range of years from
             [year1] to [year2], including both [year1] and [year2].
        death=[year]
        deathrange=[year1-year2]
        """

        # error checking on the criteria
        try:
            for criterion in criteria.split(':'):
                key, value = criterion.split('=')
        except:
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
                except:
                    match = False
            elif key == "birthrange":
                try:
                    from_year, to_year = value.split('-')
                    from_year = int(from_year)
                    to_year = int(to_year)
                    if not self.birth_range_match(from_year, to_year):
                        match = False
                except:
                    match = False
            elif key == "death":
                try:
                    year = int(value)
                    if not self.death_year_match(year):
                        match = False
                except:
                    match = False
            elif key == "deathrange":
                try:
                    from_year, to_year = value.split('-')
                    from_year = int(from_year)
                    to_year = int(to_year)
                    if not self.death_range_match(from_year, to_year):
                        match = False
                except:
                    match = False

        return match

    def surname_match(self, name):
        """Match a string with the surname of an individual"""
        (first, last) = self.get_name()
        return last.find(name) >= 0

    def given_match(self, name):
        """Match a string with the given names of an individual"""
        (first, last) = self.get_name()
        return first.find(name) >= 0

    def birth_year_match(self, year):
        """Match the birth year of an individual. Year is an integer"""
        return self.get_birth_year() == year

    def birth_range_match(self, from_year, to_year):
        """Check if the birth year of an individual is in a given range. Years are integers"""
        birth_year = self.get_birth_year()
        if from_year <= birth_year <= to_year:
            return True
        return False

    def death_year_match(self, year):
        """Match the death year of an individual. Year is an integer"""
        return self.get_death_year() == year

    def death_range_match(self, from_year, to_year):
        """Check if the death year of an individual is in a given range. Years are integers"""
        death_year = self.get_death_year()
        if from_year <= death_year <= to_year:
            return True
        return False

    def get_name(self):
        """Return a person's names as a tuple: (first, last)"""
        first = ""
        last = ""
        if not self.is_individual():
            return first, last
        for child in self.get_child_elements():
            if child.get_tag() == "NAME":
                # some older GEDCOM files don't use child tags but instead
                # place the name in the value of the NAME tag
                if child.get_value() != "":
                    name = child.get_value().split('/')
                    if len(name) > 0:
                        first = name[0].strip()
                        if len(name) > 1:
                            last = name[1].strip()
                else:
                    for childOfChild in child.get_child_elements():
                        if childOfChild.get_tag() == "GIVN":
                            first = childOfChild.get_value()
                        if childOfChild.get_tag() == "SURN":
                            last = childOfChild.get_value()
        return first, last

    def get_gender(self):
        """Return the gender of a person in string format"""
        gender = ""
        if not self.is_individual():
            return gender
        for child in self.get_child_elements():
            if child.get_tag() == "SEX":
                gender = child.get_value()
        return gender

    def is_private(self):
        """Return if the person is marked private in boolean format"""
        private = False
        if not self.is_individual():
            return private
        for child in self.get_child_elements():
            if child.get_tag() == "PRIV":
                private = child.get_value()
                if private == 'Y':
                    private = True
        return private

    def get_birth_data(self):
        """Return the birth tuple of a person as (date, place, source)"""
        date = ""
        place = ""
        source = ()
        if not self.is_individual():
            return date, place, source
        for child in self.get_child_elements():
            if child.get_tag() == "BIRT":
                for childOfChild in child.get_child_elements():
                    if childOfChild.get_tag() == "DATE":
                        date = childOfChild.get_value()
                    if childOfChild.get_tag() == "PLAC":
                        place = childOfChild.get_value()
                    if childOfChild.get_tag() == "SOUR":
                        source = source + (childOfChild.get_value(),)
        return date, place, source

    def get_birth_year(self):
        """Return the birth year of a person in integer format"""
        date = ""
        if not self.is_individual():
            return date
        for child in self.get_child_elements():
            if child.get_tag() == "BIRT":
                for childOfChild in child.get_child_elements():
                    if childOfChild.get_tag() == "DATE":
                        date_split = childOfChild.get_value().split()
                        date = date_split[len(date_split) - 1]
        if date == "":
            return -1
        try:
            return int(date)
        except:
            return -1

    def get_death_data(self):
        """Return the death tuple of a person as (date, place, source)"""
        date = ""
        place = ""
        source = ()
        if not self.is_individual():
            return date, place
        for child in self.get_child_elements():
            if child.get_tag() == "DEAT":
                for childOfChild in child.get_child_elements():
                    if childOfChild.get_tag() == "DATE":
                        date = childOfChild.get_value()
                    if childOfChild.get_tag() == "PLAC":
                        place = childOfChild.get_value()
                    if childOfChild.get_tag() == "SOUR":
                        source = source + (childOfChild.get_value(),)
        return date, place, source

    def get_death_year(self):
        """Return the death year of a person in integer format"""
        date = ""
        if not self.is_individual():
            return date
        for child in self.get_child_elements():
            if child.get_tag() == "DEAT":
                for childOfChild in child.get_child_elements():
                    if childOfChild.get_tag() == "DATE":
                        date_split = childOfChild.get_value().split()
                        date = date_split[len(date_split) - 1]
        if date == "":
            return -1
        try:
            return int(date)
        except:
            return -1

    def get_burial(self):
        """Return the burial tuple of a person as (date, place, source)"""
        date = ""
        place = ""
        source = ()
        if not self.is_individual():
            return date, place
        for child in self.get_child_elements():
            if child.get_tag() == "BURI":
                for childOfChild in child.get_child_elements():
                    if childOfChild.get_tag() == "DATE":
                        date = childOfChild.get_value()
                    if childOfChild.get_tag() == "PLAC":
                        place = childOfChild.get_value()
                    if childOfChild.get_tag() == "SOUR":
                        source = source + (childOfChild.get_value(),)
        return date, place, source

    def get_census(self):
        """Return list of census tuples (date, place) for an individual"""
        census = []
        if not self.is_individual():
            raise ValueError("Operation only valid for elements with INDI tag")
        for child in self.get_child_elements():
            if child.get_tag() == "CENS":
                date = ''
                place = ''
                source = ''
                for childOfChild in child.get_child_elements():
                    if childOfChild.get_tag() == "DATE":
                        date = childOfChild.get_value()
                    if childOfChild.get_tag() == "PLAC":
                        place = childOfChild.get_value()
                    if childOfChild.get_tag() == "SOUR":
                        source = source + (childOfChild.get_value(),)
                census.append((date, place, source))
        return census

    def get_last_change_date(self):
        """Return the last updated date of a person as (date)"""
        date = ""
        if not self.is_individual():
            return date
        for child in self.get_child_elements():
            if child.get_tag() == "CHAN":
                for childOfChild in child.get_child_elements():
                    if childOfChild.get_tag() == "DATE":
                        date = childOfChild.get_value()
        return date

    def get_occupation(self):
        """Return the occupation of a person as (date)"""
        occupation = ""
        if not self.is_individual():
            return occupation
        for child in self.get_child_elements():
            if child.get_tag() == "OCCU":
                occupation = child.get_value()
        return occupation

    def is_deceased(self):
        """Check if a person is deceased"""
        if not self.is_individual():
            return False
        for child in self.get_child_elements():
            if child.get_tag() == "DEAT":
                return True
        return False

    def get_individual(self):
        """Return this element and all of its sub-elements"""
        result = self.__unicode__()
        for child_element in self.get_child_elements():
            result += child_element.get_individual()
        return result

    def __str__(self):
        if version_info[0] >= 3:
            return self.__unicode__()
        else:
            return self.__unicode__().encode('utf-8')

    def __unicode__(self):
        """Format this element as its original string"""
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
