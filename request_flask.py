from flask import Flask, request, jsonify
from module_1 import main
from module_2 import chay
from module_3 import get_channel_info, stop_flags
from module_4 import phan_tich_chu_de
from module_5 import get_channel_module_5
from module_fetch_data import find_and_load_json
import re
from dotenv import load_dotenv
import os
import json
from dotenv import load_dotenv, set_key
app = Flask(__name__)

@app.route('/module1/function5/post', methods=['POST'])
def post_function5():
   print('da nhan được request')
   channelUrl = request.args.get('channelUrl')
   
   if not channelUrl:
       return jsonify({"error": "channelUrl parameter is required"}), 400
   
   cleaned_url = re.sub(r'[\\/:*?"<>|]', '_', channelUrl)
   
   # Lấy các tham số từ request
   production_platform = request.args.get("production_platform")
   content_structure = request.args.get("content_structure")
   call_to_action = request.args.get("call_to_action")
   thumbnail_style = request.args.get("thumbnail_style")
   channel_status = request.args.get("channel_status")
   unique_selling_proposition = request.args.get("unique_selling_proposition")
   awareness_level = request.args.get("awareness_level")
   
   # Đường dẫn đến file JSON
   directory = 'function5'
   file_path = f'{directory}/{cleaned_url}.json'
   print('duong dan la ' + file_path)
   
   try:
       # Tạo thư mục nếu chưa tồn tại
       os.makedirs(directory, exist_ok=True)
       
       # Đọc dữ liệu hiện có (nếu file tồn tại)
       existing_data = {}
       if os.path.exists(file_path):
           with open(file_path, 'r', encoding='utf-8') as file:
               loaded_data = json.load(file)
               
               # Xử lý cả array và object
               if isinstance(loaded_data, list) and loaded_data:
                   existing_data = loaded_data[0]
               elif isinstance(loaded_data, dict):
                   existing_data = loaded_data
               else:
                   existing_data = {}
       
       # Cập nhật dữ liệu mới (chỉ cập nhật các trường có giá trị)
       if production_platform is not None:
           existing_data['production_platform'] = production_platform
       if content_structure is not None:
           existing_data['content_structure'] = content_structure
       if call_to_action is not None:
           existing_data['call_to_action'] = call_to_action
       if thumbnail_style is not None:
           existing_data['thumbnail_style'] = thumbnail_style
       if channel_status is not None:
           existing_data['channel_status'] = channel_status
       if unique_selling_proposition is not None:
           existing_data['unique_selling_proposition'] = unique_selling_proposition
       if awareness_level is not None:
           existing_data['awareness_level'] = awareness_level
       
       # Lưu dữ liệu đã cập nhật vào file (giữ nguyên format array)
       final_data = [existing_data]
       with open(file_path, 'w', encoding='utf-8') as file:
           json.dump(final_data, file, ensure_ascii=False, indent=2)
       
       return jsonify({
           "message": 'Function added successfully',
           "file_path": file_path
       })
       
   except Exception as e:
       print(f"Chi tiết lỗi: {e}")
       print(f"Loại lỗi: {type(e)}")
       return jsonify({"error": f"An error occurred: {str(e)}"}), 500

