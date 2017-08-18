# Base class
class SchemaError(Exception):
    pass


class SchemaBaseError(SchemaError):
    pass


class SchemaAttributeError(SchemaError):
    pass


# Don't catch these exceptions
class SchemaBaseUnknownAttribute(SchemaBaseError):
    pass


class SchemaBaseLinkTypeNotSupported(SchemaBaseError):
    pass


class SchemaBaseUnknownObjectType(SchemaBaseError):
    pass


class SchemaBaseUnknownLinkType(SchemaBaseError):
    pass


class SchemaBaseAttributeTypeMismatch(SchemaBaseError):
    pass


class SchemaBaseInvalidObjectType(SchemaBaseError):
    pass


class SchemaBaseInvalidAttributeType(SchemaBaseError):
    pass


class SchemaBaseInvalidAttributeModification(SchemaBaseError):
    pass


class SchemaBaseInvalidAttribute(SchemaBaseError):
    pass


class SchemaBaseInvalidLinkType(SchemaBaseError):
    pass


class SchemaBaseInvalidLinkModification(SchemaBaseError):
    pass


class SchemaBaseEmptyLink(SchemaBaseError):
    pass


class SchemaBaseEmptyObject(SchemaBaseError):
    pass


# Catch these exceptions
class SchemaAttributesInvalidDigits(SchemaAttributeError):
    pass


class SchemaAttributesInvalidPhoneNumber(SchemaAttributeError):
    pass


class SchemaAttributesInvalidEmailAddress(SchemaAttributeError):
    pass


class SchemaAttributesInvalidGroupType(SchemaAttributeError):
    pass


class SchemaAttributesInvalidGender(SchemaAttributeError):
    pass


class SchemaAttributesInvalidIATA(SchemaAttributeError):
    pass


class SchemaAttributesInvalidCountryCode(SchemaAttributeError):
    pass


class SchemaAttributesInvalidGeoLocation(SchemaAttributeError):
    pass
