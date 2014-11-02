#!/usr/bin/python
# -*- coding: utf-8 -*-

# wget -O stranger.xml http://<plexserver>:32400/library/sections/1/all?type=1
# curl -o stranger.xml "http://plex:32400/library/sections/1/all?type=1"

import xml.etree.ElementTree as ET
import urllib2
import csv
import io

class PlexCompare():

  def __init__(self, stranger, host):
    self.host = host

    # File URL
    self.stranger = stranger

  def compare(self, sectionId):
    strangerFile = open(self.stranger, "r")
    strangerParsed = ET.parse(strangerFile)
    strangerFile.close()

    acquaintanceFile = urllib2.urlopen(self.host + "/library/sections/" + sectionId + "/all?type=1")
    acquaintanceParsed = ET.parse(acquaintanceFile)
    acquaintanceFile.close()

    strangerRoot = strangerParsed.getroot()
    acquaintanceRoot = acquaintanceParsed.getroot()

    # file, title, width, size, audioChannels, videoFrameRate
    newVideos = []
    betterQualityVideos = []

    for video in strangerRoot.getchildren():
      media = video.find("Media")
      part = media.find("Part")
      strangerTitle = video.attrib.get("title")
      strangerVideoWidth = media.attrib.get("width")
      strangerFile = part.attrib.get("file")
      strangerSize = part.attrib.get("size")
      strangerAudioChannels = media.attrib.get("audioChannels")
      strangerVideoFrameRate = media.attrib.get("videoFrameRate")
      strangerVideoResolution = media.attrib.get("videoResolution")

      ownThisTitle = False
      strangerHasBetterQuality = False

      for acquaintanceVideo in acquaintanceRoot.getchildren():
        acquaintanceMedia = acquaintanceVideo.find("Media")
        acquaintanceTitle = acquaintanceVideo.attrib.get("title")
        acquaintanceVideoWidth = acquaintanceMedia.attrib.get("width")
        acquaintanceVideoResolution = media.attrib.get("videoResolution")

        if strangerTitle == acquaintanceTitle:
          ownThisTitle = True

          if int(strangerVideoWidth) > int(acquaintanceVideoWidth):
            strangerHasBetterQuality = True
          break

      if ownThisTitle is True:
        if strangerHasBetterQuality is True:
          betterQualityVideos.append({"title": strangerTitle, "width": strangerVideoWidth, "file": strangerFile, "size": strangerSize, "audioChannels": strangerAudioChannels, "videoFrameRate": strangerVideoFrameRate})
      else:
        newVideos.append({"title": strangerTitle, "width": strangerVideoWidth, "file": strangerFile, "size": strangerSize, "audioChannels": strangerAudioChannels, "videoFrameRate": strangerVideoFrameRate})

    return (newVideos, betterQualityVideos)

  def sectionSize(self, sectionId):
    sectionFile = urllib2.urlopen(self.host + "/library/sections/" + sectionId + "/all?type=1")
    section = ET.parse(sectionFile)
    sectionFile.close()

    return section.getroot().attrib.get("size")

  def saveToDisk(self, videos, filename):
    with open(filename, 'wb') as f:
        dict_writer = csv.DictWriter(f, videos[0].keys())
        dict_writer.writeheader()
        for video in videos:
          dict_writer.writerow({k:v.encode('utf8') for k,v in video.items()})


  def sectionList(self):
    sectionsFile = urllib2.urlopen(self.host + "/library/sections")
    sectionsParsed = ET.parse(sectionsFile)
    sectionsRoot = sectionsParsed.getroot()

    sections = []

    for section in sectionsRoot.getchildren():
      attributes = section.attrib

      title = attributes.get("title")
      section_type = attributes.get("type")
      section_id = attributes.get("key")

      sections.append({"title": title, "type": section_type, "id": section_id})
    return sections

  def printSummary(self):
    sections = self.sectionList()

    print("There are " + str(len(sections)) + " sections available:")
    for section in sections:
      print("")
      print("\tId: " + section.get("id"))
      print("\tTitle: " + section.get("title"))
      print("\tType: " + section.get("type"))
      print("\tSize: " + self.sectionSize(section.get("id")))

    sectionChoice = raw_input("Choose a section _id_ you want to compate with: ")

    (newVideos, betterQualityVideos) = self.compare(sectionChoice)

    totalSize = 0
    for newVideo in newVideos:
      totalSize = totalSize + float(newVideo.get("size"))

    for betterQualityVideo in betterQualityVideos:
      totalSize = totalSize + float(betterQualityVideo.get("size"))


    print("")
    print("== Summary ==")
    print("New Videos: " + str(len(newVideos)))
    print("Videos with better quality: " + str(len(betterQualityVideos)))
    print("Total size of files: " + str(round(totalSize/1000/1000/1000, 2)) + "GB")
    print("")

    saveQuestion = raw_input("Do you want to save these videos to a file? (y/n)")
    if saveQuestion == "y":
      self.saveToDisk(newVideos, "new_videos.csv")
      self.saveToDisk(betterQualityVideos, "better_quality_videos.csv")


if __name__ == "__main__":
  host = raw_input("Enter the Plex Media Server IP address e.g. plex:32400: ")
  if host:
    plex = PlexCompare("stranger.xml", "http://" + host)
    plex.printSummary()
