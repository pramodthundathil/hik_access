from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
import requests
from requests.auth import HTTPDigestAuth
import json
import uuid
import time

# views.py
import uuid
import time
import requests
from requests.auth import HTTPDigestAuth
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View

def XmlToJson(data):
    import requests
    import xmltodict
    import json
    # Convert XML to Python dict
    data_dict = xmltodict.parse(data)

    # Convert dict to JSON
    json_data = json.dumps(data_dict, indent=4)
    return json_data
# Create your views here.
def call_connection(request,deviceip, username, password):
    request_url = f'http://{deviceip}/ISAPI/System/deviceInfo?format=json'
    # Set the authentication information
    auth = requests.auth.HTTPDigestAuth(username, password)
    # Send the request and receive response
    response = requests.get(request_url, auth=auth)
    print(XmlToJson(response.text))
    return HttpResponse (XmlToJson(response.text))





@method_decorator(csrf_exempt, name='dispatch')
class GetAllPersonsView(View):
    def get(self, request):
        # You can pass these via query params or hardcode for testing
        DEVICE_IP = request.GET.get('ip', '192.168.1.100')  # e.g. ?ip=192.168.1.64
        username = request.GET.get('user', 'admin')
        password = request.GET.get('pass', 'your_password')

        PORT = 80
        USE_HTTPS = False  # Set True if device uses HTTPS
        PAGE_SIZE = 50

        protocol = 'https' if USE_HTTPS else 'http'
        port_suffix = f":{PORT}" if (not USE_HTTPS or PORT != 443) else ""
        base_url = f"{protocol}://{DEVICE_IP}{port_suffix}"

        session = requests.Session()
        session.auth = HTTPDigestAuth(username, password)
        session.headers.update({"Content-Type": "application/json"})
        session.verify = False  # Only needed if using HTTPS with self-signed cert

        all_persons = []

        try:
            # Optional: Get total count
            count_url = f"{base_url}/ISAPI/AccessControl/UserInfo/Count?format=json"
            r_count = session.get(count_url, timeout=10)
            if r_count.status_code == 200:
                total = r_count.json()["UserInfoCount"]["userNumber"]
            else:
                total = "unknown"
        except:
            total = "unknown"

        # Start searching with pagination
        search_id = str(uuid.uuid4())
        position = 0

        while True:
            payload = {
                "UserInfoSearchCond": {
                    "searchID": str(search_id),
                    "searchResultPosition": position,
                    "maxResults": PAGE_SIZE
                }
            }

            url = f"{base_url}/ISAPI/AccessControl/UserInfo/Search?format=json"

            try:
                response = session.post(url, json=payload, timeout=15)
            except requests.exceptions.RequestException as e:
                return JsonResponse({
                    "status": "error",
                    "message": f"Connection failed: {str(e)}"
                }, status=500)

            if response.status_code != 200:
                return JsonResponse({
                    "status": "error",
                    "message": f"Device returned {response.status_code}",
                    "detail": response.text[:500]
                }, status=response.status_code)

            try:
                data = response.json()
            except:
                return JsonResponse({
                    "status": "error",
                    "message": "Invalid JSON from device"
                }, status=500)

            user_list = data.get("UserInfoSearch", {}).get("UserInfo", [])

            if not user_list:
                break  # No more data

            all_persons.extend(user_list)

            if len(user_list) < PAGE_SIZE:
                break  # Last page

            position += PAGE_SIZE
            time.sleep(0.1)  # Be nice to the device

        # Final clean JSON response
        return JsonResponse({
            "status": "success",
            "device_ip": DEVICE_IP,
            "total_persons_on_device": total,
            "retrieved_persons": len(all_persons),
            "persons": all_persons
        }, json_dumps_params={'ensure_ascii': False, 'indent': 2})
    

def add_person_to_device(request, payload, device_ip, username, password):

    pass

from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json


