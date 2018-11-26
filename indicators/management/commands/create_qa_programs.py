import sys
from datetime import date

from django.core.management.base import BaseCommand
from django.utils import timezone

from indicators.models import Indicator, CollectedData, PeriodicTarget
from workflow.models import Program, Country
from indicators.views.views_indicators import generate_periodic_targets
from indicators.views.views_reports import IPTT_ReportView


class Command(BaseCommand):
    help = """
        Setup targets for indicators by reading a CSV file
        """

    def add_arguments(self, parser):
        parser.add_argument('--clean', action='store_true')

    def handle(self, *args, **options):
        # ***********
        # Creates programs, indicators and results for qa testing
        # ***********
        country, created = Country.objects.get_or_create(country='Tolaland')
        if options['clean']:
            programs = Program.objects.filter(name__contains='QA')
            print "Delete these programs?  {}".format(', '.join(p.name for p in programs))
            confirm = raw_input('[yes/no]: ')
            if confirm == 'yes':
                for program in programs:
                    for indicator in program.indicator_set.all():
                        indicator.delete()
                    program.delete()
                sys.exit()

        tester_names = ['Emily', 'Hanna', 'Marie', 'Jenny']
        program_ids = []
        for t_name in tester_names:
            print t_name
            program_ids.append(self.create_program(date(2017, 3, 1), date(2019, 7, 31), country, 'QA {}'.format(t_name)))
        for program_id in program_ids:
            print 'Creating Indicators for {}'.format(Program.objects.get(id=program_id))
            indicator_ids = self.create_indicators(program_id)
            print '{} indids: {}'.format(len(indicator_ids), indicator_ids)

    @staticmethod
    def create_program(start_date, end_date, country, name):
        program = Program.objects.create(**{
            'name': name,
            'reporting_period_start': start_date,
            'reporting_period_end': end_date,
            'funding_status': 'Funded',
            'gaitid': name,
        })
        program.country.add(country)
        return program.id

    def create_indicators(self, program_id):
        indicator_ids = []
        program = Program.objects.get(id=program_id)

        seq = 1
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
                        indicator = Indicator(
                            name=indicator_name,
                            is_cumulative=is_cumulative,
                            target_frequency=freq[0],
                            unit_of_measure_type=uom_type[0],
                            direction_of_change=direction,
                            program=program
                        )
                        indicator.save()
                        indicator_ids.append(indicator.id)

                        seq += 1
                        self.make_targets(program, indicator)
                        periodic_targets = PeriodicTarget.objects.filter(indicator__id=indicator.id)
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
                                    target_increment = -50
                                    achieved_start = 400
                                    achieved_increment = -50
                                else:
                                    target_start = 500
                                    target_increment = -50
                                    achieved_start = 400
                                    achieved_increment = -50
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
                                target_increment = -5
                                achieved_start = 95
                                achieved_increment = -5

                        lop_target = 0
                        for i, pt in enumerate(periodic_targets):
                            pt.target = target_start + target_increment * i
                            pt.save()
                            cd = CollectedData(
                                periodic_target=pt,
                                indicator=indicator,
                                program=program,
                                achieved=achieved_start + achieved_increment * i)
                            cd.save()
                            if is_cumulative:
                                lop_target = pt.target
                            else:
                                lop_target += pt.target

                        indicator.lop_target = lop_target
                        indicator.save()
                        indicator_ids.append(indicator.id)

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

