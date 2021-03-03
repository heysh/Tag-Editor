import json
import os
from pathlib import Path
from shutil import copy2
import binascii
from mutagen.mp4 import MP4, MP4Cover, MutagenError
import datetime
import requests
import string
from bs4 import BeautifulSoup
import urllib
import re
import colorama
from colorama import Fore, Style


class TagEditor:

    zeroCount = 516
    name = b'\x01\x08\x6E\x61\x6D\x65'
    baseUrl = 'https://music.apple.com/us/album/'

    def setOwnerDetails(self, ownerDetails):
        self.owner = ownerDetails['owner']
        self.email = ownerDetails['email']
        self.backup = ownerDetails['backup']
        self.coverArts = ownerDetails['coverArts']
        self.recursiveSubdirectorySearching = ownerDetails['recursiveSubdirectorySearching']

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
        recursiveSubdirectorySearching = True if input(
            'Would you like to tag the songs inside subfolders? (Y/N): ').upper() == 'Y' else False
        ownerDetails = {'owner': owner, 'email': email, 'backup': backup, 'coverArts': coverArts,
                        'recursiveSubdirectorySearching': recursiveSubdirectorySearching}
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

    def isValidSong(self, directory, song):
        try:
            tags = MP4(directory / song)
            return True
        except MutagenError:
            return False

    def getAlbum(self, directory, song):
        tags = MP4(directory / song)
        self.album = tags['\xa9alb'][0]

    def createBackup(self, directory, song):
        copy2(directory / song, directory / (song + '.bkp'))

    def getDateTimeFromString(self, dateString):
        return datetime.datetime.strptime(dateString, '%Y-%m-%d %H:%M:%S')

    def getOffset(self, directory, song):
        with open(directory / song, 'rb') as f:
            match = re.search(self.name, f.read())
            f.seek(0)
            content = bytearray(binascii.hexlify(f.read()))

        # if the iTunes owner tag couldn't be found
        if not match:
            return False

        self.nameOffset = (match.start() + 6) * 2
        return True

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
                content[self.nameOffset:] = self.getOwnerInHex() + \
                    self.getZerosInHex()
                f.seek(0)
                f.write(binascii.unhexlify(content))

            return True
        except IOError:
            return False

    def setTags(self, directory, song):
        tags = MP4(directory / song)
        tags['ownr'] = [self.owner]
        tags['apID'] = [self.email]
        tags.save()

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
        url = url[:-16] + '99999x99999bb-60.jpg'
        return url

    def getCoverArt(self, directory, song):
        tags = MP4(directory / song)

        # Apple Music url construction
        album = self.urlifyAlbum(tags['\xa9alb'][0])

        try:
            playlistID = str(tags['plID'][0])
        except KeyError:
            return False

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

        colorama.init(autoreset=True)

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

            # get a list of all the subdirectories in this directory (user preference)
            if self.recursiveSubdirectorySearching:
                self.getSubdirectories()
            else:
                self.subdirectories = [self.directory]

            # iterate through every subdirectory
            for subdirectory in self.subdirectories:

                # get the file names of all the songs in this subdirectory
                self.getSongs(subdirectory)

                # if there are no songs in this subdirectory, move onto the next one
                if len(self.songs) < 1:
                    continue

                # iterate through every song
                for song in self.songs:

                    # if the song is invalid
                    if not self.isValidSong(subdirectory, song):
                        print(Fore.LIGHTRED_EX + '  ! Invalid file:',
                              Fore.LIGHTRED_EX + song)
                        continue

                    # if this is the first song
                    if self.songs.index(song) == 0:

                        # get the album
                        self.getAlbum(subdirectory, song)

                        # get the cover art (user preference)
                        # if the cover art could not be retrieved, display a message
                        if self.coverArts:
                            print('  > Retrieving cover art for',
                                  Fore.LIGHTWHITE_EX + self.album)

                            if not (retrievedCoverArt := self.getCoverArt(subdirectory, song)):
                                print(Fore.LIGHTRED_EX +
                                      '  ! Could not retrieve cover art')

                    print('  > Processing', Fore.LIGHTWHITE_EX + song)

                    # create backup of current song (user preference)
                    if self.backup:
                        self.createBackup(subdirectory, song)

                    # get the offset for the iTunes owner tag
                    # if the offset could not be found, display a message
                    if not (foundOffset := self.getOffset(subdirectory, song)):
                        print(Fore.LIGHTRED_EX +
                              '  ! Unable to set iTunes owner tag on', Fore.LIGHTRED_EX + song)

                    # # set owner details on the current song - iTunes owner tag (hex)
                    if foundOffset:
                        if not self.setiTunesOwner(subdirectory, song):
                            print(Fore.LIGHTRED_EX +
                                  '  ! Unable to set iTunes owner tag on', Fore.LIGHTRED_EX + song)

                    # set owner details on the current song - remaining owner tags (name and email)
                    self.setTags(subdirectory, song)

                    # set the cover art (user preference)
                    if self.coverArts:
                        if retrievedCoverArt:
                            self.setCoverArt(subdirectory, song)

                # output "finished processing" message
                print('Finished processing',
                      Fore.LIGHTWHITE_EX + subdirectory.name + '\n')


if __name__ == '__main__':
    TagEditor()
