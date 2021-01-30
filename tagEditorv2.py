import json
import os
from pathlib import Path
from shutil import copy2
import binascii
from mutagen.mp4 import MP4


class TagEditor:

    nameOffset = 1534
    zeroCount = 516

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
        backup = True if input(
            'Would you like to create backups? (Y/N): ').upper() == 'Y' else False
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
        copy2(self.directory / song, self.directory / (song + '.bkp'))

    def getNameInHex(self):
        return bytearray('name'.encode('utf-8').hex().encode('utf-8'))

    def getOwnerInHex(self):
        return bytearray(self.owner.encode('utf-8').hex().encode('utf-8'))

    def getZerosInHex(self):
        return (self.zeroCount - len(self.getOwnerInHex())) * bytearray('0'.encode('utf-8'))

    def setiTunesOwner(self, song):
        try:
            with open(self.directory / song, 'r+b') as f:
                content = bytearray(binascii.hexlify(f.read()))

                # if the iTunes owner tag isn't located here
                if content[self.nameOffset - 8:self.nameOffset] != self.getNameInHex():
                    return False

                content[self.nameOffset:] = self.getOwnerInHex() + \
                    self.getZerosInHex()
                f.seek(0)
                f.write(binascii.unhexlify(content))

            return True
        except IOError:
            return False

    def setTags(self, song):
        tags = MP4(self.directory / song)

        tags['ownr'] = [self.owner]
        tags['apID'] = [self.email]

        # print(tags['purd'])
        # print(type(tags['purd'][0]))

        tags.save()

    def __init__(self):

        # 1) get owner details (name and email)
        #       a) if details don't exist, ask user to enter details and store (json)
        if not self.getOwnerDetailsFromFile():
            self.getOwnerDetailsFromUser()
            os.system('cls')

        # infinite loop (to catch multiple directories)
        while True:

            # 2) get the directory (folders or files)
            #       a) if the directory isn't valid, keep asking until the directory is valid
            while not self.getDirectory():
                self.getDirectory()

            # 3) get the paths of all the songs in this directory
            self.getSongs()
            print(self.__dict__)

            # set the number of processed songs to 0
            processed = 0

            # iterate through every song
            for song in self.songs:
                print('  > Processing', song)

                # boolean to track if the current song has been processed successfully
                self.processedSuccessfully = True

                # 4) create backup of current song (user preference)
                if self.backup:
                    self.createBackup(song)

                # 5) set owner details on the current song
                #       a) iTunes owner details (hex)
                if not self.setiTunesOwner(song):
                    print('  > Unable to set iTunes owner on', song)

                #       b) remaining owner details (name and email)
                self.setTags(song)

                # increment number of processed songs
                #
            # 6) output "finished processing" message


if __name__ == '__main__':
    TagEditor()
