import ast
import json
import re

from flask import Flask, request, jsonify
import pandas as pd
from datetime import datetime
import subprocess
import csv
import csv
import pandas as pd
import re
import ast
import subprocess
from datetime import datetime
from flask import Flask, request, jsonify

app = Flask(__name__)


def encode_age_gender_2(row):
    code = 0
    if row['age'] <= 25 and row['gender'] == 0:
        code = 1
    elif row['age'] <= 25 and row['gender'] == 1:
        code = 2
    elif row['age'] >= 26 and row['age'] <= 30 and row['gender'] == 0:
        code = 3
    elif row['age'] >= 26 and row['age'] <= 30 and row['gender'] == 1:
        code = 4
    elif row['age'] >= 31 and row['age'] <= 35 and row['gender'] == 0:
        code = 5
    elif row['age'] >= 31 and row['age'] <= 35 and row['gender'] == 1:
        code = 6
    elif row['age'] >= 36 and row['age'] <= 40 and row['gender'] == 0:
        code = 7
    elif row['age'] >= 36 and row['age'] <= 40 and row['gender'] == 1:
        code = 8
    elif row['age'] >= 41 and row['age'] <= 45 and row['gender'] == 0:
        code = 9
    elif row['age'] >= 41 and row['age'] <= 45 and row['gender'] == 1:
        code = 10
    elif row['age'] >= 46 and row['age'] <= 50 and row['gender'] == 0:
        code = 11
    elif row['age'] >= 46 and row['age'] <= 50 and row['gender'] == 1:
        code = 12
    elif row['age'] >= 51 and row['age'] <= 55 and row['gender'] == 0:
        code = 13
    elif row['age'] >= 51 and row['age'] <= 55 and row['gender'] == 1:
        code = 14
    elif row['age'] >= 56 and row['age'] <= 60 and row['gender'] == 0:
        code = 15
    elif row['age'] >= 56 and row['age'] <= 60 and row['gender'] == 1:
        code = 16
    elif row['age'] >= 61 and row['age'] <= 65 and row['gender'] == 0:
        code = 17
    elif row['age'] >= 61 and row['age'] <= 65 and row['gender'] == 1:
        code = 18
    elif row['age'] >= 66 and row['age'] <= 70 and row['gender'] == 0:
        code = 19
    elif row['age'] >= 66 and row['age'] <= 70 and row['gender'] == 1:
        code = 20
    rental_time = row['rental_time_range']
    rental_time = int(rental_time)  # rental_time을 정수로 변환

    if 1 <= rental_time <= 24:
        code += 0
    elif 25 <= rental_time <= 48:
        code += 20
    elif 49 <= rental_time <= 72:
        code += 40
    elif 73 <= rental_time <= 96:
        code += 60
    elif 97 <= rental_time <= 120:
        code += 80
    elif rental_time >= 121:
        code += 100

    return code


# CSV 파일에서 차량 ID에 해당하는 모든 차량 이름을 가져오는 함수
def get_car_names_from_id(car_id, csv_file='product_mapping.csv'):
    car_names = []
    with open(csv_file, 'r', encoding='utf-8') as file:
        reader = csv.reader(file)
        for row in reader:
            if str(car_id) == row[0]:  # 첫 번째 열이 ID로 가정
                car_names.append(row[1])  # 두 번째 열이 차량 이름으로 가정
    return car_names


# 차량 이름에서 수용 인원을 추출하는 함수
def get_car_capacity(car_name):
    match = re.search(r'(\d+)인', car_name)
    return int(match.group(1)) if match else 5  # "X인" 정보가 없으면 5인으로 간주


def filter_cars_by_capacity(cars_data, people):
    suitable_cars = []
    for car in cars_data:
        # 차량 이름 중 people 수 이상의 인원을 수용할 수 있는 이름만 필터링
        suitable_names = [name for name in car['names'] if get_car_capacity(name) >= int(people)]

        # 적합한 이름이 하나라도 있는 경우에만 차량 추가
        if suitable_names:
            suitable_cars.append({'id': car['id'], 'names': suitable_names})

    return suitable_cars


