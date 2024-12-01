# financeAssignment

#Create a python virtual environment
python -m venv venv

#Python Libraries 
python -m pip install selenium, flask, datetime, apscheduler, apscheduler.schedulers.blocking, sqlite3, matplotlib, numpy, selenium.webdriver.common.by, selenium.webdriver.support.ui, selenium.webdriver.support, selenium.webdriver.chrome.options

#Run flask app
python -m flask --app ./scraper.py run

#How to test
> In scrpaer.py,
> uncomment line 141 to create some dummy data. 
> This function is later used in the scheduler to schedule repeated calls for the database.
> Run the python file simply. 
> Your database should be created.
> Then deploy your Flask app and use postman to run your apis
