import time
import threading

class SnowflakeGenerator:
    """
    Distributed Unique ID Generator (Twitter Snowflake).
    Format:
    [1 bit unused] [41 bits timestamp] [10 bits machine_id] [12 bits sequence]
    """
    def __init__(self, machine_id=1):
        self.machine_id = machine_id
        self.epoch = 1672531200000  # Custom Epoch (Jan 1, 2023)
        self.sequence = 0
        self.last_timestamp = -1
        
        # Bit configurations
        self.timestamp_bits = 41
        self.machine_id_bits = 10
        self.sequence_bits = 12
        
        # Shifts
        self.timestamp_shift = self.machine_id_bits + self.sequence_bits
        self.machine_id_shift = self.sequence_bits
        
        self.lock = threading.Lock()

    def _current_timestamp(self):
        return int(time.time() * 1000)

    def next_id(self):
        with self.lock:
            timestamp = self._current_timestamp()

            if timestamp < self.last_timestamp:
                raise Exception("Clock moved backwards. Refusing to generate id")

            if timestamp == self.last_timestamp:
                self.sequence = (self.sequence + 1) & 4095
                if self.sequence == 0:
                    # Sequence overflow, wait for next millisecond
                    while timestamp <= self.last_timestamp:
                        timestamp = self._current_timestamp()
            else:
                self.sequence = 0

            self.last_timestamp = timestamp

            id = ((timestamp - self.epoch) << self.timestamp_shift) | \
                 (self.machine_id << self.machine_id_shift) | \
                 self.sequence
            
            return id

# Global instance
snowflake = SnowflakeGenerator(machine_id=1)

def generate_id():
    return snowflake.next_id()
