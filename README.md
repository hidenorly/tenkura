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
usage: tenkura_get_weather.py [-h] [-c] [-s SCORE] [-t TIME] [-d DATE] [-dw] [-e EXCLUDE] [-i INCLUDE] [-a ACCEPTCLIMBRATES] [-w EXCLUDEWEATHERCONDITIONS] [-nn]
                              [-ns] [-m] [-r]
                              [args ...]

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
  -m, --mountainList    specify if you want to output mountain name list
  -r, --renew           get latest data although cache exists ```


 # Todo

 * [x] Add support for crossing months case. e.g. if today is 4/23 and if -d includes "1" then should handle as "5/1".
 * [x] Add weekend support
