# Python GEDCOM Parser

[![PyPI](https://img.shields.io/pypi/v/python-gedcom.svg)](https://pypi.org/project/python-gedcom/)
[![GitHub release](https://img.shields.io/github/release/nickreynke/python-gedcom.svg)](https://github.com/nickreynke/python-gedcom/releases)
![](https://img.shields.io/badge/GEDCOM%20format%20version-5.5-yellowgreen.svg)
![](https://img.shields.io/badge/Python%20version-2%20and%203-yellowgreen.svg)

A Python module for parsing, analyzing, and manipulating GEDCOM files.

GEDCOM files contain ancestry data. The parser is currently supporting
the GEDCOM 5.5 format which is detailed [here](https://chronoplexsoftware.com/gedcomvalidator/gedcom/gedcom-5.5.pdf).

> **NOTE**: This module is currently under development and **should not be used in production**!
> The current development process can be tracked in the ["develop" branch](https://github.com/reynke/python-gedcom/tree/develop).

## Installation

> **NOTE**: As of the 26 march of 2018 the beta of the new Python Package
> Index launched. I recommend reading this: "[All New PyPI is now in beta](https://pyfound.blogspot.de/2018/03/warehouse-all-new-pypi-is-now-in-beta.html)"

The module can be installed via [pip](https://pip.pypa.io/).

Run `pip install python-gedcom` to install or `pip install python-gedcom --upgrade`
to upgrade to the newest version uploaded to the [PyPI repository](https://pypi.org/project/python-gedcom/).

## Usage

When successfully installed you may import the `gedcom` module and use
it like so:

```python
from gedcom import Gedcom

file_path = '' # Path to your `.ged` file
gedcom = Gedcom(file_path)
```

### GEDCOM Quirks

Large sites like Ancesty and MyHeritage (among others) don't always produce perfectly formatted GEDCOM files.  If you encounter errors in parsing, you might consider disabling strict parsing which will make a best effort to parse the file:


```python
from gedcom import Gedcom

file_path = '' # Path to your `.ged` file
gedcom = Gedcom(file_path, False) # Disable strict parsing
```

Disabling strict parsing will allow the parser to gracefully handle the following quirks:

- Multi-line fields that don't use CONC or CONT
- Handle the last line not ending in a CRLF

### Iterate through all records, search last names and print matches

```python
all_records = gedcom.get_root_child_elements()
for record in all_records:
    if record.is_individual():
        if record.surname_match('Brodie'):
            (first, last) = record.get_name()
            print(first + " " + last)
```

## Reference

The Element class contains all the information for a single record in the GEDCOM file, for example and individual.

### Single Record Methods

Method                 | Parameters | Returns | Description
-----------------------|------------|---------|------------
get_child_elements     | none          | List of Element | Returns all the child elements of this record
get_parent_element     | none          | Element | Returns parent Element
new_child_element      | String tag, String pointer, String value | Element | Create a new Element
add_child_element      | Element child | Element | Adds the child record
set_parent_element     | Element parent| none | Not normally required to be called (add_child_element calls this automatically
is_individual          | none          | Boolean | Is this record of a person
is_family              | none          | Boolean | 
is_file                | none          | Boolean |
is_object              | none          | Boolean |
is_private             | none          | Boolean | Returns True if the record is marked Private
is_deceased            | none          | Boolean | Returns True if the individual is marked deceased
criteria_match         | colon separated string "surname=[name]:name=[name]:birth][year]:birth_range=[year-to-year]:death=[year]:death_range[year-to-year]"| Boolean | Returns True if the criteria matches
surname_match          | String | Boolean | Returns True if substring matches
given_match            | String | Boolean | Returns True if substring matches
death_range_match      | Int from, Int to | Boolean | Returns True if Death Year is in the supplied range
death_year_match       | Int | Boolean | Returns True if Death Year equals parameter
birth_range_match      | Int from, Int to | Boolean | Returns True if Birth Year is in the supplied range
birth_year_match       | Int | Boolean | Returns True if Birth Year equals parameter
get_name               | none | (String given, String surname) | Returns the Given name(s) and Surname in a tuple
get_gender             | none | String | Returns individual's gender
get_birth_data         | none | (String date, String place, Array sources) | Returns a tuple of the birth data
get_birth_year         | none | Int | Returns the Birth Year
get_death_data         | none | (String date, String place, Array sources) | Returns a tuple of the death data
get_death_year         | none | Int | Returns the Death Year
get_burial         | none | (String date, String place, Array sources) | Returns a tuple of the burial data
get_census         | none | List [String date, String place, Array sources] | Returns a List of tuple of the census data
get_last_change_date   | none | String | Returns the date of the last update to this individual
get_occupation         | none | String | Returns the individual's occupation
get_individual         | none | Individual | Returns the individual

### Gedcom operations

Method                  | Parameters | Returns | Description 
------------------------|------------|---------|------------
get_root_element        | none | Element root | Returns the virtual "root" individual
get_root_child_elements | none | List of Element | Returns a List of all Elements
get_element_dictionary  | none | Dict of Element | Returns a Dict of all Elements
get_element_list        | none | List of Element | Returns a List of all Elements
get_marriages           | Element individual | List of Marriage ("Date", "Place") | Returns List of Tuples of Marriage data (Date and Place)
find_path_to_ancestors  | Element descendant, Element ancestor||
get_family_members      | Element individual, optional String members_type - one of "ALL" (default), "PARENTS", "HUSB", "WIFE", "CHIL" | List of Element individuals||
get_parents             | Element individual, optional String parent_type - one of "ALL" (default) or "NAT" | List of Element individuals|
get_ancestors           | Element individual, optional String ancestor_type - one of "All" (default) or "NAT" ||
get_families            | Element individual optional String family_type - one of "FAMS" (default), "FAMC"||
marriage_range_match    | Element individual, Int from, Int to| Boolean | Check if individual is married within the specified range
marriage_year_match     | Element individual, Int year| Boolean | Check if individual is married in the year specified
get_marriage_years      | Element individual |List of Int| Returns Marriage event years
print_gedcom            | none | none | Prints the gedcom to STDOUT
save_gedcom             | String filename | none | Writes gedcom to specified filename

## History

This module was originally based on a GEDCOM parser written by 
Daniel Zappala at Brigham Young University (Copyright (C) 2005) which
was licensed under the GPL v2 and then continued by
[Mad Price Ball](https://github.com/madprime) in 2012.

Further updates by [Nicklas Reincke](https://github.com/nickreynke) and [Damon Brodie](https://github.com/nomadyow) in 2018.

## Changelog

**v0.2.3dev**
- Assemble Marriages properly ([#9](https://github.com/nickreynke/python-gedcom/issues/9))
- Return the top NAME record instead of the last one ([#9](https://github.com/nickreynke/python-gedcom/issues/9))

**v0.2.2dev**

- Support BOM control characters ([#5](https://github.com/nickreynke/python-gedcom/issues/5))
- Support the last line not having a CR and/or LF
- Support incorrect line splitting generated by Ancestry.  Insert CONT/CONC tag as necessary ([#6](https://github.com/nickreynke/python-gedcom/issues/6))

**v0.2.1dev**

- Changed broken links to GEDCOM format specification ([#2](https://github.com/nickreynke/python-gedcom/issues/2))

**v0.2.0dev**

- Added `develop` branch to track and update current development process
- Applied PEP 8 Style Guide conventions
- **Renamed variables and methods** to make their purpose more clear
- **Outsourced GEDCOM tags to module level**
- **Added missing inline documentation**
- Optimized `README.md` (sections and better description)
- Added `LICENSE` file
- Cleaned up and optimized code

**v0.1.1dev**

- initial release; [forked](https://github.com/madprime/python-gedcom)

## License

Licensed under the [GNU General Public License v2](http://www.gnu.org/licenses/gpl-2.0.html)

**Python GEDCOM Parser**
<br>Copyright (C) 2018 Damon Brodie (damon.brodie at gmail.com)
<br>Copyright (C) 2018 Nicklas Reincke (contact at reynke.com)
<br>Copyright (C) 2016 Andreas Oberritter
<br>Copyright (C) 2012 Madeleine Price Ball
<br>Copyright (C) 2005 Daniel Zappala (zappala at cs.byu.edu)
<br>Copyright (C) 2005 Brigham Young University

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License along
with this program; if not, write to the Free Software Foundation, Inc.,
51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
