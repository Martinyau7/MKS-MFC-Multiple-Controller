#!/usr/bin/env python3

import struct
import tkinter as tk
from tkinter import messagebox
from pymodbus.client import ModbusTcpClient
from pymodbus.exceptions import ModbusIOException

'''
Communicates with MKS MFC Using ModBUS protocol.
V 1.0.0

Martin Yau (With the help of CoPilot)
August 28th, 2025
'''
# Configuration
MFC_PORT = 502
UNIT_ID = 1
POLL_INTERVAL_MS = 100
NUMBER_OF_CONTROLLERS = 3

# Modbus register addresses
FLOW_REG = 0x4000
SETPOINT_REG = 0xA000
ZERO_FLOW_REG = 0xE003

# Float ↔ registers packing formats
PACK_FLOAT = '>f'
PACK_WORDS = '>HH'

def float_from_regs(regs):
    packed = struct.pack(PACK_WORDS, regs[0], regs[1])
    return struct.unpack(PACK_FLOAT, packed)[0]

def regs_from_float(val):
    packed = struct.pack(PACK_FLOAT, val)
    return list(struct.unpack(PACK_WORDS, packed))

class ControllerFrame:
    def __init__(self, master, client, name, disconnect_callback):
        self.client = client
        self.disconnect_callback = disconnect_callback
        #self.offset = 0.0  # Local offset for flow reading

        self.frame = tk.LabelFrame(master, text=name, padx=10, pady=10)
        self.frame.pack(fill=tk.X, padx=1, pady=5)
#Once connected, the following values appear.
#Offset was taken out, can implement later.

        self.flow_var = tk.StringVar(value='Flow: --.--')
        tk.Label(self.frame, textvariable=self.flow_var, font=('Helvetica', 16, 'bold')).grid(row=0, column=0, sticky='w')
        tk.Button(self.frame, text='Zero Flow', font=('Helvetica', 14), command=self.zero_flow).grid(row=0, column=3, sticky='e', padx=5)

        #self.offset_display_var = tk.StringVar(value='Offset Applied: 0.00')
        #tk.Label(self.frame, textvariable=self.offset_display_var, font=('Helvetica', 14)).grid(row=1, column=0, sticky='w', columnspan=3)

        self.sp_var = tk.StringVar(value='Setpoint: --.--')
        tk.Label(self.frame, textvariable=self.sp_var, font=('Helvetica', 16)).grid(row=2, column=0, sticky='w')

        self.meta_var = tk.StringVar(value='Device Info: --')
        tk.Label(self.frame, textvariable=self.meta_var, font=('Helvetica', 14)).grid(row=3, column=0, sticky='w', columnspan=3)

        setpoint_frame = tk.Frame(self.frame)
        setpoint_frame.grid(row=5, column=1, columnspan=3)

        tk.Label(setpoint_frame, text='New Setpoint:', font=('Helvetica', 14)).pack(side=tk.LEFT)
        self.sp_entry = tk.Entry(setpoint_frame, width=8, font=('Helvetica', 14))
        self.sp_entry.pack(side=tk.LEFT)
        tk.Button(setpoint_frame, text='Set', font=('Helvetica', 14), command=self.set_flow).pack(side=tk.LEFT, padx=1)

        # Blank line for spacing before offset entry
        tk.Label(self.frame, text='', font=('Helvetica', 2)).grid(row=5, column=0)

        offset_frame = tk.Frame(self.frame)
        offset_frame.grid(row=6, column=1, columnspan=3)

        #tk.Label(offset_frame, text='Flow Offset:', font=('Helvetica', 14)).pack(side=tk.LEFT)
        #self.offset_entry = tk.Entry(offset_frame, width=8, font=('Helvetica', 14))
        #self.offset_entry.pack(side=tk.LEFT)
        #tk.Button(offset_frame, text='Apply', font=('Helvetica', 14), command=self.set_offset).pack(side=tk.LEFT, padx=1)

    def poll(self):
        try:
            rr_f = self.client.read_input_registers(FLOW_REG, 2)
            raw = float_from_regs(rr_f.registers) if not rr_f.isError() else None

            rr_s = self.client.read_holding_registers(SETPOINT_REG, 2)
            sp = float_from_regs(rr_s.registers) if not rr_s.isError() else None
        except ModbusIOException:
            raw = sp = None

        if raw is not None:
            adjusted = raw
            #adjusted = raw + self.offset
            #Change .3f if more decimal points are desired for flow reading.
            self.flow_var.set(f'Flow: {adjusted:.3f} SCCM')
        else:
            self.flow_var.set('Flow: Err')

        # Change .2f if more decimal points are desired for setpoint reading.
        self.sp_var.set(f'Setpoint: {sp:.2f} SCCM' if sp is not None else 'Setpoint: Err')

    def set_flow(self):
        try:
            val = round(float(self.sp_entry.get()), 2)
        except ValueError:
            messagebox.showwarning('Invalid Input', 'Enter a numeric setpoint')
            return

        regs = regs_from_float(val)
        wr = self.client.write_registers(SETPOINT_REG, regs)
        if wr.isError():
            messagebox.showerror('Write Error', f'{self.frame["text"]}: write failed')
        else:
            # Change .2f if more decimal points are desired for setpoint setting.
            self.sp_var.set(f'Setpoint: {val:.2f} SCCM')

   ### def set_offset(self):
   #     try:
   #         self.offset = float(self.offset_entry.get())
   #         self.offset_display_var.set(f'Offset Applied: {self.offset:.2f}')
   #     except ValueError:
   ###         messagebox.showwarning('Invalid Offset', 'Enter a numeric offset')

