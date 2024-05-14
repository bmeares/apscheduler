from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from apscheduler import MaxIterationsReached
from apscheduler.triggers.calendarinterval import CalendarIntervalTrigger
from apscheduler.triggers.combining import AndTrigger, OrTrigger
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger


class TestAndTrigger:
    @pytest.mark.parametrize("threshold", [1, 0])
    def test_two_datetriggers(self, timezone, serializer, threshold):
        date1 = datetime(2020, 5, 16, 14, 17, 30, 254212, tzinfo=timezone)
        date2 = datetime(2020, 5, 16, 14, 17, 31, 254212, tzinfo=timezone)
        trigger = AndTrigger(
            [DateTrigger(date1), DateTrigger(date2)], threshold=threshold
        )
        if serializer:
            trigger = serializer.deserialize(serializer.serialize(trigger))

        if threshold:
            # date2 was within the threshold so it will not be used
            assert trigger.next() == date1

        assert trigger.next() is None

    def test_max_iterations(self, timezone, serializer):
        start_time = datetime(2020, 5, 16, 14, 17, 30, 254212, tzinfo=timezone)
        trigger = AndTrigger(
            [
                IntervalTrigger(seconds=4, start_time=start_time),
                IntervalTrigger(
                    seconds=4, start_time=start_time + timedelta(seconds=2)
                ),
            ]
        )
        if serializer:
            trigger = serializer.deserialize(serializer.serialize(trigger))

        pytest.raises(MaxIterationsReached, trigger.next)

    def test_repr(self, timezone, serializer):
        start_time = datetime(2020, 5, 16, 14, 17, 30, 254212, tzinfo=timezone)
        trigger = AndTrigger(
            [
                IntervalTrigger(seconds=4, start_time=start_time),
                IntervalTrigger(
                    seconds=4, start_time=start_time + timedelta(seconds=2)
                ),
            ]
        )
        if serializer:
            trigger = serializer.deserialize(serializer.serialize(trigger))

        assert repr(trigger) == (
            "AndTrigger([IntervalTrigger(seconds=4, "
            "start_time='2020-05-16 14:17:30.254212+02:00'), IntervalTrigger("
            "seconds=4, start_time='2020-05-16 14:17:32.254212+02:00')], "
            "threshold=1.0, max_iterations=10000)"
        )

    @pytest.mark.parametrize(
        "left_kwargs,right_kwargs,start_time,expected_datetimes",
        [
            (
                {"_class": "IntervalTrigger", "hours": 6},
                {"_class": "IntervalTrigger", "hours": 12},
                datetime(2024, 5, 1, 0, 0, 0, tzinfo=timezone.utc),
                [
                    datetime(2024, 5, 1, 0, 0, 0, tzinfo=timezone.utc),
                    datetime(2024, 5, 1, 12, 0, 0, tzinfo=timezone.utc),
                    datetime(2024, 5, 2, 0, 0, 0, tzinfo=timezone.utc),
                ],
            ),
            (
                {"_class": "IntervalTrigger", "days": 1},
                {"_class": "IntervalTrigger", "weeks": 1},
                datetime(2024, 5, 1, 0, 0, 0, tzinfo=timezone.utc),
                [
                    datetime(2024, 5, 1, 0, 0, 0, tzinfo=timezone.utc),
                    datetime(2024, 5, 8, 0, 0, 0, tzinfo=timezone.utc),
                    datetime(2024, 5, 15, 0, 0, 0, tzinfo=timezone.utc),
                ],
            ),
            (
                {
                    "_class": "CronTrigger",
                    "day_of_week": "mon-fri",
                    "hour": "*",
                    "timezone": timezone.utc,
                },
                {"_class": "IntervalTrigger", "hours": 12},
                datetime(2024, 5, 3, 0, 0, 0, tzinfo=timezone.utc),
                [
                    datetime(2024, 5, 3, 0, 0, 0, tzinfo=timezone.utc),
                    datetime(2024, 5, 3, 12, 0, 0, tzinfo=timezone.utc),
                    datetime(2024, 5, 6, 0, 0, 0, tzinfo=timezone.utc),
                ],
            ),
            (
                {
                    "_class": "CronTrigger",
                    "day_of_week": "mon-fri",
                    "timezone": timezone.utc,
                },
                {"_class": "IntervalTrigger", "days": 4},
                datetime(2024, 5, 13, 0, 0, 0, tzinfo=timezone.utc),
                [
                    datetime(2024, 5, 13, 0, 0, 0, tzinfo=timezone.utc),
                    datetime(2024, 5, 17, 0, 0, 0, tzinfo=timezone.utc),
                    datetime(2024, 5, 21, 0, 0, 0, tzinfo=timezone.utc),
                    datetime(2024, 5, 29, 0, 0, 0, tzinfo=timezone.utc),
                ],
            ),
            (
                {
                    "_class": "CalendarIntervalTrigger",
                    "months": 1,
                    "timezone": timezone.utc,
                },
                {
                    "_class": "CronTrigger",
                    "day_of_week": "mon-fri",
                    "timezone": timezone.utc,
                },
                datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
                [
                    datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
                    datetime(2024, 2, 1, 0, 0, 0, tzinfo=timezone.utc),
                    datetime(2024, 3, 1, 0, 0, 0, tzinfo=timezone.utc),
                    datetime(2024, 4, 1, 0, 0, 0, tzinfo=timezone.utc),
                    datetime(2024, 5, 1, 0, 0, 0, tzinfo=timezone.utc),
                    datetime(2024, 7, 1, 0, 0, 0, tzinfo=timezone.utc),
                    datetime(2024, 8, 1, 0, 0, 0, tzinfo=timezone.utc),
                    datetime(2024, 10, 1, 0, 0, 0, tzinfo=timezone.utc),
                    datetime(2024, 11, 1, 0, 0, 0, tzinfo=timezone.utc),
                ],
            ),
        ],
    )
    def test_overlapping_triggers(
        self, left_kwargs, right_kwargs, start_time, expected_datetimes
    ):
        """
        Verify that the `AndTrigger` fires at the intersection of two triggers.
        """
        trigger_classes = {
            'CronTrigger': CronTrigger,
            'IntervalTrigger': IntervalTrigger,
            'CalendarIntervalTrigger': CalendarIntervalTrigger,
        }
        left_trigger_class = trigger_classes[left_kwargs.pop('_class')]
        right_trigger_class = trigger_classes[right_kwargs.pop('_class')]

        left_kwargs.update(
            {
                (
                    "start_time"
                    if left_trigger_class is not CalendarIntervalTrigger
                    else "start_date"
                ): start_time,
            }
        )
        right_kwargs.update(
            {
                (
                    "start_time"
                    if right_trigger_class is not CalendarIntervalTrigger
                    else "start_date"
                ): start_time,
            }
        )

        left_trigger = left_trigger_class(**left_kwargs)
        right_trigger = right_trigger_class(**right_kwargs)
        and_trigger = AndTrigger([left_trigger, right_trigger])

        for expected_datetime in expected_datetimes:
            next_datetime = and_trigger.next()
            assert next_datetime == expected_datetime


