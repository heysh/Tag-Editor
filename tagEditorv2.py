import json
import os
from pathlib import Path
from shutil import copy2


class TagEditor:

    def setOwnerDetails(self, ownerDetails):
        self.owner = ownerDetails['owner']
        self.email = ownerDetails['email']
        self.backup = ownerDetails['backup']

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
        backup = input('Would you like to create backups? (Y/N) ').upper()
        ownerDetails = {'owner': owner, 'email': email, 'backup': backup}
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
        self.songs = [file_ for file_ in os.listdir(
            self.directory) if file_[-4:] == '.m4a']

    def createBackup(self, song):
        copy2(self.directory / song, self.directory / song / '.bkp')

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

            # 4) get the paths of all the songs in this directory

            self.getSongs()
            print(self.__dict__)

            # 5) set the number of processed songs to 0

            processed = 0

            # 6) iterate through every song

            for song in self.songs:
                print('  > Processing', song)

                # 7) create backup of current song (user preference)
                if self.backup == 'Y':
                    self.createBackup(song)

                # 8) set owner details on the current song
                #       a) iTunes owner details (hex)
                #       b) remaining owner details (name and email)
                #
                # 9) increment number of processed songs
                #
            # 10) output "finished processing" message


if __name__ == '__main__':
    TagEditor()
