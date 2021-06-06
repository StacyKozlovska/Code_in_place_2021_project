"""
Importing libraries
"""
import pandas as pd
import json
import six
import sys
sys.modules['sklearn.externals.six'] = six
from PIL import Image
import PIL
import urllib
import requests
import io


"""
Global values
"""
BING_MAPS_KEY = ''  # your own Bing Maps API key created on https://www.bingmapsportal.com/ , type - string


"""
Main function: get input countries and cities, calculate and visualize the shortest route to visit all destinations, 
give links to webpages with Covid-19 travel restrictions.
"""
def main():
    continents = pd.read_csv("countries/countries-continents.csv")     # path to the country-continent csv file

    name = greeting()  # greet and get a user's name
    input_values = get_input_countries()  # get country and city names from user
    country_list = input_values[0] # list of countries from get_input_countries()
    start_country = input_values[3] # string with start country from get_input_countries()
    destination_continents_values = get_country_continents_as_dict(country_list, continents)  # values returned from
                                                                                              # get_country_continents_as_dict()
    ready_web_end = destination_continents_values[2]  # dictionary {country: "continent/country",...} from
                                                      # get_country_continents_as_dict()
    get_csv_files(start_country, country_list)     # prepare csv files for each country
    start_city_coord = get_start_lon_lat(input_values)  # get start city coordinates
    city_lon_lat_dict = start_city_coord[2]  # dictionary {start_city: {'lon':longitude, 'lat': latitude}}
    lon_lat_values = get_lon_lat(input_values, city_lon_lat_dict)
    all_cities_coordinates_dict = lon_lat_values[2]   # dictionary with coordinates for all cities, including start city
    lat_lon_list = lon_lat_values[3]  # list of dictionaries with coordinates(lon,lat) of all cities in the input order
    get_best_route(all_cities_coordinates_dict, lat_lon_list)  # print optimized route, visualize route on map
    print_travel_bans_link(ready_web_end, name)  # print a list of links to webpages with travel restrictions for each country



"""
Function to greet the user, returns user's name
"""
def greeting():
    print("Hello! Here you can calculate the optimal route (for traveling by car) to visit several destination points around the world.")
    print("Also, you can get the link to the webpage with Covid-19 travel restrictions.")
    name = input("What is your name? ")
    print(f"Nice to meet you, {name}!")
    print("Let's begin!")
    print("P.S. Mind spelling and capital letters;)")
    return name


"""
Function get_input_countries() gets countries and cities from the user, returns: 
country_list - list with all input countries 
country_city - dictionary {country: cities} 
states_dict - if country is USA, dictionary {city: state} 
start_country = string, the start country 
start_city = string, the start city 
start_state = if start_country is USA, string of a start state, else: empty string
"""
def get_input_countries():
    print("Tell us more about your travel plans. What countries and cities would you like to visit? ")
    start_country = input("Starting point(country): ")
    start_city = input("Starting point(city): ")

    # if the start country is the USA, we ask for the state of the start city above
    if start_country == "USA" or start_country == "United States" or start_country == "United States of America":
        start_country = "USA"
        start_state = input("Starting point(state): ")
    else:
        start_state = ''
    
    country_list = []
    country_city = {}
    states_dict = {}
    
    while True:
        country = input("Destination country (press enter to quit input mode): ")
        if country == '':
            break

        # handles the difference in names of one country - USA, United States or
        # United States of America - to make the name uniform throughout the code 
        if country == "USA" or country == "United States" or country == "United States of America":
            country = "USA"
            states = input("Destination state: ")
            city = input("Destination city: ")
            states_dict[city] = states
            country_city[country] = city
        else:
            city = input("Destination city: ")
            if country not in country_city:
                country_city[country] = [city]
            else:
                country_city[country].append(city)

        country_list.append(country)

    return country_list, country_city, states_dict, start_country, start_city, start_state


