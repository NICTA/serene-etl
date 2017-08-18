WARNING - Unable to import libpostal

# Ontology Definition

This file documents the ontology:

* all known objects that can be represented (Class Nodes)
* the attributes those objects can have (Data Nodes)
* the links between objects (transactions, edges, etc)

The ontology is hierarchical and is based on 6 **base** object types:

* [Accounts](#account) - accounts give entities access to systems (typically online) and represent the entities activities within the particular system
* [Documents](#document) - documents are used to identify entities or embody information at a point in time
* [Entities](#entity) - entities are persons or organisations
* [Events](#event) - events are things that happen at a point in time
* [Locations](#location) - locations are physical locations in the real world
* [Objects](#object) - objects are physical objects

Every object is represented in the system by a label or identifier and properties or attributes.

Properties or attributes are typically things that make an object unique.

The ontology is hierarchical in that all Account objects based on the Account base type **inherit** the properties and links
from the Account base type. This applies throughout the ontology below.

# Object Types

## `Account`
 > Account base type - accounts can be associated with entities



 > Label format: Generic string with no defined format

 > Search syntax: `Account:"search term"`


| link | description | 
| --- | --- |
| Account &#8658; [AssociatedWith](#link-nondirectionaltransaction-associatedwith) &#8658; ?? | AssociatedWith implies a known association |
| ?? &#8658; [AssociatedWith](#link-nondirectionaltransaction-associatedwith) &#8658; Account | AssociatedWith implies a known association |


* * *

## Account > `Email`
 > An email address - typically in the user@domain.tld format



 > Label format: Generic string with no defined format

 > Search syntax: `Email:"search term"`


| link | description | 
| --- | --- |
| Email &#8658; [AssociatedWith](#link-nondirectionaltransaction-associatedwith) &#8658; ?? | AssociatedWith implies a known association |
| ?? &#8658; [AssociatedWith](#link-nondirectionaltransaction-associatedwith) &#8658; Email | AssociatedWith implies a known association |


* * *

## Account > `PhoneNumber`
 > Raw phone number - no normalisation of the phone number is implied



 > Label format: Integer - only digits (0-9) are allowed

 > Search syntax: `PhoneNumber:"search term"`


| link | description | 
| --- | --- |
| PhoneNumber &#8658; [AssociatedWith](#link-nondirectionaltransaction-associatedwith) &#8658; ?? | AssociatedWith implies a known association |
| ?? &#8658; [AssociatedWith](#link-nondirectionaltransaction-associatedwith) &#8658; PhoneNumber | AssociatedWith implies a known association |


* * *

## Account > PhoneNumber > `ITUE164`
 > Normalised phone number using ITU E164 format.



 > Label format: phone number in E164 format - for example 6129000000 (note it has no leading + sign!)

 > Search syntax: `ITUE164:"search term"`


| property | type | description | 
| --- | --- | --- |
| country | CountryCode | [ISO 3166 2 digit country code](countries.md) |



| link | description | 
| --- | --- |
| ITUE164 &#8658; [AssociatedWith](#link-nondirectionaltransaction-associatedwith) &#8658; ?? | AssociatedWith implies a known association |
| ?? &#8658; [AssociatedWith](#link-nondirectionaltransaction-associatedwith) &#8658; ITUE164 | AssociatedWith implies a known association |


* * *

## `Entity`
 > Generic entity type used where a more specific type does not exist



 > Label format: Generic string with no defined format

 > Search syntax: `Entity:"search term"`


| link | description | 
| --- | --- |
| Entity &#8658; [AssociatedWith](#link-nondirectionaltransaction-associatedwith) &#8658; ?? | AssociatedWith implies a known association |
| Entity &#8658; [Holds](#link-directionaltransaction-holds) &#8658; ?? | A entity holds a document |
| Entity &#8658; [Located](#link-directionaltransaction-located) &#8658; ?? | Generic location link |
| Entity &#8658; [MemberOf](#link-directionaltransaction-memberof) &#8658; ?? | A entity is a member of another entity |
| Entity &#8658; [Travelled](#link-directionaltransaction-travelled) &#8658; ?? | A person or passport travelled on a flight |
| ?? &#8658; [AssociatedWith](#link-nondirectionaltransaction-associatedwith) &#8658; Entity | AssociatedWith implies a known association |


* * *

## Entity > `Group`
 > A group of entities



 > Label format: Generic string with no defined format

 > Search syntax: `Group:"search term"`


| property | type | description | 
| --- | --- | --- |
| type | EntityGroupType | Reason why these entities are grouped. Must be one of: TravelBooking |



| link | description | 
| --- | --- |
| Group &#8658; [AssociatedWith](#link-nondirectionaltransaction-associatedwith) &#8658; ?? | AssociatedWith implies a known association |
| Group &#8658; [Holds](#link-directionaltransaction-holds) &#8658; ?? | A entity holds a document |
| Group &#8658; [Located](#link-directionaltransaction-located) &#8658; ?? | Generic location link |
| Group &#8658; [MemberOf](#link-directionaltransaction-memberof) &#8658; ?? | A entity is a member of another entity |
| Group &#8658; [Travelled](#link-directionaltransaction-travelled) &#8658; ?? | A person or passport travelled on a flight |
| ?? &#8658; [AssociatedWith](#link-nondirectionaltransaction-associatedwith) &#8658; Group | AssociatedWith implies a known association |
| ?? &#8658; [MemberOf](#link-directionaltransaction-memberof) &#8658; Group | A entity is a member of another entity |


* * *

## Entity > `Organisation`
 > An entity that is not a natural person



 > Label format: Generic string with no defined format

 > Search syntax: `Organisation:"search term"`


| link | description | 
| --- | --- |
| Organisation &#8658; [AssociatedWith](#link-nondirectionaltransaction-associatedwith) &#8658; ?? | AssociatedWith implies a known association |
| Organisation &#8658; [Holds](#link-directionaltransaction-holds) &#8658; ?? | A entity holds a document |
| Organisation &#8658; [Located](#link-directionaltransaction-located) &#8658; ?? | Generic location link |
| Organisation &#8658; [MemberOf](#link-directionaltransaction-memberof) &#8658; ?? | A entity is a member of another entity |
| Organisation &#8658; [Travelled](#link-directionaltransaction-travelled) &#8658; ?? | A person or passport travelled on a flight |
| ?? &#8658; [AssociatedWith](#link-nondirectionaltransaction-associatedwith) &#8658; Organisation | AssociatedWith implies a known association |
| ?? &#8658; [MemberOf](#link-directionaltransaction-memberof) &#8658; Organisation | A entity is a member of another entity |


* * *

## Entity > `Person`
 > A natural person



 > Label format: 
    If we know the "family name" or "surname" we CAPITALISE it in the label and add it as an attribute (surname)
    If we know the "given names" or "firstnames" we "Camel Case" them in the label (at the start) and add it as an attribute (givennames)
    Where we don't know which part is which we CAPITALISE everything and put it in the label and **dont add any attributes**
    

 > Search syntax: `Person:"search term"`


| property | type | description | 
| --- | --- | --- |
| dob | Datestamp | ISO format date stamp in UTC - [see the readme for details](README.md#searching-for-dates) |
| gender | Gender | Gender - either   M   or   F |
| surname | String | Generic string with no defined format |
| pob | CountryCode | [ISO 3166 2 digit country code](countries.md) |
| givennames | String | Generic string with no defined format |



| link | description | 
| --- | --- |
| Person &#8658; [AssociatedWith](#link-nondirectionaltransaction-associatedwith) &#8658; ?? | AssociatedWith implies a known association |
| Person &#8658; [Holds](#link-directionaltransaction-holds) &#8658; ?? | A entity holds a document |
| Person &#8658; [Located](#link-directionaltransaction-located) &#8658; ?? | Generic location link |
| Person &#8658; [MemberOf](#link-directionaltransaction-memberof) &#8658; ?? | A entity is a member of another entity |
| Person &#8658; [Travelled](#link-directionaltransaction-travelled) &#8658; ?? | A person or passport travelled on a flight |
| ?? &#8658; [AssociatedWith](#link-nondirectionaltransaction-associatedwith) &#8658; Person | AssociatedWith implies a known association |


* * *

## `Event`
 > Event base type - all events must have at the very least a timestamp (date and time) in UTC timezone



 > Label format: Generic string with no defined format

 > Search syntax: `Event:"search term"`


| property | type | description | 
| --- | --- | --- |
| timestamp | Datetimestamp | ISO format date-time stamp in UTC - [see the readme for details](README.md#searching-for-dates) |





* * *

## Event > `Flight`
 > A flight from one port to another - label is the flight number
 >     attributes route show the other airports visited



 > Label format: Generic string with no defined format

 > Search syntax: `Flight:"search term"`


| property | type | description | 
| --- | --- | --- |
| timestamp | Datetimestamp | ISO format date-time stamp in UTC - [see the readme for details](README.md#searching-for-dates) |
| route | String | Generic string with no defined format |
| arrival_port | AirportIATA | Alpha3 IATA Code for airports using a [list of airports from pyairports](airports.md) |
| departure_port | AirportIATA | Alpha3 IATA Code for airports using a [list of airports from pyairports](airports.md) |
| arrival_time | Datetimestamp | ISO format date-time stamp in UTC - [see the readme for details](README.md#searching-for-dates) |
| departure_time | Datetimestamp | ISO format date-time stamp in UTC - [see the readme for details](README.md#searching-for-dates) |



| link | description | 
| --- | --- |
| Flight &#8658; [Arrived](#link-directionaltransaction-arrived) &#8658; ?? | A flight arrived ABC |
| Flight &#8658; [Departed](#link-directionaltransaction-departed) &#8658; ?? | A flight departed ABC |
| ?? &#8658; [Travelled](#link-directionaltransaction-travelled) &#8658; Flight | A person or passport travelled on a flight |


* * *

## `IssuedDocument`
 > Issued documents base type



 > Label format: Generic string with no defined format

 > Search syntax: `IssuedDocument:"search term"`


| property | type | description | 
| --- | --- | --- |
| issued | Datestamp | ISO format date stamp in UTC - [see the readme for details](README.md#searching-for-dates) |
| expiry | Datestamp | ISO format date stamp in UTC - [see the readme for details](README.md#searching-for-dates) |
| country | CountryCode | [ISO 3166 2 digit country code](countries.md) |



| link | description | 
| --- | --- |
| IssuedDocument &#8658; [AssociatedWith](#link-nondirectionaltransaction-associatedwith) &#8658; ?? | AssociatedWith implies a known association |
| IssuedDocument &#8658; [Travelled](#link-directionaltransaction-travelled) &#8658; ?? | A person or passport travelled on a flight |
| ?? &#8658; [AssociatedWith](#link-nondirectionaltransaction-associatedwith) &#8658; IssuedDocument | AssociatedWith implies a known association |
| ?? &#8658; [Holds](#link-directionaltransaction-holds) &#8658; IssuedDocument | A entity holds a document |


* * *

## IssuedDocument > `Passport`
 > A passport is a type of ID issued for travel purposes between countries



 > Label format: Generic string with no defined format

 > Search syntax: `Passport:"search term"`


| property | type | description | 
| --- | --- | --- |
| issued | Datestamp | ISO format date stamp in UTC - [see the readme for details](README.md#searching-for-dates) |
| country | CountryCode | [ISO 3166 2 digit country code](countries.md) |
| type | PassportType | Passport type (if known) can be blank or one of 'Private', 'Diplomatic', 'Official', 'PublicAffairs', 'Service' |
| expiry | Datestamp | ISO format date stamp in UTC - [see the readme for details](README.md#searching-for-dates) |



| link | description | 
| --- | --- |
| Passport &#8658; [AssociatedWith](#link-nondirectionaltransaction-associatedwith) &#8658; ?? | AssociatedWith implies a known association |
| Passport &#8658; [Travelled](#link-directionaltransaction-travelled) &#8658; ?? | A person or passport travelled on a flight |
| ?? &#8658; [AssociatedWith](#link-nondirectionaltransaction-associatedwith) &#8658; Passport | AssociatedWith implies a known association |
| ?? &#8658; [Holds](#link-directionaltransaction-holds) &#8658; Passport | A entity holds a document |


* * *

## IssuedDocument > `Visa`
 > Label format: Generic string with no defined format

 > Search syntax: `Visa:"search term"`


| property | type | description | 
| --- | --- | --- |
| country | CountryCode | [ISO 3166 2 digit country code](countries.md) |
| application | Datestamp | ISO format date stamp in UTC - [see the readme for details](README.md#searching-for-dates) |
| expiry | Datestamp | ISO format date stamp in UTC - [see the readme for details](README.md#searching-for-dates) |
| class | String | Generic string with no defined format |
| issued | Datestamp | ISO format date stamp in UTC - [see the readme for details](README.md#searching-for-dates) |



| link | description | 
| --- | --- |
| Visa &#8658; [AssociatedWith](#link-nondirectionaltransaction-associatedwith) &#8658; ?? | AssociatedWith implies a known association |
| Visa &#8658; [Travelled](#link-directionaltransaction-travelled) &#8658; ?? | A person or passport travelled on a flight |
| ?? &#8658; [AssociatedWith](#link-nondirectionaltransaction-associatedwith) &#8658; Visa | AssociatedWith implies a known association |
| ?? &#8658; [Holds](#link-directionaltransaction-holds) &#8658; Visa | A entity holds a document |


* * *

## `Location`
 > Base location type



 > Label format: Generic string with no defined format

 > Search syntax: `Location:"search term"`


| property | type | description | 
| --- | --- | --- |
| geoloc | geoloc | - |



| link | description | 
| --- | --- |
| Location &#8658; [AssociatedWith](#link-nondirectionaltransaction-associatedwith) &#8658; ?? | AssociatedWith implies a known association |
| Location &#8658; [Located](#link-directionaltransaction-located) &#8658; ?? | Generic location link |
| ?? &#8658; [Arrived](#link-directionaltransaction-arrived) &#8658; Location | A flight arrived ABC |
| ?? &#8658; [AssociatedWith](#link-nondirectionaltransaction-associatedwith) &#8658; Location | AssociatedWith implies a known association |
| ?? &#8658; [Departed](#link-directionaltransaction-departed) &#8658; Location | A flight departed ABC |
| ?? &#8658; [Located](#link-directionaltransaction-located) &#8658; Location | Generic location link |


* * *

## Location > `Address`
 > A street address
 > 
 >     We try to do a couple of things with "Addresses".
 > 
 >         1. Where we can figure out the state, country and postcode, move them into attributes instead of the label
 >         2. Parse the rest of the label and add expansions so that searches will match common variations eg st -> street, etc
 >         3. Format the label as Street Address, Suburb, (City District) City if possible



 > Label format: Generic string with no defined format

 > Search syntax: `Address:"search term"`


| property | type | description | 
| --- | --- | --- |
| country | CountryCode | [ISO 3166 2 digit country code](countries.md) |
| state | String | Generic string with no defined format |
| geoloc | geoloc | - |
| state_district | String | Generic string with no defined format |
| postcode | String | Generic string with no defined format |



| link | description | 
| --- | --- |
| Address &#8658; [AssociatedWith](#link-nondirectionaltransaction-associatedwith) &#8658; ?? | AssociatedWith implies a known association |
| Address &#8658; [Located](#link-directionaltransaction-located) &#8658; ?? | Generic location link |
| ?? &#8658; [Arrived](#link-directionaltransaction-arrived) &#8658; Address | A flight arrived ABC |
| ?? &#8658; [AssociatedWith](#link-nondirectionaltransaction-associatedwith) &#8658; Address | AssociatedWith implies a known association |
| ?? &#8658; [Departed](#link-directionaltransaction-departed) &#8658; Address | A flight departed ABC |
| ?? &#8658; [Located](#link-directionaltransaction-located) &#8658; Address | Generic location link |


* * *

## Location > `Country`
 > 



 > Label format: Full country name from ISO 3166

 > Search syntax: `Country:"search term"`


| property | type | description | 
| --- | --- | --- |
| country | CountryCode | [ISO 3166 2 digit country code](countries.md) |
| geoloc | geoloc | - |



| link | description | 
| --- | --- |
| Country &#8658; [AssociatedWith](#link-nondirectionaltransaction-associatedwith) &#8658; ?? | AssociatedWith implies a known association |
| Country &#8658; [Located](#link-directionaltransaction-located) &#8658; ?? | Generic location link |
| ?? &#8658; [Arrived](#link-directionaltransaction-arrived) &#8658; Country | A flight arrived ABC |
| ?? &#8658; [AssociatedWith](#link-nondirectionaltransaction-associatedwith) &#8658; Country | AssociatedWith implies a known association |
| ?? &#8658; [Departed](#link-directionaltransaction-departed) &#8658; Country | A flight departed ABC |
| ?? &#8658; [Located](#link-directionaltransaction-located) &#8658; Country | Generic location link |


* * *

## Location > `Port`
 > Any type of transit point



 > Label format: Generic string with no defined format

 > Search syntax: `Port:"search term"`


| property | type | description | 
| --- | --- | --- |
| geoloc | geoloc | - |



| link | description | 
| --- | --- |
| Port &#8658; [AssociatedWith](#link-nondirectionaltransaction-associatedwith) &#8658; ?? | AssociatedWith implies a known association |
| Port &#8658; [Located](#link-directionaltransaction-located) &#8658; ?? | Generic location link |
| ?? &#8658; [Arrived](#link-directionaltransaction-arrived) &#8658; Port | A flight arrived ABC |
| ?? &#8658; [AssociatedWith](#link-nondirectionaltransaction-associatedwith) &#8658; Port | AssociatedWith implies a known association |
| ?? &#8658; [Departed](#link-directionaltransaction-departed) &#8658; Port | A flight departed ABC |
| ?? &#8658; [Located](#link-directionaltransaction-located) &#8658; Port | Generic location link |


* * *

## Location > Port > `Airport`
 > A port where flights leave from - to be considered an airport object it must appear in [this list](airports.md) otherwise it would be represented as a "Location"



 > Label format: Generic string with no defined format

 > Search syntax: `Airport:"search term"`


| property | type | description | 
| --- | --- | --- |
| city | String | Generic string with no defined format |
| geoloc | geoloc | - |
| country | CountryCode | [ISO 3166 2 digit country code](countries.md) |



| link | description | 
| --- | --- |
| Airport &#8658; [AssociatedWith](#link-nondirectionaltransaction-associatedwith) &#8658; ?? | AssociatedWith implies a known association |
| Airport &#8658; [Located](#link-directionaltransaction-located) &#8658; ?? | Generic location link |
| ?? &#8658; [Arrived](#link-directionaltransaction-arrived) &#8658; Airport | A flight arrived ABC |
| ?? &#8658; [AssociatedWith](#link-nondirectionaltransaction-associatedwith) &#8658; Airport | AssociatedWith implies a known association |
| ?? &#8658; [Departed](#link-directionaltransaction-departed) &#8658; Airport | A flight departed ABC |
| ?? &#8658; [Located](#link-directionaltransaction-located) &#8658; Airport | Generic location link |


* * *

## `MultiDayEvent`
 > Similar to Event but for events that occur over multiple days



 > Label format: Generic string with no defined format

 > Search syntax: `MultiDayEvent:"search term"`


| property | type | description | 
| --- | --- | --- |
| start_dt | Datestamp | ISO format date stamp in UTC - [see the readme for details](README.md#searching-for-dates) |
| end_dt | Datestamp | ISO format date stamp in UTC - [see the readme for details](README.md#searching-for-dates) |





* * *

## `Object`
 > A physical object that could be located somewhere



 > Label format: Generic string with no defined format

 > Search syntax: `Object:"search term"`


| link | description | 
| --- | --- |
| Object &#8658; [Located](#link-directionaltransaction-located) &#8658; ?? | Generic location link |


* * *

## `Unknown`
 > Unknown type used where no modelled data at all can be found



 > Label format: Generic string with no defined format

 > Search syntax: `Unknown:"search term"`




* * *



# Link types

## Link > DirectionalTransaction > `Arrived`
 > A flight arrived ABC



To limit results to documents containing this type of link `link_types:Arrived`


| property | type | description | 
| --- | --- | --- |
| timestamp | Datetimestamp | ISO format date-time stamp in UTC - [see the readme for details](README.md#searching-for-dates) |



| link | 
| --- | 
| [Flight](#event-flight) &#8658; Arrived &#8658; ?? |
| ?? &#8658; Arrived &#8658; [Location](#location) |


* * *

## Link > DirectionalTransaction > `Departed`
 > A flight departed ABC



To limit results to documents containing this type of link `link_types:Departed`


| property | type | description | 
| --- | --- | --- |
| timestamp | Datetimestamp | ISO format date-time stamp in UTC - [see the readme for details](README.md#searching-for-dates) |



| link | 
| --- | 
| [Flight](#event-flight) &#8658; Departed &#8658; ?? |
| ?? &#8658; Departed &#8658; [Location](#location) |


* * *

## Link > DirectionalTransaction > `Holds`
 > A entity holds a document



To limit results to documents containing this type of link `link_types:Holds`


| property | type | description | 
| --- | --- | --- |
| timestamp | Datetimestamp | ISO format date-time stamp in UTC - [see the readme for details](README.md#searching-for-dates) |



| link | 
| --- | 
| [Entity](#entity) &#8658; Holds &#8658; ?? |
| [Group](#entity-group) &#8658; Holds &#8658; ?? |
| [Organisation](#entity-organisation) &#8658; Holds &#8658; ?? |
| [Person](#entity-person) &#8658; Holds &#8658; ?? |
| ?? &#8658; Holds &#8658; [IssuedDocument](#issueddocument) |


* * *

## Link > DirectionalTransaction > `IssuedBy`
 > Documents are issued by organisations or countries



To limit results to documents containing this type of link `link_types:IssuedBy`


| property | type | description | 
| --- | --- | --- |
| timestamp | Datetimestamp | ISO format date-time stamp in UTC - [see the readme for details](README.md#searching-for-dates) |





* * *

## Link > DirectionalTransaction > `IssuedTo`
 > Documents are issued to people



To limit results to documents containing this type of link `link_types:IssuedTo`


| property | type | description | 
| --- | --- | --- |
| timestamp | Datetimestamp | ISO format date-time stamp in UTC - [see the readme for details](README.md#searching-for-dates) |





* * *

## Link > DirectionalTransaction > `Located`
 > Generic location link



To limit results to documents containing this type of link `link_types:Located`


| property | type | description | 
| --- | --- | --- |
| timestamp | Datetimestamp | ISO format date-time stamp in UTC - [see the readme for details](README.md#searching-for-dates) |



| link | 
| --- | 
| [Address](#location-address) &#8658; Located &#8658; ?? |
| [Airport](#location-port-airport) &#8658; Located &#8658; ?? |
| [Country](#location-country) &#8658; Located &#8658; ?? |
| [Entity](#entity) &#8658; Located &#8658; ?? |
| [Group](#entity-group) &#8658; Located &#8658; ?? |
| [Location](#location) &#8658; Located &#8658; ?? |
| [Object](#object) &#8658; Located &#8658; ?? |
| [Organisation](#entity-organisation) &#8658; Located &#8658; ?? |
| [Person](#entity-person) &#8658; Located &#8658; ?? |
| [Port](#location-port) &#8658; Located &#8658; ?? |


* * *

## Link > DirectionalTransaction > `MemberOf`
 > A entity is a member of another entity



To limit results to documents containing this type of link `link_types:MemberOf`


| property | type | description | 
| --- | --- | --- |
| timestamp | Datetimestamp | ISO format date-time stamp in UTC - [see the readme for details](README.md#searching-for-dates) |



| link | 
| --- | 
| [Entity](#entity) &#8658; MemberOf &#8658; ?? |
| [Group](#entity-group) &#8658; MemberOf &#8658; ?? |
| [Organisation](#entity-organisation) &#8658; MemberOf &#8658; ?? |
| [Person](#entity-person) &#8658; MemberOf &#8658; ?? |


* * *

## Link > DirectionalTransaction > `Travelled`
 > A person or passport travelled on a flight



To limit results to documents containing this type of link `link_types:Travelled`


| property | type | description | 
| --- | --- | --- |
| timestamp | Datetimestamp | ISO format date-time stamp in UTC - [see the readme for details](README.md#searching-for-dates) |



| link | 
| --- | 
| [Entity](#entity) &#8658; Travelled &#8658; ?? |
| [Group](#entity-group) &#8658; Travelled &#8658; ?? |
| [IssuedDocument](#issueddocument) &#8658; Travelled &#8658; ?? |
| [Organisation](#entity-organisation) &#8658; Travelled &#8658; ?? |
| [Passport](#issueddocument-passport) &#8658; Travelled &#8658; ?? |
| [Person](#entity-person) &#8658; Travelled &#8658; ?? |
| [Visa](#issueddocument-visa) &#8658; Travelled &#8658; ?? |
| ?? &#8658; Travelled &#8658; [Flight](#event-flight) |


* * *

## Link > NonDirectionalTransaction > `AssociatedWith`
 > AssociatedWith implies a known association



To limit results to documents containing this type of link `link_types:AssociatedWith`


| property | type | description | 
| --- | --- | --- |
| timestamp | Datetimestamp | ISO format date-time stamp in UTC - [see the readme for details](README.md#searching-for-dates) |



| link | 
| --- | 
| [Account](#account) &#8658; AssociatedWith &#8658; ?? |
| [Address](#location-address) &#8658; AssociatedWith &#8658; ?? |
| [Airport](#location-port-airport) &#8658; AssociatedWith &#8658; ?? |
| [Country](#location-country) &#8658; AssociatedWith &#8658; ?? |
| [Email](#account-email) &#8658; AssociatedWith &#8658; ?? |
| [Entity](#entity) &#8658; AssociatedWith &#8658; ?? |
| [Group](#entity-group) &#8658; AssociatedWith &#8658; ?? |
| [ITUE164](#account-phonenumber-itue164) &#8658; AssociatedWith &#8658; ?? |
| [IssuedDocument](#issueddocument) &#8658; AssociatedWith &#8658; ?? |
| [Location](#location) &#8658; AssociatedWith &#8658; ?? |
| [Organisation](#entity-organisation) &#8658; AssociatedWith &#8658; ?? |
| [Passport](#issueddocument-passport) &#8658; AssociatedWith &#8658; ?? |
| [Person](#entity-person) &#8658; AssociatedWith &#8658; ?? |
| [PhoneNumber](#account-phonenumber) &#8658; AssociatedWith &#8658; ?? |
| [Port](#location-port) &#8658; AssociatedWith &#8658; ?? |
| [Visa](#issueddocument-visa) &#8658; AssociatedWith &#8658; ?? |


* * *

