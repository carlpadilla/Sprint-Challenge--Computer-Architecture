"""CPU functionality."""
import sys


class CPU:
    """Main CPU class."""

    def __init__(self):
        """Construct a new CPU."""

        # OPCODEs
        self.opcodes = {
            "ADD": 0b10100000,
            "CALL": 0b01010000,
            "CMP": 0b10100111,
            "DIV": 0b10100011,
            "HLT": 0b00000001,
            "JEQ": 0b01010101,
            "JMP": 0b01010100,
            "JNE": 0b01010110,
            "LDI": 0b10000010,
            "MUL": 0b10100010,
            "PRN": 0b01000111,
            "POP": 0b01000110,
            "PUSH": 0b01000101,
            "RET": 0b00010001,
            "SUB": 0b10100001
        }

        # Initialize ram to hold 256 bytes of memory
        self.ram = [0] * 256

        # Eight general purpose registers
        self.reg = [0] * 8

        # self.reg[5] is reserved as the Interrupt Mark (IM)
        # self.reg[6] is reserved as the Interrupt Status (IS)
        # self.reg[7] is reserved as the Stack Pointer (SP)

        # Initialize the SP to address 0xF4
        self.reg[7] = 0xF4

        # Internal Registers

        # Program Counter - address of the currently executing instruction
        self.pc = 0

        # Instruction Register - contains a copy of the currently executing
        # instruction
        self.ir = None

        # Memory Address Register - holds the memory address we're reading or
        # writing
        self.mar = 0

        # Memory Data Register - holds the value to write or the value just read
        self.mdr = None

        # Flags Register - holds the current flags status
        # If a particular bit is set, that flag is "true"

        # FL bits: 00000LGE
        # L Less-than: during a CMP, set to 1 if registerA is less than registerB, zero otherwise.
        # G Greater-than: during a CMP, set to 1 if registerA is greater than registerB, zero otherwise.
        # E Equal: during a CMP, set to 1 if registerA is equal to registerB, zero otherwise.
        self.fl = 0b00000000

        # Loop in cpu_run() will run while this is True
        self.running = True

        # Set up a branch table
        self.branchtable = {}
        self.branchtable[self.opcodes['HLT']] = self.handle_hlt
        self.branchtable[self.opcodes['LDI']] = self.handle_ldi
        self.branchtable[self.opcodes['PRN']] = self.handle_prn
        self.branchtable[self.opcodes['PUSH']] = self.handle_push
        self.branchtable[self.opcodes['POP']] = self.handle_pop
        self.branchtable[self.opcodes['CALL']] = self.handle_call
        self.branchtable[self.opcodes['RET']] = self.handle_ret
        self.branchtable[self.opcodes['JMP']] = self.handle_jmp
        self.branchtable[self.opcodes['JEQ']] = self.handle_jeq
        self.branchtable[self.opcodes['JNE']] = self.handle_jne

    def alu(self, op, reg_a, reg_b):
        """ALU operations."""
        if op == self.opcodes['ADD']:
            self.reg[reg_a] += self.reg[reg_b]
        elif op == self.opcodes['SUB']:
            self.reg[reg_a] -= self.reg[reg_b]
        elif op == self.opcodes['MUL']:
            self.reg[reg_a] *= self.reg[reg_b]
        elif op == self.opcodes['DIV']:
            self.reg[reg_a] /= self.reg[reg_b]
        elif op == self.opcodes['CMP']:
            # Reset the flags
            self.fl = 0b00000000

            # If reg_a and reg_b are equal, set the E flag to 1 or 0 otherwise
            if self.reg[reg_a] == self.reg[reg_b]:
                self.fl = self.fl | 0b00000001

            # If reg_a is greater than reg_b, set the G flag to 1 or 0 otherwise
            if self.reg[reg_a] > self.reg[reg_b]:
                self.fl = self.fl | 0b00000010

            # If reg_a is less than reg_b, set the L flag to 1 or 0 otherwise
            if self.reg[reg_a] < self.reg[reg_b]:
                self.fl = self.fl | 0b00000100

        else:
            raise Exception("Unsupported ALU operation")

    def handle_call(self):
        # Get the address of the instruction directly after CALL
        return_address = self.pc + 2

        # Push it onto the stack
        # Decrement the Stack Pointer
        self.reg[7] -= 1

        # Store the return address at the top of the stack
        self.ram_write(self.reg[7], return_address)

        # Get the register to fetch from
        register_num = self.ram_read(self.pc + 1)

        # Grab the address stored in that register
        address = self.reg[register_num]

        # Set the PC to that address
        self.pc = address

    def handle_hlt(self):
        self.running = False
        sys.exit()

    def handle_jeq(self):
        # Isolate the equal flag
        equal = self.fl & 0b00000001

        if equal:
            # Get the register to retrieve from
            register = self.ram_read(self.pc + 1)

            # Get the address stored in that register
            address = self.reg[register]

            # Jump to that address
            self.pc = address
        else:
            # Otherwise go to the next instruction
            self.pc += 2

    def handle_jmp(self):
        # Get the register to retrieve from
        register = self.ram_read(self.pc + 1)

        # Get the address to jump to, from the register
        address = self.reg[register]

        # Set the PC to the address
        self.pc = address

    def handle_jne(self):
        # Isolate the equal flag
        equal = self.fl & 0b00000001

        if not equal:
            # Get the register to retrieve from
            register = self.ram_read(self.pc + 1)

            # Get the address stored in that register
            address = self.reg[register]

            # Jump to that address
            self.pc = address
        else:
            # Otherwise go to the next instruction
            self.pc += 2

    def handle_ldi(self):
        register = self.ram_read(self.pc + 1)
        value = self.ram_read(self.pc + 2)

        self.reg[register] = value

    def handle_pop(self):
        # Get the value from address pointed to by the Stack Pointer
        value = self.ram_read(self.reg[7])

        # Get the register number to copy into
        register = self.ram_read(self.pc + 1)

        # Copy the value into the register
        self.reg[register] = value

        # Increment the Stack Pointer
        self.reg[7] += 1

    def handle_prn(self):
        register = self.ram_read(self.pc + 1)
        print(self.reg[register])

    def handle_push(self):
        # Decrement the Stack Pointer
        self.reg[7] -= 1

        # Get the register to retrieve the value from
        register = self.ram_read(self.pc + 1)

        # Get the value from the register
        value = self.reg[register]

        # Copy the value to the address pointed to by the SP
        self.ram_write(self.reg[7], value)

    def handle_ret(self):
        # Pop the address at the top of the stack

        # Get the address pointed to by the Stack Pointer
        address = self.ram_read(self.reg[7])

        # Increment the Stack Pointer
        self.reg[7] += 1

        # Point to PC to that address
        self.pc = address

    def load(self):
        """Load a program into memory."""
        # Print an error if user did not provide a program to load
        # and exit the program
        if len(sys.argv) < 2:
            print("Please provide a file to open\n")
            print("Usage: filename file_to_open\n")
            sys.exit()

        try:
            # Open the file provided as the 2nd arg
            with open(sys.argv[1]) as file:
                for line in file:
                    # Split the line into an array, with '#' as the delimiter
                    comment_split = line.split('#')

                    # The first string is a possible instruction
                    possible_instruction = comment_split[0]

                    # If it's an empty string, this line is a comment
                    if possible_instruction == '':
                        continue

                    # If the string starts with a 1 or 0, it's an instruction
                    if possible_instruction[0] == '1' or possible_instruction[0] == '0':
                        # Get the first 8 values (remove trailing whitespace and
                        # chars)
                        instruction = possible_instruction[:8]

                        # Convert the instruction into an integer and store it
                        # in memory
                        self.ram[self.mar] = int(instruction, 2)

                        # Increment the memory address register value
                        self.mar += 1

        except FileNotFoundError:
            print(f'{sys.argv[0]}: {sys.argv[1]} not found')
            sys.exit()

    def ram_read(self, address):
        """
        Should accept the address to read and return the value stored there
        """
        # Save address to MAR
        self.mar = address

        # Save data to MDR
        self.mdr = self.ram[self.mar]

        return self.mdr

    def ram_write(self, address, value):
        """
        Should accept a value to write, and the address to write to
        """
        # Save address to MAR
        self.mar = address

        # Save value to MDR
        self.mdr = value

        # Save the value in MDR to the memory address stored in MAR
        self.ram[self.mar] = self.mdr

    def run(self):
        """Run the CPU."""
        while self.running:
            # Get the current instruction
            instruction = self.ram_read(self.pc)

            # Store a copy of the current instruction in IR register
            self.ir = instruction

            # Get the number of operands
            num_operands = instruction >> 6

            # Store the bytes at PC+1 and PC+2
            operand_a = self.ram_read(self.pc + 1)
            operand_b = self.ram_read(self.pc + 2)

            # Check if it's an ALU instruction
            is_alu_operation = (instruction >> 5) & 0b1

            if is_alu_operation:
                self.alu(self.ir, operand_a, operand_b)
            else:
                self.branchtable[self.ir]()

            # Check if this instruction  sets the PC directly
            sets_pc = (instruction >> 4) & 0b0001

            if not sets_pc:
                # Point the PC to the next instruction in memory
                self.pc += num_operands + 1

    def trace(self):
        """
        Handy function to print out the CPU state. You might want to call this
        from run() if you need help debugging.
        """

        print(f"TRACE: PC: %02X | FL:  %02X | %02X %02X %02X |" % (
            self.pc,
            self.fl,
            # self.ie,
            self.ram_read(self.pc),
            self.ram_read(self.pc + 1),
            self.ram_read(self.pc + 2)
        ), end='')

        for i in range(8):
            print(" %02X" % self.reg[i], end='')

        print()
