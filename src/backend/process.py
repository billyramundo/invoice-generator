import requests
import json
from requests.exceptions import HTTPError, Timeout, RequestException
import pdf_util as pdf_util

input_pdf = 'sales-invoice.pdf'
output_pdf = 'completed-sales-invoice.pdf'

def post_request(uuid: str):
    post_url = "https://garage-backend.onrender.com/getListing"
    data = {
        'id': uuid
    }
    headers = {
        'Content-Type': 'application/json'
    }
    try:
        response = requests.post(post_url, data=json.dumps(data), headers=headers)
        return response.json()['result']['listing']
    except HTTPError as http_err:
        print(f"HTTP error occurred during POST Request to Garage API: {http_err}")
        raise http_err
    except Timeout as timeout_err:
        print(f"Timeout error occurred during POST Request to Garage API: {timeout_err}")
        raise timeout_err
    except RequestException as req_err:
        print(f"Request error occurred during POST Request to Garage API: {req_err}")
        raise req_err
    except ValueError as json_err:
        print(f"JSON decoding error during POST Request to Garage API: {json_err}")
        raise json_err
    except Exception as err:
        print(f"An error occurred during POST Request to Garage API: {err}")
        raise err
    

def get_details(form_data: dict):
    url_list = form_data.get('url').split('listing/')
    if len(url_list) != 2 :
        raise RequestException("Not a valid Garage Listing URL")
    uuid = url_list[1]
    data_dict = post_request(uuid)
    if not data_dict:
        raise RequestException("Unique ID in URL does not match an existing Garage Listing")
    data_dict.update(form_data)
    return pdf_util.update_pdf(input_pdf, output_pdf, data_dict)

