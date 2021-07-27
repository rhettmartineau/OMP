# OMP
Code written for NSF-OTIC Ocean Microbial Profiler

This folder contains code for the Feather STM32F405, which is used to monitor the flow/pressure during a sampling event

This repository contains Python/Micropython code for a hardware system comprised of:
  1) Raspberry Pi 3
  2) Pyboard 1.1
  3) Adafruit Feather STM32F405 

The following functions are implemented:
  1) Raspberry Pi- Micropython communications over I2C
  2) Heater control with LCD output (Pyboard)
  3) Stepper Motor control (reciprocating syringe pumps) (Pyboard)
  4) Valve control (Pyboard)
  5) Flowrate monitoring (Feather STM, tracking flowrate as measured by Sensirion SLF3S-1300F Liquid Flow Sensor)

