import serial
import threading
import blinker


class rsEight:
    BTN_ID_AUTO = 0xF7
    BTN_ID_TAKE = 0xFD
    BTN_ID_FADEDSK = 0x7F
    BTN_ID_TAKEDSK = 0xBF
    BTN_ID_DDR = 0xDF
    BTN_ID_ALT = 0xEF
    BUS_ID_PGM = 2
    BUS_ID_PVW = 1
    BTN_ID_1 = 0x80
    BTN_ID_2 = 0x40
    BTN_ID_3 = 0x20
    BTN_ID_4 = 0x10
    BTN_ID_5 = 0x08
    BTN_ID_6 = 0x04
    BTN_ID_7 = 0x02
    BTN_ID_8 = 0x01
    NUM_BTNS_ON_BUS = 8
    TBAR_MAX = 40
    TBAR_MIN = 0
    ENC_MAX = 255
    ENC_MIN = 0

    evt_rseight_data_rx = blinker.signal("rs8-data-rx")
    evt_rseight_bus_xpoint_changed = blinker.signal("rs8-bus-xpoint-changed")  # int bus, int key
    evt_rseight_cmd_btn_changed = blinker.signal("rs8-cmd-btn-changed")  # int btn
    evt_rseight_tbar_value_changed = blinker.signal("rs8-tbar-value-changed")  # int value
    evt_rseight_encoder_value_changed = blinker.signal("rs8-enc-value-changed")  # int enc, int value

    def __init__(self, port):
        self.port = port
        self.panel = serial.Serial(self.port, 9600, serial.EIGHTBITS, serial.PARITY_NONE, serial.STOPBITS_ONE)

        self.evt_rseight_data_rx.connect(self.decode_data)

        print "Setting up threaded loop"

        t = threading.Thread(target=self.start_threaded_loop)
        t.start()

    def send_command(self, data):
        self.panel.write(bytearray(data, "utf-8"))

    def decode_byte_matrix(self, byte):
        """
        From a given two-character hex byte (e.g. c5), find out which of the bits are set, and return a list of the
        indices of the bits that are.
        e.g. decode_byte_matrix("c5") returns [7,6,2,0] (bitstream 11000101)
        :param byte:
        :return:
        """
        l = []
        num = int(byte, 16)
        for i in reversed(xrange(8)):
            if (num >> i) & 1: l.append(i)

        return l

    def decode_data(self, *args, **kwargs):
        data = kwargs["data"]
        if data[0] != "~":
            print "Got malformed data - string does not start with ~"
            print data
            return None

        print "Recieved signal {0}".format(data)
        if data[1] == "1" or data[1] == "2":
            # Preview or program bus buttons changed
            bits = self.decode_byte_matrix(data[2:])
            for b in bits:
                self.evt_rseight_bus_xpoint_changed.send(self, bus=data[1], key=int(b))
        elif data[1] == "3":
            # Command buttons have changed
            self.evt_rseight_cmd_btn_changed.send(self, btn=int(data[2:],16))
        elif data[1] == "4":
            # T-bar has moved
            self.evt_rseight_tbar_value_changed.send(self, value=int(data[2:], 16))
        elif data[1] == "5" or data[1] == "6" or data[1] == "7":
            # One of the encoders has changed
            self.evt_rseight_encoder_value_changed.send(self, enc=int(data[1]) - 5, value=int(data[2:], 16))

    def start_threaded_loop(self):
        while True:
            data = self.panel.read(4)
            self.evt_rseight_data_rx.send(self, data=data)

    def set_led_state_cmd(self, *args):
        """
        Sends a command to the RS8 to set the LED state for various buttions.
        To specify which buttons are lit, supply BTN_ID_* constants as the arguments.
        e.g. set_led_state_cmd(BTN_ID_AUTO, BTN_ID_DDR)
        """
        cmd = 0x00
        for a in args:
            cmd = cmd & a
        self.send_command("~3" + str(format(cmd, '02X')))

    def set_led_state_bus(self, bus, buttons):
        """
        Sends a command to the RS8 to set the LED state for buttons on the preview or program bus.
        To specify which buttons are lit, supply the bus ID and a list of numeric IDs of buttons (L-R on the panel)
        that should be lit - with the first button having ID 0.
        e.g. set_led_state_bus(BUS_ID_PVW, [0,1,5])
        :param bus: BUS_ID* constant specifying the the program or preview bus
        :param buttons: list of ints specifying which buttons on the bus row should be lit (0-7 on an RS8)
        :return: None
        """

        cmd = 0x00
        for b in buttons:
            cmd += b

        cmd = abs(~cmd)
        self.send_command("~" + str(bus) + str(format(cmd, '02X')))
