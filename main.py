import re
from datetime import datetime

fileName = input("Название файла лога: ")
errors = []
current_error = None

addr_mapping = {
    '40': 'Ошибка задней камеры',
    '41': 'Ошибка передней камеры',
    '42': 'Ошибка левой камеры',
    '43': 'Ошибка правой камеры'
}

i2c_pattern = re.compile(r'(\w+)=(\d+)', re.IGNORECASE)

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
        
        if current_error is not None:
            if '=' in line and ('i2c' in line_lower or 'clk' in line_lower or 'speed' in line_lower):
                params = i2c_pattern.findall(line)
                
                for key, value in params:
                    key_lower = key.lower()
                    if key_lower in ['clk', 'id', 'op', 'speed', 'trans_len', 'trans_stop']:
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

with open(output_file, 'w', encoding='utf-8') as f:
    f.write("=" * 80 + "\n")
    f.write("=== ОТЧЕТ ПО ОШИБКАМ I2C: TRANSFER ACK ERROR ===\n")
    f.write("=" * 80 + "\n")
    f.write(f"Всего найдено ошибок: {len(errors)}\n")
    f.write("=" * 80 + "\n\n")
    
    for i, error in enumerate(errors, 1):
        addr = error.get('addr', '?')
        addr_desc = get_addr_description(addr)
        clk = error.get('clk', '?')
        i2c_id = error.get('id', '?')
        speed = error.get('speed', '?')
        trans_len = error.get('trans_len', '?')
        
        f.write("=" * 80 + "\n")
        f.write("===+++ НАЙДЕНА ОШИБКА I2C: TRANSFER ACK ERROR +++===\n")
        f.write("=" * 80 + "\n")
        f.write(f"⌈ Адрес: {addr_desc}\n")
        f.write(f"⌈ Номер I2C контроллера: {i2c_id}\n")
        f.write(f"⌈ Тактовая частота контроллера: {clk} Гц\n")
        f.write(f"⌈ Целевая скорость шины: {speed} бит/с\n")
        f.write(f"⌈ Длина передачи: {trans_len} байт\n")
        f.write("=" * 80 + "\n")
        f.write("===----- КОНЕЦ ОШИБКИ I2C: TRANSFER ACK ERROR ------===\n")
        f.write("=" * 80 + "\n\n")
        
        print(f"\nОшибка {i}:")
        print(f"  Адрес: {addr_desc}")
        print(f"  I2C контроллер: {i2c_id}")
        print(f"  Частота: {clk} Гц")
        print(f"  Скорость: {speed} бит/с")

print(f"\nОтчет сохранен в файл: {output_file}")
print(f"Всего обработано ошибок: {len(errors)}")