# -*- coding: utf-8 -*-
"""
歐卡2發光輪胎SII檔案修改器
專門處理 .sii 格式的遊戲存檔文件
支援車牌指定和發光顏色自定義
"""

import os
import re
import shutil
from datetime import datetime
from pathlib import Path

class ETS2TireGlowModifier:
    def __init__(self):
        self.preset_colors = {
            '１': {'name': '青色發光', 'rgb': (0, 255, 255)},
            '２': {'name': '紅色發光', 'rgb': (255, 0, 0)},
            '３': {'name': '綠色發光', 'rgb': (0, 255, 0)},
            '４': {'name': '藍色發光', 'rgb': (0, 0, 255)},
            '５': {'name': '紫色發光', 'rgb': (128, 0, 255)},
            '６': {'name': '黃色發光', 'rgb': (255, 255, 0)},
            '７': {'name': '橙色發光', 'rgb': (255, 128, 0)},
            '８': {'name': '粉色發光', 'rgb': (255, 0, 255)},
            '９': {'name': '白色發光', 'rgb': (255, 255, 255)},
            '１０': {'name': '洋紅發光', 'rgb': (255, 20, 147)},
            '１１': {'name': '淺藍發光', 'rgb': (173, 216, 230)},
            '１２': {'name': '金色發光', 'rgb': (255, 215, 0)}
        }
        
        # 輪胎發光相關的正則表達式模式
        self.tire_patterns = {
            'r_tire': re.compile(r'(\s*r_tire:\s*\()([^)]+)(\))', re.IGNORECASE),
            'f_tire': re.compile(r'(\s*f_tire:\s*\()([^)]+)(\))', re.IGNORECASE)
        }
        
        # 車牌號碼識別模式
        self.license_patterns = [
            re.compile(r'license_plate:\s*"([^"]+)"', re.IGNORECASE),
            re.compile(r'licensePlate:\s*"([^"]+)"', re.IGNORECASE),
            re.compile(r'plate:\s*"([^"]+)"', re.IGNORECASE)
        ]
        
        # 拖車識別模式
        self.trailer_patterns = [
            re.compile(r'trailer\.[^{]*{[^}]*license_plate:\s*"([^"]+)"', re.IGNORECASE | re.DOTALL),
            re.compile(r'trailer_def\.[^{]*{[^}]*license_plate:\s*"([^"]+)"', re.IGNORECASE | re.DOTALL)
        ]
        
        # 車輛品牌和型號識別
        self.vehicle_patterns = {
            'scania': re.compile(r'vehicle\.scania\.[^{]*{', re.IGNORECASE),
            'volvo': re.compile(r'vehicle\.volvo\.[^{]*{', re.IGNORECASE),
            'mercedes': re.compile(r'vehicle\.mercedes\.[^{]*{', re.IGNORECASE),
            'man': re.compile(r'vehicle\.man\.[^{]*{', re.IGNORECASE),
            'iveco': re.compile(r'vehicle\.iveco\.[^{]*{', re.IGNORECASE),
            'daf': re.compile(r'vehicle\.daf\.[^{]*{', re.IGNORECASE),
            'renault': re.compile(r'vehicle\.renault\.[^{]*{', re.IGNORECASE)
        }
    
    def validate_sii_file(self, file_path):
        """驗證是否為有效的SII檔案"""
        if not file_path.lower().endswith('.sii'):
            return False, "檔案必須是 .sii 格式"
        
        if not os.path.exists(file_path):
            return False, "檔案不存在"
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read(1000)  # 讀取前1000字元檢查
                if 'SiiNunit' not in content:
                    return False, "不是有效的SII檔案格式"
        except Exception as e:
            return False, f"檔案讀取錯誤: {str(e)}"
        
        return True, "檔案驗證通過"
    
    def extract_license_plates(self, content):
        """從SII檔案內容中提取車牌號碼"""
        plates = set()
        
        for pattern in self.license_patterns:
            matches = pattern.findall(content)
            plates.update(matches)
        
        return list(plates)
    
    def extract_trailers(self, content):
        """從SII檔案內容中提取拖車資訊"""
        trailers = []
        
        for pattern in self.trailer_patterns:
            matches = pattern.findall(content)
            trailers.extend(matches)
        
        # 去重並返回
        return list(set(trailers))
    
    def extract_vehicle_info(self, content):
        """提取車輛品牌和型號資訊"""
        vehicles = {}
        
        for brand, pattern in self.vehicle_patterns.items():
            matches = pattern.findall(content)
            if matches:
                vehicles[brand] = len(matches)
        
        return vehicles
    
    def modify_all_vehicles(self, content, color_rgb):
        """修改所有車輛的輪胎發光設定"""
        modified_content = content
        modifications_count = 0
        
        # 修改所有r_tire
        r_tire_matches = self.tire_patterns['r_tire'].findall(modified_content)
        if r_tire_matches:
            modified_content = self.tire_patterns['r_tire'].sub(
                f'\\1{color_rgb[0]}, {color_rgb[1]}, {color_rgb[2]}\\3',
                modified_content
            )
            modifications_count += len(r_tire_matches)
        
        # 修改所有f_tire
        f_tire_matches = self.tire_patterns['f_tire'].findall(modified_content)
        if f_tire_matches:
            modified_content = self.tire_patterns['f_tire'].sub(
                f'\\1{color_rgb[0]}, {color_rgb[1]}, {color_rgb[2]}\\3',
                modified_content
            )
            modifications_count += len(f_tire_matches)
        
        return modified_content, f"成功修改 {modifications_count} 個輪胎設定"
    
    def batch_modify_by_brand(self, content, brand, color_rgb):
        """批量修改指定品牌車輛的輪胎發光"""
        if brand not in self.vehicle_patterns:
            return None, f"不支援的車輛品牌: {brand}"
        
        # 找到指定品牌的車輛區段
        brand_pattern = self.vehicle_patterns[brand]
        sections = []
        lines = content.split('\n')
        
        for i, line in enumerate(lines):
            if brand_pattern.search(line):
                # 找到品牌匹配的區段
                section_start = i
                brace_count = line.count('{') - line.count('}')
                section_end = i
                
                # 向下搜尋找到區段結束
                for j in range(i + 1, len(lines)):
                    brace_count += lines[j].count('{') - lines[j].count('}')
                    if brace_count <= 0:
                        section_end = j
                        break
                
                sections.append((section_start, section_end))
        
        if not sections:
            return None, f"找不到 {brand} 品牌的車輛"
        
        # 修改每個區段
        modified_content = content
        modifications_count = 0
        
        for start, end in reversed(sections):  # 反向處理避免索引變化
            section_lines = lines[start:end+1]
            section_content = '\n'.join(section_lines)
            
            # 修改輪胎設定
            original_section = section_content
            section_content = self._modify_section_tires(section_content, color_rgb)
            
            if section_content != original_section:
                # 替換內容
                new_lines = lines[:start] + section_content.split('\n') + lines[end+1:]
                modified_content = '\n'.join(new_lines)
                lines = new_lines
                modifications_count += 1
        
        return modified_content, f"成功修改 {modifications_count} 個 {brand} 車輛的輪胎設定"
    
    def _modify_section_tires(self, section_content, color_rgb):
        """修改單個區段的輪胎設定"""
        # 修改後輪胎
        if self.tire_patterns['r_tire'].search(section_content):
            section_content = self.tire_patterns['r_tire'].sub(
                f'\\1{color_rgb[0]}, {color_rgb[1]}, {color_rgb[2]}\\3',
                section_content
            )
        else:
            section_content = self._add_tire_setting(section_content, 'r_tire', color_rgb)
        
        # 修改前輪胎
        if self.tire_patterns['f_tire'].search(section_content):
            section_content = self.tire_patterns['f_tire'].sub(
                f'\\1{color_rgb[0]}, {color_rgb[1]}, {color_rgb[2]}\\3',
                section_content
            )
        else:
            section_content = self._add_tire_setting(section_content, 'f_tire', color_rgb)
        
        return section_content
    
    def generate_batch_script(self, input_files, color_selection, output_dir=None):
        """生成批次處理腳本"""
        if output_dir is None:
            output_dir = "modified_files"
        
        script_content = f"""#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 歐卡2輪胎發光批次修改腳本
# 自動生成於 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

import os
from pathlib import Path

# 批次修改設定
files_to_modify = {input_files}
output_directory = "{output_dir}"
selected_color = "{color_selection}"

# 確保輸出資料夾存在
Path(output_directory).mkdir(exist_ok=True)

# 載入修改器
from ets2_tire_modifier import ETS2TireGlowModifier
modifier = ETS2TireGlowModifier()

print("🚛 開始批次修改...")
print("=" * 50)

success_count = 0
total_files = len(files_to_modify)

for input_file in files_to_modify:
    print(f"正在處理: {{input_file}}")
    
    output_file = os.path.join(output_directory, os.path.basename(input_file))
    
    success, message, _ = modifier.process_file(
        input_file=input_file,
        license_plate="",  # 修改所有車輛
        color_selection=selected_color,
        output_file=output_file
    )
    
    if success:
        print(f"✅ {{message}}")
        success_count += 1
    else:
        print(f"❌ {{message}}")

print("=" * 50)
print(f"批次修改完成！成功: {{success_count}}/{{total_files}}")
"""
        
        return script_content
    
    def find_vehicle_sections(self, content, license_plate):
        """尋找指定車牌的車輛區段"""
        sections = []
        lines = content.split('\n')
        
        current_section = []
        in_target_section = False
        brace_count = 0
        
        for i, line in enumerate(lines):
            if license_plate in line:
                in_target_section = True
                # 向上搜尋找到區段開始
                for j in range(i, -1, -1):
                    if '{' in lines[j]:
                        current_section = lines[j:i+1]
                        brace_count = lines[j].count('{') - lines[j].count('}')
                        break
            
            if in_target_section:
                current_section.append(line)
                brace_count += line.count('{') - line.count('}')
                
                if brace_count <= 0:
                    sections.append({
                        'start_line': i - len(current_section) + 1,
                        'end_line': i,
                        'content': '\n'.join(current_section),
                        'lines': current_section.copy()
                    })
                    in_target_section = False
                    current_section = []
                    brace_count = 0
        
        return sections
    
    def modify_tire_glow(self, content, license_plate, color_rgb):
        """修改指定車牌的輪胎發光設定"""
        sections = self.find_vehicle_sections(content, license_plate)
        
        if not sections:
            return None, f"找不到車牌 '{license_plate}' 的車輛資料"
        
        modified_content = content
        modifications_count = 0
        
        for section in sections:
            section_content = section['content']
            original_section = section_content
            
            # 修改後輪胎
            if self.tire_patterns['r_tire'].search(section_content):
                section_content = self.tire_patterns['r_tire'].sub(
                    f'\\1{color_rgb[0]}, {color_rgb[1]}, {color_rgb[2]}\\3',
                    section_content
                )
                modifications_count += 1
            else:
                # 如果沒有r_tire設定，新增一個
                section_content = self._add_tire_setting(section_content, 'r_tire', color_rgb)
                modifications_count += 1
            
            # 修改前輪胎
            if self.tire_patterns['f_tire'].search(section_content):
                section_content = self.tire_patterns['f_tire'].sub(
                    f'\\1{color_rgb[0]}, {color_rgb[1]}, {color_rgb[2]}\\3',
                    section_content
                )
                modifications_count += 1
            else:
                # 如果沒有f_tire設定，新增一個
                section_content = self._add_tire_setting(section_content, 'f_tire', color_rgb)
                modifications_count += 1
            
            # 替換原內容
            modified_content = modified_content.replace(original_section, section_content)
        
        return modified_content, f"成功修改 {modifications_count} 個輪胎設定"
    
    def _add_tire_setting(self, section_content, tire_type, color_rgb):
        """在車輛區段中新增輪胎設定"""
        lines = section_content.split('\n')
        
        # 尋找合適的插入位置（在最後一個 } 之前）
        insert_index = -1
        for i in range(len(lines) - 1, -1, -1):
            if lines[i].strip() and not lines[i].strip().startswith('}'):
                insert_index = i + 1
                break
        
        if insert_index > 0:
            tire_setting = f" {tire_type}: ({color_rgb[0]}, {color_rgb[1]}, {color_rgb[2]})"
            lines.insert(insert_index, tire_setting)
        
        return '\n'.join(lines)
    
    def backup_file(self, file_path):
        """備份原始檔案"""
        backup_path = f"{file_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        shutil.copy2(file_path, backup_path)
        return backup_path
    
    def process_file(self, input_file, license_plate, color_selection, output_file=None, mode="single"):
        """處理SII檔案的主要方法 - 支援多種模式"""
        # 驗證檔案
        is_valid, message = self.validate_sii_file(input_file)
        if not is_valid:
            return False, message, None
        
        # 解析顏色
        if color_selection in self.preset_colors:
            color_rgb = self.preset_colors[color_selection]['rgb']
        elif isinstance(color_selection, (tuple, list)) and len(color_selection) == 3:
            color_rgb = tuple(color_selection)
        else:
            return False, "無效的顏色設定", None
        
        # 讀取檔案
        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            return False, f"檔案讀取失敗: {str(e)}", None
        
        # 提取各種資訊
        available_plates = self.extract_license_plates(content)
        trailers = self.extract_trailers(content)
        vehicles = self.extract_vehicle_info(content)
        
        # 根據模式處理
        if mode == "all":
            # 修改所有車輛
            modified_content, mod_message = self.modify_all_vehicles(content, color_rgb)
        elif mode == "brand" and license_plate in self.vehicle_patterns:
            # 修改指定品牌
            modified_content, mod_message = self.batch_modify_by_brand(content, license_plate, color_rgb)
        else:
            # 修改指定車牌（預設模式）
            if not license_plate:
                return False, "請輸入車牌號碼或選擇其他修改模式", available_plates
            modified_content, mod_message = self.modify_tire_glow(content, license_plate, color_rgb)
        
        if modified_content is None:
            return False, mod_message, available_plates
        
        # 備份原檔案
        backup_path = self.backup_file(input_file)
        
        # 決定輸出檔案路徑
        if output_file is None:
            file_path = Path(input_file)
            output_file = str(file_path.parent / f"{file_path.stem}_modified{file_path.suffix}")
        
        # 寫入修改後的檔案
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(modified_content)
        except Exception as e:
            return False, f"檔案寫入失敗: {str(e)}", available_plates
        
        # 準備詳細資訊
        info = {
            'plates': available_plates,
            'trailers': trailers,
            'vehicles': vehicles,
            'backup': backup_path,
            'output': output_file
        }
        
        return True, f"{mod_message}\n備份檔案: {backup_path}\n輸出檔案: {output_file}", info