@app.route('/module1/', methods=['GET'])
def module1_handler():
    function = request.args.get('function')
    
    if function == 'function1':
        user_id = request.args.get('userId')
        country = request.args.get('country')
        directory = 'function1'
        config_file = 'config.json'
        
        # Đọc danh sách countries từ file JSON
        try:
            with open(config_file, 'r', encoding='utf-8') as file:
                config_data = json.load(file)
                json_countries = config_data.get('countries', [])
        except FileNotFoundError:
            print(f"Config file {config_file} not found")
            json_countries = []
        except json.JSONDecodeError:
            print(f"Error decoding JSON from {config_file}")
            json_countries = []
        
        # Kiểm tra nếu country có trong danh sách JSON
        if country in json_countries:
            # Đọc dữ liệu từ file JSON
            filename = country + '.json'
            filepath = os.path.join(directory, filename)
            
            try:
                with open(filepath, 'r', encoding='utf-8') as file:
                    data = json.load(file)
                
                # Kiểm tra nếu data là array rỗng
                if isinstance(data, list) and len(data) == 0:
                    # Chạy hàm main để lấy dữ liệu mới
                    data = main(country, user_id)
                    return jsonify(data)
                else:
                    return jsonify(data)
                    
            except FileNotFoundError:
                print(f"File {filepath} not found")
                # Chạy hàm main để lấy dữ liệu mới
                data = main(country, user_id)
                return jsonify(data)
            except json.JSONDecodeError:
                print(f"Error decoding JSON from {filepath}")
                return jsonify({"error": "Invalid JSON format"})
            except Exception as e:
                print(f"Error reading {filepath}: {e}")
                return jsonify({"error": "Failed to read data"})
        else:
            # Country không có trong file json, thêm vào và chạy hàm main
            try:
                # Thêm country vào file config.json
                config_data['countries'].append(country)
                with open(config_file, 'w', encoding='utf-8') as file:
                    json.dump(config_data, file, indent=2, ensure_ascii=False)
                print(f"Added {country} to config.json file")
                
                # Chạy hàm main để lấy dữ liệu
                data = main(country, user_id)
                return jsonify(data)
                
            except Exception as e:
                print(f"Error updating config file: {e}")
                return jsonify({"error": "Failed to update configuration"})
    
    # return jsonify({"error": "Invalid function parameter"})



    elif function =='function2':
        method = request.args.get('method')
        option = request.args.get('option')
        function = 'function2'
        # user_id = request.args.get('userId') or ''
        # date = request.args.get('date') or ''
        if method == 'By Subscriber':
            if option == 'Last 7D':
                country = 'subs_7d'
            elif option == 'Last 28D':
                country = 'subs_30d'
            elif option == 'Last 3M':
                country = 'subs_3m'
        elif method == 'By Total Views':
            if option == 'Last 7D':
                country = 'views_7d'
            elif option == 'Last 28D':
                country = 'views_30d'
            elif option == 'Last 3M':
                country = 'views_3m'
        # username = request.args.get('username') or ''
        # cleaned_username = re.sub(r'[\\/:*?"<>|]', '_', username)
        # country = request.args.get('country') or ''
        print(country)
        data = find_and_load_json([country], function)
        print(data)
        return jsonify(data)

    elif function =='function3':
        user_id = request.args.get('userId')
        competitorUrl = request.args.get('competitorUrl')
        data = get_channel_info(user_id, competitorUrl)
        return jsonify(data)

    elif function =='function4':
        user_id = request.args.get('userId')
        group_name = request.args.get('groupName')
        keywordGroup = request.args.get('keywordGroup')
        timeRange = request.args.get('timeRange')
        viewRangeMin = request.args.get('viewRangeMin')
        viewRangeMax = request.args.get('viewRangeMax')
        data = phan_tich_chu_de(user_id, group_name, keywordGroup, timeRange, viewRangeMin,viewRangeMax)
        return jsonify(data)

    elif function == 'function5':
        user_id = request.args.get('userId')
        channelUrl = request.args.get('channelUrl')
        data = get_channel_module_5(user_id, channelUrl)
        return jsonify(data)
def add_country_to_json(country):
    """
    Thêm country mới vào file JSON
    Args:
        country (str): Tên nước cần thêm
    """
    config_file = 'config.json'
    
    # Đọc dữ liệu hiện tại từ file JSON
    try:
        with open(config_file, 'r', encoding='utf-8') as file:
            config_data = json.load(file)
    except FileNotFoundError:
        # Nếu file chưa tồn tại, tạo mới với cấu trúc mặc định
        config_data = {"countries": []}
    except json.JSONDecodeError:
        # Nếu file JSON bị lỗi format
        config_data = {"countries": []}
    
    # Kiểm tra xem countries key có tồn tại không
    if 'countries' not in config_data:
        config_data['countries'] = []
    
    # Thêm country mới nếu chưa tồn tại
    if country not in config_data['countries']:
        config_data['countries'].append(country)
        
        # Lưu lại vào file JSON
        with open(config_file, 'w', encoding='utf-8') as file:
            json.dump(config_data, file, indent=2, ensure_ascii=False)
        
        print(f"Added {country} to config.json file")
    else:
        print(f"{country} already exists in config.json file")

@app.route('/module1/function3/stop', methods=['GET'])
def stop_thread():
    thread_id = request.args.get('threadId')
    print(thread_id)
    if thread_id in stop_flags:
        stop_flags[thread_id].set()
        return jsonify({"status": "✅ Thread stopped", "threadId": thread_id})
    return jsonify({"status": "❌ Thread ID not found", "threadId": thread_id})

