# Log and command inspired from : https://www.101computing.net/LMC/#

# TODO :
    # change color/icon/style like codeboot
    # change style codemirror
    
    # add a link to the filesystem
    
    # when I change a block memory do I change code instruction associate
    # when I change the change code do I change the memory in direct, or wait the new loading ?

    # multi lang don't work (in document.body, but work with playground)
    # onchange don't work, verify why
    
    # check log (if they are correct)
    # add try catch, verification, ... (so if error don't crash)

import time, math, js, pixels

# js.host_eval('CodeBoot.prototype.event_attrs.push("onchange")')

# === Constants Instruction ===

DEFAULTS = {
    "stop_step": -10,
    "begin_step": -5,
    "max_sleep": 40,
    "memory_size": 20
}

FILENAMES = {
    "html": "lmc.html",
    "log": "lmc_log.txt"
}

class InstructionSet:

    INP_string = "IN"
    OUT_string = "OUT"
    HLT_string = "HLT"

    DAT_string = "DAT"

    STA_string = "STO"
    LDA_string = "LDA"

    ADD_string = "ADD"
    SUB_string = "SUB"

    BRA_string = "BR"
    BRZ_string = "BRZ"
    BRP_string = "BRP"
    
    
    PIXELS_SET_string = "PS"
    PIXELS_X_string = "PX"
    PIXELS_Y_string = "PY"
    PIXELS_COLOR_R_string = "PCR"
    PIXELS_COLOR_G_string = "PCG"
    PIXELS_COLOR_B_string = "PCB"

    INSTRUCTIONS = {
        PIXELS_SET_string: 999, PIXELS_X_string: 990, PIXELS_Y_string: 991,
        PIXELS_COLOR_R_string: 994, PIXELS_COLOR_G_string: 995,
        PIXELS_COLOR_B_string: 996,
        INP_string: 901, OUT_string: 902, HLT_string: 0,
        DAT_string: -1, ADD_string: 1, SUB_string: 2,
        STA_string: 3, LDA_string: 5,
        BRA_string: 6, BRZ_string: 7, BRP_string: 8
    }
    CATEGORIES = {
        "NO_OPERAND": {INP_string, OUT_string, HLT_string, PIXELS_SET_string,
                       PIXELS_X_string, PIXELS_Y_string, PIXELS_COLOR_R_string,
                       PIXELS_COLOR_G_string, PIXELS_COLOR_B_string},
        "NEED_DATA": {ADD_string, SUB_string, STA_string, LDA_string},
        "NEED_ACCUMULATOR": {STA_string, ADD_string, SUB_string, OUT_string,
                             PIXELS_SET_string, PIXELS_X_string,
                             PIXELS_Y_string, PIXELS_COLOR_R_string,
                             PIXELS_COLOR_G_string, PIXELS_COLOR_B_string},
        "BRANCH": {BRA_string, BRZ_string, BRP_string},
        "INIT_ACCUMULATOR": {LDA_string, INP_string},
        "PIXELS": {PIXELS_SET_string, PIXELS_X_string, PIXELS_Y_string,
                   PIXELS_COLOR_R_string, PIXELS_COLOR_G_string,
                   PIXELS_COLOR_B_string}
    }
    
    HELP = {
        INP_string: "take input, code : {code} (different name : IN, INP)",
        OUT_string: "output accumulator, code : {code}",
        HLT_string: "terminate, code : {code}",
        DAT_string: "store data in memory, code : {code}",
        STA_string: "store from accumulator, code : {code} (different name : STO, STA)",
        LDA_string: "load to accumulator, code : {code}",
        ADD_string: "add to accumulator, code : {code}",
        SUB_string: "sub to accumulator, code : {code}",
        BRA_string: "branch always, code : {code} (different name : BR, BRA)",
        BRZ_string: "branch if accumulator is zero, code : {code}",
        BRP_string: "branch if accumulator is positive (or zero), code : {code}",
        PIXELS_SET_string: "<b>SPECIAL CODEBOOT :</b> set pixel (using the pixel accumulator), code : {code}",
        PIXELS_X_string: "<b>SPECIAL CODEBOOT :</b> set pixel x in pixel accumulator, code : {code}",
        PIXELS_Y_string: "<b>SPECIAL CODEBOOT :</b> set pixel y in pixel accumulator, code : {code}",
        PIXELS_COLOR_R_string: "<b>SPECIAL CODEBOOT :</b> set pixel color r in pixel accumulator (for RGB), code : {code}",
        PIXELS_COLOR_G_string: "<b>SPECIAL CODEBOOT :</b> set pixel color g in pixel accumulator (for RGB), code : {code}",
        PIXELS_COLOR_B_string: "<b>SPECIAL CODEBOOT :</b> set pixel color b in pixel accumulator (for RGB), code : {code}"
    }
    
    def help_str():
        text = ""
        for k, v in InstructionSet.HELP.items():
            text += f"<li><b>{k}</b> : {v.format(code=instr_code_str(k))}</li>"
        return text
    
    def decode_instruction(value):
        """
        Decode an instruction from an LMC machine code instruction.

        Args:
            value: an LMC machine code instruction as an integer

        Returns:
            A tuple (mnemonic, operand) where:
                - mnemonic is a string representing the instruction
                - operand is an integer or None, depending on the instruction.

        Raises:
            ValueError if the instruction is not recognized
        """
    
        opcode = value // 100
        operand = value % 100
        for name, code in InstructionSet.INSTRUCTIONS.items():
            if code == opcode or code == value:
                if name in InstructionSet.CATEGORIES["NO_OPERAND"]:
                    return (name, None)
                return (name, operand)
        return (InstructionSet.DAT_string, value)

    def encode_instruction(mnemonic, operand):
        """
        Encode an instruction from an LMC assembly language instruction.

        Args:
            mnemonic: the instruction mnemonic as a string
            operand: the instruction operand as an integer or None

        Returns:
            an LMC machine code instruction as an integer
        """
    
        if mnemonic in InstructionSet.CATEGORIES["NO_OPERAND"]:
            return InstructionSet.INSTRUCTIONS[mnemonic]
        if mnemonic == InstructionSet.DAT_string:
            return int(operand) if operand else 0
        r = InstructionSet.INSTRUCTIONS[mnemonic] * 100
        r += int(lmc.labels.get(operand, operand or 0))
        return r
    
    def disassemble(memory):
        """
        Disassemble an LMC memory (list of integers) into readable instructions.

        Args:
            memory: list of integers representing LMC instructions

        Returns:
            A list of tuples (address, mnemonic, operand or None)
        """

        used_instructions, used_data = lmc.trace_used_addresses()
        reverse_labels = {}
        for label, addr in lmc.labels.items():
            reverse_labels[addr] = label
            
        all_addresses = sorted(used_instructions.union(used_data))

        program = []
        for addr in all_addresses:
            instr = memory[addr]
            if addr in used_instructions:
                mnemonic, operand = InstructionSet.decode_instruction(instr)
                if operand in reverse_labels:
                    operand = reverse_labels.get(operand)
            else:
                # Otherwise treat it as DAT (data)
                mnemonic = InstructionSet.DAT_string
                operand = instr
            label = reverse_labels.get(addr) if addr in reverse_labels else None
            program.append((addr, label, mnemonic, operand))
        return program

