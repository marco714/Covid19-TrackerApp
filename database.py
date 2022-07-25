from credentials_database import hostname, database, username, pwd, port_id
import psycopg2
import psycopg2.extras
import io
from sqlalchemy import create_engine
import pandas.io.sql as psql
import numpy as np
from psycopg2.extensions import register_adapter, AsIs

psycopg2.extensions.register_adapter(np.int64, psycopg2._psycopg.AsIs)
# psycopg2.extensions.register_adapter(np.int32, psycopg2._psycopg.AsIs)


class Database:
    def __init__(self):
        self.conn = psycopg2.connect(
            database=database, user=username, password=pwd, host=hostname, port=port_id
        )

        self.cur = self.conn.cursor()

    def close_cursor(self):
        self.cur.close()

    def close_connection(self):
        self.conn.close()

    def insert_infection(self, raw_data_weekly_infection):

        df_columns = list(raw_data_weekly_infection)
        # create (col1,col2,...)
        columns = ",".join(df_columns)

        # create VALUES('%s', '%s",...) one '%s' per column
        values = "VALUES({})".format(",".join(["%s" for _ in df_columns]))

        # create INSERT INTO table (columns) VALUES('%s',...)
        insert_stmt = "INSERT INTO {} ({}) {}".format("infections", columns, values)

        psycopg2.extras.execute_batch(
            self.cur, insert_stmt, raw_data_weekly_infection.values
        )
        self.conn.commit()

        print("success infection insert")
        return

    def insert_recoveries(self, raw_data_weekly_recoveries):

        df_columns = list(raw_data_weekly_recoveries)
        # create (col1,col2,...)
        columns = ",".join(df_columns)

        # create VALUES('%s', '%s",...) one '%s' per column
        values = "VALUES({})".format(",".join(["%s" for _ in df_columns]))

        # create INSERT INTO table (columns) VALUES('%s',...)
        insert_stmt = "INSERT INTO {} ({}) {}".format("recoveries", columns, values)

        psycopg2.extras.execute_batch(
            self.cur, insert_stmt, raw_data_weekly_recoveries.values
        )
        self.conn.commit()

        print("success recoveries insert")
        return

    def insert_deaths(self, raw_data_weekly_deaths):

        df_columns = list(raw_data_weekly_deaths)
        # create (col1,col2,...)
        columns = ",".join(df_columns)

        # create VALUES('%s', '%s",...) one '%s' per column
        values = "VALUES({})".format(",".join(["%s" for _ in df_columns]))

        # create INSERT INTO table (columns) VALUES('%s',...)
        insert_stmt = "INSERT INTO {} ({}) {}".format("deaths", columns, values)

        psycopg2.extras.execute_batch(
            self.cur, insert_stmt, raw_data_weekly_deaths.values
        )
        self.conn.commit()

        print("success deaths")
        return

    def selecting_recoveries(self):
        data_recoveries = psql.read_sql_query("select * from recoveries", self.conn)
        return data_recoveries

    def selecting_infection(self):
        data_infection = psql.read_sql_query("select * from infections", self.conn)
        return data_infection

    def selecting_deaths(self):
        data_deaths = psql.read_sql_query("select * from deaths", self.conn)
        return data_deaths

    def selecting_vaccination(self):
        data_vaccination = psql.read_sql_query("select * from vaccination", self.conn)
        return data_vaccination

    def create_infection(self):
        create_script = """CREATE TABLE IF NOT EXISTS infections (
            dateinfection DATE,
            infection int
        )
        """

        self.cur.execute(create_script)
        self.conn.commit()

    def create_recoveries(self):
        create_script = """CREATE TABLE IF NOT EXISTS recoveries (
            daterecoveries DATE,
            recoveries int
        )
        """

        self.cur.execute(create_script)
        self.conn.commit()

    def create_deaths(self):
        create_script = """CREATE TABLE IF NOT EXISTS deaths (
            datedeaths DATE,
            deaths int
        )
        """

        self.cur.execute(create_script)
        self.conn.commit()

    def create_barangay_infection(self):
        create_script = """CREATE TABLE IF NOT EXISTS infection_barangay (
            dateinfection DATE,
            age int,
            gender varchar(10),
            zones varchar(10),
            address varchar(100)
        )
        """

        self.cur.execute(create_script)
        self.conn.commit()

    def create_barangay_recoveries(self):
        create_script = """CREATE TABLE IF NOT EXISTS recoveries_barangay (
            daterecoveries DATE,
            age int,
            gender varchar(10),
            zones varchar(10),
            address varchar(100)
        )
        """

        self.cur.execute(create_script)
        self.conn.commit()

    def create_barangay_deaths(self):
        create_script = """CREATE TABLE IF NOT EXISTS deaths_barangay (
            datedeaths DATE,
            age int,
            gender varchar(10),
            zones varchar(50),
            address varchar(100)
        )
        """

        self.cur.execute(create_script)
        self.conn.commit()

    def selecting_barangay_infection(self):
        data_barangay_infection = psql.read_sql_query(
            "select * from infection_barangay", self.conn
        )
        return data_barangay_infection

    def selecting_barangay_recoveries(self):
        data_barangay_recoveries = psql.read_sql_query(
            "select * from recoveries_barangay", self.conn
        )
        return data_barangay_recoveries

    def selecting_barangay_deaths(self):
        data_barangay_deaths = psql.read_sql_query(
            "select * from deaths_barangay", self.conn
        )
        return data_barangay_deaths

    def insert_create_barangay_infection(self, zone_infection_barangay):

        df_columns = list(zone_infection_barangay)
        # create (col1,col2,...)
        columns = ",".join(df_columns)

        # create VALUES('%s', '%s",...) one '%s' per column
        values = "VALUES({})".format(",".join(["%s" for _ in df_columns]))

        # create INSERT INTO table (columns) VALUES('%s',...)
        insert_stmt = "INSERT INTO {} ({}) {}".format(
            "infection_barangay", columns, values
        )

        psycopg2.extras.execute_batch(
            self.cur, insert_stmt, zone_infection_barangay.values
        )
        self.conn.commit()

        print("success barangay infection")
        return

    def insert_create_barangay_recoveries(self, zone_recoveries_barangay):

        df_columns = list(zone_recoveries_barangay)
        # create (col1,col2,...)
        columns = ",".join(df_columns)

        # create VALUES('%s', '%s",...) one '%s' per column
        values = "VALUES({})".format(",".join(["%s" for _ in df_columns]))

        # create INSERT INTO table (columns) VALUES('%s',...)
        insert_stmt = "INSERT INTO {} ({}) {}".format(
            "recoveries_barangay", columns, values
        )

        psycopg2.extras.execute_batch(
            self.cur, insert_stmt, zone_recoveries_barangay.values
        )
        self.conn.commit()

        print("success barangay recoveries")
        return

    def insert_create_barangay_deaths(self, zone_deaths_barangay):

        df_columns = list(zone_deaths_barangay)
        # create (col1,col2,...)
        columns = ",".join(df_columns)

        # create VALUES('%s', '%s",...) one '%s' per column
        values = "VALUES({})".format(",".join(["%s" for _ in df_columns]))

        # create INSERT INTO table (columns) VALUES('%s',...)
        insert_stmt = "INSERT INTO {} ({}) {}".format(
            "deaths_barangay", columns, values
        )

        psycopg2.extras.execute_batch(
            self.cur, insert_stmt, zone_deaths_barangay.values
        )
        self.conn.commit()

        print("success barangay deaths")
        return

    def insert_row_infection(self, num_infected, date_infected):

        insert_script = (
            "INSERT INTO infections(dateinfection, infection) VALUES (%s, %s)"
        )
        insert_value = (date_infected, num_infected)

        self.cur.execute(insert_script, insert_value)
        self.conn.commit()

        print("Successfully Inserted row Infection")

    def insert_row_recoveries(self, num_recoveries, date_recoveries):

        insert_script = (
            "INSERT INTO recoveries(daterecoveries, recoveries) VALUES (%s, %s)"
        )
        insert_value = (date_recoveries, num_recoveries)

        self.cur.execute(insert_script, insert_value)
        self.conn.commit()

        print("Successfully Inserted row Recoveries")

    def create_vaccination(self):
        create_script = """CREATE TABLE IF NOT EXISTS vaccination (
                datevaccination DATE,
                firstdose int,
                seconddose int,
                thirddose int
        )
        """
        print("Successfully Created Vaccination")
        self.cur.execute(create_script)
        self.conn.commit()

    def insert_vaccination(self, raw_data_weekly_vaccination):

        df_columns = list(raw_data_weekly_vaccination)
        # create (col1,col2,...)
        columns = ",".join(df_columns)

        # create VALUES('%s', '%s",...) one '%s' per column
        values = "VALUES({})".format(",".join(["%s" for _ in df_columns]))

        # create INSERT INTO table (columns) VALUES('%s',...)
        insert_stmt = "INSERT INTO {} ({}) {}".format("vaccination", columns, values)

        psycopg2.extras.execute_batch(
            self.cur, insert_stmt, raw_data_weekly_vaccination.values
        )
        self.conn.commit()

        print("success vaccinations insert")
        return

    def selecting_zones(self):
        data_zones = psql.read_sql_query("select * from zones", self.conn)
        return data_zones

    def create_zones(self):
        create_script = """CREATE TABLE IF NOT EXISTS zones (
            zone varchar(30),
            male int,
            female int
        )
        """
        print("fully zones")
        self.cur.execute(create_script)
        self.conn.commit()

    def insert_zones(self, raw_data_zones):

        df_columns = list(raw_data_zones)
        # create (col1,col2,...)
        columns = ",".join(df_columns)

        # create VALUES('%s', '%s",...) one '%s' per column
        values = "VALUES({})".format(",".join(["%s" for _ in df_columns]))

        # create INSERT INTO table (columns) VALUES('%s',...)
        insert_stmt = "INSERT INTO {} ({}) {}".format("zones", columns, values)

        psycopg2.extras.execute_batch(
            self.cur, insert_stmt, raw_data_zones.values
        )
        self.conn.commit()

        print("success zones insert")
        return