#Tries to set zero-flow if possible. If not, then failed.
    def zero_flow(self):
        wr = self.client.write_coil(ZERO_FLOW_REG, True)
        if wr.isError():
            messagebox.showerror('Zero Flow Error', f'{self.frame["text"]}: command failed')
        else:
            messagebox.showinfo('Zero Flow', f'{self.frame["text"]}: flow zeroed')

#Initial home screen
class MultiMFCApp:
    def __init__(self, master):
        self.master = master
        master.title('MKS MFC Monitor')

        self.controllers = [None] * NUMBER_OF_CONTROLLERS
        self.clients = [None] * NUMBER_OF_CONTROLLERS
        self.ip_entries = []
        self.connect_buttons = []
        self.disconnect_buttons = []

        for i in range(NUMBER_OF_CONTROLLERS):
            ip_frame = tk.Frame(master, pady=5)
            ip_frame.pack()
            tk.Label(ip_frame, text=f'MFC {i+1} IP:', font=('Helvetica', 14)).pack(side=tk.LEFT)
            ip_entry = tk.Entry(ip_frame, width=15, font=('Helvetica', 14))
            ip_entry.pack(side=tk.LEFT, padx=5)
            self.ip_entries.append(ip_entry)

            connect_btn = tk.Button(ip_frame, text='Connect', font=('Helvetica', 14), command=lambda i=i: self.connect(i))
            connect_btn.pack(side=tk.LEFT)
            self.connect_buttons.append(connect_btn)

            disconnect_btn = tk.Button(ip_frame, text='Disconnect', font=('Helvetica', 14), command=lambda i=i: self.disconnect(i))
            disconnect_btn.pack(side=tk.LEFT)
            self.disconnect_buttons.append(disconnect_btn)
            disconnect_btn.config(state='disabled')

        self.poll_all()

    def connect(self, index):
        ip = self.ip_entries[index].get().strip()
        client = ModbusTcpClient(ip, port=MFC_PORT)
        client.unit_id = UNIT_ID
        if not client.connect():
            messagebox.showerror('Connection Error', f'Cannot connect to {ip}:{MFC_PORT}')
            return

        self.ip_entries[index].config(state='disabled')
        self.connect_buttons[index].config(state='disabled')
        self.disconnect_buttons[index].config(state='normal')

        self.clients[index] = client
        controller = ControllerFrame(self.master, client, f'MFC {ip}', self.remove_controller)
        self.controllers[index] = controller

    def disconnect(self, index):
        if self.clients[index]:
            self.clients[index].close()
            self.clients[index] = None
        if self.controllers[index]:
            self.controllers[index].frame.destroy()
            self.controllers[index] = None
        self.ip_entries[index].config(state='normal')
        self.ip_entries[index].delete(0, tk.END)
        self.connect_buttons[index].config(state='normal')
        self.disconnect_buttons[index].config(state='disabled')

    def remove_controller(self, controller):
        for i in range(3):
            if self.controllers[i] == controller:
                self.disconnect(i)
                break

    def poll_all(self):
        for controller in self.controllers:
            if controller:
                controller.poll()
        self.master.after(POLL_INTERVAL_MS, self.poll_all)

if __name__ == '__main__':
    root = tk.Tk()
    MultiMFCApp(root)
    root.mainloop()