# === Class ===
class LMC:
    def __init__(self):
        self.memory = []
        self.labels = {}
        self.program = []
        self.accumulator = 0
        self.accumulator_pixels = {
            "x": 0,
            "y": 0,
            "r": 0,
            "g": 0,
            "b": 0
        }
        self.pc = 0
        self.step = DEFAULTS["begin_step"]
        self.stack_input = []
        self.stack_input_last = []
        self.line_instruction = {}
        self.log_lines = []
        self.back_active = False
        self.stop_run = False
        self.break_run = False
        self.isRunning = False
        self.memory_size = DEFAULTS["memory_size"]

    def reset(self, all_variable = False, reset_dom = False):
        if all_variable:
            self.memory = []
            self.labels = {}
            self.program = []
            self.accumulator = 0
            self.accumulator_pixels = {
                "x": 0,
                "y": 0,
                "r": 0,
                "g": 0,
                "b": 0
            }
            self.pc = 0
        self.step = DEFAULTS["begin_step"]
        self.stack_input = []
        self.line_instruction = {}
        self.stop_run = False
        self.break_run = False
        self.isRunning = False
        if reset_dom:
            self.reset_dom()

    def reset_dom(self):  
        dom.set_disable("lmc-run-button", False)
        dom.set_disable("lmc-break-button", True)
        dom.set_disable("lmc-step-forward-button", False)
        dom.set_disable("lmc-step-back-button", True)
        dom.set_disable("lmc-stop-button", True)
        dom.set_disable("lmc-load-button", False)
        
        self.back_active = False
        display.highlight_block(clear = True)
        #dom.clear_console()
        #display.clear_pixel()
        

    def stepBack(self):
        """
        Run the LMC machine code program in reverse step mode.

        Reruns the program from the start to the two previous step,
        fast (with no interaction with the dom).
        If the previous step is reached, the input stack is reset and the
        step back mode is deactivated.
        Else, rerun the last step, while updating the dom.
        """
        if self.step < 0 :
            return
        
        stop_step=self.step-1
        self.step = DEFAULTS["begin_step"]
        self.stack_input_last = self.stack_input.copy()
        self.stack_input = []
        self.run(stop_step=stop_step-1, interaction_dom = False,
                 interaction_other = False, sleep_speed=0)
        if self.step == stop_step:
            self.is_finish(True, no_alert = True)
            self.stack_input_last = []
            
            self.back_active = False
            dom.set_disable("lmc-step-back-button", True)
            dom.set_disable("lmc-stop-button", True)
            dom.set_disable("lmc-load-button", False)
            return
        self.stepForward(interaction_dom = True, interaction_other = False)
        self.stack_input_last = []
        
    def stepForward(self, interaction_dom=True, interaction_other=True):
        """
        Run the LMC machine code program in forward step mode.

        If the back button is deactivated, it is active.
            Like we have done at least one step, we can now go back.
        """
        if self.step == DEFAULTS["begin_step"]:
            self.load()
        
        if not self.back_active:
            self.back_active = True
            dom.set_disable("lmc-step-back-button", False)
            dom.set_disable("lmc-stop-button", False)
            dom.set_disable("lmc-load-button", True)
            
        self.is_finish(self.simulate_lmc(interaction_dom = interaction_dom,
                                         interaction_other = interaction_other))

    def run(self, stop_step=DEFAULTS["stop_step"], interaction_dom = True,
            interaction_other = True, sleep_speed=-1):
        """
        Run the LMC machine code program.

        If the break button is deactivated, it is activated.
            Like we now run unstop, we can now break.
        If the back button is deactivated, it is activated.
            Like we have done at least one step, we can now go back.
        The program is run until the break button is click or the program
        is finished. If the sleep speed is not specified, in the arg,
        it is set to the value of the speed input. The program is run in chunks
        of 500 steps (in fast mode, when doing the back mode), with a delay
        between each chunk.
        """
        if self.stop_run :
            self.is_finish(True, no_alert = True)
            return
        if self.break_run :
            self.break_run = False
            return
        
        if not self.isRunning:
            self.isRunning = True
        
        if self.step == DEFAULTS["begin_step"]:
            self.load()
            
        if interaction_dom:
            dom.set_disable("lmc-run-button", True)
            dom.set_disable("lmc-break-button", False)
        
        if sleep_speed == -1:
            speed = dom.get_el("lmc-speed").value
            sleep_speed = math.log(DEFAULTS["max_sleep"]-int(speed)+1)
        
        number_chunk = 0
        stop_chunk = 500
        while True:
            if stop_step != DEFAULTS["stop_step"] and self.step >= stop_step:
                return
            finish = self.simulate_lmc(interaction_dom = interaction_dom,
                                       interaction_other = interaction_other)
            if stop_step == DEFAULTS["stop_step"]:
                if not self.back_active and interaction_dom:
                    self.back_active = True
                    dom.set_disable("lmc-step-back-button", False)
                    dom.set_disable("lmc-stop-button", False)
                    dom.set_disable("lmc-load-button", True)
                self.is_finish(finish)
                if finish:
                    return
                break
            elif number_chunk == stop_chunk:
                break
            number_chunk += 1
                
        
        js.setTimeout(lambda: self.run(stop_step = stop_step,
                                       interaction_dom = interaction_dom,
                                       interaction_other = interaction_other,
                                       sleep_speed = sleep_speed),
                      sleep_speed * 1000)

    def halt(self):
        """
        Stop the current program execution.
        """
        dom.set_disable("lmc-run-button", False)
        dom.set_disable("lmc-break-button", True)
        self.break_run = True
    
    def stop(self):
        """
        Stop the current program execution and reset the environment.
        """
        self.stop_run = True
        if not self.isRunning:
            self.is_finish(True, no_alert = True)
        
    
    def is_finish(self, finish, no_alert = False):
        """
        Called when the program finish.

        It reset the step counter, save the log,
        reset the buttons and display an alert.
        """
        
        if finish:
            self.step = DEFAULTS["begin_step"]
            # Save log
            with open(FILENAMES["log"], "w") as f:
                f.write("\n".join(self.log_lines))
            
            self.reset(reset_dom=True)
            if not no_alert:
                alert("finish")
            
    def load(self, source_code=""):
        """
        Reset the state of the Little Man Computer and load the given source code
        into memory. The source code is expected to be a string of assembly code
        with one instruction per line. The first pass of the parser is to find
        labels and assign them addresses. The second pass is to encode the
        instructions and store them in memory. The accumulator and program counter
        are reset to 0, and the step counter is reset to 0.
        """
        try:
            if source_code == "":
                source_code = display.editor_CodeMirror.getValue()

            self.reset(all_variable = True, reset_dom=True)  # Reset state

            lines = source_code.upper().splitlines()

            addr = 0

            # First pass: labels
            for i, line in enumerate(lines):
                line = line.split("#")[0].strip()
                if not line:
                    continue
                tokens = line.split()
                label = None
                if tokens[0] in InstructionSet.INSTRUCTIONS:
                    mnemonic = tokens[0]
                    operand = tokens[1] if len(tokens) > 1 else None
                else:
                    label, mnemonic = tokens[:2]
                    operand = tokens[2] if len(tokens) > 2 else None
                    self.labels[label] = addr
                self.program.append((addr, label, mnemonic, operand))
                self.line_instruction[addr] = i
                addr += 1

            self.memory = [0] * self.memory_size
            display.create_table()
            use_pixel = False
            for addr, label, mnemonic, operand in self.program:
                if mnemonic in InstructionSet.CATEGORIES["PIXELS"]:
                    use_pixel = True
                encoded = InstructionSet.encode_instruction(mnemonic, operand)
                self.memory[addr] = encoded
                dom.set_value(f"lmc-info_block-input-{addr}", encoded)
            
            if use_pixel:
                display.activate_pixel()
            else:
                display.deactivate_pixel()

            dom.clear_console()
            self.accumulator = 0
            self.pc = 0
            self.step = 0
            self.stack_input = []
        except Exception as e:
            alert(f"Error loading code: {e}")

    
    def simulate_lmc(self, interaction_dom = True, interaction_other = True):
        """
        Simulates the LMC computer for one instruction

        Args:
        interaction_dom (bool): Whether to interact with the DOM
        interaction_other (bool): Whether to interact with other parts of the system (e.g. log)

        Returns:
        Whether the simulation should finish
        """
        try:
            def log_line(msg):
                if interaction_other:
                    self.log_lines.append(msg)

            self.step += 1
            space_log = "   "
            
            if interaction_dom:
                e = None
                if self.pc in self.line_instruction:
                    e = self.line_instruction[self.pc]
                display.highlight_block(self.pc, "yellow", editor=e, clear=True)
            log_line("-" * 46)
            log_line("Fetching instruction...")
            log_line(f"{space_log}Set MAR to value held by Program Counter: {self.pc}")
            mar = self.pc
            self.pc += 1
            log_line(f"{space_log}Increment Program Counter by 1")
            log_line(f"{space_log}Fetch instruction from address stored in the MAR")
            instruction = self.memory[mar]
            log_line(f"{space_log}Fetched instruction: {instruction} stored in the MDR")
            log_line(f"{space_log}Copy instruction from the MDR to the CIR")
            cir = instruction

            mnemonic, operand = InstructionSet.decode_instruction(cir)
            
            def change_color(color):
                if interaction_dom:
                    display.highlight_block(operand, color)

            log_line(f"Decoding instruction stored in CIR : {cir}...")
            log_line(f"{space_log}{mnemonic}")

            log_line("Executing Instruction...")
            
            finish = False
            
            if mnemonic == InstructionSet.INP_string:
                log_line(f"   Waiting for user input")
                try:
                    if interaction_other:
                        val = int(prompt("Enter a number: "))
                    else:
                        self.stack_input_last.pop(0)
                except Exception:
                    val = 0
                    alert("Invalid input; defaulting to 0.")
                if interaction_dom:
                    dom.add_text("lmc-console-content", f">>> {val}\n")
                self.stack_input.append(val)
                self.accumulator = val
                log_line(f"{space_log}Store user input in Accumulator: {self.accumulator}")
            elif mnemonic == InstructionSet.OUT_string:
                log_line(f"{space_log}Output value held in the Accumulator: {self.accumulator}")
                if interaction_dom:
                    dom.add_text("lmc-console-content", f"{self.accumulator}\n")
            elif mnemonic == InstructionSet.HLT_string:
                log_line(f"{space_log}Halting execution")
                finish = True
            elif mnemonic == InstructionSet.STA_string:
                change_color("red")
                log_line(f"{space_log}Set MAR to the operand of the current instruction: {operand}")
                log_line(f"{space_log}Set MDR to the value held in the Accumulator: {self.accumulator}")
                self.memory[operand] = self.accumulator
                if interaction_dom:
                    dom.set_value(f"lmc-info_block-input-{operand}", self.accumulator)
                log_line(f"{space_log}Store MDR value {self.accumulator} at the memory location held in the MAR: {operand}")
            elif mnemonic == InstructionSet.LDA_string:
                change_color("green")
                log_line(f"{space_log}Set MAR to the operand of the current instruction: {operand}")
                self.accumulator = self.memory[operand]
                log_line(f"{space_log}Load memory[{operand}] value into Accumulator: {self.accumulator}")
            elif mnemonic == InstructionSet.ADD_string:
                change_color("green")
                log_line(f"{space_log}Add memory[{operand}] value to Accumulator: {self.accumulator} + {self.memory[operand]} = {self.accumulator + self.memory[operand]}")
                self.accumulator += self.memory[operand]
            elif mnemonic == InstructionSet.SUB_string:
                change_color("green")
                log_line(f"{space_log}Set MAR to the operand of the current instruction: {operand}")
                mdr = self.memory[operand]
                log_line(f"{space_log}Fetch data at the location held by the MAR and store it in the MDR: {mdr}")
                result = self.accumulator - mdr
                log_line(f"{space_log}Subtract MDR value from the Accumulator and store the result in the Accumulator: {self.accumulator}-{mdr}={result}")
                self.accumulator = result
            elif mnemonic == InstructionSet.BRA_string:
                log_line(f"{space_log}Set PC to the operand of the instruction: {operand}")
                self.pc = operand
            elif mnemonic == InstructionSet.BRZ_string:
                log_line(f"{space_log}Check if the value held in the accumulator is zero")
                if self.accumulator == 0:
                    log_line(f"{space_log}{self.accumulator}==0 - true")
                    self.pc = operand
                    log_line(f"{space_log}Set PC to the operand of the instruction: {operand}")
                else:
                    log_line(f"{space_log}{self.accumulator}==0 - false")
            elif mnemonic == InstructionSet.BRP_string:
                log_line(f"{space_log}Check if the value held in the accumulator is positive (>=0)")
                if self.accumulator >= 0:
                    log_line(f"{space_log}{self.accumulator}>=0 - true")
                    self.pc = operand
                    log_line(f"{space_log}Set PC to the operand of the instruction: {operand}")
                else:
                    log_line(f"{space_log}{self.accumulator}>=0 - false")

            elif mnemonic == InstructionSet.PIXELS_SET_string:
                log_line(f"{space_log}Set the pixels at position X={self.accumulator_pixels['x']}, Y={self.accumulator_pixels['y']} with color R={self.accumulator_pixels['r']}, G={self.accumulator_pixels['g']}, B={self.accumulator_pixels['b']}")
                pixels.set_pixel(self.accumulator_pixels["x"], self.accumulator_pixels["y"], rgb_to_short_hex((self.accumulator_pixels["r"], self.accumulator_pixels["g"], self.accumulator_pixels["b"])))
            elif mnemonic == InstructionSet.PIXELS_X_string:
                log_line(f"{space_log}Set X of pixels accumulator to the accumulator value: {self.accumulator}")
                self.accumulator_pixels["x"] = self.accumulator
            elif mnemonic == InstructionSet.PIXELS_Y_string:
                log_line(f"{space_log}Set Y of pixels accumulator to the accumulator value: {self.accumulator}")
                self.accumulator_pixels["y"] = self.accumulator
            elif mnemonic == InstructionSet.PIXELS_COLOR_R_string:
                log_line(f"{space_log}Set R of pixels accumulator to the accumulator value: {self.accumulator}")
                self.accumulator_pixels["r"] = self.accumulator
            elif mnemonic == InstructionSet.PIXELS_COLOR_G_string:
                log_line(f"{space_log}Set G of pixels accumulator to the accumulator value: {self.accumulator}")
                self.accumulator_pixels["g"] = self.accumulator
            elif mnemonic == InstructionSet.PIXELS_COLOR_B_string:
                log_line(f"{space_log}Set B of pixels accumulator to the accumulator value: {self.accumulator}")
                self.accumulator_pixels["b"] = self.accumulator
            
            log_line(f"{space_log}Accumulator now contains: {self.accumulator=}, {self.accumulator_pixels=}")
            if interaction_dom:
                display.set_info_panel()
            return finish
        except Exception as e:
            alert(f"Simulation error: {e}")
            return True
        
    def trace_used_addresses(self, pc=0, visited=None, dat=None):
        """
        Recursively explore all reachable instructions from memory[pc].

        Args:
            pc: current program counter
            visited: set of executed addresses
            dat: set of data addresses (we think) is use for DAT

        Returns:
            visited: set of all reachable instruction addresses
        """
        if visited is None:
            visited = set()
        if dat is None:
            dat = set()
        
        if pc < 0 or pc >= len(self.memory) or pc in visited:
            return visited, dat

        visited.add(pc)
        if pc in dat:
            dat.remove(pc)

        instr = self.memory[pc]
        mnemonic, operand = InstructionSet.decode_instruction(instr)

        if mnemonic == InstructionSet.HLT_string:
            return visited, dat
        elif mnemonic == InstructionSet.BRA_string:
            return self.trace_used_addresses(operand, visited, dat)
        elif mnemonic in InstructionSet.CATEGORIES["BRANCH"]:
            # Explore both: branch taken and fall-through
            visited1, dat1 = self.trace_used_addresses(operand, visited.copy(),
                                                       dat.copy())
            visited2, dat2 = self.trace_used_addresses(pc + 1, visited1, dat1)
            return visited2, dat2
        elif mnemonic in InstructionSet.CATEGORIES["NEED_DATA"]:
            if operand is not None:
                dat.add(operand)
            return self.trace_used_addresses(pc + 1, visited, dat)
        else:
            return self.trace_used_addresses(pc + 1, visited, dat)

