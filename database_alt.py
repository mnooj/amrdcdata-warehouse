import sys, mysql.connector as database, urllib.request, json, time

DATABASE_NAME = sys.argv[1]
TABLE = sys.argv[2]
USERNAME = sys.argv[3]
PASSWORD = sys.argv[4]

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
                if 'q1h3.txt' in item['name']:              ### Special handling for ATT levels - select level 3 only
                    data_files.append([name_formatted, item['url']])
        else:
            for item in record['resources']:
                if 'q1h' in item['name']:
                    data_files.append([name_formatted, item['url']])
    
    print("Connecting to database...")                           ### Build database
    try:
        connection = database.connect(
            user=USERNAME,
            password=PASSWORD,
            host="localhost",
            database=DATABASE_NAME
        )
        print("Successfully connected to database")
    except database.Error as e:
        print(f"Error connecting to database: {e}")

    cursor = connection.cursor()
    try:
        cursor.execute(f"CREATE TABLE {TABLE} (name VARCHAR(100), year INT, month INT, day INT, time INT, temperature FLOAT, pressure FLOAT, wind_speed FLOAT, wind_direction FLOAT, humidity FLOAT, delta_t FLOAT);")
        connection.commit()
        print(f"Table '{TABLE}' created")
    except database.Error as e:
        print(f"Error creating table: {e}")

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
            statement = f"INSERT INTO {TABLE} (name, year, month, day, time, temperature, pressure, wind_speed, wind_direction, humidity, delta_t) VALUES ('{station}', '{row[0]}', '{row[2]}', '{row[3]}', '{row[4]}', '{row[5]}', '{row[6]}', '{row[7]}', '{row[8]}', '{row[9]}', '{row[10]}')"
            try:
                cursor.execute(statement)
                connection.commit()
            except database.Error as e:
                print(f"Error adding entry to database: {e}")
        
        extracted = extracted + 1
        if extracted % 500 == 0:                            ### This block provides user feedback on progress
            print(f"Datasets extracted: {extracted} out of {len(data_files)}")

    final_time = time.perf_counter()    
    print(f"Finished. Processed {str(extracted)} datasets in {str(round((final_time - start_time) / 60))} minutes {str(round((final_time - start_time) % 60))} seconds.")

if __name__ == '__main__':
    main()