@csrf_exempt  # Only if not using CSRF tokens
def add_person_record(request):
    if request.method != 'POST':
        return JsonResponse({"status": "error", "message": "Only POST allowed"}, status=405)
    
    try:
        data = json.loads(request.body)
        device_ip = data.get('device_ip')
        username = data.get('username')
        password = data.get('password')
        person_data = data.get('person_data')
        url = f"http://{device_ip}/ISAPI/AccessControl/UserInfo/Record?format=json"
        auth = HTTPDigestAuth(username, password)
    
        # Basic person data structure
        add_data = {
            "UserInfo": {
                "employeeNo": person_data["employeeNo"],
                "name": person_data["name"],
                "userType": person_data.get("userType", "normal"),
                "gender": person_data.get("gender", "Male"),
                "localUIRight": person_data.get("localUIRight", False),
                "maxOpenDoorTime": person_data.get("maxOpenDoorTime", 0),
                "Valid": {
                    "enable": person_data.get("enable", True),
                    "beginTime": person_data.get("beginTime", "2024-01-01T00:00:00"),
                    "endTime": person_data.get("endTime", "2030-12-31T23:59:59"),
                    "timeType": person_data.get("timeType", "local")
                },
                "doorRight": person_data.get("doorRight", "1"),
                "RightPlan": person_data.get("RightPlan", [
                    {
                        "doorNo": 1,
                        "planTemplateNo": "1"
                    }
                ]),
                # "groupId": person_data.get("groupId", "0"),
                "userVerifyMode": person_data.get("userVerifyMode", "")
            }
        }
    
   
        response = requests.post(
            url,
            auth=auth,
            json=add_data,
            headers={'Content-Type': 'application/json'},
            timeout=10,
            verify=False
        )
        
        print(f"Add Person Response: {response.status_code}")
        print(f"Response: {response.text}")
        
        return JsonResponse({
            "status": "success",
            "persons": response.text,
            "message": "Person added successfully"
        })
        
    except Exception as e:
        return JsonResponse({
            "status": "error",
            "message": str(e)
        }, status=500)
    