class Display:
    def __init__(self, size=DEFAULTS["memory_size"]):
        self.editor_CodeMirror = None
        self.last_editor_index = []

    def create_page(self):
        """
        Set up the page for the LMC simulator.
        Loads the HTML from file, sets up the CodeMirror editor for the LMC code,
        and adds an event handler to update the accumulator display.
        """
        try:
            with open(FILENAMES["html"], "r") as f:
                html = f.read()
        except IOError as e:
            alert(f"Error while reading HTML file, {FILENAMES['html']}: {e}")
        
        document.body.innerHTML = html.format(max_speed=DEFAULTS["max_sleep"],
                                              memory_size=lmc.memory_size,
                                              help_instruction=InstructionSet.help_str())
        
        
        dom.add_event_change("lmc-accumulator", lambda e: change_accumulator(e))
        #for k in lmc.accumulator_pixels:
        dom.add_event_change(f"lmc-accumulator-pixel-x", lambda e: change_accumulator_pixels("x", e))
        dom.add_event_change(f"lmc-accumulator-pixel-y", lambda e: change_accumulator_pixels("y", e))
        dom.add_event_change(f"lmc-accumulator-pixel-r", lambda e: change_accumulator_pixels("r", e))
        dom.add_event_change(f"lmc-accumulator-pixel-g", lambda e: change_accumulator_pixels("g", e))
        dom.add_event_change(f"lmc-accumulator-pixel-b", lambda e: change_accumulator_pixels("b", e))
        dom.add_event_change("lmc-memory-size", lambda e: change_memory_size(e))
        
        import "https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.16/addon/mode/simple.min.js"
        import "https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.5/addon/lint/lint.min.js"
        
        self.create_table()
        time.sleep(0.5)
        
        list_instructions = "|".join(InstructionSet.INSTRUCTIONS.keys())
        while True:
            try:
                js.host_eval(f"""
                CodeMirror.defineSimpleMode("lmc", {{
                    start: [
                        {{regex: /#.*/, token: "lmc-comment"}},

                        // Labels (at the start of a line)
                        {{regex: /^[ \\t]*[A-Za-z_][A-Za-z0-9_]*(?=\\s+({list_instructions})\\b)/, token: "lmc-label"}},

                        // Instructions
                        {{regex: /\\b({list_instructions})\\b/, token: "lmc-instruction"}},

                        // Numeric operand
                        {{regex: /\\b\\d+\\b/, token: "lmc-operand-number"}},

                        // Operand labels (non-numeric operands after instructions)
                        {{regex: /\\b[A-Za-z_][A-Za-z0-9_]*\\b/, token: "lmc-operand-label"}},

                        {{regex: /\\s+/, token: null}}
                    ],
                    meta: {{
                        lineComment: "#"
                    }}
                }});
                """)
                break
            except:
                time.sleep(0.1)

        f = js.host_eval("(function (x){lmcLinter = x})")
        f(lmc_linter)
        js.host_eval("""
        lmc_editor_CodeMirror = CodeMirror.fromTextArea(document.getElementById('lmc-code-input'), {
            mode: "lmc",
            lineNumbers: true,
            theme: "lmc_default",
            gutters: ["CodeMirror-lint-markers"],
            lint: {
                getAnnotations: lmcLinter,
                async: false
            }
        });
        """)
        self.editor_CodeMirror = \lmc_editor_CodeMirror
        
        #self.activate_pixel()
        
    def create_table(self, number_columns=2, keep_val = False):
        """
        Create the HTML for the memory table in the web page.
        Generates HTML for a table with lmc.memory_size blocks, each with an id and an input field, and
        a specific number of columns.
        Also adds an event handler to update the accumulator display when the input values change.
        """
        table_html = '<thead>'
        table_html += '<tr>'
        for i in range(0, number_columns):
            table_html+='<th class="lmc-th"><span class="cb-fr">Adresse</span><span class="cb-en">Address</span></th>'
            table_html += '<th class="lmc-th"><span class="cb-fr">Valeur</span><span class="cb-en">Value</span></th>'
          
        table_html+='</tr>'
        table_html += '</thead>'
        table_html += '<tbody id="lmc-memory-table-body">'
        memory_size_previous = len(lmc.memory)
        t = lmc.memory_size//number_columns
        for i in range(0, t):
            table_html += f'<tr id="lmc-block-{i}">'
            for j in range(i*number_columns, (i+1)*number_columns):
                table_html += f'<td id="lmc-id_block-{j}" class="lmc-td">{j}</td>'
                table_html += f'<td id="lmc-info_block-{j}" class="lmc-td"><input type="number" id="lmc-info_block-input-{j}" class="lmc-input-table" min="0" max="999" value="{lmc.memory[j] if (keep_val and j < memory_size_previous) else "000"}"></td>' # onchange="lambda e: change_block(e)"
            table_html += '</tr>'
        
        table_html += f'<tr id="lmc-block-{i}">'
        for j in range(t*number_columns, lmc.memory_size):
            table_html += f'<td id="lmc-id_block-{j}" class="lmc-td">{j}</td>'
            table_html += f'<td id="lmc-info_block-{j}" class="lmc-td"><input type="number" id="lmc-info_block-input-{j}" class="lmc-input-table" min="0" max="999" value="{lmc.memory[j] if (keep_val and j < memory_size_previous) else "000"}"></td>'
        table_html += '</tr>'
        table_html += '</tbody>'
        
        dom.get_el(f"lmc-table").innerHTML = table_html
        
        for i in range(0, lmc.memory_size):
            dom.add_event_change(f"lmc-info_block-input-{i}", lambda e: change_block(e))

    def highlight_block(self, index=None, color=None, editor=None, clear=False):
        """
        Highlight a block in the memory table, and optionally an editor line.
        
        Args:
        - index: The index of the block to highlight in the table.
        - color: The color to use for the highlighting.
        - editor: The line number of the editor to highlight. If None, the editor is left unchanged.
        - clear: If True, clear all highlighting before adding the new one. If False, add the new highlighting on top of the existing one.
        """
        if clear:
            for cell in document.querySelectorAll("#lmc-memory-table-body td"):
                cell.style.backgroundColor = ""
            if self.last_editor_index is not None:
                for l_e_i in self.last_editor_index:
                    self.editor_CodeMirror.removeLineClass(l_e_i, 'background', 'lmc-highlight-line')
                self.last_editor_index = []
                

        if index is not None and color is not None:
            row = dom.get_el(f"lmc-id_block-{index}")
            if row is not None:
                row.style.backgroundColor = color
            row = dom.get_el(f"lmc-info_block-{index}")
            if row is not None:
                row.style.backgroundColor = color

        if editor is not None:
            self.editor_CodeMirror.addLineClass(editor, 'background', 'lmc-highlight-line')
            self.last_editor_index.append(editor)

    def set_info_panel(self, pc = None):
        """
        Update the values of the step number, accumulator, and program counter in the information panel.
        """
        dom.set_text("lmc-step-number", lmc.step)
        dom.set_value("lmc-accumulator", lmc.accumulator)
        for k,v in lmc.accumulator_pixels.items():
            dom.set_value(f"lmc-accumulator-pixel-{k}", v)
        #dom.set_text("lmc-pc", lmc.pc)
    
    def activate_pixel(self):
        console = dom.get_class("lmc-console")[0]
        pixel = dom.get_class("cb-pixels-window")[0]
        
        pos_console = console.getBoundingClientRect()
        pos_pixel = console.getBoundingClientRect()
        
        # reposition pixel window
        pixel.style.left = str(pos_console.right - pos_pixel.height) + 'px'
        pixel.style.top = str(pos_console.top) + 'px'
        pixel.style.zIndex = 0
        pixel.style.display = "inline"
        
        for k in lmc.accumulator_pixels:
            dom.get_el(f"lmc-accumulator-pixel-{k}").parentElement.style.display = "flex"   
  
        display.clear_pixel()
    
    def deactivate_pixel(self):
        pixel = document.getElementsByClassName("cb-pixels-window")[0]
        
        pixel.style.display = "none"
        for k in lmc.accumulator_pixels:
            dom.get_el(f"lmc-accumulator-pixel-{k}").parentElement.style.display = "none"

    def clear_pixel(self):
        pixels.fill_rectangle(0, 0, 12, 12, "#000")

