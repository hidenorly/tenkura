# tenkura

DO NOT USE THIS.

# Create mountainDic.py

```
$ python3 tenkura_list_mountains.py "https://tenkura.n-kishou.co.jp/tk/kanko/kasel.html?ba=hk&type=15" > mountainDic.py
```

# get weather

```
$ python3 tenkura_get_weather.py 櫛形山_2
```

```
usage: tenkura_get_weather.py [-h] [-c] [-s SCORE] [-t TIME] [-d DATE] [-dw] [-e EXCLUDE] [-i INCLUDE] [-a ACCEPTCLIMBRATES] [-w EXCLUDEWEATHERCONDITIONS] [-nn] [-ns] [-nu] [-m] [-r] [args ...]

Parse command line options.

positional arguments:
  args                  mountain name such as 富士山

options:
  -h, --help            show this help message and exit
  -c, --compare         compare mountains per day
  -s SCORE, --score SCORE
                        specify score key e.g. 登山_明日, 天気_今日, etc.
  -t TIME, --time TIME  specify time range e.g. 6-15
  -d DATE, --date DATE  specify date e.g. 2/14,2/16-2/17
  -dw, --dateweekend    specify if weekend (Saturday and Sunday)
  -e EXCLUDE, --exclude EXCLUDE
                        specify excluding mountain list file e.g. climbedMountains.lst
  -i INCLUDE, --include INCLUDE
                        specify including mountain list file e.g. climbedMountains.lst
  -a ACCEPTCLIMBRATES, --acceptClimbRates ACCEPTCLIMBRATES
                        specify acceptable climbRate conditions default:A,B,C
  -w EXCLUDEWEATHERCONDITIONS, --excludeWeatherConditions EXCLUDEWEATHERCONDITIONS
                        specify excluding weather conditions e.g. rain,thunder default is none then all weathers are ok)
  -nn, --noDetails      specify if you want to output mountain name only
  -ns, --noSupplementalInfo
                        specify if you want to output mountain name only
  -nu, --noUrl          specify if you want to disable tenkura url output
  -m, --mountainList    specify if you want to output mountain name list
  -r, --renew           get latest data although cache exists
```

 # Todo

 * [x] Add support for crossing months case. e.g. if today is 4/23 and if -d includes "1" then should handle as "5/1".
 * [x] Add weekend support


# tenkura_get_candidate_days.py

to list up the number of A climbrate mountains in the specified dates.

```
$ python3 tenkura_get_candidate_days.py -dw -d 9/18 --args="-i ~/yama100.csv -e ~/excludes.csv"
2023/09/16: 17
2023/09/17: 15
2023/09/18: 15
```

In this example, the the 9/16 should be the most day of the number of candidate mountains.


# get_weather.py

Before executing this, do the following (before it, you need to git clone the repo)

the following is an example (you need to modify as the path where you git-clone-ed.):

```
ln -s ~/work/get_mountain_longitude_latitude/get_mountain_list.py ~/work/tenkura
```

```
$ python3 get_weather.py --help
usage: get_weather.py [-h] [-d DATE] [-dw] [-c] [-o] [-l] [args ...]

Specify expected prefectures or mountain names

positional arguments:
  args

options:
  -h, --help            show this help message and exit
  -d DATE, --date DATE  specify date e.g. 2/14,2/16-2/17
  -dw, --dateweekend    specify if weekend (Saturday and Sunday)
  -c, --compare         compare per day
  -o, --open            specify if you want to open the page
  -l, --list            List supported area name
```

```
$ python3 get_weather.py 釧路
```

```
$ python3 get_weather.py 皇海山
```

# get_weather_mountain

capture weather map as .png

```
python3 get_weather_mountain.py --help
usage: get_weather_mountain.py [-h] [-d DATE] [-dw] [args ...]

Parse command line options.

positional arguments:
  args                  mountain name such as 富士山

options:
  -h, --help            show this help message and exit
  -d DATE, --date DATE  specify date e.g. 2/14,2/16-2/17
  -dw, --dateweekend    specify if weekend (Saturday and Sunday)
```


# get_weather_mountain_detail

detail weather info. at per-day level

```
python3 get_weather_mountain_detail.py 恵那山 -dw                                                                           
恵那山         (https://weathernews.jp/mountain/centralalps/40918/?target=trailhead)
  11(日) cloud_rain     16度/6度
```


# get_weather_mountain_detail_per_mountain

detail weather info. at three_days, per-hour, per-day(weekly) level with filtering function on day, weather and time

```
python3 get_weather_mountain_detail_per_mountain.py -i ~/gunma100.csv -i ~/tochigi100.csv -i ~/chichibu.csv -i ~/yamanashi100.csv -e ~/excludes.csv -e ~/excludes-alps.csv -t 6-15 -w rain -d 5/11 -nn
```

