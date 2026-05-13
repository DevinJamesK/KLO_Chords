import dearpygui.dearpygui as dpg
dpg.create_context()
def on_key(s, d, u):
    print(f'KEY: app_data={d}  user_data={u}')
with dpg.handler_registry():
    dpg.add_key_press_handler(key=dpg.mvKey_A, callback=on_key, user_data='A')
    dpg.add_key_press_handler(key=-1, callback=on_key, user_data='ANY')
with dpg.window(label='Press A', width=400, height=150):
    dpg.add_text('Press the A key (and any others)')
    dpg.add_text('Watch terminal. Close window to exit.')
dpg.create_viewport(title='Test', width=420, height=180)
dpg.setup_dearpygui()
dpg.show_viewport()
print('WINDOW OPEN - press A now, close window when done')
dpg.start_dearpygui()
dpg.destroy_context()
