import atem
import rseight

a = atem.Atem()
a.connectToSwitcher(("192.168.10.1", 9910))
r = rseight.rsEight("COM1")

rseight.rsEight.evt_rseight_cmd_btn_changed.connect(a.on_btn_change)
rseight.rsEight.evt_rseight_bus_xpoint_changed.connect(a.on_btn_change)
rseight.rsEight.evt_rseight_tbar_value_changed.connect(a.on_tbar_change)