import json
import os
from pathlib import Path
from shutil import copy2
import binascii
from mutagen.mp4 import MP4, MP4Cover
import datetime
import requests
import string
from bs4 import BeautifulSoup
import urllib


class TagEditor:

    zeroCount = 516
    offsetChangedDate = '2021-01-22 00:00:00'
    baseUrl = 'https://music.apple.com/us/album/'

    def setOwnerDetails(self, ownerDetails):
        self.owner = ownerDetails['owner']
        self.email = ownerDetails['email']
        self.backup = ownerDetails['backup']
        self.coverArts = ownerDetails['coverArts']

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
        coverArts = True if input(
            'Would you like to use the largest cover arts? (Y/N): ').upper() == 'Y' else False
        ownerDetails = {'owner': owner, 'email': email,
                        'backup': backup, 'coverArts': coverArts}
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

    def getSubdirectories(self):
        self.subdirectories = [Path(x[0]) for x in os.walk(self.directory)]

    def getSongs(self, directory):
        self.songs = [file_ for file_ in os.listdir(
            directory) if file_[-4:] == '.m4a']

    def getAlbum(self, directory, song):
        tags = MP4(directory / song)
        self.album = tags['\xa9alb'][0]

    def createBackup(self, directory, song):
        copy2(directory / song, directory / (song + '.bkp'))

    def getDateTimeFromString(self, dateString):
        return datetime.datetime.strptime(dateString, '%Y-%m-%d %H:%M:%S')

    def setOffset(self, directory, song):
        tags = MP4(directory / song)

        purchasedDate = self.getDateTimeFromString(tags['purd'][0])
        offsetChangedDate = self.getDateTimeFromString(self.offsetChangedDate)

        self.nameOffset = 1534 if purchasedDate > offsetChangedDate else 1352

    def getNameInHex(self):
        return bytearray('name'.encode('utf-8').hex().encode('utf-8'))

    def getOwnerInHex(self):
        return bytearray(self.owner.encode('utf-8').hex().encode('utf-8'))

    def getZerosInHex(self):
        return (self.zeroCount - len(self.getOwnerInHex())) * bytearray('0'.encode('utf-8'))

    def setiTunesOwner(self, directory, song):
        try:
            with open(directory / song, 'r+b') as f:
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

    def setTags(self, directory, song):
        tags = MP4(directory / song)

        # if the tags don't exist, invalid m4a file
        if 'ownr' not in tags or 'apID' not in tags:
            return False

        tags['ownr'] = [self.owner]
        tags['apID'] = [self.email]

        tags.save()
        return True

    def urlifyAlbum(self, album):
        album = album.lower()
        album = album.translate(str.maketrans('', '', string.punctuation))
        album = ' '.join(album.split())
        album = album.replace(' ', '-')
        return album

    def getCoverArtLink(self, soup):
        if (main := soup.find('div', {'class': 'product-info'})) is None:
            return False

        image = main.find_all('source', {'type': 'image/jpeg'})
        url = image[0]['srcset']
        url = url[:url.index(' ')]
        url = url[:-16] + '99999x99999bb-100.jpg'
        return url

    def getCoverArt(self, directory, song):
        tags = MP4(directory / song)

        # Apple Music url construction
        album = self.urlifyAlbum(tags['\xa9alb'][0])
        playlistID = str(tags['plID'][0])
        url = self.baseUrl + album + '/' + playlistID

        # in case the album doesn't correspond to an Apple Music page
        try:
            page = requests.get(url)
        except requests.exceptions.RequestException:
            return False

        soup = BeautifulSoup(page.text, 'html.parser')

        # in case there is a problem getting the link for the cover art
        if not (imageUrl := self.getCoverArtLink(soup)):
            return False

        # in case there is a problem downloading the cover art
        try:
            urllib.request.urlretrieve(imageUrl, directory / 'cover.jpg')
        except urllib.error.URLError:
            return False

        return True

    def setCoverArt(self, directory, song):
        tags = MP4(directory / song)

        with open(directory / 'cover.jpg', 'rb') as f:
            tags['covr'] = [
                MP4Cover(f.read(), imageformat=MP4Cover.FORMAT_JPEG)]

        tags.save()

    def __init__(self):

        # get owner details (name and email)
        # if details don't exist, ask user to enter details and store (json)
        if not self.getOwnerDetailsFromFile():
            self.getOwnerDetailsFromUser()
            os.system('cls')

        # infinite loop (to catch multiple directories)
        while True:

            # get the directory (folders or files)
            # if the directory isn't valid, keep asking until the directory is valid
            while not (validDirectory := self.getDirectory()):
                continue

            # get a list of all the subdirectories in this directory
            self.getSubdirectories()

            # iterate through every subdirectory
            for subdirectory in self.subdirectories:

                # get the file names of all the songs in this subdirectory
                self.getSongs(subdirectory)

                # if there are no songs in this subdirectory, move onto the next one
                if len(self.songs) < 1:
                    continue

                # get the album
                self.getAlbum(subdirectory, self.songs[0])

                # get the cover art (user preference)
                # if the cover art could not be retrieved, display a message
                if self.coverArts:
                    if not (retrievedCoverArt := self.getCoverArt(subdirectory, self.songs[0])):
                        print('  ! Could not retrieve cover art')

                # iterate through every song
                for song in self.songs:
                    print('  > Processing', song)

                    # create backup of current song (user preference)
                    if self.backup:
                        self.createBackup(subdirectory, song)

                    # get the correct offset that is to be used
                    self.setOffset(subdirectory, song)

                    # set owner details on the current song - iTunes owner details (hex)
                    if not self.setiTunesOwner(subdirectory, song):
                        print('  ! Unable to set iTunes owner tag on', song)

                    # set owner details on the current song - remaining owner details (name and email)
                    if not self.setTags(subdirectory, song):
                        print('  ! Unable to set owner detail tags on', song)

                    # set the cover art (user preference)
                    if self.coverArts:
                        if retrievedCoverArt:
                            self.setCoverArt(subdirectory, song)

                # output "finished processing" message
                print('Finished processing', self.album + '\n')


if __name__ == '__main__':
    TagEditor()
