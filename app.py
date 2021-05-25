from flask import Flask, render_template, request
import requests, asyncio
import statistics

app = Flask(__name__, template_folder='htmls')


def truncate(f, n):
    s = '{}'.format(f)
    if 'e' in s or 'E' in s:
        return '{0:.{1}f}'.format(f, n)
    i, p, d = s.partition('.')
    return '.'.join([i, (d + '0' * n)[:n]])


@app.route('/')
def get_current_time():
    return render_template('main.html')


@app.route('/api/search', methods=['GET'])
def search_weather():
    # creating url from user data
    request_get = 'https://re.jrc.ec.europa.eu/api/seriescalc?'

    lat = request.args.get('lat')
    request_get += f'lat={lat}'

    lon = request.args.get('lon')
    request_get += f'&lon={lon}'

    start_year = request.args.get('start_year')
    request_get += f'&startyear={start_year}'

    end_year = request.args.get('end_year')
    request_get += f'&endyear={end_year}'

    azimuth = request.args.get('azimuth')
    request_get += f'&aspect={azimuth}'

    slope = request.args.get('slope')
    request_get += f'&angle={slope}'

    request_get += f'&pvcalculation=1'

    technology = request.args.get('technology')
    request_get += f'&pvtechchoice={technology}'

    peakPower = request.args.get('peakPower')
    request_get += f'&peakpower={peakPower}'

    loss = request.args.get('loss')
    request_get += f'&loss={loss}'

    request_get += f'&outputformat=json'

    city = request.args.get('city')

    # get current weather and forecast form openweathermap api
    asyncio.set_event_loop(asyncio.new_event_loop())
    loop = asyncio.get_event_loop()
    current, forecast = loop.run_until_complete(get_weather(city))

    # get pvgis list from user query
    response = requests.get(request_get)
    json_response = response.json()
    temp = {'day': [],
            'morn': [],
            'eve': []}
    for i in forecast['daily']:
        temp['day'].append(i['temp']['day'])
        temp['morn'].append(i['temp']['morn'])
        temp['eve'].append(i['temp']['eve'])

    mean_day = truncate(statistics.mean(temp['day']), 2)
    mean_morn = truncate(statistics.mean(temp['morn']), 2)
    mean_eve = truncate(statistics.mean(temp['eve']), 2)
    mean_pvgis = {
        'irridiance': [],
        'power': [],
        'wind': [],

    }
    for pv in json_response['outputs']['hourly']:
        mean_pvgis['irridiance'].append(pv['G(i)'])
        mean_pvgis['power'].append(pv['P'])
        mean_pvgis['wind'].append(pv['WS10m'])

    pvgis_irr = truncate(statistics.mean(mean_pvgis['irridiance']), 2)
    pvgis_pow = truncate(statistics.mean(mean_pvgis['power']), 2)
    pvgis_wind = truncate(statistics.mean(mean_pvgis['wind']), 2)

    dict = {
        'city': city,
        'temperature': current['main']['temp'],
        'description': current['weather'][0]['description'],
        'icon': current['weather'][0]['icon'],
        'mean_day': mean_day,
        'mean_morn': mean_morn,
        'mean_eve': mean_eve,
        'mean_irr': pvgis_irr,
        'mean_pow': pvgis_pow,
        'mean_wind': pvgis_wind,
        'start_year': start_year,
        'end_year': end_year
    }

    data = []
    data.append(dict)

    return render_template('results.html', icon=dict['icon'], city=dict['city'], temperature=dict['temperature'],
                           description=dict['description'], mean_day=dict['mean_day'], mean_morn=dict['mean_morn'],
                           mean_eve=dict['mean_eve'],
                           start_year=dict['start_year'], end_year=dict['end_year'], mean_pow=dict['mean_pow'],
                           mean_wind=dict['mean_wind'],
                           mean_irr=dict['mean_irr'])


async def get_weather(city):
    url_current = 'http://api.openweathermap.org/data/2.5/weather?q={}&units=metric&appid=09b52539c46bfaeac6577c3c6f70eb29'
    url_forecast = 'https://api.openweathermap.org/data/2.5/onecall?lat={}&lon={}&exclude=current,minutely,hourly,alerts&units=metric&appid=09b52539c46bfaeac6577c3c6f70eb29'
    current = requests.get(url_current.format(city)).json()
    lat = current['coord']['lat']
    lon = current['coord']['lon']
    forecast = requests.get(url_forecast.format(lat, lon)).json()
    return current, forecast
