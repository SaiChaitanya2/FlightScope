import os

# Base paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RAW_DIR = os.path.join(BASE_DIR, "data", "raw")
PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")
DB_PATH = os.path.join(PROCESSED_DIR, "flights.db")

# Columns to keep from raw monthly CSVs
COLUMNS_TO_KEEP = [
    'Month', 'DayofMonth', 'DayOfWeek', 'FlightDate', 'Marketing_Airline_Network',
    'Operated_or_Branded_Code_Share_Partners', 'DOT_ID_Marketing_Airline',
    'IATA_Code_Marketing_Airline', 'Flight_Number_Marketing_Airline',
    'Operating_Airline ', 'DOT_ID_Operating_Airline',
    'IATA_Code_Operating_Airline', 'Tail_Number',
    'Flight_Number_Operating_Airline', 'OriginAirportID', 'OriginAirportSeqID',
    'OriginCityMarketID', 'Origin', 'OriginCityName', 'OriginState',
    'OriginStateFips', 'OriginStateName', 'OriginWac', 'DestAirportID',
    'DestAirportSeqID', 'DestCityMarketID', 'Dest', 'DestCityName', 'DestState',
    'DestStateFips', 'DestStateName', 'DestWac', 'CRSDepTime', 'DepTime',
    'DepDelay', 'DepDelayMinutes', 'DepDel15', 'DepartureDelayGroups',
    'DepTimeBlk', 'TaxiOut', 'WheelsOff', 'WheelsOn', 'TaxiIn', 'CRSArrTime',
    'ArrTime', 'ArrDelay', 'ArrDelayMinutes', 'ArrDel15', 'ArrivalDelayGroups',
    'ArrTimeBlk', 'Cancelled', 'CancellationCode', 'Diverted', 'CRSElapsedTime',
    'ActualElapsedTime', 'AirTime', 'Flights', 'Distance', 'DistanceGroup',
    'CarrierDelay', 'WeatherDelay', 'NASDelay', 'SecurityDelay',
    'LateAircraftDelay', 'DivAirportLandings', 'Duplicate'
]
