from django.utils import timezone
from rest_framework.exceptions import ValidationError
from .models import Activity

RANK_VERSION = 'rank-v2'
HARD_FILTERS = ['city', 'time', 'capacity', 'budget', 'distance']


def parse_int(value, name, minimum=None, maximum=None):
    try:
        number = int(value)
    except (TypeError, ValueError):
        raise ValidationError({name: '必须是整数'})
    if minimum is not None and number < minimum:
        raise ValidationError({name: '数值过小'})
    if maximum is not None and number > maximum:
        raise ValidationError({name: '数值过大'})
    return number


def parse_number(value, name, minimum=None, maximum=None):
    try:
        number = float(value)
    except (TypeError, ValueError):
        raise ValidationError({name: '必须是数字'})
    if minimum is not None and number < minimum:
        raise ValidationError({name: '数值过小'})
    if maximum is not None and number > maximum:
        raise ValidationError({name: '数值过大'})
    return number


def validate_intent(data):
    if not isinstance(data, dict):
        raise ValidationError({'detail': '需求条件必须是对象'})
    day = data.get('day', '不限')
    period = data.get('period', '不限')
    if day not in ('不限', '周六', '周日'):
        raise ValidationError({'day': '请选择有效日期'})
    if period not in ('不限', '上午', '下午', '晚上'):
        raise ValidationError({'period': '请选择有效时段'})
    return {
        'people': parse_int(data.get('people'), 'people', 1, 20),
        'maxDistanceKm': parse_number(data.get('maxDistanceKm'), 'maxDistanceKm', 0.01, 100),
        'budgetPerPerson': parse_number(data.get('budgetPerPerson'), 'budgetPerPerson', 0, 10000),
        'day': day,
        'period': period,
        'city': str(data.get('city') or '长沙'),
        'preferences': [str(x) for x in data.get('preferences', []) if str(x).strip()][:20],
        'uncertainFields': [str(x) for x in data.get('uncertainFields', []) if str(x).strip()][:10],
    }


def activity_period(value):
    hour = timezone.localtime(value).hour
    return '上午' if hour < 12 else '下午' if hour < 18 else '晚上'


def activity_day(value):
    return '周' + '一二三四五六日'[timezone.localtime(value).weekday()]


def recommend(data):
    activities, metadata, _ = recommend_with_meta(data)
    return activities, metadata


def recommend_with_meta(data):
    intent = validate_intent(data)
    queryset = Activity.objects.select_related('group').prefetch_related('group__members', 'group__memberships').filter(
        city=intent['city'], start_time__gt=timezone.now(), price_per_person__lte=intent['budgetPerPerson'], distance_km__lte=intent['maxDistanceKm']
    )
    candidates = list(queryset)
    results = []
    for activity in candidates:
        group = getattr(activity, 'group', None)
        joined_count = group.members.count() + sum(x.seats for x in group.memberships.all()) if group else 0
        if activity.capacity - joined_count < intent['people']:
            continue
        if intent['day'] != '不限' and activity_day(activity.start_time) != intent['day']:
            continue
        if intent['period'] != '不限' and activity_period(activity.start_time) != intent['period']:
            continue
        hits = [item for item in intent['preferences'] if item in activity.tags]
        score = round(70 + 20 * (1 - activity.distance_km / intent['maxDistanceKm']) + min(10, len(hits) * 5))
        price = '免费' if activity.price_per_person == 0 else '¥%s/人' % activity.price_per_person.normalize()
        reason = '距示例位置 %s 公里 · %s · 可安排 %s 人' % (activity.distance_km, price, intent['people'])
        if hits:
            reason += ' · 标签符合：' + '、'.join(hits)
        results.append((score, activity.distance_km, activity, reason))
    ordered = sorted(results, key=lambda row: (-row[0], row[1], row[2].id))
    metadata = {
        item.id: {'reason': reason, 'score': score}
        for score, _, item, reason in ordered
    }
    meta = {
        'rankVersion': RANK_VERSION,
        'candidateCount': len(candidates),
        'matchedCount': len(ordered),
        'hardFilters': HARD_FILTERS,
    }
    return [item for _, _, item, _ in ordered], metadata, meta
