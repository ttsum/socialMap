from datetime import datetime, timedelta
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.utils import timezone
from activities.models import Activity, Group, Member


ACTIVITIES = [
    ('a-walk', '橘子洲日落慢走', '户外', '橘子洲', '长沙市岳麓区橘子洲景区入口', 28.185, 112.960, 2.4, 0, 8, 16, ['安静', '散步', '朋友聚会'], 'mint', '洲', '沿江慢慢走，聊聊最近的小事。无需运动基础，按大家的步调出发。', '景区入口游客指示牌旁'),
    ('a-hike', '岳麓山轻徒步', '户外', '岳麓山', '长沙市岳麓区登高路岳麓山东门', 28.181, 112.942, 4.8, 20, 10, 9, ['徒步', '运动', '朋友聚会'], 'yellow', '山', '走一条轻松的山间路线，途中留出拍照和休息时间。请穿舒适的运动鞋。', '岳麓山东门广场'),
    ('a-game', '湘江边桌游小聚', '桌游', '湘江中路', '长沙市天心区湘江中路（演示场地）', 28.186, 112.972, 1.8, 58, 8, 14, ['桌游', '热闹', '朋友聚会'], 'lilac', '趣', '从简单的破冰桌游开始，新手也可以加入。活动费用为演示估算，不产生实际订单。', '场地一层接待区'),
    ('a-movie', '五一广场观影局', '观影', '五一广场', '长沙市芙蓉区五一广场（演示影院）', 28.195, 112.977, 1.2, 45, 6, 19, ['观影', '安静'], 'peach', '映', '一起看场电影，再交换彼此的观影感受。影片与场次仅用于演示，未预订座位。', '影院大厅海报墙旁'),
    ('a-coffee', '梅溪湖咖啡闲聊', '咖啡', '梅溪湖', '长沙市岳麓区梅溪湖路（演示咖啡店）', 28.191, 112.909, 8.6, 38, 8, 15, ['咖啡', '安静', '朋友聚会'], 'mint', '叙', '带一本最近在看的书，或者只带一个想分享的故事。饮品预算按人均估算。', '湖边咖啡店门口'),
    ('a-book', '城南书店阅读时光', '阅读', '天心阁附近', '长沙市天心区城南路（演示书店）', 28.179, 112.978, 3.1, 25, 8, 14, ['阅读', '安静', '朋友聚会'], 'yellow', '阅', '先各自读一会儿，再分享喜欢的段落。不设主题，也不用提前准备。', '书店一层阅读区'),
]
MEMBERS = [('u-lin', '小林', '林', '#FBD8CA'), ('u-an', '阿安', '安', '#F9DB70'), ('u-yu', '小鱼', '鱼', '#B8DFD2'), ('u-qiao', '乔乔', '乔', '#D8C9EF')]
GROUP_MEMBERS = {'g-walk': ['u-lin', 'u-an', 'u-yu'], 'g-hike': ['u-an', 'u-qiao'], 'g-game': ['u-yu', 'u-qiao', 'u-lin', 'u-an'], 'g-movie': ['u-qiao', 'u-an'], 'g-coffee': ['u-lin', 'u-yu'], 'g-book': ['u-qiao', 'u-yu', 'u-an']}


class Command(BaseCommand):
    help = 'Create or update the local demonstration activities.'

    def handle(self, *args, **options):
        today = timezone.localtime().replace(hour=0, minute=0, second=0, microsecond=0)
        days = (5 - today.weekday()) % 7
        if days == 0 and timezone.localtime().hour >= 12:
            days = 7
        base = today + timedelta(days=days)
        for item in MEMBERS:
            Member.objects.update_or_create(id=item[0], defaults={'name': item[1], 'initial': item[2], 'color': item[3]})
        for index, row in enumerate(ACTIVITIES):
            ident, title, category, location, address, lat, lng, distance, price, capacity, hour, tags, theme, symbol, description, meeting = row
            start = base + timedelta(days=1 if ident == 'a-movie' else 0, hours=hour)
            activity, _ = Activity.objects.update_or_create(id=ident, defaults={
                'title': title, 'category': category, 'location_name': location, 'address': address, 'city': '长沙', 'lat': lat, 'lng': lng, 'distance_km': distance, 'price_per_person': Decimal(str(price)), 'capacity': capacity, 'start_time': start, 'duration_hours': 2 if ident != 'a-hike' else 3, 'tags': tags, 'theme': theme, 'symbol': symbol, 'description': description, 'meeting_point': meeting,
            })
            group_id = 'g-' + ident[2:]
            group, _ = Group.objects.update_or_create(id=group_id, defaults={'activity': activity, 'host_user_id': GROUP_MEMBERS[group_id][0], 'status': 'open', 'rules': ['提前 10 分钟到达集合点', '尊重彼此，加入后请在群里打个招呼', '行程有变时及时退出，让其他伙伴有机会加入']})
            group.members.set(Member.objects.filter(id__in=GROUP_MEMBERS[group_id]))
        self.stdout.write(self.style.SUCCESS('Seeded 6 activities, 6 groups and 4 members.'))
