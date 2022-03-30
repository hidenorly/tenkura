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
usage: tenkura_get_weather.py [-h] [-c] [-s SCORE] [-t TIME] [-d DATE] [-e EXCLUDE] [-i INCLUDE] [-a ACCEPTCLIMBRATES] [-w EXCLUDEWEATHERCONDITIONS] [-nn] [-m] [args ...]

Parse command line options.

positional arguments:
  args                  mountain name such as 富士山

optional arguments:
  -h, --help            show this help message and exit
  -c, --compare         compare mountains per day
  -s SCORE, --score SCORE
                        specify score key e.g. 登山_明日, 天気_今日, etc.
  -t TIME, --time TIME  specify time range e.g. 6-15
  -d DATE, --date DATE  specify date e.g. 2/14,2/16-2/17
  -e EXCLUDE, --exclude EXCLUDE
                        specify excluding mountain list file e.g. climbedMountains.lst
  -i INCLUDE, --include INCLUDE
                        specify including mountain list file e.g. climbedMountains.lst
  -a ACCEPTCLIMBRATES, --acceptClimbRates ACCEPTCLIMBRATES
                        specify acceptable climbRate conditions default:A,B,C
  -w EXCLUDEWEATHERCONDITIONS, --excludeWeatherConditions EXCLUDEWEATHERCONDITIONS
                        specify excluding weather conditions default:rain,thunder
  -nn, --noDetails      specify if you want to output mountain name only
  -m, --mountainList    specify if you want to output mountain name list
 ```