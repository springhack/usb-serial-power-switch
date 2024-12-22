#!/usr/bin/env python3

import os
import time
import json
import serial
import serial.tools.list_ports
from http.server import HTTPServer, BaseHTTPRequestHandler

HOST = ("0.0.0.0", 5432)
DEVICE = "/dev/serial/by-id/usb-1a86_5523-if00-port0"

DATA_ON = bytes(b'\xA0\x01\x01\xA2')
DATA_OFF = bytes(b'\xA0\x01\x00\xA1')
DATA_STATE = bytes(b'\xA0\x01\x05\xA6')
DATA_ERROR = bytes(b'\xFF\xFF\xFF\xFF')
DATA_STATE_INVALID = bytes(b'\x00\x00\x00\x00')

BYTE_ON = 0x01
BYTE_OFF = 0x00
BYTE_ERROR = 0xFF

PATH_COMMAND_MAP = {
  "/on": DATA_ON,
  "/off": DATA_OFF,
  "/state": DATA_STATE,
}

PORT = None

def send_port(data):
  global PORT
  if PORT == None:
    try:
      PORT = serial.Serial(DEVICE, 115200)
    except Exception as err:
      print(err)
      return DATA_ERROR
  try:
    PORT.write(data)
    if data[2] == DATA_STATE[2]:
      result = PORT.read(4)
      if result[0] == DATA_STATE_INVALID[0]:
        count = 0
        while count < 10 and result[0] == 0:
          count = count + 1
          PORT.write(data)
          result = PORT.read(4)
          time.sleep(1)
      return result
    else:
      return data
  except Exception as err:
    print(err)
    PORT = None
    return DATA_ERROR

def state_string(data):
  if data == BYTE_ON:
    return "on"
  else:
    return "off"

class Resquest(BaseHTTPRequestHandler):
  def do_GET(self):
      self.send_response(200)
      self.send_header("Content-type", "application/json")
      self.end_headers()
      if self.path in PATH_COMMAND_MAP:
        result = send_port(PATH_COMMAND_MAP[self.path])
        data = {
          "state": state_string(result[2]),
          "error": result[2] == BYTE_ERROR,
          "message": "",
        }
        self.wfile.write(json.dumps(data).encode())
      else:
        data = {
          "error": True,
          "state": "off",
          "message": "invalid command",
        }
        self.wfile.write(json.dumps(data).encode())

if __name__ == "__main__":
  server = HTTPServer(HOST, Resquest)
  try:
    print("Starting server, listen at: %s:%s" % HOST)
    server.serve_forever()
  except:
    exit()
