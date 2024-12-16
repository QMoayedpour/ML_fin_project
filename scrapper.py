#! /usr/bin/env python3
# coding: utf-8

from utils.scrap import scrap_speechs

import argparse
import logging as lg
import os

lg.basicConfig(level=lg.INFO)


def check_availability(file):
    #path_data_dir = os.path.join(os.getcwd(), 'data')
    try:
        if os.path.isfile(f'data/{file}'):
            lg.warning(
                f'{file} is already existing. Do you want to erase it?')
            choice = input('y/n? ')
            while choice not in ['y', 'n']:
                choice = input('You must type y or n: ')
            if choice == 'y':
                return True
            else:
                return False
        else:
            return True
    except FileNotFoundError as e:
        lg.error(e)
    except:
        lg.error('Destination unknown')


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('--scrap', action='store_true',
                        help='Decide whether to scrap data or not')
    parser.add_argument('-n', '--file_name', type=str,
                        help='Scrapped data file name')
    parser.add_argument('-l', '--lang', nargs='*', type=str, default='en',
                        help='List of languages to scrap')
    parser.add_argument('-y', '--years', nargs='*', type=int,
                        help=('Range of years to scrap. If only one value is',
                              'passed, it is considered as an upper bound.'))
    parser.add_argument('--url', type=str, default="",
                        help="If the links are already scrapped")
    parser.add_argument('--prep', action='store_true',
                        help='Decide wheter to process some data or not')
    parser.add_argument('-o', '--output', type=str,
                        default='processed_data.csv',
                        help='Processed data file name')
    parser.add_argument("--topic", type=str, default="")
    parser.add_argument("--waiter", type=int, default=10, 
                        help=("How many time you want to wait when logging the page (the more you wait, the more articles you have)"))
    return parser.parse_args()


def main():
    args = parse_arguments()
    from_url = args.url
    scrap = args.scrap
    prep = args.prep
    file_name = args.file_name
    lang = args.lang
    years = args.years
    topic = args.topic
    waiter = args.waiter
    
    scrap_speechs(lang, years, file_name, True, topic, waiter, from_url)



if __name__ == '__main__':
    main()