@app.route('/module1/function5/get', methods=['GET'])
def get_function5():
    channelUrl = request.args.get('channelUrl')
    
    if not channelUrl:
        return jsonify({"error": "channelUrl parameter is required"}), 400
    
    cleaned_url = re.sub(r'[\\/:*?"<>|]', '_', channelUrl)
    # Đường dẫn đến file JSON
    file_path = f'function5/{cleaned_url}.json'
    
    # Các trường dữ liệu cần lấy
    required_fields = [
        'production_platform',
        'content_structure', 
        'call_to_action',
        'thumbnail_style',
        'channel_status',
        'unique_selling_proposition',
        'awareness_level'
    ]
    
    # Khởi tạo kết quả với giá trị mặc định
    result = {field: "" for field in required_fields}
    
    try:
        # Kiểm tra xem file có tồn tại không
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                
                # Kiểm tra nếu data là array và có ít nhất 1 phần tử
                if isinstance(data, list) and len(data) > 0:
                    # Lấy phần tử đầu tiên trong array
                    first_item = data[0]
                    
                    # Lấy các trường dữ liệu cần thiết
                    for field in required_fields:
                        if field in first_item and first_item[field] is not None:
                            result[field] = first_item[field]
                
        return jsonify(result)
        
    except json.JSONDecodeError:
        # Nếu file JSON không hợp lệ
        return jsonify(result)
    except Exception as e:
        # Xử lý các lỗi khác
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

# @app.route('/module1/function5/post', methods=['POST'])
# def post_function5():
#     channelUrl = request.args.get('channelUrl')
    
#     if not channelUrl:
#         return jsonify({"error": "channelUrl parameter is required"}), 400
#     cleaned_url = re.sub(r'[\\/:*?"<>|]', '_', channelUrl)
#     # Lấy các tham số từ request
#     production_platform = request.args.get("production_platform")
#     content_structure = request.args.get("content_structure")
#     call_to_action = request.args.get("call_to_action")
#     thumbnail_style = request.args.get("thumbnail_style")
#     channel_status = request.args.get("channel_status")
#     unique_selling_proposition = request.args.get("unique_selling_proposition")
#     awareness_level = request.args.get("awareness_level")
    
#     # Đường dẫn đến file JSON
#     file_path = f'function5/{cleaned_url}.json'
    
#     try:
#         # Đọc dữ liệu hiện có (nếu file tồn tại)
#         existing_data = {}
#         if os.path.exists(file_path):
#             with open(file_path, 'r', encoding='utf-8') as file:
#                 existing_data = json.load(file)
        
#         # Cập nhật dữ liệu mới (chỉ cập nhật các trường có giá trị)
#         if production_platform is not None:
#             existing_data['production_platform'] = production_platform
#         if content_structure is not None:
#             existing_data['content_structure'] = content_structure
#         if call_to_action is not None:
#             existing_data['call_to_action'] = call_to_action
#         if thumbnail_style is not None:
#             existing_data['thumbnail_style'] = thumbnail_style
#         if channel_status is not None:
#             existing_data['channel_status'] = channel_status
#         if unique_selling_proposition is not None:
#             existing_data['unique_selling_proposition'] = unique_selling_proposition
#         if awareness_level is not None:
#             existing_data['awareness_level'] = awareness_level
        
#         # Lưu dữ liệu đã cập nhật vào file
#         with open(file_path, 'w', encoding='utf-8') as file:
#             json.dump(existing_data, file, ensure_ascii=False, indent=2)
        
#         return jsonify({
#                 "message": 'Function added successfully',
#                 })
        
#     except json.JSONDecodeError:
#         return jsonify({"error": "Invalid JSON file format"}), 500
#     except Exception as e:
#         return jsonify({"error": f"An error occurred: {str(e)}"}), 500

@app.route('/module1/fetch-data/', methods=['GET'])
def module1_data():
    function = request.args.get('function')
    username = request.args.get('username') or ''
    cleaned_username = re.sub(r'[\\/:*?"<>|]', '_', username)
    country = request.args.get('country') or ''
    data = find_and_load_json([cleaned_username,country], function)
    return jsonify(data)

if __name__ == '__main__':
    app.run(port=5030, host='0.0.0.0', debug=True)