"""
Function returns the information to use in the web link for travelbans website. It returns:
d_continents - dictionary {country: continent} 
new_country_continent - dictionary {lowercase country: lowercase continent} 
ready_web_end - dictionary {country: 'lowercase_continent/lowercase_country'} - values are ready for a web link
"""
def get_country_continents_as_dict(country_list, continents):
    d_continents = {}
    for d_country in country_list:
        if d_country == 'USA':
            d_country = 'US'

        continent = continents.loc[(continents['Country'] == d_country), 'Continent'].iloc[0]

        if d_country == 'US':
            d_country = 'USA'
        d_continents[d_country] = continent

    web_continents = {
          'Europe': 'europe', 
          'Asia': 'asia', 
          'North America': 'north-america', 
          'South America': 'south-america', 
          'Africa': 'africa', 
          'Oceania': 'oceania-australia', 
          'Australia': 'oceania-australia'
    }
    new_country_continent = {}
    ready_web_end = {}

    for country in d_continents:
        continent_from_dict = d_continents[country]
        new_cont = web_continents[continent_from_dict]
        new_country = country.lower()
        new_country = new_country.replace(' ', '-')
        new_country_continent[new_country] = new_cont
        ready_web_end[country] = new_cont + "/" + new_country

    return d_continents, new_country_continent, ready_web_end


"""
Function gets and transforms(changes names of columns) csv files of every input country. ALso it handles USA and 
Czech Republic (user can write the name differently) to get right csv files. After running this function we can work 
with needed csv files without changing something.
"""
def get_csv_files(start_country, country_list):
    df_start = pd.read_csv("countries/" + start_country + ".csv")
    df_start.rename(columns={"City": "city", "Latitude": "lat", "Longitude": "lon", 
                             "Population": "popul"}, inplace=True)
    df_start["country"] = start_country
    df_start.to_csv("countries/" + start_country + ".csv", index=False)

    for country in country_list:
        if country == "Czech Republic":  # handles the difference in names of one country -
                                         # Czech Republic and Czechia - to access the right csv file
            df = pd.read_csv("countries/Czechia.csv")
            df.rename(
                columns={
                     "City": "city", 
                     "Latitude": "lat", 
                     "Longitude": "lon", 
                     "Population": "popul", 
                     "State": "state"
                } 
                , inplace=True
            )        
            df["country"] = "Czechia"
            df.to_csv("countries/Czechia.csv", index=False)
        else:
            df = pd.read_csv("countries/" + country + ".csv")
            df.rename(
                columns={
                     "City":"city", 
                     "Latitude": "lat", 
                     "Longitude": "lon", 
                     "Population": "popul", 
                     "State":"state"
                 }
                 , inplace=True
            )            
            df["country"] = country
            df.to_csv("countries/" + country + ".csv", index=False)


"""
Function get_start_lon_lat(input_values) takes in values returned from get_input_countries() - input_values - as an
argument and returns:
start_city_lon - start city longitude as a float
start_city_lat - start city latitude as a float
city_coordinates_dict - dictionary {'city': {'lon': longitude, 'lat': latitude}}
"""
def get_start_lon_lat(input_values):
    start_country = input_values[3]
    start_city = input_values[4]
    start_state = input_values[5]
    city_coordinates_dict = {}

    if start_country == 'USA':
        city_lon_lat_dict = {}
        df_start = (
            pd.read_csv("countries/" + start_country + ".csv")
            [lambda x: x['state'] == str(start_state)]
        )
        
        start_city_loc = df_start[df_start['city'] == str(start_city)].index.values
        start_city_lon = df_start.loc[start_city_loc, 'lon'].iloc[0]
        start_city_lat = df_start.loc[start_city_loc, 'lat'].iloc[0]
        city_lon_lat_dict['lon'] = start_city_lon
        city_lon_lat_dict['lat'] = start_city_lat
        city_coordinates_dict[start_city] = city_lon_lat_dict
    else:
        city_lon_lat_dict = {}
        df_start = pd.read_csv("countries/" + start_country + ".csv")
        start_city_loc = df_start[df_start['city'] == start_city].index.values
        start_city_lon = df_start.loc[start_city_loc, 'lon'].iloc[0]
        start_city_lat = df_start.loc[start_city_loc, 'lat'].iloc[0]
        city_lon_lat_dict['lon'] = start_city_lon
        city_lon_lat_dict['lat'] = start_city_lat
        city_coordinates_dict[start_city] = city_lon_lat_dict

    return start_city_lon, start_city_lat, city_coordinates_dict