class TestOrTrigger:
    def test_two_datetriggers(self, timezone, serializer):
        date1 = datetime(2020, 5, 16, 14, 17, 30, 254212, tzinfo=timezone)
        date2 = datetime(2020, 5, 18, 15, 1, 53, 940564, tzinfo=timezone)
        trigger = OrTrigger([DateTrigger(date1), DateTrigger(date2)])

        assert trigger.next() == date1

        if serializer:
            trigger = serializer.deserialize(serializer.serialize(trigger))

        assert trigger.next() == date2
        assert trigger.next() is None

    def test_two_interval_triggers(self, timezone, serializer):
        start_time = datetime(2020, 5, 16, 14, 17, 30, 254212, tzinfo=timezone)
        end_time1 = start_time + timedelta(seconds=16)
        end_time2 = start_time + timedelta(seconds=18)
        trigger = OrTrigger(
            [
                IntervalTrigger(seconds=4, start_time=start_time, end_time=end_time1),
                IntervalTrigger(seconds=6, start_time=start_time, end_time=end_time2),
            ]
        )
        if serializer:
            trigger = serializer.deserialize(serializer.serialize(trigger))

        assert trigger.next() == start_time
        assert trigger.next() == start_time + timedelta(seconds=4)
        assert trigger.next() == start_time + timedelta(seconds=6)
        assert trigger.next() == start_time + timedelta(seconds=8)
        assert trigger.next() == start_time + timedelta(seconds=12)
        assert trigger.next() == start_time + timedelta(seconds=16)
        # The end time of the 4 second interval has been reached
        assert trigger.next() == start_time + timedelta(seconds=18)
        # The end time of the 6 second interval has been reached
        assert trigger.next() is None

    def test_repr(self, timezone):
        date1 = datetime(2020, 5, 16, 14, 17, 30, 254212, tzinfo=timezone)
        date2 = datetime(2020, 5, 18, 15, 1, 53, 940564, tzinfo=timezone)
        trigger = OrTrigger([DateTrigger(date1), DateTrigger(date2)])
        assert repr(trigger) == (
            "OrTrigger([DateTrigger('2020-05-16 14:17:30.254212+02:00'), "
            "DateTrigger('2020-05-18 15:01:53.940564+02:00')])"
        )
