import requests

post_text = "not important"

response = requests.post("http://127.0.0.1:8000/", json=post_text)

print(response.text)