"""
Function get_lon_lat(input_values, city_coordinate_dict) takes in values returned from get_input_countries() - 
input_values - and the dictionary {city: {'lon': longitude, 'lat': latitude}} as arguments and returns:
cities_lon - dictionary {city: longitude,...} for every input city
cities_lat - dictionary {city: latitude,...} for every input city
all_cities_coord_dict - dictionary of coordinates of all cities {city: {'lon': longitude, 'lat': latitude},...}
"""
def get_lon_lat(input_values, city_coordinate_dict):
    country_city = input_values[1]
    states_dict = input_values[2]
    all_cities_coord_dict = city_coordinate_dict
    cities_lon = {}
    cities_lat = {}
    directory_city_dict = {}

    for country in country_city:
        new_city = country_city[country]
        
        # handles the difference in names of one country -
        # (Czech Republic and Czechia) - it helps to access the right csv file 
        if country == "Czech Republic":
            country = "Czechia"
            directory_city_dict["countries/" + country + ".csv"] = new_city
        else:
            directory_city_dict["countries/" + country + ".csv"] = new_city

        if country == "USA":
            directory_city_dict["countries/" + country + ".csv"] = states_dict

    for directory in directory_city_dict.keys():
        df = pd.read_csv(directory)
        city = directory_city_dict[directory]
        
        if directory == "countries/USA.csv":
            for us_city in city.keys():
                us_state = city[us_city]
                loc_dict = {}
                city_lon = df.loc[(df['state'] == us_state) & (df['city'] == us_city), 'lon'].iloc[0]
                city_lat = df.loc[(df['state'] == us_state) & (df['city'] == us_city), 'lat'].iloc[0]
                cities_lon[us_city] = city_lon
                cities_lat[us_city] = city_lat
                loc_dict['lon'] = city_lon
                loc_dict['lat'] = city_lat
        else:
            loc_dict = {}           
            for i in range(1, len(city)+1):
                i -= 1
                get_city = city[i]
                city_lon = df.loc[(df['city'] == get_city), 'lon'].iloc[0]
                cities_lon[get_city] = city_lon
                city_lat = df.loc[(df['city'] == get_city), 'lat'].iloc[0]
                cities_lat[get_city] = city_lat
                loc_dict['lon'] = city_lon
                loc_dict['lat'] = city_lat

    for city in cities_lon.keys():
        temp_coord = {}
        temp_coord['lon'] = cities_lon[city]
        temp_coord['lat'] = cities_lat[city]
        all_cities_coord_dict[city] = temp_coord

    lat_lon_list = []
    for coordinates in all_cities_coord_dict.values():
        lat_lon_list.append(coordinates)

    return cities_lon, cities_lat, all_cities_coord_dict, lat_lon_list


"""
Function get_url_link(test_routeUrl, imagery_url, all_cities_coord_dict) is used inside the function get_distance().
It returns strings with API links with the coordinates of all cities. These strings will be used to get an optimized 
route from Bing Maps and visualize a map with that route.
test_routeUrl - complete string for getting optimized route
imagery_url - complete string for getting png map
wp_city_dict - dictionary {waypoint+number : city,...}, used to print out the route for the user to read
"""
def get_url_link(route_url, all_cities_coord_dict, lat_lon_list):
    wp_city_dict = {}
    count = 0
    for i in range(len(lat_lon_list)):
        if count == 0:
            route_url += "wp."
        else:
            route_url += "&wp."

        route_url += str(count)
        route_url += "="
        route_url += str(lat_lon_list[count]['lat'])
        route_url += ","
        route_url += str(lat_lon_list[count]['lon'])
        city_name = list(all_cities_coord_dict.keys())[count]
        wp_name = "wp." + str(count)
        wp_city_dict[wp_name] = city_name
        count += 1

    route_url += "&wp."
    route_url += str(count)
    route_url += "="
    route_url += str(lat_lon_list[0]['lat'])
    route_url += ","
    route_url += str(lat_lon_list[0]['lon'])
    route_url += "&optwp=true&optimize=timeWithTraffic"
    route_url += "&key="
    route_url += BING_MAPS_KEY

    return route_url, wp_city_dict


