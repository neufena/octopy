import os
import csv

class OctoKeyMap:
    def __init__(self, settings, files):
        self.settings = settings
        self.files = files
        self.path = os.path.expanduser(self.settings.get_localmedia()) + "/keymap.csv"
        self.keymap = {}
        self.hasKeymap = False
        try:
            with open(self.path, newline='') as csvfile:  
                reader = csv.reader(csvfile)
                self.hasKeymap = True
                for index, row in enumerate(reader):
                    if index > 0:
                        key = row[0].strip()
                        fileName = row[1].strip()
                        
                        if settings.get_verbose():
                            print("Keymap: " + key + "=>" + fileName)
                        fileIndex = self.__findFileIndex(fileName)   
                        if fileIndex != None:
                            self.keymap[key] = fileIndex
        except FileNotFoundError:
            if settings.get_verbose():
                print("Keymap not found at " + self.path)

    def __findFileIndex(self, filename):
        for index, item in enumerate(self.files.getfiles()):
            if item.name == filename:
                return index + 1
        else:
            print("Filename in keymap not found: " + filename)

    def getFileIndex(self, key):
        if self.hasKeymap == False:
            return
        try:
            return self.keymap[key]
        except:
            return

        