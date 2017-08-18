
if __name__ == "__main__" and __package__ is None:
    #use the local version of schema
    import sys, os
    if os.getcwd().endswith('serene_schema'):
        sys.path.insert(0, os.getcwd())
    elif os.getcwd().endswith('helpers'):
        sys.path.insert(0, os.path.join(os.getcwd(), '..', '..'))

from serene_schema import attributes, VALID_TYPES, VALID_TRANSACTIONS


def make_link(name, title):
    return '[{}](#{})'.format(name, title.lower()
                                         .replace('.', '')
                                         .replace(' > ', '-')
                                         .replace(' ', '-')
                                         .replace('`', ''))


def object_title(o):
    path = o.class_path()
    path[-1] = '`{}`'.format(path[-1])
    return '{}'.format(' > '.join(path))


def link_title(o):
    path = o.class_path()
    path[-1] = '`{}`'.format(path[-1])
    return 'Link > {}'.format(' > '.join(path))


def print_doc(cls):

    if cls.__doc__:
        for line in cls.__doc__.strip().split('\n'):
            print(' > {}'.format(line))
        print('\n\n')


def print_objects():
    for cls in sorted(VALID_TYPES, key=lambda _: '.'.join(_.class_path())):
        attrs = cls.attrs

        print('## {}'.format(object_title(cls)))
        print_doc(cls)

        if cls.label.__doc__:
            print(' > Label format: {}\n'.format(cls.label.__doc__))

        print(' > Search syntax: `{}:"search term"`\n\n'.format(cls.name()))

        if attrs:
            print('| property | type | description | \n| --- | --- | --- |')

            for k in attrs:
                txt = attrs[k].__doc__.strip() if attrs[k].__doc__ else '-'
                assert '\n' not in txt, attrs[k].__name__
                assert len(txt.strip().split('\n')) <= 1, attrs[k].__name__
                print('| {} | {} | {} |'.format(k, attrs[k].__name__, txt))

            print('\n\n')

        links = getattr(cls, 'links', [])
        rev_links = cls.reverse_links()

        if links or rev_links:
            print('| link | description | \n| --- | --- |')

        for l in sorted(links, key=lambda k:k.name()):
            assert l.__doc__,l
            txt = l.__doc__.strip()
            title = make_link(l.name(), link_title(l))
            assert len(txt.strip().split('\n')) <= 1, l.__doc__
            print('| {} &#8658; {} &#8658; ?? | {} |'.format(cls.name(),title, txt))

        for l in sorted(rev_links, key=lambda k:k.name()):
            txt = l.__doc__.strip()
            title = make_link(l.name(), link_title(l))
            assert len(txt.strip().split('\n')) <= 1, l.__doc__
            print('| ?? &#8658; {} &#8658; {} | {} |'.format(title, cls.name(), txt))

        print('\n\n* * *\n')


def print_transactions():
    for cls in sorted(VALID_TRANSACTIONS, key=lambda _: '.'.join(_.class_path())):
        attrs = cls.attrs

        print('## {}'.format(link_title(cls)))
        print_doc(cls)

        print('To limit results to documents containing this type of link `link_types:{}`\n\n'.format(cls.name()))

        if attrs:
            print('| property | type | description | \n| --- | --- | --- |')

            for k in attrs:
                txt = attrs[k].__doc__.strip() if attrs[k].__doc__ else '-'
                assert '\n' not in txt, attrs[k].__name__
                assert len(txt.strip().split('\n')) <= 1, attrs[k].__name__
                print('| {} | {} | {} |'.format(k, attrs[k].__name__, txt))

            print('\n\n')

        links = getattr(cls, 'links', [])

        rev_links = cls.reverse_links()

        if links or rev_links:
            print('| link | \n| --- | '.format(cls.name()))

        for link in sorted(rev_links, key=lambda k:k.name()):
            title = make_link(link.name(), object_title(link))
            print('| {} &#8658; {} &#8658; ?? |'.format(title, cls.name()))

        for link in sorted(links, key=lambda k: k.name()):
            if link in rev_links:
                continue
            title = make_link(link.name(), object_title(link))
            print('| ?? &#8658; {} &#8658; {} |'.format(cls.name(), title))

        print('\n\n* * *\n')


def main():
    print("""
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
""")
    print_objects()
    print("""

# Link types
""")
    print_transactions()


if __name__ == '__main__':
    main()


