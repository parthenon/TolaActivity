import sys
import math
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from indicators.models import Indicator, Result, PeriodicTarget, Level
from workflow.models import Program, Country, Documentation, Organization
from indicators.views.views_indicators import generate_periodic_targets
from indicators.views.views_reports import IPTT_ReportView


class Command(BaseCommand):
    help = """
        Setup targets for indicators by reading a CSV file
        """

    def add_arguments(self, parser):
        parser.add_argument('--clean', action='store_true')
        parser.add_argument('--clean_tolaland', action='store_true')
        parser.add_argument('--names')
        parser.add_argument('--only_named', action='store_true')

    def handle(self, *args, **options):
        # ***********
        # Creates programs, indicators and results for qa testing
        # ***********

        # levels at which there should be no data
        self.NULL_LEVELS = {
            'INDICATORS': 1,
            'TARGETS': 2,
            'RESULTS': 3,
            'EVIDENCE': 4,
        }

        org = Organization.objects.get(id=1)
        country, created = Country.objects.get_or_create(
            country='Tolaland', defaults={
                'latitude': 21.4, 'longitude': -158, 'zoom': 6, 'organization': org, 'code': 'TO'})
        if options['clean_tolaland']:
            country = Country.objects.get(country='Tolaland')
            country.delete()
            sys.exit()
        if options['clean']:
            programs = Program.objects.filter(name__contains='QA Program -')
            print "Delete these programs?\n{}".format('\n'.join(p.name for p in programs))
            confirm = raw_input('[yes/no]: ')
            # confirm = 'yes'
            if confirm == 'yes':
                for program in programs:
                    print 'Deleting program:', program
                    for indicator in program.indicator_set.all():
                        indicator.delete()
                    program.delete()
                sys.exit()

        if options['names']:
            tester_names = options['names'].split(',')
        else:
            tester_names = ['Emily', 'Hanna', 'Marie', 'Jenny']

        main_start_date = (date.today() + relativedelta(months=-18)).replace(day=1)
        main_end_date = (main_start_date + relativedelta(months=+32)).replace(day=1) - timedelta(days=1)

        # Create programs for specific people
        program_ids = []
        for t_name in tester_names:
            program_name = 'QA Program - {}'.format(t_name)
            program_id = self.create_program(main_start_date, main_end_date, country, program_name)
            print 'Creating Indicators for {}'.format(Program.objects.get(id=program_id))
            self.create_full_indicator_set(program_id)

        if options['only_named']:
            sys.exit()
        # Create a program whose end date has passed ond one whose start date is in the future
        passed_end_date = main_start_date - timedelta(days=1)
        passed_start_date = (passed_end_date + relativedelta(months=-19)).replace(day=1)

        program_id = self.create_program(
            passed_start_date, passed_end_date, country, 'QA Program -- Ghost of Programs Past')
        self.create_full_indicator_set(program_id)

        # Create program with lots of indicators
        program_id = self.create_program(
            main_start_date, main_end_date, country, 'QA Program -- I Love Indicators So Much')
        self.create_full_indicator_set(program_id)
        print 'Creating moar indicators'
        moar_indicator_ids = self.create_full_indicator_set(program_id, 'moar1')
        moar_indicator_ids.extend(self.create_full_indicator_set(program_id, 'moar2'))
        moar_indicator_ids.extend(self.create_full_indicator_set(program_id, 'moar3'))
        print 'moar indids: {}:'.format(len(moar_indicator_ids))

        # Create programs with various levels of no data indicators
        print 'Creating null program with no indicators'
        self.create_program(main_start_date, main_end_date, country, 'QA Program --- No Indicators Here')

        print 'Creating null program with no targets'
        null_id = self.create_program(main_start_date, main_end_date, country, 'QA Program --- No Targets Here')
        self.create_full_indicator_set(null_id, null_level=self.NULL_LEVELS['TARGETS'])

        print 'Creating null program with no results'
        null_id = self.create_program(main_start_date, main_end_date, country, 'QA Program --- No Results Here')
        self.create_full_indicator_set(null_id, null_level=self.NULL_LEVELS['RESULTS'])

        print 'Creating null program with no evidence'
        null_id = self.create_program(main_start_date, main_end_date, country, 'QA Program --- No Evidence Here')
        self.create_full_indicator_set(null_id, null_level=self.NULL_LEVELS['EVIDENCE'])

        print 'Creating PaQ indicator set'
        paq_id = self.create_program(main_start_date, main_end_date, country, 'QA Program - PaQ')
        self.create_partial_indicator_set(paq_id)

        print 'Creating partial indicator set'
        paq_id = self.create_program(main_start_date, main_end_date, country, 'QA Program -- Small Indicator Set')
        self.create_partial_indicator_set(paq_id)

        print 'Creating partial indicator set with multiple countries'
        paq_id = self.create_program(
            main_start_date, main_end_date, country, 'QA Program -- Multi-country', multi_country=True)
        self.create_partial_indicator_set(paq_id)

    @staticmethod
    def create_program(start_date, end_date, country, name, multi_country=False):
        program = Program.objects.create(**{
            'name': name,
            'reporting_period_start': start_date,
            'reporting_period_end': end_date,
            'funding_status': 'Funded',
            'gaitid': name,
        })
        program.country.add(country)
        if multi_country:
            country2 = Country.objects.get(country="Tunisia")
            program.country.add(country2)
        return program.id

    def create_full_indicator_set(self, program_id, indicator_suffix='', null_level=0):
        if null_level == self.NULL_LEVELS['INDICATORS']:
            return
        indicator_ids = []
        program = Program.objects.get(id=program_id)

        seq = 0
        for direction in (Indicator.DIRECTION_OF_CHANGE_POSITIVE, Indicator.DIRECTION_OF_CHANGE_NEGATIVE):
            for uom_type in Indicator.UNIT_OF_MEASURE_TYPES:
                for freq in Indicator.TARGET_FREQUENCIES:
                    for is_cumulative in (True, False):
                        if is_cumulative:
                            cumulative_text = 'cumulative'
                        else:
                            cumulative_text = 'non-cumulative'
                        indicator_name = '{} | {} | {} | {}'.format(
                            freq[1],
                            uom_type[1],
                            Indicator.DIRECTION_OF_CHANGE[direction-1][1],
                            cumulative_text
                        )
                        levels = Level.objects.values_list('id', flat=True)
                        indicator = Indicator(
                            name=indicator_name + indicator_suffix,
                            is_cumulative=is_cumulative,
                            target_frequency=freq[0],
                            unit_of_measure='This is a UOM',
                            baseline=0,
                            unit_of_measure_type=uom_type[0],
                            direction_of_change=direction,
                            program=program,
                            level=Level.objects.get(id=levels[seq % len(levels)])
                        )
                        indicator.save()
                        indicator_ids.append(indicator.id)

                        seq += 1
                        if null_level == self.NULL_LEVELS['TARGETS']:
                            continue
                        self.make_targets(program, indicator)
                        if null_level == self.NULL_LEVELS['RESULTS']:
                            continue
                        periodic_targets = PeriodicTarget.objects.filter(indicator__id=indicator.id)

                        # Different combinations of UOM type, direction of change and cummulativeness require
                        # different inputs.
                        if uom_type[0] == Indicator.NUMBER:
                            if direction == Indicator.DIRECTION_OF_CHANGE_POSITIVE:
                                if is_cumulative:
                                    target_start = 100
                                    target_increment = target_start
                                    achieved_start = 90
                                    achieved_increment = achieved_start
                                else:
                                    target_start = 100
                                    target_increment = target_start
                                    achieved_start = 90
                                    achieved_increment = achieved_start
                            else:
                                if is_cumulative:
                                    target_start = 500
                                    target_increment = -int(math.floor((target_start/len(periodic_targets))/10)*10)
                                    achieved_start = 400
                                    achieved_increment = -(target_increment - 2)
                                else:
                                    target_start = 500
                                    target_increment = -int(math.floor((target_start/len(periodic_targets))/10)*10)
                                    achieved_start = 400
                                    achieved_increment = -(target_increment - 2)
                        else:
                            if direction == Indicator.DIRECTION_OF_CHANGE_POSITIVE:
                                # Don't need to check cumulative because we don't really handle it
                                target_start = 5
                                target_increment = 5
                                achieved_start = 4
                                achieved_increment = 5
                            else:
                                # Don't need to check cumulative because we don't really handle it
                                target_start = 90
                                target_increment = max(-math.floor(target_start/len(periodic_targets)), -2)
                                achieved_start = 95
                                achieved_increment = target_increment + 1

                        lop_target = 0
                        day_offset = timedelta(days=2)
                        for i, pt in enumerate(periodic_targets):
                            # Create the target amount (the PeriodicTarget object has already been created)
                            pt.target = target_start + target_increment * i
                            pt.save()

                            if is_cumulative:
                                lop_target = pt.target
                            else:
                                lop_target += pt.target

                            # Users shouldn't put in results with a date in the future, so neither should we.
                            if pt.start_date and date.today() < pt.start_date + day_offset:
                                continue

                            # Now create the Results and their related Records
                            if pt.start_date:
                                date_collected = pt.start_date + day_offset
                            else:
                                date_collected = date.today()
                            rs = Result(
                                periodic_target=pt,
                                indicator=indicator,
                                program=program,
                                achieved=achieved_start + achieved_increment * i,
                                date_collected=date_collected)
                            rs.save()

                            if null_level == self.NULL_LEVELS['EVIDENCE']:
                                continue

                            rs.evidence_name = 'Evidence link for RSid {}'.format(rs.id)
                            rs.evidence_url = 'http://my/evidence/here/'
                            rs.save()

                        indicator.lop_target = lop_target
                        indicator.save()

        return indicator_ids

    def create_partial_indicator_set(self, program_id, indicator_suffix=''):
        indicator_ids = []
        program = Program.objects.get(id=program_id)
        frequency_labels = {
            Indicator.LOP: 'Life of Program (LoP) only',
            Indicator.MID_END: 'Midline and endline',
            Indicator.ANNUAL: 'Annual',
            Indicator.QUARTERLY: 'Quarterly',
        }
        uom_labels = {
            Indicator.DIRECTION_OF_CHANGE_NONE: "Direction of change (not applicable)",
            Indicator.NUMBER: 'Number (#)',
            Indicator.PERCENTAGE:"Percentage (%)",
        }
        direction_labels = {
            Indicator.DIRECTION_OF_CHANGE_NONE: "Direction of change (not applicable)",
            Indicator.DIRECTION_OF_CHANGE_POSITIVE: "Increase (+)",
            Indicator.DIRECTION_OF_CHANGE_NEGATIVE: "Decrease (-)",
        }


        indicator_types = [
            {'freq': Indicator.ANNUAL, 'uom_type': Indicator.NUMBER, 'is_cumulative': True, 'direction': Indicator.DIRECTION_OF_CHANGE_POSITIVE},
            {'freq': Indicator.ANNUAL, 'uom_type': Indicator.PERCENTAGE, 'is_cumulative': True, 'direction': Indicator.DIRECTION_OF_CHANGE_NONE},
            {'freq': Indicator.QUARTERLY, 'uom_type': Indicator.NUMBER, 'is_cumulative': False, 'direction': Indicator.DIRECTION_OF_CHANGE_NONE},
            {'freq': Indicator.QUARTERLY, 'uom_type': Indicator.PERCENTAGE, 'is_cumulative': True, 'direction': Indicator.DIRECTION_OF_CHANGE_NEGATIVE},
            {'freq': Indicator.LOP, 'uom_type': Indicator.NUMBER, 'is_cumulative': True, 'direction': Indicator.DIRECTION_OF_CHANGE_NONE},
            {'freq': Indicator.LOP, 'uom_type': Indicator.PERCENTAGE, 'is_cumulative': True, 'direction': Indicator.DIRECTION_OF_CHANGE_NONE},
            {'freq': Indicator.MID_END, 'uom_type': Indicator.NUMBER, 'is_cumulative': True, 'direction': Indicator.DIRECTION_OF_CHANGE_NONE},
            {'freq': Indicator.MID_END, 'uom_type': Indicator.PERCENTAGE, 'is_cumulative': True, 'direction': Indicator.DIRECTION_OF_CHANGE_NONE},
        ]

        for q, combo in enumerate(indicator_types):

            if combo['is_cumulative']:
                cumulative_text = 'cumulative'
            else:
                cumulative_text = 'non-cumulative'
            indicator_name = '{} | {} | {} | {}'.format(
                frequency_labels[combo['freq']],
                uom_labels[combo['uom_type']],
                direction_labels[combo['direction']],
                cumulative_text
            )
            indicator = Indicator(
                name=indicator_name + indicator_suffix,
                is_cumulative=combo['is_cumulative'],
                target_frequency=combo['freq'],
                unit_of_measure='This is a UOM',
                baseline=0,
                unit_of_measure_type=combo['uom_type'],
                direction_of_change=combo['direction'],
                program=program,
                level=Level.objects.get(name='Goal')
            )
            indicator.save()
            indicator_ids.append(indicator.id)
            if q in [2, 3, 7]:
                continue
            self.make_targets(program, indicator)

            periodic_targets = PeriodicTarget.objects.filter(indicator__id=indicator.id)

            # Different combinations of UOM type, direction of change and cummulativeness require
            # different inputs.
            if q == 4:
                continue
            if combo['uom_type'] == Indicator.NUMBER:
                if combo['direction'] == Indicator.DIRECTION_OF_CHANGE_POSITIVE:
                    if combo['is_cumulative']:
                        target_start = 100
                        target_increment = target_start
                        achieved_start = 90
                        achieved_increment = achieved_start
                    else:
                        target_start = 100
                        target_increment = target_start
                        achieved_start = 90
                        achieved_increment = achieved_start
                else:
                    if combo['is_cumulative']:
                        target_start = 500
                        target_increment = -int(math.floor((target_start/len(periodic_targets))/10)*10)
                        achieved_start = 400
                        achieved_increment = -(target_increment-2)
                    else:
                        target_start = 500
                        target_increment = -int(math.floor((target_start/len(periodic_targets))/10)*10)
                        achieved_start = 400
                        achieved_increment = -(target_increment-2)
            else:
                if combo['direction'] == Indicator.DIRECTION_OF_CHANGE_POSITIVE:
                    # Don't need to check cumulative because we don't really handle it
                    target_start = 5
                    target_increment = 5
                    achieved_start = 4
                    achieved_increment = 5
                else:
                    # Don't need to check cumulative because we don't really handle it
                    target_start = 90
                    target_increment = max(-math.floor(target_start/len(periodic_targets)), -2)
                    achieved_start = 95
                    achieved_increment = target_increment + 1

            lop_target = 0
            day_offset = timedelta(days=2)
            for i, pt in enumerate(periodic_targets):
                # Create the target amount (the PeriodicTarget object has already been created)
                pt.target = target_start + target_increment * i
                pt.save()

                if combo['is_cumulative']:
                    lop_target = pt.target
                else:
                    lop_target += pt.target

                # Users shouldn't put in results with a date in the future, so neither should we.
                if pt.start_date and date.today() < pt.start_date + day_offset:
                    continue

                # Now create the Results and their related Records
                if pt.start_date:
                    date_collected = pt.start_date + day_offset
                else:
                    date_collected = date.today()
                rs = Result(
                    periodic_target=pt,
                    indicator=indicator,
                    program=program,
                    achieved=achieved_start + achieved_increment * i,
                    date_collected=date_collected)
                rs.save()

                if q in [5, 6]:
                    continue

                rs.evidence_name = 'Evidence link for RSid {}'.format(rs.id)
                rs.evidence_url = 'http://my/evidence/here/'
                rs.save()

            indicator.lop_target = lop_target
            indicator.save()

        return indicator_ids

    @staticmethod
    def make_targets(program, indicator):
        if indicator.target_frequency == Indicator.EVENT:
            for i in range(3):
                PeriodicTarget.objects.create(**{
                    'indicator': indicator,
                    'customsort': i,
                    'edit_date': timezone.now(),
                    'period': 'Event {}'.format(i + 1),
                })
            return

        num_periods = IPTT_ReportView._get_num_periods(
            program.reporting_period_start, program.reporting_period_end, indicator.target_frequency)
        targets_json = generate_periodic_targets(
            tf=indicator.target_frequency, start_date=program.reporting_period_start, numTargets=num_periods)
        for i, pt in enumerate(targets_json):
            if indicator.target_frequency in [Indicator.LOP, Indicator.MID_END]:
                PeriodicTarget.objects.create(**{
                    'indicator': indicator,
                    'customsort': i,
                    'edit_date': timezone.now(),
                    'period': 'Period {}'.format(i+1),
                })
            else:
                PeriodicTarget.objects.create(**{
                    'indicator': indicator,
                    'customsort': i,
                    'edit_date': timezone.now(),
                    'period': 'Period {}'.format(i+1),
                    'start_date': pt['start_date'],
                    'end_date': pt['end_date'],
                })

    @staticmethod
    def calc_increment(target, period_count):
        return int(math.ceil((target/period_count)/10)*10)
