import pycountry


def main():
    print("""\

# ISO 3166 Countries

These are the 2-digit codes used for country attributes

## Current countries

| Name | alpha 2 (used for country attribute) | alpha 3 (not used) |
| --- | --- | --- |""")

    for country in pycountry.countries:
        print(u'| {} | {} | {} |'.format(country.name, country.alpha2, country.alpha3).encode('utf-8'))

    print("""\

## Historic countries

| Name | alpha 2 (used for country attribute) | alpha 3 (not used) |
| --- | --- | --- |""")

    for country in pycountry.historic_countries:
        if getattr(country, 'date_withdrawn', False):
            print(u'| {} | {} | {} |'.format(country.name, country.alpha2, country.alpha3).encode('utf-8'))
