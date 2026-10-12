import json
from pathlib import Path

from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError

from activities.management.commands.seed_demo import Command as SeedDemoCommand
from ai_service.evaluation import evaluate


class Command(BaseCommand):
    help = 'Run the intent parsing and recommendation safety evaluation.'

    def add_arguments(self, parser):
        parser.add_argument('--dataset', required=True)
        parser.add_argument('--provider', choices=('mock', 'glm'), default='mock')
        parser.add_argument('--output', required=True)
        parser.add_argument('--limit', type=int, default=0, help='Only evaluate the first N cases; useful for a controlled live smoke test.')

    def handle(self, *args, **options):
        dataset = Path(options['dataset'])
        output = Path(options['output'])
        if not dataset.is_file():
            raise CommandError('评测集不存在：' + str(dataset))
        if options['provider'] in ('mock', 'glm'):
            call_command('migrate', verbosity=0, interactive=False)
            SeedDemoCommand().handle(verbosity=0)
        if options['limit'] < 0:
            raise CommandError('--limit 不能为负数')
        report = evaluate(dataset, provider_name=options['provider'], limit=options['limit'] or None)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
        self.stdout.write(json.dumps({
            'provider': report['provider'],
            'caseCount': report['caseCount'],
            'coreFieldMacroAccuracy': report['metrics']['coreFieldMacroAccuracy'],
            'preferenceF1': report['metrics']['preferenceF1'],
            'uncertainFieldRecall': report['metrics']['uncertainFieldRecall'],
            'hardFilterViolations': report['recommendationSafety']['hardFilterViolations'],
            'output': str(output),
        }, ensure_ascii=False))
