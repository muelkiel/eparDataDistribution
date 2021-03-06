#app/views.py

"""
Copyright 2018 Evans Policy Analysis and Research Group (EPAR)

This project is licensed under the 3-Clause BSD License. Please see the 
license.txt file for more information.
"""
from app import app
from sqlalchemy.sql import select
from sqlalchemy import and_, or_
from os import environ
from flask import render_template, request, Response
from app.database import db_session
from app.models import Estimates,GenCons
from app.dbhelper import formHandler
from app.dlhelper import make_csv

@app.route('/', methods={"GET","POST"})
def index():
	"""
	Handles requests to the main page of the website

	This function handles all of the requests to the default page it takes 
	no parameters, but relies on the request.form global for the flask
	session to populate the indicators for the selected category

	:returns: HTML file representing the index page
	"""

	# Creating the variables to be used throughout the method
	indicators=[] # the list of indicators to display
	goDisabled = True 

	# These database queries are for populating the filter lists for indicator
	# category, georgraphy, and years
	
	indicatorCategory = [r.indicatorCategory for r in
			db_session.query(Estimates.indicatorCategory).distinct()]
	years = ["All Years", "Most Recent Survey"]
	geography = []

	# If this page was accessed using post then request.form should not be 
	# empty. In which case this code block will get the list of indicator names
	# to be displayed in the indicators filter.
	if request.form:
		selectedCategories = request.form.getlist('indicatorCategory')
		if selectedCategories:
			# Get a list of all of the geographies
			geography = [r.geography for r in 
					db_session.query(Estimates.geography).distinct()]
			# Get a list of all indicators in the selected categories
			indicators = [r.indicatorName for r in
				db_session.query(
					Estimates.indicatorName).distinct().filter(
						Estimates.indicatorCategory.in_(selectedCategories))]
			# If the db query returned something, enable the go button
			if len(indicators) > 0:
				goDisabled = False
	
	return render_template("index.html",indicators=indicators, 
		geography=geography, indicatorCategory=indicatorCategory, 
		goDisabled=goDisabled)

@app.route('/login')
def login():
	"""
	Place holder for a login page

	This will be where any login handling will be done when the login
	system is created

	:returns: HTML page for displaying a login screen. 
	"""
	return render_template("login.html")

@app.route('/results', methods={"POST"})
def results():
	"""
	Creates the results page

	Passes the filter state from the index page to the form handler function
	before passing the results to the JINJA Template for rendering into an
	HTML page which is returned. Requires the request object to have the
	necessary filters.

	:returns: an HTML page to be displayed by the website
	"""
	indicators = formHandler(request, db_session)
	# Check if anything is returned from the formHandler. If no, then show the
	# error page
	if not indicators:
		return render_template("no-inds.html"), 406

	return render_template("results.html", indicators=indicators)

@app.route('/get-csv',methods={"GET","POST"})
def get_csv():
	"""
	Handles requests to download CSV Files containing the estimates

	Passes the state of the filters on the index page to the formHandler 
	function. It then collates the results into a CSV file which is
	then offered as a download by the website.

	:returns: a Response object containing a CSV of the required variables
	"""
	# Get the estimates from the formhandler
	indicators = formHandler(request, db_session)

	# Check if any indicators were selected
	if not indicators:
		return render_template("no-inds.html"), 406

	# Get the headers based on the columns of the database
	headers = Estimates.__table__.columns.keys()
	headers = headers[1:]

	#Generate a string which is the final csv 
	csv = make_csv(headers, indicators)
	
	return Response(csv, mimetype="text/csv",
			headers={"Content-Disposition": 
				"attachment;filename=indicator_estimates.csv"})

@app.route('/about-data/')
def about_data():
	"""
	Creates the About Data page

	Gets the general constructions decisions from the database and passes them
	to the template before returning the html page.

	:returns: An HTML page to be displayed by the website
	"""
	decisions = db_session.query(GenCons).all()
	return render_template('about-data.html', decisions=decisions)

@app.teardown_appcontext
def shutdown_session(exception=None):
	"""
	When the http session is over this kills the database session.

	:returns: none
	"""
	db_session.remove()