class DOM:
    def get_el(self, id):
        try:
            return document.getElementById(id)
        except:
            alert(f"Element {id} not found")
            return None

    def get_class(self, string):
        try:
            return document.getElementsByClassName(string)
        except:
            alert(f"Error while getting elements with class {string}")
            return []

    def add_event_change(self, id, func):
        self.get_el(id).addEventListener("change", lambda e: func(e))

    def set_disable(self, id, disable):
        self.get_el(id).disabled = disable

    def set_value(self, id, text):
        self.get_el(id).value = str(text)
        
    def set_text(self, id, text):
        self.get_el(id).innerText = str(text)

    def add_text(self, id, text):
        self.get_el(id).innerText += str(text)

    def clear_console(self):
        self.set_text("lmc-console-content", "")

# === Event functions ===

def change_accumulator(e):
    try:
        lmc.accumulator = int(e.target.value)
    except:
        alert("Invalid accumulator value")

def change_accumulator_pixels(id, e):
    try:
        lmc.accumulator_pixels[id] = int(e.target.value)
    except:
        alert(f"Invalid pixel value for {id}")

def change_memory_size(e):
    try:
        size = int(e.target.value)
        if size > 0 and size < 100:
            lmc.memory_size = size
        else:
            raise ValueError()
        if not lmc.isRunning:
            display.create_table(keep_val=True)
    except:
        alert("Invalid memory size")

