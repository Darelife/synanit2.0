from PIL import Image, ImageDraw, ImageFont
import re
import requests
import json
import io
import os

class ContestGraphImageGenerator:
    def __init__(self, contestId, descText, imageSelected, regex=r"^(2023|2024|2022).{9}$", overrideContestName=False, overrideText=""):
        self.imageList = ["dark.png", "brown.png", "purple.png", "blue.png"]
        self.textColour = ["#e1e1de", "#ffe5c0", "#e4caf4", "#cbdcfd"]
        self.regex = regex
        self.contestId = contestId
        self.descText = descText
        self.imageSelected = imageSelected % len(self.textColour)
        self.overrideContestName = overrideContestName
        self.overrideText = overrideText
        self.background = None
        self.width = None
        self.height = None
        self.draw = None
        self.titleFont = None
        self.lineFont = None
        self.titleBoldFont = None
        # Base paths for assets - assuming run from project root
        self.assets_dir = "./assets"

    def fetchDatabase(self):
        url = "https://algoxxx.onrender.com/database"
        try:
            req = requests.get(url, timeout=5)
            data = req.json()
        except:
            data = []
        data.append({"_id":"123","name":"Meet Parmar","bitsid":"2023A7PS0406G","cfid":"meeeet"})
        return data

    def filterEntries(self, dataa):
        return [
            [entry.get("name", "").title(), entry.get("cfid", "").lower()]
            for entry in dataa
            if re.search(self.regex, entry.get("bitsid", ""))
        ]

    def fetchContestStandings(self):
        url = f"https://codeforces.com/api/contest.standings?contestId={self.contestId}&showUnofficial=true"
        req = requests.get(url)
        if req.status_code != 200:
            raise Exception(f"Failed to fetch contest standings: {req.status_code}")
        return req.json()
    
    def drawGraph(self, data):
        if not data:
            return
        
        validData = []
        for name, handle, rank, penalty, point, isOurStudent in data:
            if rank > 0:
                points = point*500-penalty
                validData.append((name, handle, rank, points, isOurStudent))
        
        if not validData:
            return
        
        validData.sort(key=lambda x: x[2])
        
        graphX = 70
        graphY = self.height - 400
        graphWidth = 825
        graphHeight = 250
        
        maxRank = max(entry[2] for entry in validData)
        minRank = min(entry[2] for entry in validData)
        maxPoints = max(entry[3] for entry in validData)
        minPoints = min(entry[3] for entry in validData)
        
        rankRange = max(1, maxRank - minRank)
        pointsRange = max(1, maxPoints - minPoints)
        
        graphOverlay = Image.new('RGBA', (graphWidth + 100, graphHeight + 80), (0, 0, 0, 0))
        graphDraw = ImageDraw.Draw(graphOverlay)
        
        graphDraw.rectangle([80, 30, graphWidth + 80, graphHeight + 30], 
                   fill=(0, 0, 0, 40), outline=self.textColour[self.imageSelected])
        
        for i in range(5):
            y = 30 + (i * graphHeight // 4)
            graphDraw.line([(80, y), (graphWidth + 80, y)], 
                  fill=self.textColour[self.imageSelected] + "40", width=1)
            x = 80 + (i * graphWidth // 4)
            graphDraw.line([(x, 30), (x, graphHeight + 30)], 
                  fill=self.textColour[self.imageSelected] + "40", width=1)
        
        graphDraw.line([(80, graphHeight + 30), (graphWidth + 80, graphHeight + 30)], 
                  fill=self.textColour[self.imageSelected], width=3)
        graphDraw.line([(80, 30), (80, graphHeight + 30)], 
                  fill=self.textColour[self.imageSelected], width=3)
        
        scaledPoints = []
        for name, handle, rank, points, isOurStudent in validData:
            x = 80 + ((rank - minRank) / rankRange) * graphWidth
            y = 30 + graphHeight - ((points - minPoints) / pointsRange) * graphHeight
            scaledPoints.append((x, y, name, rank, points, isOurStudent))
        
        if len(scaledPoints) > 1:
            linePoints = [(x, y) for x, y, _, _, _, _ in scaledPoints]
            for i in range(len(linePoints) - 1):
                graphDraw.line([linePoints[i], linePoints[i + 1]], 
                          fill=self.textColour[self.imageSelected], width=4)
        
        for x, y, name, rank, points, isOurStudent in scaledPoints:
            if isOurStudent:
                if rank <= 5:
                    dotColor = "#FFD700"
                    glowColor = (255, 215, 0)
                elif rank <= 15:
                    dotColor = "#C0C0C0"
                    glowColor = (192, 192, 192)
                else:
                    dotColor = "#CD7F32"
                    glowColor = (205, 127, 50)
                
                for radius in [6, 4]:
                    alpha = 80 - (radius * 10)
                    color = glowColor + (alpha,)
                    graphDraw.ellipse([x-radius, y-radius, x+radius, y+radius], 
                        fill=color)
                
                graphDraw.ellipse([x-4, y-4, x+4, y+4], 
                    fill="#101010")

                graphDraw.ellipse([x-3, y-3, x+3, y+3], 
                    fill=dotColor)
            else:
                dotColor = "#808080"
                graphDraw.ellipse([x-1, y-1, x+1, y+1], 
                    fill=dotColor)
                    
        smallFont = ImageFont.truetype(os.path.join(self.assets_dir, "fonts/Montserrat-Light.ttf"), 20)
        
        graphDraw.text((graphWidth//2 + 80, graphHeight + 50), "Rank", 
              font=smallFont, fill=self.textColour[self.imageSelected], anchor="mm")
        
        graphDraw.text((40, graphHeight//2 + 30), "Points", 
              font=smallFont, fill=self.textColour[self.imageSelected], anchor="mm")
        
        tinyFont = ImageFont.truetype(os.path.join(self.assets_dir, "fonts/Montserrat-Light.ttf"), 16)
        
        graphDraw.text((80, graphHeight + 45), str(int(minRank)), 
              font=tinyFont, fill=self.textColour[self.imageSelected], anchor="mm")
        graphDraw.text((graphWidth + 80, graphHeight + 45), str(int(maxRank)), 
              font=tinyFont, fill=self.textColour[self.imageSelected], anchor="mm")
        
        quarterRank = minRank + (maxRank - minRank) * 0.25
        threeQuarterRank = minRank + (maxRank - minRank) * 0.75
        graphDraw.text((80 + graphWidth * 0.25, graphHeight + 45), str(int(quarterRank)), 
              font=tinyFont, fill=self.textColour[self.imageSelected], anchor="mm")
        graphDraw.text((80 + graphWidth * 0.75, graphHeight + 45), str(int(threeQuarterRank)), 
              font=tinyFont, fill=self.textColour[self.imageSelected], anchor="mm")
        
        graphDraw.text((70, graphHeight + 30), str(int(minRank)), 
              font=tinyFont, fill=self.textColour[self.imageSelected], anchor="rm")
        graphDraw.text((70, 30), str(int(maxPoints)), 
              font=tinyFont, fill=self.textColour[self.imageSelected], anchor="rm")
        
        quarterPoints = minPoints + (maxPoints - minPoints) * 0.25
        threeQuarterPoints = minPoints + (maxPoints - minPoints) * 0.75
        graphDraw.text((70, 30 + graphHeight * 0.75), str(int(quarterPoints)), 
              font=tinyFont, fill=self.textColour[self.imageSelected], anchor="rm")
        graphDraw.text((70, 30 + graphHeight * 0.25), str(int(threeQuarterPoints)), 
              font=tinyFont, fill=self.textColour[self.imageSelected], anchor="rm")
        
        self.background.paste(graphOverlay, (graphX, graphY), graphOverlay)


    def getContestName(self, resp):
        if resp["status"] == "OK":
            contestName = resp["result"]["contest"]["name"]
        else:
            contestName = "Unknown Contest"
        if self.overrideContestName:
            contestName = self.overrideText
        return contestName

    def mapCfidToName(self, filteredEntries):
        return {cfid: name for name, cfid in filteredEntries}

    def extractStandings(self, resp, cfidToName):
        data = []
        if resp["status"] == "OK":
            for row in resp["result"]["rows"]:
                handle = row["party"]["members"][0]["handle"].lower()
                rank = row["rank"]
                name = cfidToName.get(handle, handle)
                penalty = row.get("penalty", 0)
                points = row.get("points", 0)
                isOurStudent = handle in cfidToName
                data.append([name, handle, rank, penalty, points, isOurStudent])
        return data

    def getTop5(self, data):
        return sorted([entry for entry in data if entry[2] != 0 and entry[5]], key=lambda x: x[2])[:min(5, len(data))]

    def truncate(self, text):
        return text if len(text) <= 17 else text[:14] + "..."

    def setupImage(self):
        bg_path = os.path.join(self.assets_dir, "BGCL", self.imageList[self.imageSelected])
        self.background = Image.open(bg_path)
        self.width, self.height = self.background.size
        self.draw = ImageDraw.Draw(self.background)
        fontPath = os.path.join(self.assets_dir, "fonts/Montserrat-Light.ttf")
        boldFontPath = os.path.join(self.assets_dir, "fonts/Montserrat-Bold.ttf")
        self.titleFont = ImageFont.truetype(fontPath, 100)
        self.lineFont = ImageFont.truetype(fontPath, 40)
        self.titleBoldFont = ImageFont.truetype(boldFontPath, 57)

    def drawTitle(self, contestName):
        self.draw.text(
            (self.width // 2, 550),
            contestName.upper(),
            font=self.titleBoldFont,
            fill=self.textColour[self.imageSelected],
            anchor="mm"
        )
        self.draw.text(
            (self.width // 2, 725),
            self.descText,
            font=self.titleFont,
            fill=self.textColour[self.imageSelected],
            anchor="mm"
        )

    def drawTable(self, top5):
        startY = 1035
        gap = 90
        xName = 70
        xHandle = 485
        xPoints = 1020
        for idx, (name, handle, rank, pen, point, isOurStudent) in enumerate(top5):
            y = startY + idx * gap
            nameTrunc = self.truncate(name)
            handleTrunc = self.truncate(handle)
            self.draw.text((xName, y), f"{nameTrunc}", font=self.lineFont, fill=self.textColour[self.imageSelected])
            self.draw.text((xHandle, y), f"{handleTrunc}", font=self.lineFont, fill=self.textColour[self.imageSelected])
            self.draw.text((xPoints, y), f"{int(rank)}", font=self.lineFont, fill=self.textColour[self.imageSelected], anchor="ra")

    def saveImage(self):
        # Return BytesIO instead of saving to disk
        buffer = io.BytesIO()
        self.background.save(buffer, format="PNG")
        buffer.seek(0)
        return buffer

    def generate(self):
        dataa = self.fetchDatabase()
        filteredEntries = self.filterEntries(dataa)
        resp = self.fetchContestStandings()
        contestName = self.getContestName(resp)
        cfidToName = self.mapCfidToName(filteredEntries)
        data = self.extractStandings(resp, cfidToName)
        top5 = self.getTop5(data)
        self.setupImage()
        self.drawTitle(contestName)
        self.drawGraph(data)
        self.drawTable(top5)
        return self.saveImage()
