from PyEspecLib.models import SEG_021H

if __name__ == '__main__':
    seg = SEG_021H(serial_port='/dev/ttyUSB1')
    """test get command"""
    # print(seg.get_rom_version())
    # print(seg.get_temp_pv())
    # print(seg.get_temp_all())
    # print(seg.get_temp_high_limit())
    # print(seg.get_running_mode())
    # print(seg.get_running_status())
    # print(seg.get_heat_output_value())
    # print(seg.get_const_sv())
    # print(seg.set_const_value(125))

    """test set command pgm mode"""
    # print(seg.set_pgm_step_value(pgm_id=1, step=1, run=True, hours=1, mins=25, temp_sv=124.5))
    # print(seg.set_pgm_step_value(pgm_id=1, step=2, run=True, hours=1, mins=25, temp_sv=125.5))
    # print(seg.get_pgm_step_setting(1, 1))
    # print(seg.get_pgm_step_setting(1, 2))
    # print(seg.run_pgm(1))
    # print(seg.get_running_status())

    """test set command const mode"""
    print(seg.set_const_value(125))
    print(seg.run_const())
    print(seg.get_running_status())
