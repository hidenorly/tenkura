#   Copyright 2026 hidenorly
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

#!/usr/bin/env python3

import argparse
import json
import re
import statistics
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta, date
import requests

LAPSE_RATE_C_PER_KM = 6.5


@dataclass
class WeatherPoint:
    time: datetime
    temperature_c: float
    precipitation_mm: float
    precipitation_probability: float
    wind_speed_ms: float
    wind_gust_ms: float
    weather_code: str


@dataclass
class WeatherQuery:
    lat: float
    lon: float
    altitude: float
    dates: list[date]
    time_range: tuple[int, int] | None = None


@dataclass
class WeatherResponse:
    hourly: dict[date, list[WeatherPoint]] | None
    daily: dict | None
    dropped_dates: list[date]


def parse_time_range(text):
    m = re.match(r"^(\d{1,2})-(\d{1,2})$", text)
    if not m:
        raise ValueError("invalid time range")

    start = int(m.group(1))
    end = int(m.group(2))

    if start > end:
        raise ValueError("time start > end")

    return start, end


def parse_mmdd(token, today=None):
    if today is None:
        today = date.today()

    m = re.match(r"^\s*(\d{1,2})/(\d{1,2})\s*$", token)
    if not m:
        raise ValueError(f"invalid date: {token}")

    month = int(m.group(1))
    day = int(m.group(2))

    candidate = date(today.year, month, day)

    if candidate < today:
        candidate = date(today.year + 1, month, day)

    return candidate


def parse_explicit_dates(spec, today):
    dates = []

    if not spec:
        return dates

    for token in spec.split(","):
        token = token.strip()
        if not token:
            continue

        if "-" in token:
            start_s, end_s = token.split("-", 1)
            start = parse_mmdd(start_s, today)

            end_raw = re.match(r"^\s*(\d{1,2})/(\d{1,2})\s*$", end_s)
            if not end_raw:
                raise ValueError(f"invalid date range: {token}")

            end_month = int(end_raw.group(1))
            end_day = int(end_raw.group(2))

            if (end_month, end_day) < (start.month, start.day):
                end = date(start.year + 1, end_month, end_day)
            else:
                end = date(start.year, end_month, end_day)

            if end < start:
                raise ValueError(f"invalid range: {token}")

            cur = start
            while cur <= end:
                dates.append(cur)
                cur += timedelta(days=1)
        else:
            dates.append(parse_mmdd(token, today))

    return dates


def get_nearest_weekend(today=None):
    if today is None:
        today = date.today()

    weekday = today.weekday()

    offsets = {
        0: [5, 6],
        1: [4, 5],
        2: [3, 4],
        3: [2, 3],
        4: [1, 2],
        5: [0, 1],
        6: [0, 6, 7],
    }

    return [today + timedelta(days=d) for d in offsets[weekday]]


def parse_target_dates(date_spec=None, weekend=False):
    today = date.today()
    dates = []

    if weekend:
        dates.extend(get_nearest_weekend(today))

    dates.extend(parse_explicit_dates(date_spec, today))

    if not dates:
        dates = [today]

    return sorted(set(dates))


class WeatherProvider:
    def get_mesh_size_km(self):
        return 10.0 #default

    def get_max_forecast_days(self) -> int:
        raise NotImplementedError

    def _fetch(
        self,
        lat,
        lon,
        altitude,
        start_date,
        end_date,
    ):
        raise NotImplementedError

    def _clip_dates(self, dates):
        today = date.today()
        limit = today + timedelta(
            days=self.get_max_forecast_days() - 1
        )

        valid = []
        dropped = []

        for d in sorted(set(dates)):
            if d <= limit:
                valid.append(d)
            else:
                dropped.append(d)

        return valid, dropped

    def _filter_time(self, points, time_range):
        if time_range is None:
            return points

        start, end = time_range
        return [
            p for p in points
            if start <= p.time.hour <= end
        ]

    def _aggregate(self, points):
        if not points:
            return None

        weather = sorted(set(p.weather_code for p in points))

        return {
            "temp_min": min(p.temperature_c for p in points),
            "temp_max": max(p.temperature_c for p in points),
            "precip_total": sum(p.precipitation_mm for p in points),
            "precip_prob_min": min(
                p.precipitation_probability for p in points
            ),
            "precip_prob_max": max(
                p.precipitation_probability for p in points
            ),
            "wind_avg": statistics.mean(
                p.wind_speed_ms for p in points
            ),
            "wind_max": max(
                p.wind_speed_ms for p in points
            ),
            "gust_max": max(
                p.wind_gust_ms for p in points
            ),
            "weather": weather,
        }

    def _aggregate_daily(self, hourly):
        result = {}

        for d, points in hourly.items():
            result[d] = self._aggregate(points)

        return result

    def get_weather(self, query: WeatherQuery):
        valid_dates, dropped_dates = self._clip_dates(
            query.dates
        )

        if not valid_dates:
            return WeatherResponse(
                hourly={},
                daily={},
                dropped_dates=dropped_dates
            )

        all_points = self._fetch(
            query.lat,
            query.lon,
            query.altitude,
            valid_dates[0],
            valid_dates[-1],
        )

        grouped = {}
        for p in all_points:
            grouped.setdefault(
                p.time.date(),
                []
            ).append(p)

        hourly = {}

        for d in valid_dates:
            points = grouped.get(d, [])
            points = self._filter_time(
                points,
                query.time_range
            )
            hourly[d] = points

        daily = self._aggregate_daily(hourly)

        return WeatherResponse(
            hourly=hourly,
            daily=daily,
            dropped_dates=dropped_dates,
        )


