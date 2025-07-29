from django.utils import timezone
import datetime
start_of_day = datetime.datetime(2024, 12, 11, 0, 0, 0)
aware_time = timezone.make_aware(start_of_day)
print(aware_time)
