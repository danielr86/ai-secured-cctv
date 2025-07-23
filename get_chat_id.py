import requests

TOKEN = '8037950501:AAFZGTIhG6WKafogoblSvMOUYSFn0zACBJU'
url = f'https://api.telegram.org/bot{TOKEN}/getUpdates'

response = requests.get(url)
print(response.json())
