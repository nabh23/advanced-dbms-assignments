import psycopg2 as pg
import argparse
import csv
import time

# queries to create all the tables

NUM_TUPLES = 10000
TRACK_REPLICA_TABLE = 'public."TrackReplica"'

tables = {
    
"Album":"""CREATE TABLE IF NOT EXISTS "Album"
(
    "AlbumId" INT NOT NULL,
    "Title" VARCHAR(160) NOT NULL,
    "ArtistId" INT NOT NULL,
    CONSTRAINT "PK_Album" PRIMARY KEY  ("AlbumId")
);""",

"Artist":"""CREATE TABLE IF NOT EXISTS "Artist"
(
    "ArtistId" INT NOT NULL,
    "Name" VARCHAR(120),
    CONSTRAINT "PK_Artist" PRIMARY KEY  ("ArtistId")
);""",

"Customer":"""CREATE TABLE IF NOT EXISTS "Customer"
(
    "CustomerId" INT NOT NULL,
    "FirstName" VARCHAR(40) NOT NULL,
    "LastName" VARCHAR(20) NOT NULL,
    "Company" VARCHAR(80),
    "Address" VARCHAR(70),
    "City" VARCHAR(40),
    "State" VARCHAR(40),
    "Country" VARCHAR(40),
    "PostalCode" VARCHAR(10),
    "Phone" VARCHAR(24),
    "Fax" VARCHAR(24),
    "Email" VARCHAR(60) NOT NULL,
    "SupportRepId" INT,
    CONSTRAINT "PK_Customer" PRIMARY KEY  ("CustomerId")
);""",

"Employee":"""CREATE TABLE IF NOT EXISTS "Employee"
(
    "EmployeeId" INT NOT NULL,
    "LastName" VARCHAR(20) NOT NULL,
    "FirstName" VARCHAR(20) NOT NULL,
    "Title" VARCHAR(30),
    "ReportsTo" INT,
    "BirthDate" TIMESTAMP,
    "HireDate" TIMESTAMP,
    "Address" VARCHAR(70),
    "City" VARCHAR(40),
    "State" VARCHAR(40),
    "Country" VARCHAR(40),
    "PostalCode" VARCHAR(10),
    "Phone" VARCHAR(24),
    "Fax" VARCHAR(24),
    "Email" VARCHAR(60),
    CONSTRAINT "PK_Employee" PRIMARY KEY  ("EmployeeId")
);""",

"Genre":"""CREATE TABLE IF NOT EXISTS "Genre"
(
    "GenreId" INT NOT NULL,
    "Name" VARCHAR(120),
    CONSTRAINT "PK_Genre" PRIMARY KEY  ("GenreId")
);""",

"Invoice":"""CREATE TABLE IF NOT EXISTS "Invoice"
(
    "InvoiceId" INT NOT NULL,
    "CustomerId" INT NOT NULL,
    "InvoiceDate" TIMESTAMP NOT NULL,
    "BillingAddress" VARCHAR(70),
    "BillingCity" VARCHAR(40),
    "BillingState" VARCHAR(40),
    "BillingCountry" VARCHAR(40),
    "BillingPostalCode" VARCHAR(10),
    "Total" NUMERIC(10,2) NOT NULL,
    CONSTRAINT "PK_Invoice" PRIMARY KEY  ("InvoiceId")
);""",

"InvoiceLine":"""CREATE TABLE IF NOT EXISTS "InvoiceLine"
(
    "InvoiceLineId" INT NOT NULL,
    "InvoiceId" INT NOT NULL,
    "TrackId" INT NOT NULL,
    "UnitPrice" NUMERIC(10,2) NOT NULL,
    "Quantity" INT NOT NULL,
    CONSTRAINT "PK_InvoiceLine" PRIMARY KEY  ("InvoiceLineId")
);""",

"MediaType":"""CREATE TABLE IF NOT EXISTS "MediaType"
(
    "MediaTypeId" INT NOT NULL,
    "Name" VARCHAR(120),
    CONSTRAINT "PK_MediaType" PRIMARY KEY  ("MediaTypeId")
);""",

"Playlist":"""CREATE TABLE IF NOT EXISTS "Playlist"
(
    "PlaylistId" INT NOT NULL,
    "Name" VARCHAR(120),
    CONSTRAINT "PK_Playlist" PRIMARY KEY  ("PlaylistId")
);""",

"PlaylistTrack":"""CREATE TABLE IF NOT EXISTS "PlaylistTrack"
(
    "PlaylistId" INT NOT NULL,
    "TrackId" INT NOT NULL,
    CONSTRAINT "PK_PlaylistTrack" PRIMARY KEY  ("PlaylistId", "TrackId")
);""",

"Track":"""CREATE TABLE IF NOT EXISTS "Track"
(
    "TrackId" INT NOT NULL,
    "Name" VARCHAR(200) NOT NULL,
    "AlbumId" INT,
    "MediaTypeId" INT NOT NULL,
    "GenreId" INT,
    "Composer" VARCHAR(220),
    "Milliseconds" INT NOT NULL,
    "Bytes" INT,
    "UnitPrice" NUMERIC(10,2) NOT NULL,
    CONSTRAINT "PK_Track" PRIMARY KEY  ("TrackId")
);""",

}

# function to load the data into the relevant table in the database

