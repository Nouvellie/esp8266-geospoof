# ARDUINO
## INSTALL
#### Download:

```sh
$ curl -O https://www.arduino.cc/download_handler.php
```

#### Install as root:

```sh
$ sudo su
$ sudo unzip arduino-1.8.9-linux64.tar.xz
$ cd arduino-1.8.9-linux64/arduino-1.8.9/
$ sudo bash ./install.sh
```

## Settings
#### Additional boards manager URLs:

In *file/preferences/additional-boards-urls* add: *http://arduino.esp8266.com/stable/package_esp8266com_index.json* and **OK**.

#### Manage libraries:

In *tool/manage/libraries* add:
- Adafruit ESP8266 by adafruit.
- Adafruit SSD1306 by adafruit.
- Adafruit GFX library by adafruit.
- AceButton by Brian T. Park.

#### Options:

In *tool* select:

- **Board**: "NodeMCU 1.0 (ESP-12E Module)"
- **Upload Speed**: "115200"
- **CPU Frequency**: "80 MHz"
- **Flash size**: "4M(1M SPIFFS)"
- **Debug port**: "Disabled"
- **Debug level**: "None"
- **IwIP Variant**: "v1.4 Higher Bandwidth"
- **VTable**: "Flash"
- **Exceptions**: "Disabled"
- **Erase Flash**: "Only Sketch"
- **SSL Support**: "All SSL ciphers (most compatible)"
- **PORT**: "COMX"
- **Programmer**: "AVRISP mkll"


## To reset arduino

Open *ino* format and click *Verify*.

## To install custom .ino

Open *ino* format and click *Upload*.

## Give chmod to the device to avoid errors 

```sh
$ sudo chmod -R 777 /<dev>/<ttyUSB0>
```