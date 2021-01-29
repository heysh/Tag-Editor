import json
import os
from pathlib import Path


class TagEditor:

    def setOwnerDetails(self, ownerDetails):
        self.owner = ownerDetails['owner']
        self.email = ownerDetails['email']

    def getOwnerDetailsFromFile(self):
        try:
            with open(Path(os.path.dirname(__file__)) / 'ownerDetails.json', 'r') as detailsFile:
                ownerDetails = json.loads(detailsFile.read())

            self.setOwnerDetails(ownerDetails)
            return True

        except IOError:
            return False

    def getOwnerDetailsFromUser(self):
        owner = input('Enter your name: ')
        email = input('Enter your email: ')
        ownerDetails = {'owner': owner, 'email': email}
        self.setOwnerDetails(ownerDetails)

        with open(Path(os.path.dirname(__file__)) / 'ownerDetails.json', 'w') as detailsFile:
            detailsFile.write(json.dumps(ownerDetails))

    def getDirectory(self):
        path = input('Drag the music here: ').strip('"').strip("'")

        if Path(path).exists():
            self.directory = Path(
                path).parent if path[-4:] == ".m4a" else Path(path)
            return True
        else:
            return False

    def getSongs(self):
        return

    def __init__(self):

        # 1) get owner details (name and email)
        #       a) if details don't exist, ask user to enter details and store (json)

        if not self.getOwnerDetailsFromFile():
            self.getOwnerDetailsFromUser()

        # 2) infinite loop (to catch multiple directories)

        while True:

            # 3) get the directory (folders or files)
            #       a) if the directory isn't valid, keep asking until the directory is valid

            while not self.getDirectory():
                self.getDirectory()

            print("valid directory")
            print(self.__dict__)

            # 4) get the paths of all the songs in this directory
            #
            # 5) set the number of processed songs to 0
            #
            # 6) iterate through every song
            #
            # 7) create backup of current song
            #
            # 8) set owner details on the current song
            #       a) iTunes owner details (hex)
            #       b) remaining owner details (name and email)
            #
            # 9) increment number of processed songs
            #
            # 10) output "finished processing" message


if __name__ == '__main__':
    TagEditor()
