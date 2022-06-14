import sys, sqlite3, urllib.request, json, time, math

DATABASE_NAME = sys.argv[1]

def main():
    ### Search for AWS QC data on repository and add dataset URLs to record_list list
    response = urllib.request.urlopen('https://amrdcdata.ssec.wisc.edu/api/action/package_search?q=aws+quality_controlled&rows=1000')
    record_list = json.loads(response.read())
    record_count = record_list['result']['count']           ### NOTE: If record_count > 1000, must slice + return multiple lists (Update 5/18/2022: 729 records)
    data_files = []
    print("Fetching records from repository...")            ### Extract station name and individual data file URLs from every record in record_list and add to data_files list
    for record in record_list['result']['results']:
        title = record['title'].split()
        name = []
        for word in title:
            if word == "Automatic":
                break
            else:
                name.append(word)
        name_formatted = ' '.join(name)
        if name_formatted == "Alexander Tall Tower":
            for item in record['resources']:
                if 'q1h3.txt' in item['name']:              ### Special handling for ATT levels - select level 1 only
                    data_files.append([name_formatted, item['url']])
        else:
            for item in record['resources']:
                if 'q1h' in item['name']:
                    data_files.append([name_formatted, item['url']])
    print("Creating database...")                           ### Build database
    database = sqlite3.connect(DATABASE_NAME)
    database.execute('''CREATE TABLE aws_data 
                        (id INT PRIMARY KEY, name TEXT, year INT, month INT, day INT, time INT, temperature INT, pressure INT, wind_speed INT, wind_direction INT, humidity INT, delta_t INT)''')
    id_count = 0
    print("Database '{0}' created".format(DATABASE_NAME))
    print("Extracting resources")                           ### Extract data from every resource in data_files and add to database
    extracted = 0
    start_time = time.perf_counter()
    for resource in data_files:
        station = resource[0]
        target = resource[1]
        data = urllib.request.urlopen(target)
        for line in range(2):
            next(data)
        for line in data:
            decoded_line = line.decode("utf-8")
            row = decoded_line.split()
            database.execute("INSERT INTO aws_data VALUES ('{0}', '{1}', '{2}', '{3}', '{4}', '{5}', '{6}', '{7}', '{8}', '{9}', '{10}', '{11}')".format(id_count, station, row[0], row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9], row[10]))
            id_count = id_count + 1
        extracted = extracted + 1
        if extracted % 300 == 0:                            ### This block provides user feedback on progress
            percent_complete = round((extracted/len(data_files))*100)
            new_time = time.perf_counter()
            time_elapsed = new_time - start_time
            time_left = round(((100/percent_complete) * time_elapsed) - time_elapsed)
            if time_left > 120:
                time_left = str(int(math.ceil(time_left / 60))) + ' minutes'
            else:
                time_left = str(time_left) + ' seconds'
            print("Percent complete: {0}%, Estimated time left: {1}".format(str(percent_complete), time_left))
    final_time = time.perf_counter()
    database.commit()
    database.close()
    print("Finished. Processed {0} datasets in {1} minutes {2} seconds.".format(str(extracted), str(round((final_time - start_time) / 60)), str(round((final_time - start_time) % 60))))

if __name__ == '__main__':
    main()