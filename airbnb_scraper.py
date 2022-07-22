#!/usr/bin/env python
# coding: utf-8

'''
Takes in property IDs as arguments and returns a DataFrame with the name, type, no. bedrooms, no. baths, and amenities of the properties found. 
Returns None if no properties are found.

Throws exception if property or information on property is not found.
'''

import pandas as pd
import numpy as np
import time
from urllib.request import urlopen
from urllib.error import HTTPError
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By

# Time to wait (in seconds) for loading url
WAIT_TIME = 5

def get_info(*args):
    # Initialize lists for info requested
    ids, names, types, beds, baths, amenities = [], [], [], [], [], []
    
    # Initiate webdriver (port set via service class to avoid DeprecationWarning)
    driver_path = '/usr/bin/safaridriver'
    s = Service(executable_path=driver_path)
    browser = webdriver.Safari(service=s)
    
    # For loop for processing each property by ID
    for property_id in args:
        # Tries to fetch HTML for the URL associated with the property ID, throws exception if not found
        url = 'https://www.airbnb.co.uk/rooms/' + str(property_id)
        try:
            html = urlopen(url)
            browser.get(url)
            time.sleep(WAIT_TIME)
        except HTTPError as http_error:
            print('Property {} could not be located on Airbnb ({})'.format(property_id, http_error))
            continue
        
        # Creates BeautifulSoup object
        bs = BeautifulSoup(html, 'html.parser')
        
        # Locates information on property and button element for viewing amenities, throws exception if at least one is not found
        try:
            property_name = bs.find('h1', attrs={'class': '_fecoyn4'}).get_text()
            property_description = bs.find('h2', attrs={'class': '_14i3z6h'}).get_text()
            parent = bs.find('ol', attrs={'class': 'l7n4lsf dir dir-ltr'})
            children = parent.findChildren()
            property_beds = children[4].get_text()
            property_baths = children[-1].get_text()
            amenitiesButton = browser.find_element(By.CLASS_NAME, 'b65jmrv')
        except AttributeError as attribute_error:
            print("Information on property {} could not be located, please check class names or indices for children ({})".format(property_id, attribute_error))
            continue
            
        # Splits description string to define property time
        property_type = property_description.split('hosted')[0]
        
        # Splits strings for beds and baths to get number (e.g., "1 bedroom" becomes "1")
        num_beds = property_beds.split()[0]
        num_baths = property_baths.split()[0]
        
        # Checks if bathroom description for property is formatted properly (e.g., "Toilet with sink" would become "1")
        if not num_baths.isnumeric():
            num_baths = '1'
        
        # Clicks button to view full amenities and fetches its HTML
        amenitiesButton.click()
        time.sleep(WAIT_TIME)
        amenitieshtml = browser.page_source
        amenitiesbs = BeautifulSoup(amenitieshtml, 'html.parser')
        
        # Locates amenities and stores in list, throws exception if not found
        try:
            property_amenities = amenitiesbs.findAll('div', attrs={'class': '_gw4xx4'})
        except AttributeError as attribute_error:
            print("Amenities for property {} could not be located, please check class name ({})".format(property_id, attribute_error))
            continue
        amenities_list = []
        for property_amenity in property_amenities:
            amenity = property_amenity.get_text()
            amenities_list.append(amenity)
        
        # Appends details of property to their respective lists
        ids.append(property_id)
        names.append(property_name)
        types.append(property_type)
        beds.append(num_beds)
        baths.append(num_baths)
        amenities.append(', '.join(amenities_list))
    
    # Closes browser
    browser.close()
    
    # Creates DataFrame from lists and sets its index to the 'ID' column
    info = pd.DataFrame({
        'ID': ids,
        'Name': names,
        'Type': types,
        'No. Bedrooms': beds,
        'No. Bathrooms': baths,
        'Amenities': amenities,
        })
    info.set_index('ID', inplace=True)
    
    # Returns None if no properties were found, else returns the DataFrame  
    if info.size == 0:
        return None
    else:
        return info