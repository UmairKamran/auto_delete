from helium import *
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import pandas as pd
import os
from pprint import pprint
import config

SUCCESSFULLY_DELETED = []
NOT_FOUND = []
NOT_SAFE_TO_DELETE = []
DELETE_ATTEMPTED_BUT_FAILED = []

LOGIN_LINK = config.LOGIN_LINK
USERNAME = config.USERNAME
PASSWORD = config.PASSWORD
FILE_NAME = config.FILE_NAME
COLUMN_NAME = config.COLUMN_NAME
SHEET_NAME = config.SHEET_NAME

# The code won't proceed with delete if number of packages found against an ID are greater than 5
MAX_DELETE_LIMIT = 5


def login():
    try:
        print(f'Attempting to login with username: {USERNAME} and password: {PASSWORD}')
        driver = start_chrome(url=LOGIN_LINK, headless=True)
        time.sleep(1)
        write(USERNAME, into="User name")
        write(PASSWORD, into="Password")
        time.sleep(1)
        click('sign in')
        time.sleep(1)
        click('pending cs')
        time.sleep(1)
        print("Login successful.")
        return driver
    except Exception as error:
        print("Some error occurred during login.")
        print(error)
        exit(1)


def enter_and_delete_id(driver, one_id):

    print(f"Attempting to delete ID={one_id}")
    write(one_id, into="Scan or enter")
    time.sleep(2)
    filter_btn = WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.ID, "TEST-FILTER-BUTTON")))

    driver.execute_script("(arguments[0]).click();", filter_btn)
    time.sleep(2)

    try:
        checkbox = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.ID, "select_all_packages")))
        driver.execute_script("(arguments[0]).click();", checkbox)
        time.sleep(2)
        delete_btn = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.ID, "DELETE_N_PACKAGES")))
        number_of_packages_found = delete_btn.text.split()[1]
        print(f"Number packages found for ID({one_id}) = {number_of_packages_found}")

        if int(number_of_packages_found) > MAX_DELETE_LIMIT:
            print(f"Aborting delete for ID={one_id}. Too many packages found. Something probably went wrong.")
            NOT_SAFE_TO_DELETE.append(one_id)
            return

        print("Attempting delete.")
        driver.execute_script("(arguments[0]).click();", delete_btn)
        time.sleep(2)
        click('confirm')

        print("Attempted delete. Double checking ...")
        time.sleep(2)
        double_check_delete(driver, one_id)
        time.sleep(2)

    except Exception as error:
        NOT_FOUND.append(one_id)
        print(f"No results found for ID={one_id}.")
        print(error)


def double_check_delete(driver, one_id):
    write(one_id, into="Scan or enter")
    time.sleep(2)
    filter_btn = WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.ID, "TEST-FILTER-BUTTON")))
    driver.execute_script("(arguments[0]).click();", filter_btn)
    time.sleep(2)

    try:
        # If we still find "select all packages" checkbox then ID was not deleted
        WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.ID, "select_all_packages")))
        print(f"Attempted delete unsuccessful for ID={one_id}.")
        time.sleep(2)
        DELETE_ATTEMPTED_BUT_FAILED.append(one_id)

    except Exception as error:
        SUCCESSFULLY_DELETED.append(one_id)
        print(f"Successfully deleted packages against ID={one_id}.")
        print(error)
        time.sleep(2)


def read_file():
    try:
        print("Reading excel file.")
        path = os.getcwd()
        df = pd.ExcelFile(f"{path}\{FILE_NAME}").parse(SHEET_NAME)
        tracking_ids = df[COLUMN_NAME].tolist()
        return tracking_ids

    except Exception as error:
        print(error)
        print("Error while reading from file.")
        exit(1)


def main():
    try:

        tracking_ids = read_file()
        print("Processing the following IDs : ")
        pprint(tracking_ids)
        print()

        driver = login()

        for each_id in tracking_ids:
            enter_and_delete_id(driver=driver, one_id=each_id)

        print("\n \n \n#################### FINAL RESULTS ######################### \n \n \n")

        if SUCCESSFULLY_DELETED:
            print(f"Successfully deleted the following IDS : ")
            pprint(SUCCESSFULLY_DELETED)

        if NOT_FOUND:
            print("The following IDS were not found (they may be deleted already) : ")
            pprint(NOT_FOUND)

        if NOT_SAFE_TO_DELETE:
            print("The following IDS returned too many packages and require supervision : ")
            pprint(NOT_SAFE_TO_DELETE)

        if DELETE_ATTEMPTED_BUT_FAILED:
            print("Attempted to delete the following IDS but failed : ")
            pprint(DELETE_ATTEMPTED_BUT_FAILED)

    except Exception as error:
        print("Some error occurred in main function.")
        print(error)


if __name__ == '__main__':
    main()
