"""raspi control"""
import RPi.GPIO as GPIO
import tm1637
import threading
import queue
from enum import Flag, auto
from time import sleep, time
from . import sound


class ClickStatus(Flag):
    NONE = auto()
    SINGLE = auto()
    DOUBLE = auto()
    LONG = auto()


class Raspi:
    def __init__(self, t):
        # Timeout Limit
        self.limit_t_minutes = t

        # Input Action Settings
        self.LONG_INTERVAL = 0.65
        self.DOUBLE_INTERVAL = 0.11

        # Pin Assignment
        self.freq = 1000  #  PWM frequency [Hz]
        RED = 22
        GREEN = 13  # PWM 1
        BLUE = 27
        self.COLOR_LED_PORTS = [RED, GREEN, BLUE]
        self.SELECT = 18
        self.OPTION = 15
        self.BUTTONS = [self.SELECT, self.OPTION]
        LED_SELECT = 19
        LED_OPTION = 17
        self.BUTTONS_LED = [LED_SELECT, LED_OPTION]
        self.LED_RED = {self.SELECT: LED_SELECT, self.OPTION: LED_OPTION}

        # {"COLOR NAME": [RED(0|1), GREEN(duty), BLUE(0|1)]}
        self.COLOR = {
            "RED": [1, 0, 0],
            "AMBER": [1, 0.2, 0],
            "YELLOW": [1, 1, 0],
            "GREEN": [0, 1, 0],
            "CYAN": [0, 1, 1],
            "BLUE": [0, 0, 1],
            "MAGENTA": [1, 0, 1],
            "WHITE": [1, 1, 1],
            "BLACK": [0, 0, 0],
        }

        # TMNUMS = {Actual Show: Internal Value}
        self.TMNUMS = {
            0: 63,
            1: 6,
            2: 91,
            3: 79,
            4: 102,
            5: 109,
            6: 125,
            7: 7,
            8: 127,
            9: 111,
            "": 0,
        }

        # segment = {"NAME": 2bit}
        #   HGFEDCBA
        # 0b01101101 = 0x6D = 109 = show "5"
        self.segment = {
            "G": 0b01000000,  #       A
            "F": 0b00100000,  #      ---
            "E": 0b00010000,  #   F |   | B   *
            "D": 0b00001000,  #      -G-      H (on 2nd segment)
            "C": 0b00000100,  #   E |   | C   *
            "B": 0b00000010,  #      ---
            "A": 0b00000001,  #       D
        }

    def pin_setup(self):
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)

        # GPIO Setup
        GPIO.setup(self.COLOR_LED_PORTS, GPIO.OUT)
        GPIO.setup(self.BUTTONS, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.BUTTONS_LED, GPIO.OUT)
        # Full color LED (GREEN only) PWM Setup
        self.pwm = GPIO.PWM(self.COLOR_LED_PORTS[1], self.freq)  # PWM (GREEN, freq)
        self.pwm.start(0)
        # tm1637 Setup
        CLK = 2
        DIO = 3
        self.tm = tm1637.TM1637(clk=CLK, dio=DIO)

    def value_reset(self, before):
        # Initializing Variables
        self.flag = True
        self.command = ClickStatus.NONE
        self.digit = 0
        self.temp_input_num = int(before[0])
        self.current_num_temp = [int(before[i]) for i in range(len(before))]
        self.current_view = queue.Queue(maxsize=1)
        self.key_result = queue.Queue(maxsize=1)
        self.input_result = queue.Queue(maxsize=1)
        self.event_flash = threading.Event()

        # Display Initialization
        self.color_led("BLACK")
        self.tm_put()
        self.tm_get_write()

    # Release Pin Settings
    def clear_pin(self):
        sleep(0.2)
        self.tm.write([0, 0, 0, 0])
        GPIO.output(self.COLOR_LED_PORTS, self.COLOR["BLACK"])

    # Performance of The Opening
    def initial_check(self):
        self.flow = threading.Thread(target=self.tm_flow)
        self.flow.start()
        self.flow = threading.Thread(target=self.led_flow)
        self.flow.start()
        # self.flow.join()

    # for tm1637 Flow Display
    def tm_flow(self):
        self.tm.write([0, 0, 0, 0])
        for i in range(3):
            self.input_seg("FABCDEGBAFGCDE")

    def input_seg(self, str_command):
        n = 0b00000000
        for i in range(len(str_command)):
            n ^= self.segment[str_command[i]]
            m = int(n)
            self.tm.write([m, m, m, m])
            sleep(0.043)

    # color_led("NAME") --> Full Color LED Lighting
    def color_led(self, color_name):
        GPIO.output(
            [self.COLOR_LED_PORTS[0], self.COLOR_LED_PORTS[2]],
            [self.COLOR[color_name][0], self.COLOR[color_name][2]],
        )
        # Green Only PWM Control
        self.pwm.ChangeDutyCycle(self.COLOR[color_name][1] * 100)

    # for LED Flow Display
    def led_flow(self):
        switching = True
        for j in range(3):
            for i, key in enumerate(self.COLOR):
                switching = not switching
                self.color_led(key)
                GPIO.output(self.LED_RED[self.SELECT], int(switching))
                GPIO.output(self.LED_RED[self.OPTION], int(not switching))
                sleep(0.1)
        self.click_led_off(self.SELECT)
        self.click_led_off(self.OPTION)

    # Red LEDs light up in conjunction with the button. key = SELECT or OPTION
    def click_led_on(self, key):
        GPIO.output(self.LED_RED[key], GPIO.HIGH)

    def click_led_off(self, key):
        GPIO.output(self.LED_RED[key], GPIO.LOW)

    # actual number --> tm value
    def tm_conversion(self, nums_list):
        tmnums_list = [self.TMNUMS[x] for x in nums_list]
        return tmnums_list

    # tm1637 Display
    def tm_get_write(self):
        self.tm.write(self.tm_conversion([x for x in self.current_view.get()]))

    def tm_put(self):
        self.current_view.put(self.current_num_temp)

    # current digit <-- input number
    def tm_pop_insert(self):
        if self.digit < 4:
            self.current_num_temp.pop(self.digit)
            self.current_num_temp.insert(self.digit, self.temp_input_num)

    def check_timeout(self):
        t_flag = time() - self.count_time < self.limit_t_minutes * 60
        if t_flag:
            return t_flag
        else:
            self.flag = False
            self.input_result.put(self.current_num_temp)
            self.digit = 5
            return t_flag

    # Blinking Current Digit
    def flash(self):
        self.blinking = True
        while self.flag:

            # Input Stage
            while (
                self.key_result.empty()
                and self.command == ClickStatus.NONE
                and self.digit < 4
                and self.check_timeout()
                and not self.event_flash.wait(0.1)
            ):
                if self.blinking:  # ON
                    self.tm_pop_insert()
                    self.tm_put()
                    self.tm_get_write()
                    sleep(0.5)
                else:  # OFF
                    self.tm.write([0], self.digit)
                    sleep(0.2)
                self.blinking = not self.blinking

            # Confirmation Stage
            while (
                self.key_result.empty()
                and self.digit == 4
                and self.check_timeout()
                and not self.event_flash.wait(0.1)
            ):
                if self.blinking:  # ON
                    self.tm_put()
                    self.tm_get_write()
                    sleep(0.4)
                else:  # OFF
                    self.tm.write([0, 0, 0, 0])
                self.blinking = not self.blinking
            self.event_flash.set()
            self.event_flash.clear()
            sleep(0.01)

    # Long press judgment
    def long_click(self):
        self.event_flash.set()
        while ClickStatus.LONG == self.command:
            sleep(0.1)
            self.temp_input_num = (self.temp_input_num + 1) % 10
            self.tm_pop_insert()
            self.tm_put()
            self.tm_get_write()
            sound.play(self.SELECT)
            sleep(0.2)
        self.event_flash.clear()

    # Reflect Button Behavior
    def click_to_num(self):
        self.on_key = self.key_result.get()

        # SELECT
        if self.SELECT in self.on_key:
            self.blinking = True
            if ClickStatus.SINGLE in self.on_key:
                self.temp_input_num = (self.temp_input_num + 1) % 10
            elif ClickStatus.DOUBLE in self.on_key:
                self.temp_input_num = (self.temp_input_num - 1) % 10
            else:
                long_pushed = threading.Thread(target=self.long_click)
                long_pushed.start()

        # OPTION
        elif self.OPTION in self.on_key:
            self.blinking = False
            if ClickStatus.SINGLE in self.on_key:
                if self.digit < 4:
                    self.digit += 1
                    if self.digit < 4:
                        self.temp_input_num = self.current_num_temp[self.digit]
                    else:
                        pass
                else:
                    self.digit = 0
                    self.temp_input_num = self.current_num_temp[self.digit]

            elif ClickStatus.DOUBLE in self.on_key:
                if self.digit > 0:
                    self.digit -= 1
                    if self.digit < 4:
                        self.temp_input_num = self.current_num_temp[self.digit]
                else:
                    self.digit = 3
                    self.temp_input_num = self.current_num_temp[self.digit]

            elif ClickStatus.LONG in self.on_key:
                if self.digit < 4:
                    self.digit = 4
                else:
                    self.flag = False
                    self.input_result.put(self.current_num_temp)
                    self.digit += 1

        # Display Reflection
        self.tm_pop_insert()
        self.tm_put()
        self.tm_get_write()
        print(self.on_key)
        # Blink Initialization
        self.event_flash.clear()

    # Wait for Button Input
    def standby_click(self, key):
        self.event_flash.set()
        t_on = time()
        self.click_led_on(key)
        sound.play(key)

        # LONG
        while self.command != ClickStatus.LONG:
            if not GPIO.input(key) == GPIO.LOW:
                t_off = time()
                break
            elif time() - t_on > self.LONG_INTERVAL and GPIO.input(key) == GPIO.LOW:
                self.command = ClickStatus.LONG
                break
            sleep(0.01)

        # SINGLE
        if self.command != ClickStatus.LONG:
            self.command = ClickStatus.SINGLE

            # DOUBLE
            while time() - t_off < self.DOUBLE_INTERVAL:
                if GPIO.input(key) == GPIO.LOW:
                    self.command = ClickStatus.DOUBLE
                    break
                sleep(0.01)

        # Update Value
        self.key_result.put([key, self.command])
        self.click_to_num()

        # Wait until Release
        while True:
            if not GPIO.input(key) == GPIO.LOW:
                break
            sleep(0.01)
        self.click_led_off(key)

    # main function
    def click_run(self, before, t):
        try:
            # Initialization
            self.count_time = t
            self.value_reset(before)
            thread_flash = threading.Thread(target=self.flash)
            thread_flash.start()

            # loop flag <-- Confirm Input (False)
            while self.flag:
                # Input Stage
                while self.digit < 4:
                    self.command = ClickStatus.NONE
                    if GPIO.input(self.SELECT) == GPIO.LOW:
                        self.standby_click(self.SELECT)
                    elif GPIO.input(self.OPTION) == GPIO.LOW:
                        self.standby_click(self.OPTION)
                    sleep(0.01)

                # Confirmation Stage
                while self.digit == 4:
                    self.command = ClickStatus.NONE
                    if GPIO.input(self.OPTION) == GPIO.LOW:
                        self.standby_click(self.OPTION)
                    sleep(0.01)

        finally:
            out = ""
            result = self.input_result.get()
            for i in range(4):
                out += str(result[i])
            self.tm.write([0, 0, 0, 0])
            return out  # e.g. "1234"


# Further processing is only performed if this code is called directly as a script.
if __name__ == "__main__":
    inst = Raspi()
    input_pass = inst.click_run()
