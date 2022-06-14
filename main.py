import datetime, sqlalchemy, flask_excel
from flask import Flask, jsonify, request, render_template

app = Flask(__name__)

metadata = {}

def get_metadata():
    # con = sqlite3.connect('aws.db')
    engine = sqlalchemy.create_engine('sqlite:///aws.db')
    with engine.connect() as con:
        for row in con.execute('SELECT DISTINCT(year), name FROM aws_data'):
            metadata.setdefault(row[0], []).append(row[1])

def get_years():
    years = []
    for key in metadata.keys():
        years.append(key)
    years.sort()
    return years

def get_names(years):
    names = []
    for year in years:
        for name in metadata[int(year)]:
            if name not in names:
                names.append(name)
    names.sort()
    return names

def query_db(years, names, measurements):
    namelist = []
    for name in names:
        newname = f'name==\'{name}\''.replace('%20', ' ')
        namelist.append(newname)
    yearlist = []
    for year in years:
        yearlist.append('(year=={0} AND ({1}))'.format(int(year), ' OR '.join(namelist)))
    select = 'SELECT name, year, month, day, time, {0} FROM aws_data WHERE {1} ORDER BY year, name'.format(', '.join(measurements), ' OR '.join(yearlist))
    data_array = []
    header = ['name', 'year', 'month', 'day', 'time']
    for meas in measurements:
        header.append(meas)
    data_array.append(header)
    engine = sqlalchemy.create_engine('sqlite:///aws.db')
    with engine.connect() as con:
        for row in con.execute(select):
            data_array.append(row)
    return data_array

@app.route('/')
def home_page():
    get_metadata()
    return render_template('index.html')

@app.route('/year_list')
def year_list():
    return jsonify(get_years())

@app.route('/station_list')
def station_list():
    years = request.args.get('year').split(',')
    return jsonify(get_names(years))

@app.route('/download', methods=['GET'])
def download_data():
    years = request.args.get('year').split(',')
    stations = request.args.get('station').split(',')
    measurements = request.args.get('meas').split(',')
    extension_type = request.args.get('format')
    data_array = query_db(years, stations, measurements)
    flask_excel.init_excel(app)
    filename = f'AMRDC_AWS_datawarehouse_{datetime.date.today()}.{extension_type}'
    return flask_excel.make_response_from_array(data_array, file_type=extension_type, file_name=filename)

@app.route('/citation', methods=['GET'])
def generate_citation():
    years = request.args.get('year').split(',')
    if len(years) == 0:
        citation = ""
    elif len(years) == 1:
        citation = f"Antarctic Meteorological Research and Data Center: Automatic Weather Station quality-controlled observational data, {years[0]}. AMRDC Data Repository, accessed {datetime.date.today()}, https://doi.org/10.48567/1hn2-nw60."
    else:
        citation = f"Antarctic Meteorological Research and Data Center: Automatic Weather Station quality-controlled observational data. AMRDC Data Repository. Subset used: {years[0]} - {years[-1]}, accessed {datetime.date.today()}, https://doi.org/10.48567/1hn2-nw60."
    return citation

if __name__ == '__main__':
    flask_excel.init_excel(app)
    app.run()