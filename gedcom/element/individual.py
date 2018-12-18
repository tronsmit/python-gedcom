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
from gedcom.element.element import Element
import gedcom.tags


class NotAnActualIndividualError(Exception):
    pass


class Individual(Element):

    def is_individual(self):
        """Check if this element is an actual individual
        :rtype: bool
        """
        return self.get_tag() == gedcom.tags.GEDCOM_TAG_INDIVIDUAL

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

    def surname_match(self, name):
        """Match a string with the surname of an individual
        :type name: str
        :rtype: bool
        """
        (given_name, surname) = self.get_name()
        return regex.search(name, surname, regex.IGNORECASE)

    def given_match(self, name):
        """Match a string with the given names of an individual
        :type name: str
        :rtype: bool
        """
        (given_name, surname) = self.get_name()
        return regex.search(name, given_name, regex.IGNORECASE)

    def is_child(self):
        """Check if this element is a child within a family
        :rtype: bool
        """
        if not self.is_individual():
            raise NotAnActualIndividualError(
                "Operation only valid for elements with %s tag" % gedcom.tags.GEDCOM_TAG_INDIVIDUAL
            )

        found_child = False

        for child in self.get_child_elements():
            if child.get_tag() == gedcom.tags.GEDCOM_TAG_FAMILY_CHILD:
                found_child = True

        return found_child

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
            raise NotAnActualIndividualError(
                "Operation only valid for elements with %s tag" % gedcom.tags.GEDCOM_TAG_INDIVIDUAL
            )

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
