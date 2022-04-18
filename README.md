# IMDB-Popular-Movie-Crawler
Program Name: IMDB Popular Movie Crawler for SI 507
Student: Amanda Wang
Uniqname: awwangaw

Project Description:
This project allows users to interact with and view different reports of IMDB popular movie information and analysis. Uswers will also be able to play an interactive "game" that checks to see if two actors have acted in the same popular movie before, and including the name of that movie if applicable.

Imported Tools:
This program uses Flask (render_template, request), requests, Beautiful Soup, sqlite3, and plotly. There are also several additional python built-in packages that are used.

This program uses the IMDB API. 

Instructions:
Please ensure that all of the required packages are installed before running the python file.

Download the python file: finalproject.py. Use the command python finalproject.py in the command line to run the program.

As a note, it might take some time for the program to initialize itself. Please be patient during this time. Reading the cache file and generating tables in the database is why this step may take a couple minutes.

After the program is initialized, users will be able to go to their web browser address bar and type in: localhost:5000

This will take users to the home page of the application. There are five links that are presented in the home page. Users will be able to click on these links to interact with the program. The first four links on the home page gives users reports in graph formats of different IMDB popular movie analysis. The fifth link on the home page will allow users to choose two actors from drop-down lists. The program will then print on the screen whether those two chosen actors have acted in the same popular movie together before with the respective movie name if applicable.

Here is a link to a  video that demonstrates how a user could interact with this program:
