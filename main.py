import re
from datetime import datetime

fileName = input("Название файла лога: ")
errors = []
current_error = None

addr_mapping = {
    '40': 'Камера заднего вида',
    '41': 'Камера переднего вида',
    '42': 'Левая камера',
    '43': 'Правая камера',
    '44': 'Камера?'
}

time_pattern = re.compile(r'\[(\s*\d+\.\d+)\]')
process_pattern = re.compile(r'\((\d+)\)\[(\d+):([^\]]+)\]')
bus_pattern = re.compile(r'i2c i2c-(\d+):')
i2c_param_pattern = re.compile(r'([A-Za-z_]+)=([0-9a-fA-Fx]+)')

with open(fileName, 'r', encoding='utf-8') as file:
    for line in file:
        line_lower = line.lower()
        
        if "ack error" in line_lower and "addr" in line_lower:
            if current_error is not None:
                errors.append(current_error)
            
            current_error = {}
            
            addr_match = re.search(r'addr[:\s]+(\d+)', line_lower)
            if addr_match:
                current_error['addr'] = addr_match.group(1)
            
            time_match = time_pattern.search(line)
            if time_match:
                time_val = time_match.group(1).strip()
                current_error['time'] = time_val
            
            proc_match = process_pattern.search(line)
            if proc_match:
                current_error['process'] = proc_match.group(3)
                current_error['pid'] = proc_match.group(2)
            
            bus_match = bus_pattern.search(line)
            if bus_match:
                current_error['bus'] = bus_match.group(1)
            
            current_error['has_params'] = False
        
        if current_error is not None:
            if 'i2c structure:' in line_lower or 'i2c structure' in line_lower:
                current_error['has_params'] = True
                
            params = i2c_param_pattern.findall(line)
            for key, value in params:
                key_lower = key.lower()
                if key_lower in ['clk', 'id', 'op', 'speed', 'trans_len', 'trans_stop', 'total_len', 'irq_stat']:
                    current_error[key_lower] = value
        
        if "i2c_dump_info ------------------------------------------" in line_lower:
            if current_error is not None and 'addr' in current_error:
                errors.append(current_error)
                current_error = None

if current_error is not None and 'addr' in current_error:
    errors.append(current_error)

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
base_name = fileName.rsplit('.', 1)[0] if '.' in fileName else fileName
output_file = f"{base_name}_export_{timestamp}.log"

def get_addr_description(addr):
    if addr in addr_mapping:
        return f"{addr} ({addr_mapping[addr]})"
    else:
        return addr

def check_power_status(error):
    if error.get('has_params', False):
        return "ЕСТЬ (обнаружены параметры I2C)"
    elif error.get('clk') or error.get('speed') or error.get('trans_len'):
        return "ЕСТЬ (есть данные передачи)"
    else:
        return "НЕТ ДАННЫХ (возможно нет питания или обрыв шины)"

with open(output_file, 'w', encoding='utf-8') as f:
    f.write("=" * 80 + "\n")
    f.write("=== ОТЧЕТ ПО ОШИБКАМ I2C (ACK ERROR) ===\n")
    f.write("=" * 80 + "\n")
    f.write(f"Файл лога: {fileName}\n")
    f.write(f"Дата отчета: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n")
    f.write(f"Всего найдено ошибок: {len(errors)}\n")
    f.write("=" * 80 + "\n\n")
    
    for i, error in enumerate(errors, 1):
        addr = error.get('addr', '?')
        addr_desc = get_addr_description(addr)
        time_str = error.get('time', '?')
        bus = error.get('bus', '?')
        process = error.get('process', '?')
        pid = error.get('pid', '?')
        clk = error.get('clk', '?')
        i2c_id = error.get('id', '?')
        speed = error.get('speed', '?')
        trans_len = error.get('trans_len', error.get('total_len', '?'))
        power_status = check_power_status(error)
        
        f.write("=" * 80 + "\n")
        f.write("===+++ НАЙДЕНА ОШИБКА I2C: TRANSFER ACK ERROR +++===\n")
        f.write("=" * 80 + "\n")
        f.write(f"├ Время ошибки: {time_str} сек\n")
        f.write(f"├ Устройство: {addr_desc}\n")
        f.write(f"├ Номер I2C шины: {bus}\n")
        f.write(f"├ Процесс: {process} (PID: {pid})\n")
        f.write(f"├ Питание на шине: {power_status}\n")
        
        if i2c_id != '?':
            f.write(f"├ Номер I2C контроллера: {i2c_id}\n")
        if clk != '?':
            f.write(f"├ Тактовая частота: {clk} Гц\n")
        if speed != '?':
            f.write(f"├ Целевая скорость шины: {speed} бит/с\n")
        if trans_len != '?':
            f.write(f"├ Длина передачи: {trans_len} байт\n")
        
        f.write("\n")
        f.write("├ ПОЯСНЕНИЕ:\n")
        if power_status == "ЕСТЬ (обнаружены параметры I2C)":
            f.write("├   - Питание на шине присутствует\n")
            f.write("├   - Устройство не отвечает (возможно неисправно или отключено)\n")
            f.write("├   - Проверить подключение устройства, целостность проводов\n")
        elif power_status == "ЕСТЬ (есть данные передачи)":
            f.write("├   - Питание на шине присутствует\n")
            f.write("├   - Устройство не отвечает на запросы\n")
            f.write("├   - Проверить само устройство и соединения\n")
        else:
            f.write("├   - НЕТ ДАННЫХ О ПИТАНИИ НА ШИНЕ!\n")
            f.write("├   - Возможные причины:\n")
            f.write("├     * Нет питания на устройстве\n")
            f.write("├     * Обрыв шины I2C (провода SDA/SCL)\n")
            f.write("├     * Короткое замыкание в цепи\n")
            f.write("├     * Неисправность блока управления\n")
        
        f.write("=" * 80 + "\n")
        f.write("===----- КОНЕЦ ОШИБКИ I2C: TRANSFER ACK ERROR ------===\n")
        f.write("=" * 80 + "\n\n")
        
        print(f"\nОшибка {i}:")
        print(f"  Устройство: {addr_desc}")
        print(f"  Время: {time_str} сек")
        print(f"  Шина I2C: {bus}")
        print(f"  Питание: {power_status}")
        if process != '?':
            print(f"  Процесс: {process}")

print(f"\n{'='*60}")
print("СТАТИСТИКА:")
print(f"{'='*60}")

device_stats = {}
power_issues = 0

for error in errors:
    addr = error.get('addr', '?')
    if addr in device_stats:
        device_stats[addr] += 1
    else:
        device_stats[addr] = 1
    
    if not error.get('has_params', False) and not error.get('clk'):
        power_issues += 1

for addr, count in sorted(device_stats.items(), key=lambda x: x[1], reverse=True):
    desc = get_addr_description(addr)
    print(f"  {desc}: {count} ошибок")

if power_issues > 0:
    print(f"\nВНИМАНИЕ: {power_issues} ошибок без признаков питания на шине!")
    print("  Проверьте подачу питания на проблемные устройства.")

print(f"\nОтчет сохранен в файл: {output_file}")
print(f"Всего обработано ошибок: {len(errors)}")