# PRTG-Duplicate-Device-Finder

## Summary
This script will count the total number of alerts found in Opsgenie the week before. Optionally, counts of alerts during specific timeframes during last week can also be appended to the report. Desired alerts can be specified with tags relating to relevant alerts. 
It will then email a report of these numbers.

_Note: If you have any questions or comments you can always use GitHub
discussions, or email me at farinaanthony96@gmail.com._

#### Why
Provides insight for the number of alerts a given instance of Opsgenie has 
generated. This information can be further refined to provide statistics about 
the environment and related alerts to give a better picture on what types of 
alerts are being generated and why.

## Requirements
- Python >= 3.10.2
- configparser >= 5.2.0
- pytz >= 2021.3
- requests >= 2.27.1

## Usage
- Use any additional desired features in the Opsgenie API.
    - Reference to the Opsgenie API: https://docs.opsgenie.com/docs/api-overview

- Edit the config file with relevant Opsgenie, email, timeframe, and timezone information.

- Simply run the script using Python:
  `python Opsgenie-Alerts-Reporter.py`

## Compatibility
Should be able to run on any machine with a Python interpreter. This script
was only tested on a Windows machine running Python 3.10.2.

## Disclaimer
The code provided in this project is an open source example and should not
be treated as an officially supported product. Use at your own risk. If you
encounter any problems, please log an
[issue](https://github.com/CC-Digital-Innovation/Opsgenie-Alerts-Reporter/issues).

## Contributing
1. Fork it!
2. Create your feature branch: `git checkout -b my-new-feature`
3. Commit your changes: `git commit -am 'Add some feature'`
4. Push to the branch: `git push origin my-new-feature`
5. Submit a pull request ツ

## History
- version 2.0.0 - 2022/3/17
    - Added timeframe feature
    - Added ability to specify tags for Opsgenie alerts
    - Added customizable email configurations
    - Updated to Python 3.10
    - Updated relevant packages
    - Cleaned / refactored code

- version 1.0.0 - 2021/11/30
    - (initial release)

## Credits
Anthony Farina <<farinaanthony96@gmail.com>>