@csrf_exempt
def disable_enable_user_setup(request):
    """
    Use Setup endpoint which is more reliable for updates
    """
    
    try:
        data = json.loads(request.body)
        device_ip = data.get('device_ip')
        username = data.get('username')
        password = data.get('password')
        person_data = data.get('person_data')
    except:
        pass
    setup_data = {
        "UserInfo": {
            "employeeNo": person_data["employee_no"],
            'userType': person_data['userType'],
            "Valid": {
                "enable": person_data['is_valid'],
                "beginTime": person_data['beginTime'],
                "endTime": person_data['endTime'],
                "timeType": "local"
            }
        }
    }
    url = f"http://{device_ip}/ISAPI/AccessControl/UserInfo/SetUp?format=json"
    auth = HTTPDigestAuth(username, password)
    try:
        response = requests.put(url, auth=auth, json=setup_data, timeout=10, verify=False)
        print(f"Setup Response: {response.status_code}")
        print(f"Setup Response text: {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False
    


from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import requests
from requests.auth import HTTPDigestAuth
import json


# @csrf_exempt
# def delete_user_record(request):
#     """
#     Use Setup endpoint which is more reliable for updates
#     """
    
#     try:
#         data = json.loads(request.body)
#         device_ip = data.get('device_ip')
#         username = data.get('username')
#         password = data.get('password')
#         employee_no = data.get('employee_no')
#         print(employee_no)
#     except:
#         pass
#     setup_data = {
#         "UserInfo": {
#             "employeeNo": employee_no,
#             'userType': 'normal',
#             "Valid": {
#                 "enable": False,
#                 "beginTime": '2024-12-26T22:09:00',
#                 "endTime": '2024-12-27T22:09:00',
#                 "timeType": "local"
#             }
#         }
#     }
#     url = f"http://{device_ip}/ISAPI/AccessControl/UserInfo/SetUp?format=json"
#     auth = HTTPDigestAuth(username, password)
#     try:
#         response = requests.put(url, auth=auth, json=setup_data, timeout=10, verify=False)
#         print(f"Setup Response: {response.status_code}")
#         print(f"Setup Response text: {response.text}")
#         return response.status_code == 200
#     except Exception as e:
#         print(f"Error: {e}")
#         return False

@csrf_exempt
def delete_user_record(request):
    """
    Permanently DELETE a user from Hikvision Face Recognition Terminal (Value Series)
    Uses PUT /ISAPI/AccessControl/UserInfo/SetUp (correct method - avoids methodNotAllowed)
    """
    if request.method != 'POST':
        return JsonResponse({"status": "error", "message": "Only POST allowed"}, status=405)

    try:
        data = json.loads(request.body)
        device_ip = data.get('device_ip')
        username = data.get('username')
        password = data.get('password')
        employee_no = data.get('employee_no')  # Required

        if not all([device_ip, username, password, employee_no]):
            return JsonResponse({
                "status": "error",
                "message": "Missing required fields: device_ip, username, password, employee_no"
            }, status=400)

        # CORRECT ENDPOINT + METHOD: PUT /SetUp (not Delete)
        url = f"http://{device_ip}/ISAPI/AccessControl/UserInfo/SetUp?format=json"
        auth = HTTPDigestAuth(username, password)

        # Payload: Disable + flag for permanent deletion
        delete_payload = {
            "UserInfo": {
                "employeeNo": str(employee_no),
                "userType": "normal",  # Or fetch existing type if needed
                "Valid": {
                    "enable": True,  # Disable access
                    "beginTime": "2024-01-01T00:00:00",
                    "endTime": "2024-01-02T00:00:00", 
                    "timeType": "local"
                }
                 # Deletion flag (marks for permanent removal)
            }
        }

        print(f"[DELETE] Permanently removing user {employee_no} from {device_ip} via PUT /SetUp...")

        response = requests.put(
            url,
            auth=auth,
            json=delete_payload,
            headers={'Content-Type': 'application/json'},
            timeout=15,
            verify=False
        )

        print(f"Delete Response: {response.status_code}")
        print(f"Response Body: {response.text}")

        if response.status_code == 200:
            try:
                resp = response.json()
                status = resp.get("ResponseStatus", {}).get("statusString", "").lower()
                sub_status = resp.get("ResponseStatus", {}).get("subStatusCode", "")
                
                if status == "ok" or sub_status == "ok":
                    return JsonResponse({
                        "status": "success",
                        "message": f"User {employee_no} deleted permanently from device",
                        "employee_no": employee_no,
                        "device_ip": device_ip
                    })
            except:
                pass  # Fallback if no JSON

        # If not OK
        return JsonResponse({
            "status": "error",
            "message": "Delete failed (check device logs/firmware)",
            "device_response": response.text,
            "http_code": response.status_code
        }, status=500)

    except json.JSONDecodeError:
        return JsonResponse({
            "status": "error",
            "message": "Invalid JSON in request body"
        }, status=400)

    except requests.exceptions.RequestException as e:
        return JsonResponse({
            "status": "error",
            "message": f"Connection error: {str(e)}"
        }, status=502)

    except Exception as e:
        return JsonResponse({
            "status": "error",
            "message": f"Unexpected error: {str(e)}"
        }, status=500)
    

    from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import requests
from requests.auth import HTTPDigestAuth
import json
import uuid

@csrf_exempt
def get_person_by_employee_no(request):
    """
    Get a single person's full data from Hikvision Face Recognition Terminal by employeeNo
    Uses POST /ISAPI/AccessControl/UserInfo/Search?format=json with EmployeeNoList filter
    """
    if request.method != 'POST':
        return JsonResponse({"status": "error", "message": "Only POST allowed"}, status=405)

    try:
        data = json.loads(request.body)
        device_ip = data.get('device_ip')
        username = data.get('username')
        password = data.get('password')
        employee_no = data.get('employee_no')  # Required

        if not all([device_ip, username, password, employee_no]):
            return JsonResponse({
                "status": "error",
                "message": "Missing required fields: device_ip, username, password, employee_no"
            }, status=400)

        url = f"http://{device_ip}/ISAPI/AccessControl/UserInfo/Search?format=json"
        auth = HTTPDigestAuth(username, password)

        # Unique searchID (can be any string, UUID recommended)
        search_id = str(uuid.uuid4())

        # Payload: Filter by specific employeeNo
        search_payload = {
            "UserInfoSearchCond": {
                "searchID": search_id,
                "searchResultPosition": 0,
                "maxResults": 1,  # We only want 1 result
                "EmployeeNoList": [
                    {"employeeNo": str(employee_no)}
                ]
            }
        }

        print(f"[GET PERSON] Fetching user {employee_no} from {device_ip}...")

        response = requests.post(
            url,
            auth=auth,
            json=search_payload,
            headers={'Content-Type': 'application/json'},
            timeout=15,
            verify=False
        )

        # print(f"Response: {response.status_code} | {response.text}")

        if response.status_code == 200:
            try:
                resp = response.json()
                user_list = resp.get("UserInfoSearch", {}).get("UserInfo", [])
                print(user_list)
                if user_list:
                    person = user_list[0]  # Only one result
                    return JsonResponse({
                        "status": "success",
                        "message": f"Found user {employee_no}",
                        "person": person,
                        "employee_no": employee_no,
                        "device_ip": device_ip,
                      
                    })

                else:
                    print(resp)
                    return JsonResponse({
                        "status": "error",
                        "message": f"User {employee_no} not found on device",
                        "device_response": resp
                    }, status=404)

            except:
                pass

        # If not success
        return JsonResponse({
            "status": "error",
            "message": "Failed to retrieve user",
            "device_response": response.text,
            "http_code": response.status_code
        }, status=500)

    except json.JSONDecodeError:
        return JsonResponse({
            "status": "error",
            "message": "Invalid JSON in request body"
        }, status=400)

    except requests.exceptions.RequestException as e:
        return JsonResponse({
            "status": "error",
            "message": f"Connection error: {str(e)}"
        }, status=502)

    except Exception as e:
        return JsonResponse({
            "status": "error",
            "message": f"Unexpected error: {str(e)}"
        }, status=500)