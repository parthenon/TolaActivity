from collections import OrderedDict
import csv
from workflow.models import Country, Province, District, AdminLevelThree, Village

"""
Import admin levels from a csv file.  First column should be country, second
should be province, etc...  Country should be created before you try to upload the file, this
script will not add counties that aren't in the database.

Requires module django-extensions

Syntax: sudo py manage.py runscript import_adminlevels --script-args /path/to/file.csv
"""


def run(*args):
    counts = OrderedDict([
        ('provinces', 0), ('districts', 0), ('admin level 3s', 0),
        ('villages', 0), ])
    skipped = {}

    with open(args[0], 'rb') as csvfile:
        reader = csv.reader(csvfile, delimiter=',', quotechar='"')
        for row in reader:
            try:
                c = Country.objects.get(country=row[0])

                p, created = Province.objects.get_or_create(name=row[1], country=c)
                if created:
                    counts['provinces'] += 1

                d, created = District.objects.get_or_create(name=row[2], province=p)
                if created:
                    counts['districts'] += 1

                a3, created = AdminLevelThree.objects.get_or_create(name=row[3], district=d)
                if created:
                    counts['admin level 3s'] += 1

                v, created = Village.objects.get_or_create(name=row[4], admin_3=a3, district=d)
                if created:
                    counts['villages'] += 1

            except IndexError:
                pass
            except Country.DoesNotExist:
                try:
                    skipped[row[0]] += 1
                except KeyError:
                    skipped[row[0]] = 1

    for key in counts:
        print "Inserted %s: %s" % (key, counts[key])
    print ''
    if len(skipped) > 0:
        for country in sorted(skipped.keys()):
            print "Couldn't find the country \"%s\" in the database. Skipped %s rows associated with %s." % (
                country, skipped[country], country)
