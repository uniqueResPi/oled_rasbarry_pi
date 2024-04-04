import asyncio
import requests
import json
import time
import RPi.GPIO as GPIO
import board
import digitalio
from PIL import Image, ImageDraw, ImageFont
import adafruit_ssd1306


SCREEN_WIDTH = 128
SCREEN_HEIGHT = 32
OLED_RESET = None  # Reset pin not used with RPi
# SCREEN_ADDRESS = 0x3C

# Initializing I2C communication
i2c = board.I2C()

# Creating the SSD1306 object
oled = adafruit_ssd1306.SSD1306_I2C(SCREEN_WIDTH, SCREEN_HEIGHT, i2c)

nextButtonPin = 23
prevButtonPin = 24

updateTimeCount = 0
updateTime = 30  # seconds

serverAddress = "script.google.com"
serverPort = 443

nextCommand = "next"
previousCommand = "previous"
currentCommand = "current"
allCommand = "all"

currentRow = 0
currentColumn = 0
totalRows = 0
totalColumns = 0
value = ""

MAX_ROWS = 150
MAX_COLUMNS = 150
allCellValues = [["" for _ in range(MAX_COLUMNS)] for _ in range(MAX_ROWS)]

def setup():
    #GPIO.setmode(GPIO.BOARD)
    GPIO.setup(nextButtonPin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(prevButtonPin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    load_preferences()
    display_text(value)

async def loop():
    global updateTimeCount, value, currentRow, currentColumn, totalRows, totalColumns
    while True:
        await asyncio.sleep(0)
        
        if GPIO.input(nextButtonPin) == GPIO.LOW:
            print("next button is pressed:")
            #print("current  values are currentRow index=")
            #print(currentRow)
            #print("currentColumn")
            #print(currentColumn)
            currentColumn += 1
            if currentColumn >= totalColumns:
                currentRow += 1
                currentColumn = 0
                if currentRow >= totalRows:
                    currentRow = 0
                    currentColumn = 0
            #print("updated values are currentRow index=")
            #print(currentRow)
            #print("currentColumn")
            #print(currentColumn)
            value = allCellValues[currentRow][currentColumn]
            display_text(value)
            save_preferences()

        elif GPIO.input(prevButtonPin) == GPIO.LOW:
            print("prev Butotn is pressed:")
            #print("currnet values are currentRow index=")
            #print(currentRow)
            #print("currentColumn")
            #print(currentColumn)
            currentColumn -= 1
            if currentColumn < 0:
                currentRow -= 1
                currentColumn = totalColumns 
                if currentRow < 0:
                    currentRow = totalRows 
                    currentColumn = totalColumns
    #         print("updated values are currentRow index=")
    #         print(currentRow)
    #         print("currentColumn")
    #         print(currentColumn)
            value = allCellValues[currentRow][currentColumn]
            display_text(value)
            save_preferences()

        if time.time() - updateTimeCount > updateTime:
            print("update time is over now updateing:")
            asyncio.create_task(send_request(allCommand, MAX_ROWS, MAX_COLUMNS))
            updateTimeCount = time.time()




async def send_request(command, row, column):
    url = f"https://{serverAddress}/macros/s/AKfycbz-2sLxWJGjahPHEGOiEEsabQv3_X4m6Fzsjsfoj3skxL5rj8qL2zrlNwZea_BlLBh0/exec"
    params = {
        "command": command,
        "row": row+1,
        "column": column+1
    }
    try:
        
        response = await asyncio.to_thread(requests.get, url, params=params, timeout=25)

        if response.status_code == 200:
            response_data = response.json()
        #print("google sheet  response :")
        #print(json.dumps(response_data))
            parse_response(response_data, command)
            print(f"Value: {value}")
            print(f"Row: {currentRow+1}")
            print(f"Column: {currentColumn+1}")
            print(f"TotalRow: {totalRows+1}")
            print(f"TotalColumn: {totalColumns+1}")
            if currentRow < 0 or currentRow > totalRows or currentColumn < 0 or currentColumn > totalColumns:
                print("somthing is out of range after fetechting data from network  in x and y")
                currentRow=0
                currentColumn=0
                
            value=allCellValues[currentRow][currentColumn]
            #print("now value is set and go to save new data: value is =")
            #print(value)
            display_text(value)
            save_preferences()
        else:
            print(f"Error: HTTP status code {response.status_code}")
    except requests.Timeout:
        print("Error: Request timed out")
    except requests.RequestException as e:
        print(f"exception Error: {type(e).__name__}")
def parse_response(response_data, command):
    global allCellValues, currentRow, currentColumn, totalRows, totalColumns, value

    if command != allCommand:
        value = response_data["value"]
        print("this line never print")
        currentRow = response_data["row"]
        currentColumn = response_data["column"]
        totalRows = response_data["totalRows"] -1
        totalColumns = response_data["totalColumns"] -1
    else:
        
        all_cell_values = response_data["value"]
        print(all_cell_values)
        totalRows = response_data["totalRows"] -1
        totalColumns = response_data["totalColumns"] -1
        print("totla rows")
        print(totalRows)
        print("totalColumns")
        print(totalColumns)
        for i in range(min(totalRows, MAX_ROWS)):
            inner_array = all_cell_values[i]
            for j in range(min(totalColumns, MAX_COLUMNS)):
                allCellValues[i][j] = inner_array[j]
        #print("now all 2d table is parse and print value:")
        #for row in allCellValues:
            #print(" ".join(map(str,row)))
        


def save_preferences():
     preferences = {
        "currentRow": currentRow,
        "currentColumn": currentColumn,
        "totalRows": totalRows,
        "totalColumns": totalColumns,
        "allCellValues": allCellValues
     }
     with open("preferences.json", "w") as file:
        json.dump(preferences, file)

def load_preferences():
    try:
        with open("preferences.json", "r") as file:
            preferences = json.load(file)
            global currentRow, currentColumn, totalRows, totalColumns, allCellValues
            currentRow = preferences["currentRow"]
            currentColumn = preferences["currentColumn"]
            totalRows = preferences["totalRows"]
            totalColumns = preferences["totalColumns"]
            print("load total Rows")
            print(totalRows)
            print("laod total columes")
            print(totalColumns)
            allCellValues = preferences["allCellValues"]
            print("loaded table expected: ")
            print(allCellValues)
    except FileNotFoundError:
           print("data not exist");
        
def display_text(text):
    global oled  # Accessing the global oled object

    # Clearing the display
    oled.fill(0)
    oled.show()

    # Creating a blank image for drawing
    image = Image.new("1", (oled.width, oled.height))
    draw = ImageDraw.Draw(image)

    # Loading a font
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 28)
    #font = ImageFont.truetype('PixelOperator.ttf', 16)
    # Getting the dimensions of the text
    text_width, text_height = draw.textsize(text, font)

    # Calculating the position to center the text
    x = (oled.width - text_width) // 2
    y = (oled.height - text_height) // 2

    # Drawing the text in the center
    draw.text((x, y), text, font=font, fill=255)

    # Displaying the image
    oled.image(image)
    oled.show()

if __name__ == "__main__":
    try:
        setup()
        #while True:
          asyncio.run(loop())
    except KeyboardInterrupt:
        GPIO.cleanup()
