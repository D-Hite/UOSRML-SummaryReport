Documentation for Summary_Reports.py

To make convert summary reports to PDF
download
https://wkhtmltopdf.org/downloads.html

Add filepath to wkhtmltopdf.exe to convert_to_pdf


Files / Filepaths:

	Station_Data:
		A folder containing station folders that have all necessary files
		ex. /ASO contains  ASO_YYYY_ComprehensiveFormat and ASO_YYYY_HourFormat

		Change where station data is accessed in file functions at top of python file (get_filename...)


	My_Daily_Totals:
		station folders containing daily total files
		ex. /BUO/BUO_2001_yt.csv
		Change where yearly totals are saved in test_yearly_totals

	My_Hourly_totals:
		station folders containing hourly total files
		ex. /ASO/ASO_2001_ht.csv

		Change where yearly totals are saved in test_hourly

	Summary_reports:
		All files used to make summary reports and finished summary reports go here
		/outcsv/station
			csv of all data graphed in summary report
		/pics
			all pictures used in summary reports
	
		Change destinations in make_hourly_report and make_summary_report


Common variables:
	Station:
		Example: 'ASO', 'BUO'

	year:
		YYYY : 2001

	sensor:
		ex: 'GHI'

Variables within main functions:

	Data dictionarys:
		depending on the stage at which the process is at, the data dictionary is generally a python dictionary such that:
		dictionary[sensor] = [[top info for the sensor], [data from respective file], [extra information for further process]]
		sometimes dictionary does not contain 3rd list depending on what is being processed

Use:

	To make Daily total file for a single year:
		Yearly_Totals(station, year)
		(returns a pandas dataframe, csv not generated yet)

	To make Daily total files for a range of years:
		test_yearly_totals(start_year, end_year, station)

	to make Hourly file for a single year:
		Hourly_Totals(station, year)
		(returns a pandas dataframe, csv not generated yet)

	to make Hourly total files for a range of years:
		test_hourly(start_year, end_year, station)

	To make summary report:
		make_hourly_report(station, syear, eyear)
	or
		make_summary_report(station, syear, eyear)
		(this version does not include hourly graph)


