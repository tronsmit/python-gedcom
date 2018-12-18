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
from gedcom.element import Element
import gedcom.tags


class Gedcom:
    """Parses and manipulates GEDCOM 5.5 format data

    For documentation of the GEDCOM 5.5 format, see:
    http://homepages.rootsweb.ancestry.com/~pmcbride/gedcom/55gctoc.htm

    This parser reads and parses a GEDCOM file.
    Elements may be accessed via:
      - a list (all elements, default order is same as in file)
      - a dict (only elements with pointers, which are the keys)
    """

    def __init__(self, file_path, use_strict=True):
        """Initialize a GEDCOM data object. You must supply a GEDCOM file
        :type file_path: str
        """
        self.__element_list = []
        self.__element_dictionary = {}
        self.invalidate_cache()
        self.__root_element = Element(-1, "", "ROOT", "")
        self.__parse(file_path, use_strict)
        self.__use_strict = use_strict

    def invalidate_cache(self):
        """Cause get_element_list() and get_element_dictionary() to return updated data

        The update gets deferred until each of the methods actually gets called.
        """
        self.__element_list = []
        self.__element_dictionary = {}

    def get_element_list(self):
        """Return a list of all the elements in the GEDCOM file

        By default elements are in the same order as they appeared in the file.

        This list gets generated on-the-fly, but gets cached. If the database
        was modified, you should call invalidate_cache() once to let this
        method return updated data.

        Consider using `get_root_element()` or `get_root_child_elements()` to access
        the hierarchical GEDCOM tree, unless you rarely modify the database.

        :rtype: list of Element
        """
        if not self.__element_list:
            for element in self.get_root_child_elements():
                self.__build_list(element, self.__element_list)
        return self.__element_list

    def get_element_dictionary(self):
        """Return a dictionary of elements from the GEDCOM file

        Only elements identified by a pointer are listed in the dictionary.
        The keys for the dictionary are the pointers.

        This dictionary gets generated on-the-fly, but gets cached. If the
        database was modified, you should call invalidate_cache() once to let
        this method return updated data.

        :rtype: dict of Element
        """
        if not self.__element_dictionary:
            self.__element_dictionary = {
                element.get_pointer(): element for element in self.get_root_child_elements() if element.get_pointer()
            }

        return self.__element_dictionary

    def get_root_element(self):
        """Returns a virtual root element containing all logical records as children

        When printed, this element converts to an empty string.

        :rtype: Element
        """
        return self.__root_element

    def get_root_child_elements(self):
        """Return a list of logical records in the GEDCOM file

        By default, elements are in the same order as they appeared in the file.

        :rtype: list of Element
        """
        return self.get_root_element().get_child_elements()

    # Private methods

    def __parse(self, file_path, use_strict=True):
        """Open and parse file path as GEDCOM 5.5 formatted data
        :type file_path: str
        """
        gedcom_file = open(file_path, 'rb')
        line_number = 1
        last_element = self.__root_element
        for line in gedcom_file:
            last_element = self.__parse_line(line_number, line.decode('utf-8-sig'), last_element, use_strict)
            line_number += 1

    @staticmethod
    def __parse_line(line_number, line, last_element, use_strict=True):
        """Parse a line from a GEDCOM 5.5 formatted document

        Each line should have the following (bracketed items optional):
        level + ' ' + [pointer + ' ' +] tag + [' ' + line_value]

        :type line_number: int
        :type line: str
        :type last_element: Element
        :rtype: Element
        """

        # Level must start with non-negative int, no leading zeros.
        level_regex = '^(0|[1-9]+[0-9]*) '

        # Pointer optional, if it exists it must be flanked by `@`
        pointer_regex = '(@[^@]+@ |)'

        # Tag must be alphanumeric string
        tag_regex = '([A-Za-z0-9_]+)'

        # Value optional, consists of anything after a space to end of line
        value_regex = '( [^\n\r]*|)'

        # End of line defined by `\n` or `\r`
        end_of_line_regex = '([\r\n]{1,2})'

        # Complete regex
        gedcom_line_regex = level_regex + pointer_regex + tag_regex + value_regex + end_of_line_regex
        regex_match = regex.match(gedcom_line_regex, line)

        if regex_match is None:
            if use_strict:
                error_message = ("Line %d of document violates GEDCOM format 5.5" % line_number
                                 + "\nSee: https://chronoplexsoftware.com/gedcomvalidator/gedcom/gedcom-5.5.pdf")
                raise SyntaxError(error_message)
            else:
                # Quirk check - see if this is a line without a CRLF (which could be the last line)
                last_line_regex = level_regex + pointer_regex + tag_regex + value_regex
                regex_match = regex.match(last_line_regex, line)
                if regex_match is not None:
                    line_parts = regex_match.groups()

                    level = int(line_parts[0])
                    pointer = line_parts[1].rstrip(' ')
                    tag = line_parts[2]
                    value = line_parts[3][1:]
                    crlf = '\n'
                else:
                    # Quirk check - Sometimes a gedcom has a text field with a CR.
                    # This creates a line without the standard level and pointer.
                    # If this is detected then turn it into a CONC or CONT.
                    line_regex = '([^\n\r]*|)'
                    cont_line_regex = line_regex + end_of_line_regex
                    regex_match = regex.match(cont_line_regex, line)
                    line_parts = regex_match.groups()
                    level = last_element.get_level()
                    tag = last_element.get_tag()
                    pointer = None
                    value = line_parts[0][1:]
                    crlf = line_parts[1]
                    if tag != gedcom.tags.GEDCOM_TAG_CONTINUED and tag != gedcom.tags.GEDCOM_TAG_CONCATENATION:
                        # Increment level and change this line to a CONC
                        level += 1
                        tag = gedcom.tags.GEDCOM_TAG_CONCATENATION
        else:
            line_parts = regex_match.groups()

            level = int(line_parts[0])
            pointer = line_parts[1].rstrip(' ')
            tag = line_parts[2]
            value = line_parts[3][1:]
            crlf = line_parts[4]

        # Check level: should never be more than one higher than previous line.
        if level > last_element.get_level() + 1:
            error_message = ("Line %d of document violates GEDCOM format 5.5" % line_number
                             + "\nLines must be no more than one level higher than previous line."
                             + "\nSee: https://chronoplexsoftware.com/gedcomvalidator/gedcom/gedcom-5.5.pdf")
            raise SyntaxError(error_message)

        # Create element. Store in list and dict, create children and parents.
        element = Element(level, pointer, tag, value, crlf, multi_line=False)

        # Start with last element as parent, back up if necessary.
        parent_element = last_element

        while parent_element.get_level() > level - 1:
            parent_element = parent_element.get_parent_element()

        # Add child to parent & parent to child.
        parent_element.add_child_element(element)

        return element

    def __build_list(self, element, element_list):
        """Recursively add elements to a list containing elements
        :type element: Element
        :type element_list: list of Element
        """
        element_list.append(element)
        for child in element.get_child_elements():
            self.__build_list(child, element_list)

    # Methods for analyzing individuals and relationships between individuals

    def get_marriages(self, individual):
        """Return list of marriage tuples (date, place) for an individual
        :type individual: Element
        :rtype: tuple
        """
        marriages = []
        if not individual.is_individual():
            raise ValueError("Operation only valid for elements with %s tag" % gedcom.tags.GEDCOM_TAG_INDIVIDUAL)
        # Get and analyze families where individual is spouse.
        families = self.get_families(individual, gedcom.tags.GEDCOM_TAG_FAMILY_SPOUSE)
        for family in families:
            for family_data in family.get_child_elements():
                if family_data.get_tag() == gedcom.tags.GEDCOM_TAG_MARRIAGE:
                    date = ''
                    place = ''
                    for marriage_data in family_data.get_child_elements():
                        if marriage_data.get_tag() == gedcom.tags.GEDCOM_TAG_DATE:
                            date = marriage_data.get_value()
                        if marriage_data.get_tag() == gedcom.tags.GEDCOM_TAG_PLACE:
                            place = marriage_data.get_value()
                    marriages.append((date, place))
        return marriages

    def get_marriage_years(self, individual):
        """Return list of marriage years (as int) for an individual
        :type individual: Element
        :rtype: list of int
        """
        dates = []
        if not individual.is_individual():
            raise ValueError("Operation only valid for elements with %s tag" % gedcom.tags.GEDCOM_TAG_INDIVIDUAL)
        # Get and analyze families where individual is spouse.
        families = self.get_families(individual, gedcom.tags.GEDCOM_TAG_FAMILY_SPOUSE)
        for family in families:
            for child in family.get_child_elements():
                if child.get_tag() == gedcom.tags.GEDCOM_TAG_MARRIAGE:
                    for childOfChild in child.get_child_elements():
                        if childOfChild.get_tag() == gedcom.tags.GEDCOM_TAG_DATE:
                            date = childOfChild.get_value().split()[-1]
                            try:
                                dates.append(int(date))
                            except ValueError:
                                pass
        return dates

    def marriage_year_match(self, individual, year):
        """Check if one of the marriage years of an individual matches the supplied year. Year is an integer.
        :type individual: Element
        :type year: int
        :rtype: bool
        """
        years = self.get_marriage_years(individual)
        return year in years

    def marriage_range_match(self, individual, from_year, to_year):
        """Check if one of the marriage years of an individual is in a given range. Years are integers.
        :type individual: Element
        :type from_year: int
        :type to_year: int
        :rtype: bool
        """
        years = self.get_marriage_years(individual)
        for year in years:
            if from_year <= year <= to_year:
                return True
        return False

    def get_families(self, individual, family_type=gedcom.tags.GEDCOM_TAG_FAMILY_SPOUSE):
        """Return family elements listed for an individual

        family_type can be `gedcom.tags.GEDCOM_TAG_FAMILY_SPOUSE` (families where the individual is a spouse) or
        `gedcom.tags.GEDCOM_TAG_FAMILY_CHILD` (families where the individual is a child). If a value is not
        provided, `gedcom.tags.GEDCOM_TAG_FAMILY_SPOUSE` is default value.

        :type individual: Element
        :type family_type: str
        :rtype: list of Element
        """
        if not individual.is_individual():
            raise ValueError("Operation only valid for elements with %s tag." % gedcom.tags.GEDCOM_TAG_INDIVIDUAL)
        families = []
        element_dictionary = self.get_element_dictionary()
        for child_element in individual.get_child_elements():
            is_family = (child_element.get_tag() == family_type
                         and child_element.get_value() in element_dictionary
                         and element_dictionary[child_element.get_value()].is_family())
            if is_family:
                families.append(element_dictionary[child_element.get_value()])
        return families

    def get_ancestors(self, individual, ancestor_type="ALL"):
        """Return elements corresponding to ancestors of an individual

        Optional `ancestor_type`. Default "ALL" returns all ancestors, "NAT" can be
        used to specify only natural (genetic) ancestors.

        :type individual: Element
        :type ancestor_type: str
        :rtype: list of Element
        """
        if not individual.is_individual():
            raise ValueError("Operation only valid for elements with %s tag." % gedcom.tags.GEDCOM_TAG_INDIVIDUAL)
        parents = self.get_parents(individual, ancestor_type)
        ancestors = []
        ancestors.extend(parents)
        for parent in parents:
            ancestors.extend(self.get_ancestors(parent))
        return ancestors

    def get_parents(self, individual, parent_type="ALL"):
        """Return elements corresponding to parents of an individual

        Optional parent_type. Default "ALL" returns all parents. "NAT" can be
        used to specify only natural (genetic) parents.

        :type individual: Element
        :type parent_type: str
        :rtype: list of Element
        """
        if not individual.is_individual():
            raise ValueError("Operation only valid for elements with %s tag." % gedcom.tags.GEDCOM_TAG_INDIVIDUAL)
        parents = []
        families = self.get_families(individual, gedcom.tags.GEDCOM_TAG_FAMILY_CHILD)
        for family in families:
            if parent_type == "NAT":
                for family_member in family.get_child_elements():
                    if family_member.get_tag() == gedcom.tags.GEDCOM_TAG_CHILD and family_member.get_value() == individual.get_pointer():
                        for child in family_member.get_child_elements():
                            if child.get_value() == "Natural":
                                if child.get_tag() == gedcom.tags.GEDCOM_PROGRAM_DEFINED_TAG_MREL:
                                    parents += self.get_family_members(family, gedcom.tags.GEDCOM_TAG_WIFE)
                                elif child.get_tag() == gedcom.tags.GEDCOM_PROGRAM_DEFINED_TAG_FREL:
                                    parents += self.get_family_members(family, gedcom.tags.GEDCOM_TAG_HUSBAND)
            else:
                parents += self.get_family_members(family, "PARENTS")
        return parents

    def find_path_to_ancestor(self, descendant, ancestor, path=None):
        """Return path from descendant to ancestor
        :rtype: object
        """
        if not descendant.is_individual() and ancestor.is_individual():
            raise ValueError("Operation only valid for elements with %s tag." % gedcom.tags.GEDCOM_TAG_INDIVIDUAL)
        if not path:
            path = [descendant]
        if path[-1].get_pointer() == ancestor.get_pointer():
            return path
        else:
            parents = self.get_parents(descendant, "NAT")
            for parent in parents:
                potential_path = self.find_path_to_ancestor(parent, ancestor, path + [parent])
                if potential_path is not None:
                    return potential_path
        return None

    def get_family_members(self, family, members_type="ALL"):
        """Return array of family members: individual, spouse, and children

        Optional argument `members_type` can be used to return specific subsets.
        "ALL": Default, return all members of the family
        "PARENTS": Return individuals with "HUSB" and "WIFE" tags (parents)
        "HUSB": Return individuals with "HUSB" tags (father)
        "WIFE": Return individuals with "WIFE" tags (mother)
        "CHIL": Return individuals with "CHIL" tags (children)

        :type family: Element
        :type members_type: str
        :rtype: list of Element
        """
        if not family.is_family():
            raise ValueError("Operation only valid for element with %s tag." % gedcom.tags.GEDCOM_TAG_FAMILY)
        family_members = []
        element_dictionary = self.get_element_dictionary()
        for child_element in family.get_child_elements():
            # Default is ALL
            is_family = (child_element.get_tag() == gedcom.tags.GEDCOM_TAG_HUSBAND
                         or child_element.get_tag() == gedcom.tags.GEDCOM_TAG_WIFE
                         or child_element.get_tag() == gedcom.tags.GEDCOM_TAG_CHILD)
            if members_type == "PARENTS":
                is_family = (child_element.get_tag() == gedcom.tags.GEDCOM_TAG_HUSBAND
                             or child_element.get_tag() == gedcom.tags.GEDCOM_TAG_WIFE)
            elif members_type == "HUSB":
                is_family = child_element.get_tag() == gedcom.tags.GEDCOM_TAG_HUSBAND
            elif members_type == "WIFE":
                is_family = child_element.get_tag() == gedcom.tags.GEDCOM_TAG_WIFE
            elif members_type == "CHIL":
                is_family = child_element.get_tag() == gedcom.tags.GEDCOM_TAG_CHILD
            if is_family and child_element.get_value() in element_dictionary:
                family_members.append(element_dictionary[child_element.get_value()])
        return family_members

    # Other methods

    def print_gedcom(self):
        """Write GEDCOM data to stdout"""
        from sys import stdout
        self.save_gedcom(stdout)

    def save_gedcom(self, open_file):
        """Save GEDCOM data to a file
        :type open_file: file
        """
        if version_info[0] >= 3:
            open_file.write(self.get_root_element().get_individual())
        else:
            open_file.write(self.get_root_element().get_individual().encode('utf-8'))