def change_block(e):
    try:
        id_el = int(e.target.id.split("-")[-1])
        if 0 <= id_el < len(lmc.memory):
            lmc.memory[id_el] = int(e.target.value)
        else:
            raise IndexError()
    except:
        alert("Invalid memory block value")

def download_log():
    js.host_eval(f'blob = new Blob(["{'\\n'.join(lmc.log_lines).replace('"', '\\"') }"], {{ type: "text/plain" }});')
    js.host_eval("url = URL.createObjectURL(blob)")
    
    a = document.createElement('a')
    a.href = \url
    a.download = 'lmc-log.txt'
    document.body.appendChild(a)
    a.click()
    
    js.host_eval("URL.revokeObjectURL(url)")
    document.body.removeChild(a)

def memory_to_code():
    disassembled = InstructionSet.disassemble(lmc.memory)
    text_code = ""
    for addr, label, mnemonic, operand in disassembled:
        text_code += f"{label:}" if label else "     "
        text_code += f" {mnemonic} "
        text_code += f"{operand:02}" if operand is not None else ""
        text_code += "\n"
    display.editor_CodeMirror.setValue(text_code)

def hide_help():
    dom.get_el("lmd-help-box").style.display="none"
def show_help():
    dom.get_el("lmd-help-box").style.display="block"