class OpenMeteoProvider(WeatherProvider):
    OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"

    def get_max_forecast_days(self):
        return 16

    def weather_code_to_text(self, code):
        if code == 0:
            return "clear"
        if code in (1, 2, 3):
            return "cloudy"
        if code in (45, 48):
            return "fog"
        if 51 <= code <= 67:
            return "rain"
        if 71 <= code <= 77:
            return "snow"
        if 80 <= code <= 82:
            return "rain"
        if 85 <= code <= 86:
            return "snow"
        if 95 <= code <= 99:
            return "thunder"
        return "unknown"

    def _fetch(self, lat, lon, altitude, start_date, end_date):
        params = {
            "latitude": lat,
            "longitude": lon,
            "hourly": ",".join([
                "temperature_2m",
                "precipitation",
                "precipitation_probability",
                "weather_code",
                "wind_speed_10m",
                "wind_gusts_10m",
            ]),
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "timezone": "Asia/Tokyo",
        }

        r = requests.get(
            self.OPEN_METEO_URL,
            params=params,
            timeout=30
        )
        r.raise_for_status()
        data = r.json()

        api_elevation = data.get("elevation", altitude)
        delta_alt = altitude - api_elevation
        temp_adjust = -(delta_alt / 1000.0) * LAPSE_RATE_C_PER_KM

        hourly = data["hourly"]
        result = []

        for i, ts in enumerate(hourly["time"]):
            t = datetime.fromisoformat(ts)
            temp = hourly["temperature_2m"][i] + temp_adjust

            result.append(
                WeatherPoint(
                    time=t,
                    temperature_c=temp,
                    precipitation_mm=hourly["precipitation"][i],
                    precipitation_probability=hourly[
                        "precipitation_probability"
                    ][i],
                    wind_speed_ms=hourly["wind_speed_10m"][i] / 3.6,
                    wind_gust_ms=hourly["wind_gusts_10m"][i] / 3.6,
                    weather_code=self.weather_code_to_text(
                        hourly["weather_code"][i]
                    ),
                )
            )

        return result


class ProviderFactory:
    @staticmethod
    def create(name):
        providers = {
            "openmeteo": OpenMeteoProvider,
        }

        provider_cls = providers.get(name)

        if provider_cls is None:
            raise ValueError(
                f"Unknown provider: {name}"
            )

        return provider_cls()


def print_human(day, agg):
    print(day.isoformat())
    print(
        f" temp min/max       : "
        f"{agg['temp_min']:.1f}/{agg['temp_max']:.1f} C"
    )
    print(
        f" precip probability : "
        f"{agg['precip_prob_min']:.0f}/"
        f"{agg['precip_prob_max']:.0f} %"
    )
    print(
        f" precip total       : "
        f"{agg['precip_total']:.1f} mm"
    )
    print(
        f" wind avg/max       : "
        f"{agg['wind_avg']:.1f}/{agg['wind_max']:.1f} m/s"
    )
    print(
        f" gust max           : "
        f"{agg['gust_max']:.1f} m/s"
    )
    print(
        f" weather            : "
        f"{', '.join(agg['weather'])}"
    )
    print()


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("lat", type=float)
    parser.add_argument("lon", type=float)
    parser.add_argument("altitude", type=float)

    parser.add_argument("-p", "--provider", default="openmeteo")
    parser.add_argument("-d", "--date")
    parser.add_argument("-dw", "--dateweekend", action="store_true")
    parser.add_argument("-t", "--time")
    parser.add_argument("-H", "--hourly", action="store_true")
    parser.add_argument("-j", "--json", action="store_true")

    args = parser.parse_args()

    provider = ProviderFactory.create(args.provider)

    dates = parse_target_dates(
        args.date,
        args.dateweekend
    )

    time_range = (
        parse_time_range(args.time)
        if args.time else None
    )

    query = WeatherQuery(
        lat=args.lat,
        lon=args.lon,
        altitude=args.altitude,
        dates=dates,
        time_range=time_range,
    )

    response = provider.get_weather(query)

    if args.hourly:
        output = {}
        for day, points in response.hourly.items():
            output[day.isoformat()] = [
                {
                    **asdict(p),
                    "time": p.time.isoformat()
                }
                for p in points
            ]
    else:
        output = {
            d.isoformat(): agg
            for d, agg in response.daily.items()
        }

    if args.json:
        print(
            json.dumps(
                output,
                ensure_ascii=False,
                indent=2
            )
        )
        return

    if args.hourly:
        for day, rows in output.items():
            print(day)
            for row in rows:
                print(
                    f"{row['time']} "
                    f"temp={row['temperature_c']:.1f}C "
                    f"rain={row['precipitation_mm']:.1f}mm "
                    f"prob={row['precipitation_probability']}% "
                    f"wind={row['wind_speed_ms']:.1f} "
                    f"gust={row['wind_gust_ms']:.1f} "
                    f"{row['weather_code']}"
                )
            print()
    else:
        for day, agg in output.items():
            if agg:
                print_human(
                    datetime.fromisoformat(day).date(),
                    agg
                )


if __name__ == "__main__":
    main()