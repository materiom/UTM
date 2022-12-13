import sys
import json
from controller.py import Controller

if __name__ == "__main__":
	
	try:
		if sys.argv[1]: # If the config has been sent over the CLI as a KJSON string then use it here
			config = json.loads(sys.argv[1])
		else:
			# else try to load it ourselves from a known default file
			# This will probably be useful when doing 'headless' tests without the GUI
			config = None 



		controller = Controller(config)
		controller.run()

	except BaseExeption as err:
		print(err)
		sys.exit()