# === Utils ===

def rgb_to_short_hex(rgb):
    # Ensure each channel is a multiple of 17 (i.e., 0x11)
    text = ""
    for c in rgb:
        t = c % 17
        if t != 0:
            #raise ValueError("RGB values must be multiples of 17 to be represented in 3-digit hex.")
            if t < 8:
                text += f'{(c-t) // 17:X}'
            else:
                text += f'{(c+17-t) // 17:X}'
        else:
            text += f'{c // 17:X}'
    return '#' + text.lower()    

def instr_code_str(instr):
    if InstructionSet.INSTRUCTIONS[instr] <= 0 or InstructionSet.INSTRUCTIONS[instr] > 10:
        return str(InstructionSet.INSTRUCTIONS[instr])
    else:
        return str(InstructionSet.INSTRUCTIONS[instr]) + "XX"

# === Error Detection ===

def lmc_linter(text, options, cm):
    try:
        errors = []
        lines = text.split('\n')
        test_label_regex = js.host_eval("""
        (function (label){
            const labelRegex = /^[A-Za-z_][A-Za-z0-9_]*$/;
            return labelRegex.test(label);
        })
    """)
        get_cm_pos = js.host_eval("""
        (function (i, j){
            return CodeMirror.Pos(i, j);
        })
    """)

        labels = set()
        used_labels = {}
        accumulator_initialized = False
        addr = 0
        index_change = []

        for index, line in enumerate(lines):
            line_number = index
            
            line = line.upper()
            
            code = line.split("#")[0].strip()
            if not code:
                continue

            tokens = code.split()
            label, instr, operand = None, None, None

            if len(tokens) == 1:
                instr = tokens[0]
            elif tokens[0] in InstructionSet.INSTRUCTIONS:
                instr, operand = tokens[0], tokens[1]
            else:
                label, instr = tokens[0], tokens[1]
                if len(tokens) > 2:
                    operand = tokens[2]
            
            if lmc.back_active:
        
                # de we add instruction, if yes it didn't exists before, so we can't compare
                if addr < len(lmc.program):
                    last_addr, last_label, last_instr, last_operand = lmc.program[addr]
                    # do we have a link for this instruction ?
                    last_index = lmc.line_instruction[addr] if addr in lmc.line_instruction else None
                    
                    # for the next instruction, did the line in the code change
                    # (we add a comment or new line)
                    if index != last_index:
                        
                        # was the previous index highlighted, if yes change the location
                        if last_index is not None and last_index not in index_change and last_index in display.last_editor_index:
                            display.last_editor_index.remove(last_index)
                            display.last_editor_index.append(index)
                            index_change.append(index) # to not rechange it
                            display.editor_CodeMirror.removeLineClass(last_index, 'background', 'lmc-highlight-line')
                            display.editor_CodeMirror.addLineClass(index, 'background', 'lmc-highlight-line')
                        
                        # is it really the same instruction, if yes update the link
                        if last_label == label and last_instr == instr and last_operand == operand:
                            lmc.line_instruction[addr] = index
                            
                    # the instruction changed, remove the link
                    if last_index is not None and (last_label != label or last_instr != instr or last_operand != operand):
                        lmc.line_instruction.pop(addr)
                        
                    addr += 1

            if label:
                if not test_label_regex(label):
                    errors.append({
                        "from": get_cm_pos(line_number, 0),
                        "end": get_cm_pos(line_number, 0 + len(label)),
                        "message": "Invalid label name",
                        "severity": "error",
                        "className": "lmc-error"
                    })
                elif label in labels:
                    errors.append({
                        "from": get_cm_pos(line_number, 0),
                        "end": get_cm_pos(line_number, 0 + len(label)),
                        "message": "Duplicate label",
                        "severity": "error",
                        "className": "lmc-error"
                    })
                else:
                    labels.add(label)

            if instr not in InstructionSet.INSTRUCTIONS:
                col = line.find(instr)
                errors.append({
                    "from": get_cm_pos(line_number, col),
                    "end": get_cm_pos(line_number, col + len(instr)),
                    "message": "Unknown instruction",
                    "severity": "error",
                    "className": "lmc-error"
                })

            if operand and instr != 'DAT':
                col = line.find(operand)
                if instr in InstructionSet.CATEGORIES["NO_OPERAND"]:
                    errors.append({
                        "from": get_cm_pos(line_number, col),
                        "end": get_cm_pos(line_number, col + len(operand)),
                        "message": "No operand expected",
                        "severity": "error",
                        "className": "lmc-error"
                    })
                if not operand.isdigit() and not test_label_regex(operand):
                    errors.append({
                        "from": get_cm_pos(line_number, col),
                        "end": get_cm_pos(line_number, col + len(operand)),
                        "message": "Invalid operand",
                        "severity": "error",
                        "className": "lmc-error"
                    })
                if not operand.isdigit():
                    if operand not in used_labels: used_labels[operand] = []
                    used_labels[operand].append((line_number, col, operand))

            if instr in InstructionSet.CATEGORIES["NEED_ACCUMULATOR"] and not accumulator_initialized:
                errors.append({
                    "from": get_cm_pos(line_number, 0),
                    "end": get_cm_pos(line_number, 0 + len(line)),
                    "message": "Accumulator used before being initialized",
                    "severity": "warning",
                    "className": "lmc-warning"
                })

            if instr in InstructionSet.CATEGORIES["INIT_ACCUMULATOR"]:
                accumulator_initialized = True

        for label, info_lines in used_labels.items():
            if label not in labels:
                for line, col, _ in info_lines:
                    errors.append({
                        "from": get_cm_pos(line, col),
                        "end": get_cm_pos(line, col + len(label)),
                        "message": "Undefined label",
                        "severity": "error",
                        "className": "lmc-error"
                    })

        #return errors # Don't show any style for the errors, so do it manually
        js.host_eval("""lmc_editor_CodeMirror.getDoc().getAllMarks().forEach(mark => mark.clear())""")
        for error in errors:
            display.editor_CodeMirror.getDoc().markText(
                {"line": error["from"].line, "ch": error["from"].ch},
                {"line": error["end"].line, "ch": error["end"].ch},
                {"className": error["className"], "title": error["message"]}
            )
        
        return []
    except Exception as e:
        alert(f"Error while validating code: {e}")
        return []

# === Main ===

display = Display()
dom = DOM()
lmc = LMC()

display.create_page()
