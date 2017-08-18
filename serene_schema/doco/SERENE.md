# Serene Schema / Ontology

See [SCHEMA.md](SCHEMA.md) for the details

* Accounts
* Documents
* Entities
* Events
* Location
* Objects

See [countries.md](countries.md) for the country code lookup table

# Schema

The schema determines how the data in the collection is indexed into solr (ie what fields you can search on)
and what the objects/entities, attributes and relationships are represented in the data.

## Base fields

You should include a description 
of the fields available from serene_metadata


## Solr Search Syntax


The query parser is based on Solr v 6.0 which is backed by a Lucene Index.

A query is broken up into *terms* and *operators*


### Terms: single terms and phrases

Terms take two types:

* A _single term_ is a single word such as "test" or "hello"
* A _phrase_ is a group of words surrounded by double quotes such as "hello dolly"

Multiple terms can be combined together with Boolean operators to form more complex queries.

### Term modifiers

Solr supports a variety of term modifiers that add flexibility or precision, as needed, to searches.

These modifiers include wildcard characters, characters for making a search "fuzzy" or more general, and so on.

#### Wildcard searches

SOLR supports wildcard searches within single terms (not phrases).

For example, you would need to do `term:test*` rather than `term:"test* one"`

| Wildcard search type ​| --- | --- |
| --- | --- | --- |
| ​Single character | ​? | ​The search string te?t would match both test and text |
| ​Multiple characters (matches zero or more sequential characters) ​| * | ​tes* would match test,  testing and tester.
| | | te*t would match terrorist and text |
| | | *est would match tempest and test |


#### Fuzzy searches

Solr supports fuzzy searching using a concept called "Edit distance". This means that a fuzzy search will discover terms that are similar to a specified term without necessarily being an exact match.

To perform a fuzzy search add a tilde ~ symbol at the end of a single word term.

For example, a search for roam~ will match roams, foam, foams, etc.

An optional distance parameter specifies the maximum number of edits allowed, between 0 and 2, defaulting to 2.

For example, roam~1 will match terms like roams and foam but not foams since it has an edit distance of "2".

#### Proximity searches

A proximity search looks for terms that are within a specific distance from one another.

To perform a proximity search, add the tilde character ~ and a numeric value to the end of a search phrase.

For example - to search for apache and jakarta within 10 words of each other, you would search for "jakarta apache"~10

The distance referred to here is the number of term movements needed to match the specified phrase.

#### Range searches

A range search specifies a range of values for a field (a range with an upper bound and a lower bound). The query matches documents whose values for the specified field or fields fall within the range.

Range queries can be inclusive or exclusive of the upper and lower bounds. Sorting is done lexicographically, except on numeric fields.

Range queries are not limited to date fields or numeric fields. You could also use a range query with non-date fields:

```PhoneNumber:[0280000000 to 02800008000] - this would find all Phone Numbers in the range```

The brackets around a query determine its inclusiveness.

* Square brackets [] denote an inclusive range query that matches values including the upper and lower bound.
* Curly brackets {} denote an exclusive range query that matches values excluding the upper and lower bound.
( You can mix these so one end of the range is inclusive and the other is exclusive.

Boosting a term with ^

Lucene / Solr provides the relevance level of matching documents based on the terms found. To boost the importance of a term you can use the caret symbol ^.

By default the boost factor is 1. Although the boost factor must be positive, it can be less than 1 (for example it could be 0.2)

#### Specifying fields

Data indexed in Solr is organized in fields. In Serene we index fields corresponding to either a object type (for example, a Person or a Passport) or a attribute of an object (eg Date of birth for Person, Expiry date for passport).

By default, if you don't specify a field Solr will search the default field which includes everything (including raw data where we haven't mapped it to a object).

If you want to narrow your search to either an object or attribute we have mapped you can specify this using fields.

Each time you launch the client it automatically updates the list of available Object types and Transaction types (attribute types are coming the next update) just below the query box.

So to search for all records that contain a Person name "Marty MCFLY" with the phone number 02 8888 8888:

```Person:"Marty MCFLY" AND PhoneNumber:0288888888```

You will note we have added the boolean operator AND - this indicates that the search should only match documents that contain both a person named "Marty MCFLY" with a phone number as specified.

Note that searches are CaSe InSeNsItIvE. That means it doesn't matter what Case you USE it will match on the letters.

#### Full word matches

Also, unless you add a wildcard (see above) your search terms will look for full word matches.

That means Person:Brad will not match Person:Bradley (but will match Person:Brad SMITH). You could search Person:Brad* to find "Bradley SMITH" though.

This applies to all searches (whether you add a field or not). The system is looking for a full word match - if you want a _partial word match_ you need to add wildcard terms.

### Boolean Operators Supported by Solr

| ​Boolean Operator | ​Alternative Symbol | ​Description  |
| --- | --- | --- |
|​ AND | ​```&&``` | ​Requires both terms on either side of the Boolean operator to be present for a match |
​| NOT ​| ```!``` ​| Requires that the following term not be present |
​| OR ​|   | ​Requires that either term (or both terms) be present for a match  |
​|  | ​```+``` | ​Requires that the following term be present  |
|  |​ ```-``` | ​Prohibits the following term (that is, matches on a fields or documents that do not include that term) |
|  |  | The - operator is funcationly similar to the boolean operator !. Because it's used by popular search engines like Google it may be familiar to some user communities |

The **default** operator is OR - so if you do not include AND between search terms then documents will match that contain either terms.

#### Escaping special characters

Solr gives the following characters special meaning when they appear in a query:

``` `+ - && || ! ( ) { } [ ] ^ " ~ * ? : / ```

To make Solr interpret any of these characters literally, rather than as a special character, precede the character with a blackslash character \.

For example to search for (1+1):2 without having Solr interpret the plus sign and parentheses as special characters for formulating a sub-query with two terms, escape the characters by preceding each one with a backslash:

``` \(1\+1\)\:2 ```

#### Grouping terms to form sub-queries

Solr supports using parentheses to group clauses to form sub-queries. This can be very useful if you want to control the Boolean logic for a query.

For example, to search for either "comanche" or "apache" and "website":

``` (comanche OR apache) AND website ```

## Specifying dates and times

Dates and times must be formatted so that Solr recognises them in a consistent manner.

SOLR stores all timestamps and dates in the following format:

``` YYYY-MM-DDThh:mm:ssZ ```

* YYYY is the year.
* MM is the month.
* DD is the day of the month.
* hh is the hour of the day as on a 24-hour clock.
* mm is minutes.
* ss is seconds.
* Z is a literal 'Z' character indicating that this string representation of the date is in UTC

Note that no time zone can be specified; SOLR representations of dates is always expressed in Coordinated
Universal Time (UTC).

### Searching for dates

While SOLR stores all date/time objects as a UTC timestamp, your searches do not need to be in the same format.

You can search for dates using what is called "truncated dates" which represent the entire date span to the precision indicated.

For example:
* ```2000``` – The entire year 2000
* ```2000-11``` – The entire month of November, 2000.
* ```2000-11T13``` – Likewise but for the 13th hour of the day (1pm-2pm).
* ```[2000-11-01 TO 2014-12-01]``` – The specified date range at a day resolution.
* ```[2014 TO 2014-12-01]``` – From the start of 2014 till the end of the first day of December.
* ```[* TO 2014-12-01]``` – From the earliest representable time thru till the end of 2014-12-01.

Limitations: The range syntax doesn't support embedded date math.