def load(arguments):

    with pg.connect(host = arguments.host, dbname = arguments.dbname, user = arguments.user, password = arguments.password) as connection:

        # setup a cursor
        with connection.cursor() as cursor:

            # create a new table if it doesn't exist
            cursor.execute(tables[arguments.table])

            table = 'public."' + arguments.table + '"'

            # truncate table
            cursor.execute("TRUNCATE TABLE %s CASCADE" % table)

            # extract operation type argument
            insert_type = arguments.insert_type
            if insert_type == 'Single_Inserts':
                perform_standard_inserts(arguments, cursor, table, connection)
            elif insert_type == 'PostgreSQL_COPY':
                perform_postgres_bulk_insert(arguments, cursor, table, connection)
            elif insert_type == 'SQL_Batch_Insert':
                perform_sql_batch_inserts(arguments, cursor, table, connection)
            elif insert_type == 'INSERT_SELECT':
                perform_insert_select(arguments, cursor, table, connection)
            else:
                print("Unknown Operation!")
            
    print('Data loaded succesfully!')

#  function to perform insert/select type of insert
def perform_insert_select(arguments, cursor, table, connection):
    # open the file to read data from
    with open(arguments.file) as data:
        # skip the header
        next(data)     
        # truncate source table
        cursor.execute("TRUNCATE TABLE " + TRACK_REPLICA_TABLE)         
        # populate source table                                  
        cursor.copy_from(data, TRACK_REPLICA_TABLE, sep = ',', size = NUM_TUPLES) 
        connection.commit()
    start = time.time()
    # populate destination/target table
    cursor.execute("INSERT INTO " + table + " SELECT * FROM " + TRACK_REPLICA_TABLE)
    connection.commit()
    end = time.time()
    print_metrics(start, end)

# function to perform bulk insert using PostgreSQL COPY FROM operation
def perform_postgres_bulk_insert(arguments, cursor, table, connection):
    # open the csv file
    with open(arguments.file) as data:
        # skip the header
        next(data)                                                
        start = time.time()
        # load data into the table
        cursor.copy_from(data, table, sep = ',', size = NUM_TUPLES)   
        connection.commit()
        end = time.time()
        print_metrics(start, end)

# function to perform standard SQL (sequential) inserts
def perform_standard_inserts(arguments, cursor, table, connection):
    insert_command = ""
    # open the CSV file
    with open(arguments.file) as data:
        # read the file as CSV
        csv_reader = csv.reader(data, delimiter = ',')
        # skip the header
        next(csv_reader)
        # concat INSERT statements for each row
        for row in csv_reader:
            insert_command += "INSERT INTO " + table + " VALUES (" + get_values_string(row) + ");"
        start = time.time()
        # execute the insert statements on the database
        cursor.execute(insert_command)
        connection.commit()
        end = time.time()
        print_metrics(start, end)  

# function to perform batch inserts using standard SQL syntax
def perform_sql_batch_inserts(arguments, cursor, table, connection):
    insert_command = ""
    values_batch_string = ""
    # open the CSV file
    with open(arguments.file) as data:
        # read the file as CSV
        csv_reader = csv.reader(data, delimiter = ',')
        # skip the header
        header_row = next(csv_reader)
        num_columns = len(header_row)
        counter = 0
        # for each row in the file create a batch of counter % batch_size records
        for row in csv_reader:
            counter += 1 
            values_batch_string += "(" + get_values_string(row) + "),"
            if counter % arguments.batch_size == 0:
                insert_command += "INSERT INTO " + table + " VALUES " + values_batch_string[:-1] + ";"
                values_batch_string = ""

        start = time.time()
        # execute the inserts
        cursor.execute(insert_command)
        connection.commit()
        end = time.time()
        print_metrics(start, end)  

# function to create the values string for an INSERT statement based on a row of data
def get_values_string(row):
    result = ""
    for column in row:
        result += ",'" + column + "'"
    return result[1:]

# function to create the formatter string for an INSERT statement based on the number of columns
def get_values_formatter_string(num_columns):
    result = ""
    counter = 0
    while counter < num_columns:
        result += "%s, "
        counter += 1
    return result[:-2]

# function to print the time and throughput metrics for an operation
def print_metrics(start_time, end_time):
    time_taken = end_time - start_time
    print("Time for data inserts:", time_taken)
    print("Throughput:", NUM_TUPLES/time_taken)


# main function
def main():
    help_string = ("Load the data from .csv file into its respective table.\n "
                   "Example run command:\n  "
                   "python load_script.py localhost Chinook_IMT563 <user> <password>\n "
                   "csv_output/synth-0000.csv Track Single_Inserts <batch_size>")
    parser = argparse.ArgumentParser(description = help_string)

    # read the information from command line

    parser.add_argument('host', metavar = 'host', type = str, help = 'host name (database)')
    parser.add_argument('dbname', metavar = 'dbname', type = str, help = 'name of the database')
    parser.add_argument('user', metavar = 'user', type = str, help = 'user name (database)')
    parser.add_argument('password', metavar = 'password', type = str, help = 'password (database)')

    parser.add_argument('file', metavar = 'file', type = str, help = 'name/path of the file')
    parser.add_argument('table', metavar = 'table', type = str, help = 'name of the table')

    parser.add_argument('insert_type', metavar = 'insert_type', type = str, 
        help = 'type of insert to perform', choices = ['Single_Inserts', 'SQL_Batch_Insert', 
        'PostgreSQL_COPY', 'INSERT_SELECT'])

    parser.add_argument('batch_size', metavar = 'batch_size', type = int, help = 'batch size for bulk insert',
        default = -1, nargs = '?')

    arguments = parser.parse_args()

    load(arguments)

if __name__ == '__main__':
    main()