@app.route('/rental_info', methods=['POST'])
def rental_info():
    try:
        age = request.json['age']
        gender = request.json['gender']
        start_period = request.json['start_period']
        end_period = request.json['end_period']
        people = request.json['people']
        view = request.json['view']

        print(
            f"age: {age}, gender: {gender}, start_period: {start_period}, end_period: {end_period}, people: {people}, view: {view}")

        # 나이와 성별 처리
        age = int(age)
        view = int(view)
        gender = 0 if gender == "Male" else 1

        start_dt = datetime.strptime(start_period, '%Y/%m/%d')
        end_dt = datetime.strptime(end_period, '%Y/%m/%d')
        time_range = (end_dt - start_dt).total_seconds() / 3600

        # 데이터프레임 생성 및 코드 인코딩
        df = pd.DataFrame({
            'age': [age],
            'gender': [gender],
            'rental_time_range': [time_range]
        })
        df['code'] = df.apply(encode_age_gender_2, axis=1)  # 가정: 이 함수가 정의되어 있음

        # encode_age_gender_2 함수에 전달되는 데이터프레임 로그 출력
        print(f"encode_age_gender_2 함수에 전달되는 데이터프레임:\n {df}")

        # 인코딩된 'code' 로그 출력
        encoded_code = df['code'].values[0]
        print(f"인코딩된 'code': {encoded_code}")

        send_code = str(df['code'].values[0])
        combined_data = f"{send_code},{view}"

        print(f"모델로 전달되는 데이터: {combined_data}")

        # 모델 실행
        background_result = subprocess.run(
            ["python", "model.py"],
            input=combined_data,
            capture_output=True,
            text=True,
            check=True,
        )

        # 모델 출력 처리
        final_result = background_result.stdout.split("\n")
        item_recommend_count_str = final_result[2]

        # 차량 ID 목록 파싱
        dict_str = item_recommend_count_str.split(", ", 1)[1].rsplit(")", 1)[0]
        car_ids_dict = ast.literal_eval(dict_str)
        car_ids = car_ids_dict[next(iter(car_ids_dict))]

        # 차량 이름 가져오기 및 필터링
        cars_data = []
        for car_id in car_ids:
            names = get_car_names_from_id(str(car_id))
            car_data = {
                "id": car_id,
                "names": names
            }
            cars_data.append(car_data)

        # 필터링 전 차량 정보 로그 출력 (ID 별로 그룹화)
        print("\n필터링 전 차량 정보:")
        car_info_pre_filter = {}
        for car in cars_data:
            car_id = car['id']
            car_info_pre_filter.setdefault(car_id, set()).update(car['names'])
        for car_id, names in car_info_pre_filter.items():
            print(f"ID {car_id}: {', '.join(names)}")

        # 인원 수에 맞는 차량 필터링
        cars_data = filter_cars_by_capacity(cars_data, people)

        # 필터링 후 차량 정보 로그 출력 (ID 별로 그룹화)
        print("\n필터링 후 차량 정보:")
        car_info_post_filter = {}
        for car in cars_data:
            car_id = car['id']
            car_info_post_filter.setdefault(car_id, set()).update(car['names'])
        for car_id, names in car_info_post_filter.items():
            print(f"ID {car_id}: {', '.join(names)}")

        # 적합한 차량이 없을 경우 모델 재실행
        if not cars_data:
            view = 15
            combined_data = f"{send_code},{view}"
            # 모델 실행
            print(f"모델로 전달되는 데이터: {combined_data}")

            background_result = subprocess.run(
                ["python", "model.py"],
                input=combined_data,
                capture_output=True,
                text=True,
                check=True,
            )
            # 모델 출력 처리
            final_result = background_result.stdout.split("\n")
            item_recommend_count_str = final_result[2]

            # 차량 ID 목록 파싱
            dict_str = item_recommend_count_str.split(", ", 1)[1].rsplit(")", 1)[0]
            car_ids_dict = ast.literal_eval(dict_str)
            car_ids = car_ids_dict[next(iter(car_ids_dict))]

            # 차량 이름 가져오기 및 필터링
            cars_data = []
            for car_id in car_ids:
                names = get_car_names_from_id(str(car_id))
                car_data = {
                    "id": car_id,
                    "names": names
                }
                cars_data.append(car_data)

            # 필터링 전 차량 정보 로그 출력 (ID 별로 그룹화)
            print("\n재실행 후 필터링 전 차량 정보:")
            car_info_pre_filter = {}
            for car in cars_data:
                car_id = car['id']
                car_info_pre_filter.setdefault(car_id, set()).update(car['names'])
            for car_id, names in car_info_pre_filter.items():
                print(f"ID {car_id}: {', '.join(names)}")

            # 인원 수에 맞는 차량 필터링
            cars_data = filter_cars_by_capacity(cars_data, people)

            print("\n재실행 후 필터링 차량 정보:")
            car_info_after_rerun = {}
            for car in cars_data:
                car_id = car['id']
                car_info_after_rerun.setdefault(car_id, set()).update(car['names'])
            for car_id, names in car_info_after_rerun.items():
                print(f"ID {car_id}: {', '.join(names)}")




        response = {
            "status": "success",
            "cars": cars_data
        }
        return jsonify(response), 200

    except Exception as e:
        print(f"error: {e}")
        return jsonify({"status": "fail"}), 400


# 0.메소드 방식은 post
# 1.모델불러오기
# 2.agegender onehotencoding하기
# 3.onehotencoding한것을 다시 edge형태로 바꾸기
# 4.모델에 삽입
# 5.결과 불러오기
# 6.결과를 차량데이터 csv파일에서 id로 매칭하기.


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