"""
Function get_image_url_link(imagery_url, all_cities_coord_dict, cities_in_route) takes as arguments the beginning of the
Bing Maps imagery link (imagery_url), dictionary {city: {'lat': latitude, 'lon': longitude},...}, and list of cities 
in optimized order (cities_in_route). This function returns the url link used to get the map in the png format with the
optimized route on.
"""
def get_image_url_link(imagery_url, all_cities_coord_dict, cities_in_route):
    new_lat_lon_list = []
    
    for city in cities_in_route:
        coord = all_cities_coord_dict[city]
        city_lat = coord['lat']
        city_lon = coord['lon']
        temp_dict = {}
        temp_dict['lat'] = city_lat
        temp_dict['lon'] = city_lon
        new_lat_lon_list.append(temp_dict)

    count = 0
    for city_coord in range(len(new_lat_lon_list)):
        if count == 0:
            imagery_url += "wp."
        else:
            imagery_url += "&wp."

        imagery_url += str(count)
        imagery_url += "="
        imagery_url += str(new_lat_lon_list[count]['lat'])
        imagery_url += ","
        imagery_url += str(new_lat_lon_list[count]['lon'])
        imagery_url += ";37;"
        city_name = cities_in_route[count]
        imagery_url += str(city_name)
        count += 1

    imagery_url += "&wp."
    imagery_url += str(count)
    imagery_url += "="
    imagery_url += str(new_lat_lon_list[0]['lat'])
    imagery_url += ","
    imagery_url += str(new_lat_lon_list[0]['lon'])
    imagery_url += ";37"
    imagery_url += "&key="
    imagery_url += BING_MAPS_KEY

    return imagery_url


"""
Function get_best_route(all_cities_coord_dict) takes in the dictionary {city: {'lon':longitude, 'lat':latitude},...} 
as an argument and returns the optimized route and the map with that route on
"""
def get_best_route(all_cities_coord_dict, lat_lon_list):
    routeUrl_start = "http://dev.virtualearth.net/REST/V1/Routes/Driving?"
    imagery_url = "https://dev.virtualearth.net/REST/v1/Imagery/Map/Road/Routes?"

    routeUrl, wp_city_dict = get_url_link(routeUrl_start, all_cities_coord_dict, lat_lon_list)

    request = urllib.request.Request(routeUrl)
    response = urllib.request.urlopen(request)
    r = response.read().decode(encoding="utf-8")
    result = json.loads(r)
    
    optimized_route = result["resourceSets"][0]["resources"][0]["waypointsOrder"]
    print("Your optimized route is:")
    
    count_print = 1
    new_optimized_route = optimized_route[:-1]
    cities_in_route = []
    for point in new_optimized_route:
        city = wp_city_dict[point]
        print(f"{count_print}) {city}")
        count_print += 1
        cities_in_route.append(city)
    print(f" And then back to {wp_city_dict['wp.0']};)")

    image_Url = get_image_url_link(imagery_url, all_cities_coord_dict, cities_in_route)

    itineraryItems = result["resourceSets"][0]["resources"][0]["travelDistance"]
    print("Total distance is", itineraryItems, 'km')

    response = requests.get(image_Url)
    image_bytes = io.BytesIO(response.content)
    img = PIL.Image.open(image_bytes)
    img.show()
    image_bytes.close()


"""
Function print_travel_bans_link(ready_web_end) takes in ready_web_end -  a dictionary {country: "continent/country"} -
as an argument and prints out links for all countries that the user has entered. 
"""
def print_travel_bans_link(ready_web_end, name):
    travel_bans_link = "https://travelbans.org/"
    for country in ready_web_end.keys():
        print ("Check out travel restrictions for", country, "here: ")
        travel_link = travel_bans_link + ready_web_end[country]
        print(travel_link)
    print (f"Have a nice trip, {name}!")


if __name__ ==  "__main__":
    main()