def show_color_menu():
    """顯示彩色的顏色選單"""
    print("\n🎨 選擇發光顏色:")
    print("=" * 50)
    
    # ANSI顏色代碼
    colors = {
        '１': '\033[96m',   # 青色
        '２': '\033[91m',   # 紅色  
        '３': '\033[92m',   # 綠色
        '４': '\033[94m',   # 藍色
        '５': '\033[95m',   # 紫色
        '６': '\033[93m',   # 黃色
        '７': '\033[38;5;208m',  # 橙色
        '８': '\033[95m',   # 粉色
        '９': '\033[97m',   # 白色
        '１０': '\033[38;5;199m', # 洋紅
        '１１': '\033[38;5;117m', # 淺藍
        '１２': '\033[38;5;220m'  # 金色
    }
    
    reset = '\033[0m'
    
    modifier = ETS2TireGlowModifier()
    for key, color_info in modifier.preset_colors.items():
        color_code = colors.get(key, '')
        print(f"{color_code}  {key}. {color_info['name']} {color_info['rgb']}{reset}")
    
    print("=" * 50)
    print("💡 或輸入自訂RGB (格式: R,G,B，例如: 255,128,64)")
    return input("\n請選擇顏色編號或輸入RGB: ").strip()


def main():
    """命令行介面主程式"""
    print("=" * 70)
    print("🚛 歐卡２發光輪胎修改器")
    print("   V1.0.0測試版  by白月")
    print("2025/07/29下午18:42製作")
    print("注意:如修改失敗或檔案損毀請自行負責")
    print("=" * 70)
    
    modifier = ETS2TireGlowModifier()
    
    while True:
        print("\n📋 請選擇操作:")
        print("=" * 40)
        print("１. 🔧 修改ＳＩＩ檔案")
        print("２. 🎨 檢視可用顏色預設")
        print("３. 📋 檢視檔案中的車牌")
        print("４. 🚚 全部車輛修改模式")
        print("５. 🏭 品牌批次修改模式")
        print("６. 📊 檔案詳細分析")
        print("７. 📝 生成批次處理腳本")
        print("８. 📖 使用說明")
        print("０. 🚪 退出程式")
        print("=" * 40)
        
        choice = input("請輸入選項 (０-８): ").strip()
        
        if choice == '０' or choice == '0':
            print("\n🙏 感謝使用歐卡２發光輪胎修改器！")
            print("⚠️  記得備份您的遊戲存檔喔！")
            break
        
        elif choice == '１' or choice == '1':
            # 修改檔案
            print("\n" + "="*60)
            print("🔧 ＳＩＩ檔案修改模式")
            print("="*60)
            
            input_file = input("📁 請輸入ＳＩＩ檔案路徑: ").strip().strip('"')
            
            if not input_file:
                print("❌ 檔案路徑不能為空")
                continue
            
            # 驗證檔案
            is_valid, message = modifier.validate_sii_file(input_file)
            if not is_valid:
                print(f"❌ {message}")
                continue
            
            # 讀取並顯示可用車牌
            try:
                with open(input_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                plates = modifier.extract_license_plates(content)
                
                if plates:
                    print(f"\n🚗 檔案中發現的車牌:")
                    for i, plate in enumerate(plates, 1):
                        print(f"   {i}. {plate}")
                else:
                    print("\n⚠️  檔案中未發現車牌號碼")
            except:
                print("⚠️  無法讀取檔案內容")
            
            license_plate = input("\n🎯 請輸入要修改的車牌號碼: ").strip()
            if not license_plate:
                print("❌ 車牌號碼不能為空")
                continue
            
            # 顯示顏色選單
            color_input = show_color_menu()
            
            if color_input in modifier.preset_colors:
                color = color_input
                selected_color = modifier.preset_colors[color_input]
                print(f"✅ 已選擇: {selected_color['name']} {selected_color['rgb']}")
            else:
                try:
                    rgb_values = [int(x.strip()) for x in color_input.split(',')]
                    if len(rgb_values) != 3 or any(x < 0 or x > 255 for x in rgb_values):
                        raise ValueError
                    color = tuple(rgb_values)
                    print(f"✅ 已選擇自訂顏色: RGB{color}")
                except:
                    print("❌ 無效的顏色格式示範：２５５，２５５，２５５")
                    continue
            
            output_file = input("\n💾 輸出檔案路徑 (留空使用預設): ").strip().strip('"')
            if not output_file:
                output_file = None
            
            # 處理檔案
            print("\n⏳ 正在處理檔案，請稍候...")
            print("🔄 正在分析車輛資料...")
            success, message, available_plates = modifier.process_file(
                input_file, license_plate, color, output_file
            )
            
            print("\n" + "="*60)
            if success:
                print("🎉 檔案修改成功！")
                print("✅", message)
                print("\n💡 提醒事項:")
                print("   • 請先在單機模式測試效果")
                print("   • 已自動備份原始檔案")
            else:
                print("❌ 檔案修改失敗！")
                print("📝", message)
                if available_plates:
                    print(f"💡 檔案中可用的車牌: {', '.join(available_plates)}")
            print("="*60)
        
        elif choice == '２' or choice == '2':
            # 顯示顏色預設
            print("\n🎨 可用的顏色預設:")
            print("=" * 50)
            
            # 使用彩色顯示
            colors = {
                '１': '\033[96m',   # 青色
                '２': '\033[91m',   # 紅色  
                '３': '\033[92m',   # 綠色
                '４': '\033[94m',   # 藍色
                '５': '\033[95m',   # 紫色
                '６': '\033[93m',   # 黃色
                '７': '\033[38;5;208m',  # 橙色
                '８': '\033[95m',   # 粉色
                '９': '\033[97m',   # 白色
                '１０': '\033[38;5;199m', # 洋紅
                '１１': '\033[38;5;117m', # 淺藍
                '１２': '\033[38;5;220m'  # 金色
            }
            reset = '\033[0m'
            
            for key, color_info in modifier.preset_colors.items():
                color_code = colors.get(key, '')
                print(f"{color_code}  {key}. {color_info['name']} - RGB{color_info['rgb']}{reset}")
            
            print("=" * 50)
            print("💡 您也可以使用自訂RGB格式: R,G,B")
        
        elif choice == '３' or choice == '3':
            # 檢視檔案中的車牌
            print("\n📋 車牌檢視模式")
            print("=" * 40)
            
            input_file = input("📁 請輸入ＳＩＩ檔案路徑: ").strip().strip('"')
            
            is_valid, message = modifier.validate_sii_file(input_file)
            if not is_valid:
                print(f"❌ {message}")
                continue
            
            try:
                with open(input_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                plates = modifier.extract_license_plates(content)
                
                if plates:
                    print(f"\n🚗 檔案中的車牌號碼 (共 {len(plates)} 個):")
                    print("=" * 40)
                    for i, plate in enumerate(plates, 1):
                        print(f"   {i:2d}. {plate}")
                    print("=" * 40)
                else:
                    print("\n⚠️  檔案中未發現車牌號碼")
                    print("💡 可能原因:")
                    print("   • 檔案格式不正確")
                    print("   • 不是車輛存檔檔案")
                    print("   • 車牌資料格式特殊")
            except Exception as e:
                print(f"❌ 讀取檔案失敗: {str(e)}")
        
        elif choice == '４' or choice == '4':
            # 修改全部車輛
            print("\n" + "="*60)
            print("🚚 全部車輛修改模式")
            print("="*60)
            
            input_file = input("📁 請輸入ＳＩＩ檔案路徑: ").strip().strip('"')
            
            if not input_file:
                print("❌ 檔案路徑不能為空")
                continue
            
            is_valid, message = modifier.validate_sii_file(input_file)
            if not is_valid:
                print(f"❌ {message}")
                continue
            
            color_input = show_color_menu()
            
            if color_input in modifier.preset_colors:
                color = color_input
                selected_color = modifier.preset_colors[color_input]
                print(f"✅ 已選擇: {selected_color['name']} {selected_color['rgb']}")
            else:
                try:
                    rgb_values = [int(x.strip()) for x in color_input.split(',')]
                    if len(rgb_values) != 3 or any(x < 0 or x > 255 for x in rgb_values):
                        raise ValueError
                    color = tuple(rgb_values)
                    print(f"✅ 已選擇自訂顏色: RGB{color}")
                except:
                    print("❌ 無效的顏色格式示範：２５５，２５５，２５５")
                    continue
            
            print("\n⏳ 正在修改全部車輛，請稍候...")
            success, message, info = modifier.process_file(
                input_file, "", color, mode="all"
            )
            
            print("\n" + "="*60)
            if success:
                print("🎉 全部車輛修改成功！")
                print("✅", message)
                if isinstance(info, dict) and 'vehicles' in info:
                    print(f"📊 修改統計: 共處理 {sum(info['vehicles'].values())} 輛車")
            else:
                print("❌ 修改失敗！")
                print("📝", message)
            print("="*60)
        
        elif choice == '５' or choice == '5':
            # 依品牌批次修改
            print("\n" + "="*60)
            print("🏭 品牌批次修改模式")
            print("="*60)
            
            input_file = input("📁 請輸入ＳＩＩ檔案路徑: ").strip().strip('"')
            
            if not input_file:
                print("❌ 檔案路徑不能為空")
                continue
            
            is_valid, message = modifier.validate_sii_file(input_file)
            if not is_valid:
                print(f"❌ {message}")
                continue
            
            # 顯示可用品牌
            try:
                with open(input_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                vehicles = modifier.extract_vehicle_info(content)
                
                if vehicles:
                    print("\n🚚 檔案中的車輛品牌:")
                    for brand, count in vehicles.items():
                        print(f"   {brand.upper()}: {count} 輛")
                else:
                    print("\n⚠️  檔案中未發現車輛資料")
                    continue
            except:
                print("⚠️  無法讀取檔案內容")
                continue
            
            brand = input("\n🏭 請輸入要修改的品牌 (scania/volvo/mercedes/man/iveco/daf/renault): ").strip().lower()
            
            if brand not in modifier.vehicle_patterns:
                print("❌ 不支援的車輛品牌")
                continue
            
            color_input = show_color_menu()
            
            if color_input in modifier.preset_colors:
                color = color_input
                selected_color = modifier.preset_colors[color_input]
                print(f"✅ 已選擇: {selected_color['name']} {selected_color['rgb']}")
            else:
                try:
                    rgb_values = [int(x.strip()) for x in color_input.split(',')]
                    if len(rgb_values) != 3 or any(x < 0 or x > 255 for x in rgb_values):
                        raise ValueError
                    color = tuple(rgb_values)
                    print(f"✅ 已選擇自訂顏色: RGB{color}")
                except:
                    print("❌ 無效的顏色格式示範：２５５，２５５，２５５")
                    continue
            
            print(f"\n⏳ 正在修改 {brand.upper()} 品牌車輛，請稍候...")
            success, message, info = modifier.process_file(
                input_file, brand, color, mode="brand"
            )
            
            print("\n" + "="*60)
            if success:
                print(f"🎉 {brand.upper()} 品牌車輛修改成功！")
                print("✅", message)
            else:
                print("❌ 修改失敗！")
                print("📝", message)
            print("="*60)
        
        elif choice == '６' or choice == '6':
            # 檔案詳細分析
            print("\n📊 檔案詳細分析")
            print("=" * 60)
            
            input_file = input("📁 請輸入ＳＩＩ檔案路徑: ").strip().strip('"')
            
            is_valid, message = modifier.validate_sii_file(input_file)
            if not is_valid:
                print(f"❌ {message}")
                continue
            
            try:
                with open(input_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                plates = modifier.extract_license_plates(content)
                trailers = modifier.extract_trailers(content)
                vehicles = modifier.extract_vehicle_info(content)
                
                print(f"\n📄 檔案資訊:")
                print(f"   檔案大小: {len(content):,} 字元")
                print(f"   行數: {len(content.split('\n')):,} 行")
                
                print(f"\n🚗 車輛統計:")
                if vehicles:
                    total_vehicles = sum(vehicles.values())
                    print(f"   總車輛數: {total_vehicles}")
                    for brand, count in vehicles.items():
                        percentage = (count / total_vehicles) * 100
                        print(f"   {brand.upper()}: {count} 輛 ({percentage:.1f}%)")
                else:
                    print("   未發現車輛資料")
                
                print(f"\n📋 車牌統計:")
                if plates:
                    print(f"   總車牌數: {len(plates)}")
                    for i, plate in enumerate(plates[:10], 1):  # 只顯示前10個
                        print(f"   {i:2d}. {plate}")
                    if len(plates) > 10:
                        print(f"   ... 還有 {len(plates) - 10} 個車牌")
                else:
                    print("   未發現車牌資料")
                
                print(f"\n🚛 拖車統計:")
                if trailers:
                    print(f"   拖車數量: {len(trailers)}")
                    for i, trailer in enumerate(trailers[:5], 1):  # 只顯示前5個
                        print(f"   {i}. {trailer}")
                    if len(trailers) > 5:
                        print(f"   ... 還有 {len(trailers) - 5} 個拖車")
                else:
                    print("   未發現拖車資料")
                
            except Exception as e:
                print(f"❌ 分析失敗: {str(e)}")
        
        elif choice == '７' or choice == '7':
            # 生成批次腳本
            print("\n📝 生成批次處理腳本")
            print("=" * 50)
            
            files_input = input("📁 請輸入要處理的檔案路徑 (多個檔案用逗號分隔): ").strip()
            if not files_input:
                print("❌ 檔案路徑不能為空")
                continue
            
            files_list = [f.strip().strip('"') for f in files_input.split(',')]
            
            color_input = show_color_menu()
            if color_input not in modifier.preset_colors:
                print("❌ 批次腳本僅支援預設顏色")
                continue
            
            output_dir = input("📂 輸出資料夾 (留空使用預設): ").strip() or "modified_files"
            
            script_content = modifier.generate_batch_script(files_list, color_input, output_dir)
            
            script_file = f"batch_modify_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py"
            
            try:
                with open(script_file, 'w', encoding='utf-8') as f:
                    f.write(script_content)
                print(f"✅ 批次腳本已生成: {script_file}")
                print("💡 執行方式: python " + script_file)
            except Exception as e:
                print(f"❌ 腳本生成失敗: {str(e)}")
        
        elif choice == '８' or choice == '8':
            # 使用說明
            print("\n📖 使用說明")
            print("=" * 70)
            print("🎯 功能說明:")
            print("   本工具專門用於修改歐洲卡車模擬器２的SII存檔檔案")
            print("   可以為指定車牌的車輛設定發光輪胎效果")
            print()
            print("📋 新功能特色:")
            print("   １. 指定車牌修改 - 精確修改特定車牌的車輛")
            print("   ２. 全部車輛修改 - 一鍵修改檔案中所有車輛")
            print("   ３. 品牌批次修改 - 按車輛品牌批量修改")
            print("   ４. 詳細檔案分析 - 完整的檔案內容統計")
            print("   ５. 批次腳本生成 - 自動化處理多個檔案")
            print("   ６. 拖車識別支援 - 自動識別拖車資訊")
            print()
            print("📋 操作步驟:")
            print("   １. 準備好您的SII存檔檔案")
            print("   ２. 選擇適合的修改模式")  
            print("   ３. 輸入檔案路徑")
            print("   ４. 根據模式選擇車牌/品牌/全部")
            print("   ５. 選擇發光顏色")
            print("   ６. 等待處理完成")
            print()
            print("🚚 支援的車輛品牌:")
            print("   • SCANIA (斯堪尼亞)")
            print("   • VOLVO (富豪)")
            print("   • MERCEDES (賓士)")
            print("   • MAN (曼恩)")
            print("   • IVECO (依維柯)")
            print("   • DAF (達夫)")
            print("   • RENAULT (雷諾)")
            print()
            print("⚠️  安全提醒:")
            print("   • 使用前請務必備份原始存檔")
            print("   • 建議先在單機模式測試")
            print("   • 程式會自動建立備份檔案")
            print()
            print("🎨 顏色說明:")
            print("   • 提供１２種預設發光顏色")
            print("   • 支援自訂RGB顏色 (0-255)")
            print("   • 前後輪胎會設定為相同顏色")
            print()
            print("📁 檔案說明:")
            print("   • 僅支援.sii格式檔案")
            print("   • 輸出檔案會加上_modified後綴")
            print("   • 自動建立帶時間戳記的備份檔")
            print("=" * 70)
        
        else:
            print("❌ 無效選項，請輸入０-８之間的數字")


if __name__ == "__main__":
    main()


# 使用範例
"""
# 建立修改器實例
modifier = ETS2TireGlowModifier()

# 指定車牌修改
success, message, info = modifier.process_file(
    input_file="game.sii",
    license_plate="ABC-123",
    color_selection="１",  # 青色發光
    output_file="game_modified.sii",
    mode="single"
)

# 修改全部車輛
success, message, info = modifier.process_file(
    input_file="game.sii",
    license_plate="",
    color_selection="２",  # 紅色發光
    mode="all"
)

# 按品牌批次修改
success, message, info = modifier.process_file(
    input_file="game.sii", 
    license_plate="scania",  # 品牌名稱
    color_selection=(128, 255, 192),
    mode="brand"
)

# 檔案分析
with open("game.sii", 'r', encoding='utf-8') as f:
    content = f.read()

plates = modifier.extract_license_plates(content)
trailers = modifier.extract_trailers(content)  
vehicles = modifier.extract_vehicle_info(content)

print("車牌:", plates)
print("拖車:", trailers)
print("車輛品牌:", vehicles)

if success:
    print("修改成功:", message)
    print("詳細資訊:", info)
else:
    print("修改失敗:", message)
"""
